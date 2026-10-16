"""Etapa 3 — testes das análises SQL.

Quatro camadas:
  1. REAL     : cada análise é recalculada por um oráculo independente (pandas / Python puro) a partir dos CSVs.
  2. INJETADO : cenários pequenos, com números calculados À MÃO, num mart miniatura (tests/mini_mart.py).
  3. MUTAÇÃO  : o SQL é adulterado de propósito; o oráculo precisa PASSAR no original e FALHAR no adulterado.
  4. PROCESSO : determinismo (hash do CSV), CSVs de origem intactos, cabeçalhos documentados, rótulos obrigatórios.
"""
import hashlib
import shutil
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import mini_mart
import oraculos as O
from empresax.consultas import executar_arquivo, executar_todas, para_csv

RAIZ = Path(__file__).resolve().parent.parent
ANALISE = RAIZ / "sql" / "analise"
DATA = RAIZ / "data"


def norm(df):
    """Datas do DuckDB -> texto ISO (mesmo formato dos CSVs / oráculos)."""
    import datetime as dt
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
        elif df[c].dtype == object and df[c].dropna().map(lambda x: isinstance(x, dt.date)).all() and df[c].notna().any():
            df[c] = df[c].map(lambda x: x.isoformat() if x is not None and x == x else None)
    return df


def rodar(con, arquivo, cfg, pasta=ANALISE):
    """Executa um arquivo de análise e devolve {nome_do_bloco: DataFrame}."""
    return {r.nome: norm(r.df) for r in executar_arquivo(con, pasta / (arquivo), cfg or None_cfg())}


@pytest.fixture(scope="module")
def cfg(etl, tmp_path_factory):
    return replace(etl["cfg"], pasta_consultas_saida=tmp_path_factory.mktemp("consultas"))


@pytest.fixture(scope="module")
def R(etl, cfg):
    """Todos os resultados da execução padrão, por nome."""
    out = {}
    for r in executar_todas(cfg, con=etl["con"]):
        r.df = norm(r.df)
        out[r.nome] = r
    return out


# =============================================================== 1. REAL — oráculos independentes
def test_21_resultados_gerados(R):
    assert len(R) == 21 and all(len(r.df) > 0 for r in R.values())


def test_01_faturamento(R, csv_):
    O.o_01a(R["01a_faturamento_mensal"].df, csv_)
    O.o_01b(R["01b_faturamento_anual_ytd"].df, csv_)


def test_01_reconciliacao_registrada_igual_entregues_mais_devolucoes(R):
    d = R["01a_faturamento_mensal"].df
    assert (d.receita_registrada - d.vendas_entregues - d.devolucoes).abs().max() < 0.01
    assert (d.receita_ajustada - d.vendas_entregues).abs().max() < 0.01


def test_01_nao_ha_meses_futuros(R):
    assert R["01a_faturamento_mensal"].df.mes.max() == "2026-09-01"
    assert len(R["01a_faturamento_mensal"].df) == 33


def test_01_2026_so_compara_com_meses_equivalentes(R, csv_):
    b = R["01b_faturamento_anual_ytd"].df
    assert list(b.periodo_ytd_comparado) == ["jan a 09"] * 3 and list(b.meses_realizados_no_ano) == [12, 12, 9]


def test_02_ranking_e_curva_abc(R, csv_):
    O.o_02a(R["02a_ranking_produtos_receita"].df, csv_)
    c = R["02b_receita_por_categoria"].df
    assert abs(c.participacao_pct.sum() - 1) < 1e-6
    v = O.vendas(csv_).merge(csv_["dim_produto"][["id_produto", "categoria"]], on="id_produto")
    O._near(c.set_index("categoria").receita_ajustada.sort_index(), v.groupby("categoria").ent.sum().sort_index())


@pytest.mark.parametrize("piso", [0, 200, 1500])
def test_03_margem_com_piso_configuravel(etl, cfg, csv_, piso):
    r = rodar(etl["con"], "03_margem_produtos.sql", replace(cfg, piso_linhas_margem=piso))
    O.o_03a(r["03a_margem_por_produto"], csv_, piso)
    linhas = O.vendas(csv_).query("status=='Entregue'").groupby("id_produto").size().reindex(csv_["dim_produto"].id_produto, fill_value=0)
    s = r["03b_filtro_piso_resumo"].iloc[0]
    assert s.produtos_no_cadastro == 39 and s.produtos_incluidos == (linhas >= piso).sum()
    assert s.produtos_incluidos + s.produtos_excluidos_pelo_piso == 39


def test_03_piso_1500_realmente_exclui_alguem(etl, cfg):
    r = rodar(etl["con"], "03_margem_produtos.sql", replace(cfg, piso_linhas_margem=1500))
    assert 0 < len(r["03a_margem_por_produto"]) < 39


def test_04_despesas_por_filial(R, csv_):
    O.o_04a(R["04a_despesas_por_filial"].df, csv_)
    g = R["04b_despesas_filial_por_grupo"].df
    por_filial = g.groupby("id_filial").despesas.sum()
    O._near(por_filial.sort_index(), csv_["fact_despesas"].groupby("id_filial").valor.sum().sort_index())
    assert abs(g.participacao_no_total_pct.sum() - 1) < 1e-5


def test_05_resultado_operacional(R, csv_):
    O.o_05a(R["05a_resultado_operacional_mensal"].df, csv_)
    b = R["05b_resultado_anual_ytd"].df
    assert b.rotulo.str.contains("nao e lucro liquido contabil").all() and list(b.meses_no_ytd) == [9, 9, 9]


def test_06_orcado_realizado(R, csv_):
    O.o_06c(R["06c_leitura_ingenua_vs_correta"].df, csv_)
    a = R["06a_orcado_realizado_departamento_ytd"].df
    o, e = csv_["fact_orcamento"], csv_["fact_despesas"]
    o26 = o[(o.mes >= "2026-01-01") & (o.mes <= "2026-09-01")].valor_orcado.sum()
    e26 = e[e.data >= "2026-01-01"].valor.sum()
    assert abs(a.orcamento_acumulado.sum() - o26) < 0.01 and abs(a.realizado_acumulado.sum() - e26) < 0.01
    b = R["06b_orcado_realizado_categoria_ytd"].df
    assert abs(b.orcado_ytd.sum() - o26) < 0.01 and abs(b.realizado_ytd.sum() - e26) < 0.01
    assert (a.orcamento_anual >= a.orcamento_acumulado).all()


def _oraculo_07(csv_, nivel, lim_mom, lim_yoy):
    v = O.vendas(csv_); ms = O.meses(csv_)
    if nivel == "empresa":
        s = {0: v.groupby("mes").ent.sum()}
    else:
        col = "id_filial" if nivel == "filial" else "id_produto"
        dim = csv_["dim_filial" if nivel == "filial" else "dim_produto"][col]
        g = v.groupby([col, "mes"]).ent.sum()
        s = {k: g.xs(k, level=0) if k in g.index.get_level_values(0) else pd.Series(dtype=float) for k in dim}
    out = {"MoM": [0, 0, 0], "YoY": [0, 0, 0]}
    for ser in s.values():
        x = ser.reindex(ms, fill_value=0.0).values
        for i in range(len(x)):
            for lag, lim, k in ((1, lim_mom, "MoM"), (12, lim_yoy, "YoY")):
                st, p = O.status_e_pct(x[i], x[i - lag] if i >= lag else None)
                if st != "comparavel": out[k][2] += 1
                elif p <= lim: out[k][0] += 1
                else: out[k][1] += 1
    return out


def test_07_quedas_todos_os_niveis(R, cfg, csv_):
    O.o_07a(R["07a_quedas_empresa"].df, csv_, cfg.limiar_queda_mom, cfg.limiar_queda_yoy)
    d = R["07d_resumo_quedas_por_nivel"].df
    for nivel in ("empresa", "filial", "produto"):
        esp = _oraculo_07(csv_, nivel, cfg.limiar_queda_mom, cfg.limiar_queda_yoy)
        for comp in ("MoM", "YoY"):
            r = d[(d.nivel == nivel) & (d.comparacao == comp)].iloc[0]
            assert [r.quedas_relevantes, r.sem_queda_relevante, r.nao_comparaveis] == esp[comp], (nivel, comp)
    # as listas detalhadas batem com as contagens do resumo
    assert len(R["07c_quedas_produto_yoy"].df) == d[(d.nivel == "produto") & (d.comparacao == "YoY")].quedas_relevantes.iloc[0]
    assert (R["07c_quedas_produto_yoy"].df.variacao_yoy_pct <= cfg.limiar_queda_yoy).all()


def test_07_limiares_sao_configuraveis(etl, cfg, csv_):
    r = rodar(etl["con"], "07_quedas.sql", replace(cfg, limiar_queda_mom=-0.30, limiar_queda_yoy=-0.05))
    O.o_07a(r["07a_quedas_empresa"], csv_, -0.30, -0.05)
    assert (r["07a_quedas_empresa"].classificacao_mom == "queda_relevante").sum() < 4   # com -15% eram 4


def test_07_periodos_sem_base_nao_viram_crescimento_nem_zero(R):
    e = R["07a_quedas_empresa"].df
    assert e.variacao_mom_pct.iloc[0] != e.variacao_mom_pct.iloc[0]                     # NaN
    assert (e.classificacao_mom.iloc[0], e.classificacao_yoy.iloc[:12].unique().tolist()) == ("sem_base", ["sem_base"])


def test_08_decomposicao_fecha_com_oraculo_python_puro(R, csv_):
    O.o_08a(R["08a_decomposicao_total"].df, csv_)


def test_08_verificacao_e_produto(R):
    v = R["08d_decomposicao_verificacao"].df
    assert v.maior_residuo_por_produto.max() < 0.01
    assert list(v.comparacoes_validas) == [32, 21]
    c = R["08c_decomposicao_produto_ultimo_mes"].df
    assert c.residuo_produto.abs().max() < 0.01 and (c.periodo == "2026-09-01").all()


def test_08b_contribuicoes_somam_a_variacao(R):
    b = R["08b_contribuicao_por_dimensao"].df
    s = b.groupby(["tipo_comparacao", "periodo", "dimensao"]).agg(c=("contribuicao", "sum"), t=("variacao_total", "first"))
    assert (s.c - s.t).abs().max() < 0.01
    p = b.dropna(subset=["participacao_na_variacao"]).groupby(["tipo_comparacao", "periodo", "dimensao"]).participacao_na_variacao.sum()
    assert (p - 1).abs().max() < 1e-6


def test_08_variacao_ajustada_bate_com_serie_01(R):
    a, m = R["08a_decomposicao_total"].df, R["01a_faturamento_mensal"].df.set_index("mes")
    x = a[(a.tipo_comparacao == "MoM") & (a.status_base == "comparavel")]
    esp = (m.receita_ajustada - m.receita_ajustada.shift(1)).reindex(x.periodo)
    O._near(x.variacao_receita_ajustada.values, esp.values)


# =============================================================== 2. INJETADO — números calculados à mão
M0, M1 = "2025-01-01", "2025-02-01"
MESES = [M0, M1]


def venda(mes, prod, q, bruta, **kw):
    return dict(mes=mes, prod=prod, q=q, bruta=bruta, **kw)


def pvm_mini(vendas, **kw):
    con = mini_mart.criar(vendas, kw.pop("meses", MESES), kw.pop("ultimo", M1), **kw)
    return con, rodar(con, "08_fatores_variacao.sql", None_cfg())["08a_decomposicao_total"]


def None_cfg():
    from empresax.config import Config
    return Config()


def mom(df):
    return df[df.tipo_comparacao == "MoM"].set_index("periodo").loc[M1]


def efeitos(r):
    return {k: round(float(r[f"efeito_{k}"]), 4) for k in ("volume", "mix", "preco", "desconto", "impostos", "produto_novo", "produto_descontinuado")}


def test_inj_so_preco():
    # A: 10 un. a R$100 -> 10 un. a R$110. Só o preço mudou: efeito = 10 x 10 = 100.
    _, d = pvm_mini([venda(M0, 1, 10, 1000), venda(M1, 1, 10, 1100)])
    r = mom(d)
    assert efeitos(r) == dict(volume=0, mix=0, preco=100, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)
    assert r.variacao_registrada == 100 and abs(r.residuo_registrada) < 1e-9


def test_inj_so_volume():
    # A 10@100 e B 10@50 (R$1.500) -> o dobro de cada: volume = +1.500, mix zero.
    v = [venda(M0, 1, 10, 1000), venda(M0, 2, 10, 500), venda(M1, 1, 20, 2000), venda(M1, 2, 20, 1000)]
    _, d = pvm_mini(v)
    assert efeitos(mom(d)) == dict(volume=1500, mix=0, preco=0, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)


def test_inj_so_mix():
    # Total de unidades fixo (20): A (R$100) 10->15 e B (R$50) 10->5. Mix = +5x100 -5x50 = +250; volume = 0.
    v = [venda(M0, 1, 10, 1000), venda(M0, 2, 10, 500), venda(M1, 1, 15, 1500), venda(M1, 2, 5, 250)]
    _, d = pvm_mini(v)
    r = mom(d)
    assert efeitos(r) == dict(volume=0, mix=250, preco=0, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)
    assert r.variacao_registrada == 250


def test_inj_preco_e_mix_juntos_sao_atribuidos_separadamente():
    # Mesmo mix acima, mas A também sobe de R$100 para R$110: preço = 15 x 10 = 150 (SÓ de A), mix = 250. Total = 400.
    v = [venda(M0, 1, 10, 1000), venda(M0, 2, 10, 500), venda(M1, 1, 15, 1650), venda(M1, 2, 5, 250)]
    con, d = pvm_mini(v)
    r = mom(d)
    assert efeitos(r) == dict(volume=0, mix=250, preco=150, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)
    assert r.variacao_registrada == 400
    por_prod = con.execute("SELECT id_produto, efeito_preco, efeito_mix FROM analise_pvm_produto WHERE tipo_comparacao='MoM' AND periodo=? ORDER BY 1", [M1]).fetchall()
    assert [(p, round(a, 4), round(b, 4)) for p, a, b in por_prod] == [(1, 150.0, 500.0), (2, 0.0, -250.0)]   # B não tem efeito-preço


def test_inj_desconto():
    # A 10 un. a R$100; desconto 10% -> 20%; imposto 10% do valor após desconto. R$810 -> R$720: efeito desconto = -1000 x 0,10 x 0,90 = -90.
    v = [venda(M0, 1, 10, 1000, desc=100, imp=90), venda(M1, 1, 10, 1000, desc=200, imp=80)]
    _, d = pvm_mini(v)
    r = mom(d)
    assert efeitos(r) == dict(volume=0, mix=0, preco=0, desconto=-90, impostos=0, produto_novo=0, produto_descontinuado=0)
    assert r.variacao_registrada == -90


def test_inj_imposto():
    # Sem desconto, imposto de 10% -> 12% sobre R$1.000: R$900 -> R$880. Efeito imposto = -1000 x 1 x 0,02 = -20.
    _, d = pvm_mini([venda(M0, 1, 10, 1000, imp=100), venda(M1, 1, 10, 1000, imp=120)])
    assert efeitos(mom(d)) == dict(volume=0, mix=0, preco=0, desconto=0, impostos=-20, produto_novo=0, produto_descontinuado=0)


def test_inj_produto_novo_descontinuado_e_sem_vendas():
    prods = ((1, "A", "Cat"), (2, "B", "Cat"), (3, "C", "Cat"))
    # A estável; B existe só em jan (descontinuado: -500); C só em fev (novo: +300); (nenhum produto fica sem entrada)
    v = [venda(M0, 1, 10, 1000), venda(M0, 2, 10, 500), venda(M1, 1, 10, 1000), venda(M1, 3, 6, 300)]
    con, d = pvm_mini(v, produtos=prods + ((4, "D", "Cat"),))        # D nunca vendeu
    r = mom(d)
    assert efeitos(r) == dict(volume=0, mix=0, preco=0, desconto=0, impostos=0, produto_novo=300, produto_descontinuado=-500)
    assert r.variacao_registrada == -200 and abs(r.residuo_registrada) < 1e-9
    cls = dict(con.execute("SELECT id_produto, classe_produto FROM analise_pvm_produto WHERE tipo_comparacao='MoM' AND periodo=?", [M1]).fetchall())
    assert cls == {1: "continuante", 2: "descontinuado", 3: "novo", 4: "sem_vendas"}
    assert (r.produtos_novos, r.produtos_descontinuados) == (1, 1)


def test_inj_base_zerada_nao_vira_crescimento():
    # Janeiro existe no calendário mas sem nenhuma venda; fevereiro vende. A base é zero: sem percentual, tudo é "produto novo".
    con, d = pvm_mini([venda(M1, 1, 10, 1000)])
    r = mom(d)
    assert r.status_base == "base_zerada" and pd.isna(r.variacao_receita_ajustada_pct)
    assert r.efeito_produto_novo == 1000 and abs(r.residuo_registrada) < 1e-9
    q = rodar(con, "07_quedas.sql", None_cfg())["07a_quedas_empresa"].set_index("mes")
    assert q.loc[M1, "classificacao_mom"] == "base_zerada" and pd.isna(q.loc[M1, "variacao_mom_pct"])


def test_inj_sem_base_no_inicio_da_serie():
    _, d = pvm_mini([venda(M0, 1, 10, 1000), venda(M1, 1, 10, 1100)])
    r = d[(d.tipo_comparacao == "MoM") & (d.periodo == M0)].iloc[0]
    assert r.status_base == "sem_base" and pd.isna(r.efeito_volume) and pd.isna(r.variacao_receita_ajustada_pct)
    y = d[(d.tipo_comparacao == "YoY")]
    assert (y.status_base == "sem_base").all()                                       # 12 meses atrás não existe no calendário


def test_inj_devolucao_leva_da_registrada_para_a_ajustada():
    # Fev: mesmas 10 un. entregues + 5 un. devolvidas (R$500). Registrada +500 (volume), devoluções -500, ajustada 0.
    v = [venda(M0, 1, 10, 1000), venda(M1, 1, 10, 1000), venda(M1, 1, 5, 500, status="Devolvido")]
    _, d = pvm_mini(v)
    r = mom(d)
    assert r.variacao_registrada == 500 and r.efeito_volume == 500
    assert r.efeito_devolucoes == -500 and r.variacao_receita_ajustada == 0 and abs(r.residuo_ajustada) < 1e-9


def test_inj_participacao_nula_quando_variacao_total_zera():
    # Filial 1 +100 e filial 2 -100: variação total 0. A participação (÷ 0) tem de ser NULL, nunca inf nem erro.
    fil = ((1, "F1", "Filial"), (2, "F2", "Filial"))
    v = [venda(M0, 1, 10, 1000, filial=1), venda(M0, 1, 10, 1000, filial=2),
         venda(M1, 1, 10, 1100, filial=1), venda(M1, 1, 10, 900, filial=2)]
    con = mini_mart.criar(v, MESES, M1, filiais=fil)
    b = rodar(con, "08_fatores_variacao.sql", None_cfg())["08b_contribuicao_por_dimensao"]
    f = b[(b.tipo_comparacao == "MoM") & (b.periodo == M1) & (b.dimensao == "filial")].sort_values("chave")
    assert list(f.contribuicao) == [100, -100] and (f.variacao_total == 0).all() and f.participacao_na_variacao.isna().all()


def test_inj_produto_ausente_em_um_periodo_no_yoy_e_no_ranking_de_margem():
    # 13 meses; A vende em todos, B só no 1º mês (jan/24). Em jan/25 B está ausente: YoY base>0, atual=0 => -100% (queda relevante).
    ms = [f"2024-{m:02d}-01" for m in range(1, 13)] + ["2025-01-01"]
    v = [venda(m, 1, 10, 1000) for m in ms] + [venda(ms[0], 2, 4, 200)]
    con = mini_mart.criar(v, ms, ms[-1])
    cfg0 = replace(None_cfg(), piso_linhas_margem=0)
    q = rodar(con, "07_quedas.sql", cfg0)
    b = q["07c_quedas_produto_yoy"]
    assert list(b.produto) == ["B"] and b.variacao_yoy_pct.iloc[0] == -1.0 and b.queda_yoy_em_reais.iloc[0] == 200
    # produto sem vendas nenhuma + piso 0: entra no ranking de margem com margem NULA, por último
    con2 = mini_mart.criar(v, ms, ms[-1], produtos=((1, "A", "Cat"), (2, "B", "Cat"), (3, "Z", "Cat")))
    m = rodar(con2, "03_margem_produtos.sql", cfg0)["03a_margem_por_produto"]
    assert list(m.produto)[-1] == "Z" and pd.isna(m.margem_bruta_ajustada_pct.iloc[-1])
    m2 = rodar(con2, "03_margem_produtos.sql", replace(cfg0, piso_linhas_margem=200))["03a_margem_por_produto"]
    assert len(m2) == 0                                                          # piso 200: ninguém tem 13 linhas
    assert rodar(con2, "03_margem_produtos.sql", replace(cfg0, piso_linhas_margem=200))["03b_filtro_piso_resumo"].produtos_excluidos_pelo_piso.iloc[0] == 3


def test_inj_filial_antes_de_abrir_e_sem_atividade():
    # Filial 2 só vende em fev: fev é 'base_zerada' (nem queda nem crescimento); jan é 'sem_base'; filial 1 é comparável.
    fil = ((1, "F1", "Filial"), (2, "F2", "Filial"))
    ms = ["2025-01-01", "2025-02-01", "2025-03-01"]
    v = [venda(m, 1, 10, 1000, filial=1) for m in ms] + [venda(ms[1], 1, 10, 500, filial=2)]
    con = mini_mart.criar(v, ms, ms[-1], filiais=fil)
    rodar(con, "07_quedas.sql", None_cfg())
    t = con.execute("SELECT nome, mes, status_mom, classificacao_mom FROM analise_quedas WHERE nivel='filial' ORDER BY nome, mes").fetchall()
    d = {(n, str(m)): c for n, m, _, c in t}
    assert d[("F2", "2025-01-01")] == "sem_base" and d[("F2", "2025-02-01")] == "base_zerada"
    assert d[("F2", "2025-03-01")] == "queda_relevante"          # 500 -> 0 (-100%)
    assert d[("F1", "2025-02-01")] == "sem_queda_relevante"


# =============================================================== 3. MUTAÇÃO — o oráculo precisa pegar SQL adulterado
def _mutar(tmp_path, arquivo, antigo, novo):
    pasta = tmp_path / "analise"
    shutil.copytree(ANALISE, pasta)
    texto = (pasta / arquivo).read_text(encoding="utf-8")
    assert texto.count(antigo) >= 1, f"trecho a mutar não encontrado: {antigo!r}"
    (pasta / arquivo).write_text(texto.replace(antigo, novo), encoding="utf-8")
    return pasta


def _detecta(fn):
    try:
        fn()
    except (AssertionError, KeyError, ValueError):
        return True
    return False


def test_mut_preco_com_desconto_errado(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "08_fatores_variacao.sql", "* (1 - d0v / b0) * (1 - i0 / (b0 - d0v)) ELSE 0 END AS efeito_preco",
               "* (1 - d1v / b1) * (1 - i0 / (b0 - d0v)) ELSE 0 END AS efeito_preco")
    ok = rodar(etl["con"], "08_fatores_variacao.sql", cfg)["08a_decomposicao_total"]
    O.o_08a(ok, csv_)
    assert _detecta(lambda: O.o_08a(rodar(etl["con"], "08_fatores_variacao.sql", cfg, p)["08a_decomposicao_total"], csv_))


def test_mut_mix_formula(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "08_fatores_variacao.sql", "(q1 - q1c * q0 / q0c) * (r0 / q0)", "(q1 - q0) * (r0 / q0)")
    assert _detecta(lambda: O.o_08a(rodar(etl["con"], "08_fatores_variacao.sql", cfg, p)["08a_decomposicao_total"], csv_))


def test_mut_yoy_com_lag_errado(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "07_quedas.sql", "lag(valor, 12)", "lag(valor, 11)")
    O.o_07a(rodar(etl["con"], "07_quedas.sql", cfg)["07a_quedas_empresa"], csv_, cfg.limiar_queda_mom, cfg.limiar_queda_yoy)
    assert _detecta(lambda: O.o_07a(rodar(etl["con"], "07_quedas.sql", cfg, p)["07a_quedas_empresa"], csv_, cfg.limiar_queda_mom, cfg.limiar_queda_yoy))


def test_mut_remover_tratamento_sem_atividade_e_detectado_no_cenario_injetado(tmp_path):
    p = _mutar(tmp_path, "07_quedas.sql", "WHEN base_mom = 0 AND valor = 0 THEN 'sem_atividade'", "")
    fil = ((1, "F1", "Filial"), (2, "F2", "Filial"))
    ms = ["2025-01-01", "2025-02-01", "2025-03-01"]
    v = [venda(m, 1, 10, 1000, filial=1) for m in ms] + [venda(ms[0], 1, 10, 500, filial=2)]    # F2 vende só em jan -> fev=0 após jan>0; mar: 0 e 0
    con = mini_mart.criar(v, ms, ms[-1], filiais=fil)
    def classe(pasta):
        rodar(con, "07_quedas.sql", None_cfg(), pasta)
        return con.execute("SELECT classificacao_mom FROM analise_quedas WHERE nivel='filial' AND nome='F2' AND mes='2025-03-01'").fetchone()[0]
    assert classe(ANALISE) == "sem_atividade" and classe(p) == "base_zerada"        # o original separa; o mutante confunde


def test_mut_remover_piso_de_linhas(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "03_margem_produtos.sql", "FROM p WHERE linhas_entregues >= {PISO_LINHAS})", "FROM p)")
    c = replace(cfg, piso_linhas_margem=1500)
    O.o_03a(rodar(etl["con"], "03_margem_produtos.sql", c)["03a_margem_por_produto"], csv_, 1500)
    assert _detecta(lambda: O.o_03a(rodar(etl["con"], "03_margem_produtos.sql", c, p)["03a_margem_por_produto"], csv_, 1500))


def test_mut_execucao_orcamentaria_sobre_o_orcamento_anual(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "06_orcado_vs_realizado.sql", "realizado_acumulado::DOUBLE / nullif(orcamento_acumulado, 0)",
               "realizado_acumulado::DOUBLE / nullif(orcamento_anual, 0)")
    assert _detecta(lambda: O.o_06c(rodar(etl["con"], "06_orcado_vs_realizado.sql", cfg, p)["06c_leitura_ingenua_vs_correta"], csv_))


def test_mut_curva_abc_sem_descontar_o_proprio_produto(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "02_produtos_receita.sql", "participacao_acumulada_pct - participacao_pct <", "participacao_acumulada_pct <")
    assert _detecta(lambda: O.o_02a(rodar(etl["con"], "02_produtos_receita.sql", cfg, p)["02a_ranking_produtos_receita"], csv_))


def test_mut_media_movel_como_media_de_percentuais(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "05_lucratividade.sql",
               "sum(resultado_operacional_estimado) OVER w3::DOUBLE / nullif(sum(receita_ajustada) OVER w3, 0)",
               "avg(resultado_operacional_estimado::DOUBLE / nullif(receita_ajustada, 0)) OVER w3")
    assert _detecta(lambda: O.o_05a(rodar(etl["con"], "05_lucratividade.sql", cfg, p)["05a_resultado_operacional_mensal"], csv_))


def test_mut_quedas_pelo_limiar_errado_e_detectado(etl, cfg, csv_, tmp_path):
    p = _mutar(tmp_path, "07_quedas.sql", "variacao_mom_pct <= {LIMIAR_MOM}", "variacao_mom_pct < {LIMIAR_YOY}")
    assert _detecta(lambda: O.o_07a(rodar(etl["con"], "07_quedas.sql", cfg, p)["07a_quedas_empresa"], csv_, cfg.limiar_queda_mom, cfg.limiar_queda_yoy))


# =============================================================== 4. PROCESSO — determinismo, integridade, documentação
def test_exportacao_deterministica(etl, cfg, tmp_path):
    a = {r.nome: r.sha256 for r in executar_todas(replace(cfg, pasta_consultas_saida=tmp_path / "a"), con=etl["con"])}
    b = {r.nome: r.sha256 for r in executar_todas(replace(cfg, pasta_consultas_saida=tmp_path / "b"), con=etl["con"])}
    assert a == b and len(a) == 21
    for n in a:
        assert (tmp_path / "a" / f"{n}.csv").read_bytes() == (tmp_path / "b" / f"{n}.csv").read_bytes()
        assert hashlib.sha256((tmp_path / "a" / f"{n}.csv").read_bytes()).hexdigest() == a[n]


def test_para_csv_nao_exporta_zero_negativo():
    assert para_csv(pd.DataFrame({"a": [-0.0, -1e-12, 0.0]})) == "a\n0.000000\n0.000000\n0.000000\n"


def test_para_csv_e_estavel():
    df = pd.DataFrame({"a": [1.0 / 3, np.nan], "b": ["x", None]})
    assert para_csv(df) == para_csv(df.copy()) == "a,b\n0.333333,x\n,\n"


def test_csvs_de_origem_inalterados(etl):
    assert etl["csv_inalterados"] is True


def test_executar_nao_escreve_no_banco(etl, cfg):
    antes = etl["con"].execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema','pg_catalog')").fetchone()[0]
    executar_todas(cfg, con=etl["con"])
    depois = etl["con"].execute("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('information_schema','pg_catalog')").fetchone()[0]
    assert antes == depois


@pytest.mark.parametrize("arq", sorted(p.name for p in ANALISE.glob("[0-9][0-9]_*.sql")))
def test_cabecalho_documentado(arq):
    topo = (ANALISE / arq).read_text(encoding="utf-8").split("-- @@")[0]
    assert "Pergunta:" in topo and "Técnicas:" in topo, f"{arq}: cabeçalho sem Pergunta/Técnicas"


def test_sao_exatamente_oito_analises():
    assert len(list(ANALISE.glob("[0-9][0-9]_*.sql"))) == 8


def test_parametros_sem_placeholder_esquecido(cfg):
    from empresax.consultas import parametros
    for arq in ANALISE.glob("*.sql"):
        t = arq.read_text(encoding="utf-8")
        for k, v in parametros(cfg).items():
            t = t.replace(k, v)
        assert "{LIMIAR" not in t and "{PISO" not in t and "{TOL" not in t, arq.name


def test_rotulos_obrigatorios_nos_resultados(R):
    assert R["01a_faturamento_mensal"].df.columns.tolist()[:4] == ["mes", "receita_registrada", "vendas_entregues", "devolucoes"] \
        or {"receita_registrada", "vendas_entregues", "devolucoes", "receita_ajustada"} <= set(R["01a_faturamento_mensal"].df.columns)
    assert R["08a_decomposicao_total"].df.leitura.str.contains("HIPOTESE").all()
    assert R["03a_margem_por_produto"].df.filtro_aplicado.nunique() == 1
