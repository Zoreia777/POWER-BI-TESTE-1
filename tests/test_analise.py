"""Etapa 4 — testes das investigações em Python.

Camadas: (1) pandas × SQL × Python puro; (2) cenários injetados com contas feitas à mão; (3) números-chave × cálculo independente
direto dos CSVs; (4) mutação do código de cálculo; (5) rótulos/linguagem do relatório; (6) determinismo e integridade.
"""
import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import oraculos as O
from empresax.analise import dados as dados_mod, eventos, fmt, inv_margem, inv_relacoes, pvm
from empresax.analise.achados import HIPOTESE, OBSERVACAO, PROGRAMADO, CONCLUSAO, TIPOS, Achado
from empresax.analise.relatorio import executar_todas, gravar, gerar_markdown
from empresax.consultas import executar_arquivo

RAIZ = Path(__file__).resolve().parent.parent
T = pd.Timestamp


@pytest.fixture(scope="module")
def D(etl):
    return dados_mod.carregar(etl["cfg"], con=etl["con"])


@pytest.fixture(scope="module")
def I(etl, D):
    return executar_todas(etl["cfg"], D)


def mk(linhas):
    """DataFrame mínimo de vendas para a decomposição: (mes, produto, q, bruta, desc, imp[, dev])."""
    d = pd.DataFrame(linhas, columns=["mes", "id_produto", "quantidade", "receita_bruta", "desconto_valor", "impostos_valor", "receita_liquida_devolvida"][:len(linhas[0])])
    if "receita_liquida_devolvida" not in d:
        d["receita_liquida_devolvida"] = 0.0
    d["mes"] = pd.to_datetime(d["mes"])
    return d


M0, M1 = T("2025-01-01"), T("2025-02-01")


# ================================================================ 1. pandas × SQL × Python puro
def test_pvm_pandas_igual_ao_sql_em_todas_as_comparacoes(etl, D):
    r = {x.nome: x.df for x in executar_arquivo(etl["con"], RAIZ / "sql/analise/08_fatores_variacao.sql", etl["cfg"])}["08a_decomposicao_total"]
    r = r[r.status_base == "comparavel"]
    assert len(r) == 53
    for tipo in ("MoM", "YoY"):
        s = pvm.serie(D.vendas, D.meses, tipo).set_index("periodo")
        x = r[r.tipo_comparacao == tipo]
        for _, linha in x.iterrows():
            e = s.loc[T(linha.periodo)]
            for k, c in (("volume", "efeito_volume"), ("mix", "efeito_mix"), ("preco", "efeito_preco"), ("desconto", "efeito_desconto"), ("impostos", "efeito_impostos")):
                assert abs(e[k] - linha[c]) < 0.01, (tipo, linha.periodo, k)
            assert abs(e["efeito_devolucoes"] - linha.efeito_devolucoes) < 0.01
        assert len(s) == len(x)


def test_pvm_pandas_igual_ao_oraculo_em_python_puro(D, csv_):
    agg = O.agregar(O.vendas(csv_))
    prods = list(csv_["dim_produto"].id_produto)
    for m in (T("2025-03-01"), T("2026-09-01"), T("2026-02-01")):
        for lag in (1, 12):
            b = m - pd.DateOffset(months=lag)
            r, _ = pvm.decompor(D.vendas, m, b)
            o = O.pvm(agg, prods, m.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d"))
            for k in ("volume", "mix", "preco", "desconto", "impostos"):
                assert abs(r[k] - o[k]) < 0.01, (m, lag, k)
            assert abs(r["residuo"]) < 0.01


def test_pvm_por_recorte_soma_para_o_total(D):
    """Decompondo cada filial separadamente, os efeitos de preço/desconto somam ao da empresa? NÃO (a base de volume muda).
    Mas a variação registrada soma exatamente — e cada recorte fecha com resíduo zero."""
    m, b = T("2026-09-01"), T("2026-08-01")
    tot, _ = pvm.decompor(D.vendas, m, b)
    soma = 0.0
    for f in D.filiais.id_filial:
        r, _ = pvm.decompor(D.vendas[D.vendas.id_filial == f], m, b)
        assert abs(r["residuo"]) < 0.01
        soma += r["variacao_registrada"]
    assert abs(soma - tot["variacao_registrada"]) < 0.01


# ================================================================ 2. cenários injetados (à mão)
def ef(r):
    return {k: round(r[k], 4) for k in pvm.EFEITOS}


def test_inj_preco():
    r, _ = pvm.decompor(mk([[M0, 1, 10, 1000, 0, 0], [M1, 1, 10, 1100, 0, 0]]), M1, M0)
    assert ef(r) == dict(volume=0, mix=0, preco=100, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)


def test_inj_volume():
    v = mk([[M0, 1, 10, 1000, 0, 0], [M0, 2, 10, 500, 0, 0], [M1, 1, 20, 2000, 0, 0], [M1, 2, 20, 1000, 0, 0]])
    assert ef(pvm.decompor(v, M1, M0)[0]) == dict(volume=1500, mix=0, preco=0, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)


def test_inj_mix_e_preco_atribuidos_separadamente():
    v = mk([[M0, 1, 10, 1000, 0, 0], [M0, 2, 10, 500, 0, 0], [M1, 1, 15, 1650, 0, 0], [M1, 2, 5, 250, 0, 0]])
    r, por = pvm.decompor(v, M1, M0)
    assert ef(r) == dict(volume=0, mix=250, preco=150, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)
    assert round(por.loc[1, "preco"], 4) == 150 and round(por.loc[2, "preco"], 4) == 0   # preço só no produto A
    assert round(por.loc[1, "mix"], 4) == 500 and round(por.loc[2, "mix"], 4) == -250


def test_inj_desconto_e_imposto():
    r, _ = pvm.decompor(mk([[M0, 1, 10, 1000, 100, 90], [M1, 1, 10, 1000, 200, 80]]), M1, M0)
    assert ef(r)["desconto"] == -90 and ef(r)["preco"] == 0 and r["variacao_registrada"] == -90
    r, _ = pvm.decompor(mk([[M0, 1, 10, 1000, 0, 100], [M1, 1, 10, 1000, 0, 120]]), M1, M0)
    assert ef(r)["impostos"] == -20


def test_inj_produto_novo_descontinuado_e_ausente():
    v = mk([[M0, 1, 10, 1000, 0, 0], [M0, 2, 10, 500, 0, 0], [M1, 1, 10, 1000, 0, 0], [M1, 3, 6, 300, 0, 0]])
    r, por = pvm.decompor(v, M1, M0)
    assert ef(r)["produto_novo"] == 300 and ef(r)["produto_descontinuado"] == -500 and abs(r["residuo"]) < 1e-9
    assert por.loc[2, "produto_descontinuado"] == -500 and por.loc[3, "produto_novo"] == 300


def test_inj_base_zerada_e_atual_zerado_nao_dao_divisao_por_zero():
    r, _ = pvm.decompor(mk([[M1, 1, 10, 1000, 0, 0]]), M1, M0)         # base sem vendas: tudo é produto novo
    assert r["produto_novo"] == 1000 and r["volume"] == 0 and np.isfinite(list(r.values())).all()
    r, _ = pvm.decompor(mk([[M0, 1, 10, 1000, 0, 0]]), M1, M0)         # atual sem vendas: tudo é descontinuado
    assert r["produto_descontinuado"] == -1000 and np.isfinite(list(r.values())).all()


def test_inj_devolucao_leva_a_ajustada():
    v = mk([[M0, 1, 10, 1000, 0, 0, 0], [M1, 1, 10, 1000, 0, 0, 0], [M1, 1, 5, 500, 0, 0, 500]])
    r, _ = pvm.decompor(v, M1, M0)
    assert r["variacao_registrada"] == 500 and r["efeito_devolucoes"] == -500 and r["variacao_ajustada"] == 0


def _vm(linhas):
    return pd.DataFrame(linhas, columns=["id_produto", "receita_liquida_entregue", "custo_entregue"])


def test_margem_mix_e_taxa_a_mao():
    # base: A 50% da receita, margem 50%; B 50%, margem 20%  => M0 = 35%.  atual: A 80%, B 20% (margens iguais) => M1 = 44%
    base = _vm([[1, 500, 250], [2, 500, 400]])
    atual = _vm([[1, 800, 400], [2, 200, 160]])
    r, por = inv_margem.decompor_margem(atual, base)
    assert round(r["delta"], 6) == 0.09 and round(r["mix"], 6) == 0.09 and abs(r["taxa"]) < 1e-12
    assert round(por.loc[1, "efeito_mix"], 6) == 0.045 and round(por.loc[2, "efeito_mix"], 6) == 0.045   # centrado na margem média
    # só taxa: pesos iguais, margem de A cai de 50% para 40%  => efeito = 0,5 x (−0,10) = −0,05
    r, _ = inv_margem.decompor_margem(_vm([[1, 500, 300], [2, 500, 400]]), base)
    assert round(r["taxa"], 6) == -0.05 and abs(r["mix"]) < 1e-12 and round(r["delta"], 6) == -0.05


def test_margem_entrada_e_saida_fecham():
    base = _vm([[1, 500, 250], [2, 500, 400]])
    atual = _vm([[1, 500, 250], [3, 500, 100]])         # produto 2 sai, 3 entra
    r, _ = inv_margem.decompor_margem(atual, base)
    assert abs(r["residuo"]) < 1e-12 and abs(r["entrada_saida"]) > 0


def test_margem_fecha_nos_dados_reais(I):
    for k, r in I["INV4"].metricas["decomposicao"].items():
        assert abs(r["residuo"]) < 1e-12 and abs(r["mix"] + r["taxa"] + r["entrada_saida"] - r["delta"]) < 1e-12


# ================================================================ 3. números-chave × CSVs (independente)
def test_inv1_porto_alegre_contra_csv(I, csv_):
    v = O.vendas(csv_).merge(csv_["dim_filial"][["id_filial", "filial"]], on="id_filial")
    pa = v[v.filial == "Porto Alegre"]
    f25, f26 = pa[pa.mes == "2025-02-01"], pa[pa.mes == "2026-02-01"]
    m = I["INV1"].metricas
    assert abs(m["yoy"] - (f26.ent.sum() / f25.ent.sum() - 1)) < 1e-9
    assert abs(m["var_pedidos"] - (f26.id_pedido.nunique() / f25.id_pedido.nunique() - 1)) < 1e-9
    assert abs(m["var_linhas"] - (len(f26) / len(f25) - 1)) < 1e-9
    assert abs(m["var_unidades"] - (f26.quantidade.sum() / f25.quantidade.sum() - 1)) < 1e-9
    top = f25.groupby("id_produto").ent.sum().sort_values(ascending=False).index[0]
    assert m["pvm_produto_top"] == top == 1


def test_inv1_sensibilidade_e_concentracao(I, csv_):
    v = O.vendas(csv_); pa = v[(v.id_filial == 5)]
    b = pa[pa.mes == "2025-02-01"].ent.sort_values(ascending=False)
    a = pa[pa.mes == "2026-02-01"].ent.sum()
    m = I["INV1"].metricas
    assert abs(m["sens_sem_3_maiores"] - (a / (b.sum() - b.head(3).sum()) - 1)) < 1e-9
    assert abs(m["top5_linhas_base"] - b.head(5).sum() / b.sum()) < 1e-9
    assert m["prod_base_eh_maximo"] and m["pa_eh_minimo"]


def test_inv2_contagens_batem_com_etapa3_e_com_csv(R_sql, I, csv_):
    d = R_sql["07d_resumo_quedas_por_nivel"]
    f = d[(d.nivel == "filial") & (d.comparacao == "YoY")].quedas_relevantes.iloc[0]
    p = d[(d.nivel == "produto") & (d.comparacao == "YoY")].quedas_relevantes.iloc[0]
    assert I["INV2"].metricas["n_quedas_filial"] == f == 18 and I["INV2"].metricas["n_quedas_produto"] == p == 104
    # independente: pivot direto do CSV
    v = O.vendas(csv_); ms = O.meses(csv_)
    t = v.groupby(["mes", "id_filial"]).ent.sum().unstack().reindex(ms, fill_value=0.0)
    y = (t / t.shift(12) - 1).where(t.shift(12) > 0)
    assert int((y <= -0.10).sum().sum()) == f


def test_inv2_persistencia_e_programados(I):
    tp, tf = I["INV2"].tabelas["quedas_produto_yoy"], I["INV2"].tabelas["quedas_filial_yoy"]
    assert tp.persistente.sum() == (tp.sequencia_meses >= 3).sum() == I["INV2"].metricas["n_prod_persistentes"]
    assert (tf.sequencia_meses >= 1).all() and tf.queda_rs.is_monotonic_decreasing
    top = tp.iloc[0]
    assert top.produto == 'Notebook Pro 14"' and top.mes == T("2025-08-01") and top.programado.startswith("P09")
    assert abs(top.yoy_pct - (-0.954134)) < 1e-5


def test_inv3_smartphone_contra_csv(I, csv_):
    v = csv_["fact_vendas"].merge(csv_["dim_produto"][["id_produto", "produto"]], on="id_produto")
    neg = v[v.custo_total > v.receita_liquida]
    m = I["INV3"].metricas
    assert m["linhas_neg_total"] == len(neg) == 612 and m["linhas_neg_sp"] == int((neg.produto == "Smartphone X Max").sum()) == 607
    assert abs(m["prejuizo_total"] - (neg.custo_total - neg.receita_liquida).sum()) < 0.01
    sp = v[v.produto == "Smartphone X Max"].assign(mes=lambda d: d.data.str[:7])
    g = sp.groupby("mes").apply(lambda d: (d.custo_total > d.receita_liquida).mean())
    assert m["mes_todas_linhas_neg"] == T(g[g >= 0.999].index[0] + "-01")
    assert m["mes_metade_linhas_neg"] == T(g[g >= 0.5].index[0] + "-01")
    cu = sp.groupby("mes").apply(lambda d: d.custo_total.sum() / d.quantidade.sum())
    assert abs(m["custo_un_fim"] - cu.iloc[-1]) < 1e-6


def test_inv3_preco_necessario_zera_a_margem(I):
    t = I["INV3"].metricas
    p0 = t["tab_preco"][0]["preco_bruto_necessario"]
    liquido_un = p0 * (1 - t["desc_ef_ult"]) * (1 - t["imp_ef_ult"])
    assert abs(liquido_un - t["custo_un_fim"]) < 1e-6          # receita líquida por unidade = custo por unidade => margem 0
    prox = [x["preco_bruto_necessario"] for x in t["tab_preco"]]
    assert prox == sorted(prox)                                  # margem-alvo maior exige preço maior


def test_inv4_ytd_contra_csv(I, csv_):
    v = O.vendas(csv_); d = csv_["fact_despesas"].assign(mes=lambda x: x.data.str[:7] + "-01")
    for r in I["INV4"].metricas["ytd"]:
        a = r["ano"]
        vv = v[(v.mes >= f"{a}-01-01") & (v.mes <= f"{a}-09-01")]
        dd = d[(d.mes >= f"{a}-01-01") & (d.mes <= f"{a}-09-01")]
        assert abs(r["receita_ajustada"] - vv.ent.sum()) < 0.01 and abs(r["despesas"] - dd.valor.sum()) < 0.01
        assert abs(r["margem_bruta"] - (1 - vv.custo_ent.sum() / vv.ent.sum())) < 1e-9
        assert abs(r["margem_operacional"] - (vv.ent.sum() - vv.custo_ent.sum() - dd.valor.sum()) / vv.ent.sum()) < 1e-9


def test_inv4_margem_operacional_igual_bruta_menos_despesas(I):
    m = I["INV4"].metricas
    assert abs(m["delta_mo"] - (m["delta_mb"] - m["delta_desp_ratio"])) < 1e-12


def test_inv5_orcamento_contra_csv(I, csv_):
    o, d = csv_["fact_orcamento"], csv_["fact_despesas"]
    m = I["INV5"].metricas
    assert abs(m["orc_anual"] - o[o.mes.str[:4] == "2026"].valor_orcado.sum()) < 0.01          # ANUAL = 12 meses, inclusive futuros
    assert abs(m["orc_acum"] - o[(o.mes >= "2026-01-01") & (o.mes <= "2026-09-01")].valor_orcado.sum()) < 0.01
    assert abs(m["real_acum"] - d[d.data >= "2026-01-01"].valor.sum()) < 0.01
    assert abs(m["exec_correta"] - m["real_acum"] / m["orc_acum"]) < 1e-12 and abs(m["exec_ingenua"] - m["real_acum"] / m["orc_anual"]) < 1e-12
    assert m["exec_ingenua"] < 0.75 < m["exec_linear"] < 1.0
    assert abs(m["projecao"] - m["orc_anual"] * m["exec_correta"]) < 1e-6


def test_inv5_desvios_ecoam_programados(I):
    m = I["INV5"].metricas
    assert m["mk_4t"] > 1.10 > m["mk_ref"] - 0.05 and m["sw_26"] > 1.10 and m["ju_25"] > m["ju_24"]


def test_inv6_regressao_efeito_fixo_igual_a_regressao_com_dummies(D):
    v = D.vendas
    b, _ = inv_relacoes._fe_ols(v.quantidade.to_numpy(float), v.desconto_pct.to_numpy(float), v.id_produto.to_numpy())
    X = np.column_stack([v.desconto_pct.to_numpy(float), pd.get_dummies(v.id_produto).to_numpy(float)])
    coef, *_ = np.linalg.lstsq(X, v.quantidade.to_numpy(float), rcond=None)
    assert abs(b - coef[0]) < 1e-6


def test_inv6_confusao_o_coeficiente_cai_ao_controlar(I):
    m = I["INV6"].metricas
    assert m["coef_desc_qtd"] > 5 * abs(m["coef_desc_qtd_controlado"]) and m["reducao_associacao"] > 0.9


def test_inv6_spearman_contra_postos(D, I):
    m = inv_relacoes._mensal(D)
    r = np.corrcoef(m.desconto_efetivo.rank(), m.margem_bruta.rank())[0, 1]
    assert abs(r - I["INV6"].metricas["corr_desc_margem"]) < 1e-12


def test_inv6_pvm_anual_soma_variacao(I):
    for ano, t in I["INV6"].metricas["pvm_anos"].items():
        assert abs(t["volume"] + t["mix"] + t["preco"] + t["desconto"] + t["impostos"] - t["variacao_registrada"]) < 0.5


# ================================================================ 4. mutação do código de cálculo
def _fonte(arq, ini, fim=None):
    t = (RAIZ / "src/empresax/analise" / arq).read_text(encoding="utf-8")
    i = t.index(ini)
    return t[i:t.index(fim, i)] if fim else t[i:]


def _mutante(src, antigo, novo, ns):
    assert antigo in src, antigo
    exec(src.replace(antigo, novo), ns)
    return ns


PVM_SRC = _fonte("pvm.py", "EFEITOS =", "def serie")


def _ns_pvm(mut=None):
    ns = {"np": np, "pd": pd}
    src = PVM_SRC if not mut else PVM_SRC.replace(*mut)
    assert mut is None or mut[0] in PVM_SRC
    exec(src, ns)
    return ns["decompor"]


CENARIO_PM = mk([[M0, 1, 10, 1000, 0, 0], [M0, 2, 10, 500, 0, 0], [M1, 1, 15, 1650, 0, 0], [M1, 2, 5, 250, 0, 0]])
CENARIO_DESC = mk([[M0, 1, 10, 1000, 100, 90], [M1, 1, 10, 1000, 200, 80]])
CENARIO_VM = mk([[M0, 1, 10, 1000, 0, 0], [M0, 2, 10, 500, 0, 0], [M1, 1, 30, 3000, 0, 0], [M1, 2, 10, 500, 0, 0]])
CENARIO_PD = mk([[M0, 1, 10, 1000, 100, 0], [M1, 1, 10, 1100, 220, 0]])


def _passa_nos_testes_a_mao(decompor):
    try:
        r, _ = decompor(CENARIO_PM, M1, M0)
        assert ef(r) == dict(volume=0, mix=250, preco=150, desconto=0, impostos=0, produto_novo=0, produto_descontinuado=0)
        r, _ = decompor(CENARIO_DESC, M1, M0)
        assert ef(r)["desconto"] == -90
        # preço e desconto mudam juntos: preço = 10 un × R$10 × (1 − 10% de desconto da base) = 90;
        # desconto = −(20% − 10%) × 1.100 = −110; total = (1.100 − 220) − 900 = −20 = 90 − 110
        # volume total dobra com mix: A 10→30 un. (R$100), B 10→10 un. (R$50): volume = 1.500, mix = 1.000 − 500 = 500
        r, _ = decompor(CENARIO_VM, M1, M0)
        assert ef(r)["volume"] == 1500 and ef(r)["mix"] == 500 and ef(r)["preco"] == 0
        r, _ = decompor(CENARIO_PD, M1, M0)
        assert ef(r)["preco"] == 90 and ef(r)["desconto"] == -110
        return True
    except (AssertionError, KeyError, ValueError):
        return False


def test_mut_original_passa_e_mutantes_falham():
    assert _passa_nos_testes_a_mao(_ns_pvm())
    muts = [("(1 - d0) * (1 - t0)", "(1 - d1) * (1 - t0)"),                 # preço com desconto errado
            ("(c1.q - q1c * c0.q / q0c) * (c0.r / c0.q)", "(c1.q - c0.q) * (c0.r / c0.q)"),   # mix sem normalizar o volume
            ("(q1c - q0c) * c0.r / q0c", "(q1c - q0c) * c0.r / q1c"),        # volume com base errada
            ("c1.q * (P1 - P0)", "c0.q * (P1 - P0)")]                       # preço com quantidade da base
    for m in muts:
        assert not _passa_nos_testes_a_mao(_ns_pvm(m)), m


MARGEM_SRC = _fonte("inv_margem.py", "def decompor_margem", "def executar")


def _ns_margem(mut=None):
    ns = {"np": np, "pd": pd}
    exec(MARGEM_SRC if not mut else MARGEM_SRC.replace(*mut), ns)
    return ns["decompor_margem"]


def _margem_ok(f):
    try:
        base, atual = _vm([[1, 500, 250], [2, 500, 400]]), _vm([[1, 800, 400], [2, 200, 160]])
        r, por = f(atual, base)
        assert round(r["mix"], 6) == 0.09 and round(por.loc[1, "efeito_mix"], 6) == 0.045
        r, _ = f(_vm([[1, 500, 300], [2, 500, 400]]), base)
        assert round(r["taxa"], 6) == -0.05
        r, _ = f(_vm([[1, 800, 480], [2, 200, 160]]), base)      # pesos diferentes: taxa = 0,8 × (0,4 − 0,5)
        assert round(r["taxa"], 6) == -0.08 and round(r["mix"], 6) == 0.09      # mix usa a margem da BASE (0,045 + 0,045)
        return True
    except (AssertionError, KeyError, ValueError):
        return False


def test_mut_margem():
    assert _margem_ok(_ns_margem())
    for m in [("a.w * (a.m - b.m)", "b.w * (a.m - b.m)"),                      # taxa com peso da base
              ("(a.w - b.w) * (b.m - M0)", "(a.w - b.w) * b.m"),               # mix sem centrar
              ("(a.w - b.w) * (b.m - M0)", "(a.w - b.w) * (a.m - M0)")]:       # mix com margem atual
        assert not _margem_ok(_ns_margem(m)), m


# ================================================================ 5. rótulos, linguagem, relatório
def test_todo_achado_tem_tipo_valido_e_toda_investigacao_separa_hipotese(I):
    for inv in I.values():
        assert inv.achados and all(a.tipo in TIPOS for a in inv.achados)
        tipos = {a.tipo for a in inv.achados}
        assert OBSERVACAO in tipos and (HIPOTESE in tipos), inv.id
        assert inv.pergunta and inv.metodo and inv.limitacoes and inv.recomendacoes and inv.proximas


def test_achado_com_tipo_invalido_e_rejeitado():
    with pytest.raises(AssertionError):
        Achado("x", "CAUSA", "texto")


CAUSAIS = re.compile(r"\b(causou|provocou|por causa d|foi causad|devido a|culpa|culpad[oa])\b", re.I)


def test_linguagem_sem_causalidade_fora_de_hipotese(I):
    for inv in I.values():
        for a in inv.achados:
            if a.tipo in (OBSERVACAO, CONCLUSAO):
                m = CAUSAIS.search(a.texto)
                # 'culpado' só aparece entre aspas para negar a leitura causal
                assert not m or "'culpado'" in a.texto, (a.id, m.group(0))


def test_recomendacoes_sao_condicionais(I):
    for inv in I.values():
        assert all(r.lower().startswith(("se ", "em ambos", "criar", "usar", "acompanhar", "definir", "reportar", "incluir", "se,")) for r in inv.recomendacoes), inv.id
        assert sum(r.lower().startswith("se ") for r in inv.recomendacoes) >= 1, inv.id


def test_relatorio_markdown_estrutura_e_sem_lixo(I, D):
    md = gerar_markdown(I, D, {})
    for rotulo in ("Pergunta de negócio", "Método", "Evidências", "Limitações dos dados", "Recomendações gerenciais (condicionais)", "Próximas perguntas para uma empresa real"):
        assert md.count(rotulo) >= 6 or rotulo == "Método" and md.count("**Método.**") == 6
    assert "100% sintéticos" in md and "não é lucro líquido contábil" in md.replace("não é lucro líquido contábil", "não é lucro líquido contábil")
    for lixo in (" nan", "None", "{", "inf%", "NaN"):
        assert lixo not in md.replace("{}", ""), lixo


def test_resumo_executivo_usa_numeros_calculados(I, D):
    from empresax.analise.relatorio import resumo_executivo
    r = resumo_executivo(I, D)
    assert len(r) == 7 and "-48,9%" in r[3] and "100,5%" in r[5] and "71,8%" in r[5]


def test_eventos_programados_rotulo():
    assert eventos.rotular(T("2025-08-01"), id_produto=1).startswith("P09")
    assert eventos.rotular(T("2025-07-01"), id_filial=5).startswith("P10")
    assert eventos.rotular(T("2025-07-01"), id_filial=1) == "" and eventos.rotular(T("2025-08-01"), id_produto=2) == ""
    assert eventos.rotular(T("2025-08-01")) == ""         # sem escopo não rotula nada


def test_formatacao_ptbr():
    assert fmt.brl(1234.6) == "R$ 1.235" and fmt.brl(-1234.567, 2) == "-R$ 1.234,57"
    assert fmt.pct(0.4893) == "48,9%" and fmt.var(-0.4893) == "-48,9%" and fmt.var(0.029) == "+2,9%"
    assert fmt.mil(171871.23) == "R$ 171,9 mil" and fmt.mil(-2.5e6) == "-R$ 2,50 mi" and fmt.num(-0.0001, 2) == "0,00"
    assert fmt.pp(-0.0307) == "-3,1 p.p." and fmt.mes(T("2026-02-01")) == "fev/26"


# ================================================================ 6. determinismo e integridade
@pytest.fixture(scope="module")
def R_sql(etl):
    from empresax.consultas import executar_todas as exec_sql
    cfg = replace(etl["cfg"], pasta_consultas_saida=etl["cfg"].pasta_relatorios / "consultas_a4")
    return {r.nome: r.df for r in exec_sql(cfg, con=etl["con"])}


def test_gravacao_deterministica_e_completa(etl, D, I, tmp_path):
    h1 = gravar(I, D, etl["cfg"], tmp_path / "a")
    h2 = gravar(executar_todas(etl["cfg"], D), D, etl["cfg"], tmp_path / "b")
    h1.pop("manifesto.json", None); h2.pop("manifesto.json", None)
    assert h1 == h2
    nomes = set(h1)
    assert {"RELATORIO_EXECUTIVO.md", "RELATORIO_EXECUTIVO.html"} <= nomes
    assert sum(n.startswith("graficos/") for n in nomes) == 13
    assert sum(n.endswith("_achados.json") for n in nomes) == 6
    for n, s in h1.items():
        assert hashlib.sha256((tmp_path / "a" / n).read_bytes()).hexdigest() == s
    man = json.loads((tmp_path / "a" / "manifesto.json").read_text(encoding="utf-8"))
    assert set(man) == nomes


def test_html_nao_depende_de_internet_para_os_dados(etl, D, I, tmp_path):
    gravar(I, D, etl["cfg"], tmp_path)
    h = (tmp_path / "RELATORIO_EXECUTIVO.html").read_text(encoding="utf-8")
    assert h.count("cdn.plot.ly") == 1 and h.count('class="plotly-graph-div"') == 13


def test_csvs_originais_intactos_apos_etapa4(etl, I):
    assert etl["csv_inalterados"] is True


def test_dados_somente_leitura(etl, D):
    with pytest.raises(Exception):
        etl["con"].execute("CREATE TABLE mart.x_proibido(a INT)")
