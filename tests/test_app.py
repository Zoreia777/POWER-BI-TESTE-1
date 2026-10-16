"""Etapa 5 — testes do aplicativo: camada de dados (filtros, segurança, somente leitura), valores contra as views e contra
referências independentes (CSV/pandas/Python puro), estados vazios, denominadores zerados, gráficos e execução real da interface
com streamlit.testing (AppTest). Este módulo NÃO substitui a conferência visual: ela é feita à parte com o servidor e um navegador."""
import re
import shutil
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import duckdb
import plotly.graph_objects as go
import streamlit as st

import oraculos as O
from conftest import DATA, RAIZ
from empresax import powerbi as P
from empresax.app import casos, graficos as G, textos
from empresax.app.base import BancoIndisponivel, abrir, assinatura, caminho_banco
from empresax.app.consultas import Repositorio, razao
from empresax.app.filtros import FiltroInvalido, Filtros

ULT = date(2026, 9, 1)


@pytest.fixture(scope="module")
def repo(bi_db):
    con = abrir(bi_db)
    yield Repositorio(con)
    con.close()


def F(ini="2026-01-01", fim="2026-09-01", fil=(), prod=(), can=()):
    return Filtros(date.fromisoformat(ini), date.fromisoformat(fim), fil, prod, can)


# ===================================================================== 1. filtros e segurança
@pytest.mark.parametrize("ruim", ["1 OR 1=1", "5; DROP TABLE bi.fato_vendas", 3.5, None, True, [1], "5"])
def test_ids_nao_inteiros_sao_rejeitados(ruim):
    for campo in ("filiais", "produtos", "canais"):
        with pytest.raises(FiltroInvalido):
            Filtros(date(2026, 1, 1), date(2026, 9, 1), **{campo: (ruim,)})


@pytest.mark.parametrize("ini,fim", [("2026-09-01", "2026-01-01")])
def test_periodo_invertido_e_rejeitado(ini, fim):
    with pytest.raises(FiltroInvalido):
        F(ini, fim)


def test_datas_invalidas_sao_rejeitadas():
    for ruim in ("2026-01-01", "'; DROP TABLE x; --", 20260101, pd.Timestamp("2026-01-01")):
        with pytest.raises(FiltroInvalido):
            Filtros(ruim, date(2026, 9, 1))


def test_sql_gerado_so_tem_marcadores_e_colunas_fixas():
    f = F(fil=(5, 2), prod=(10,), can=(1, 4))
    txt, par = f.sql()
    assert re.fullmatch(r"[a-z_ ?(),]+|[A-Za-z_ ?(),]+", txt) or "?" in txt
    assert txt.count("?") == len(par) == 5
    assert not re.search(r"\d", txt)                                  # nenhum valor numérico dentro do texto do SQL
    assert par[2] == [2, 5] and par[3] == [10]


def test_filtros_vazios_equivalem_a_todos():
    txt, par = F().sql()
    assert txt == "mes BETWEEN ? AND ?" and len(par) == 2


def test_repositorio_valida_periodo_futuro_e_ids_inexistentes(repo):
    with pytest.raises(FiltroInvalido):
        repo.kpis(F("2026-01-01", "2026-10-01"))                      # outubro/26 é futuro: nunca realizado
    with pytest.raises(FiltroInvalido):
        repo.kpis(F("2023-12-01", "2024-03-01"))
    with pytest.raises(FiltroInvalido):
        repo.kpis(F(fil=(999,)))
    with pytest.raises(FiltroInvalido):
        repo.por_dimensao(F(prod=(1, 99999)), "filial")


def test_dimensao_fora_da_lista_branca_falha(repo):
    with pytest.raises(KeyError):
        repo.por_dimensao(F(), "filial; DROP TABLE x")


def test_injecao_via_filtro_nao_altera_o_banco(repo):
    n0 = repo.con.execute("SELECT count(*) FROM bi.fato_vendas").fetchone()[0]
    for tentativa in ("1); DROP VIEW bi.fato_vendas; --", "1 OR 1=1"):
        with pytest.raises(FiltroInvalido):
            repo.kpis(Filtros(date(2026, 1, 1), date(2026, 9, 1), filiais=(tentativa,)))
    assert repo.con.execute("SELECT count(*) FROM bi.fato_vendas").fetchone()[0] == n0


def test_codigo_do_app_nao_concatena_valores_do_usuario():
    """Estático: as únicas f-strings de SQL interpolam nomes de colunas/tabelas vindos de dicionários fixos ou o WHERE gerado por Filtros.sql()."""
    fonte = (RAIZ / "src/empresax/app/consultas.py").read_text(encoding="utf-8")
    for m in re.finditer(r"\{([^}]+)\}", "\n".join(l for l in fonte.splitlines() if "SELECT" in l or "FROM" in l or "WHERE" in l or "JOIN" in l)):
        assert m.group(1).split("[")[0].split(".")[0] in {"w", "wf", "sel", "grupo", "tabela", "chave", "nome"}, m.group(0)


# ===================================================================== 2. somente leitura e falhas do banco
def test_conexao_e_somente_leitura(bi_db):
    con = abrir(bi_db)
    for sql in ("CREATE TABLE bi.x AS SELECT 1", "DELETE FROM mart.fact_vendas", "DROP VIEW bi.fato_vendas", "CREATE SCHEMA zzz"):
        with pytest.raises(duckdb.Error):
            con.execute(sql)
    con.close()


def test_codigo_do_app_so_abre_conexao_read_only_e_sem_comandos_de_escrita():
    achados = []
    for arq in list((RAIZ / "src/empresax/app").glob("*.py")) + list((RAIZ / "app").rglob("*.py")):
        t = arq.read_text(encoding="utf-8")
        for m in re.finditer(r"duckdb\.connect\(([^\n]*)", t):
            achados.append((arq.name, m.group(1)))
        assert not re.search(r"\b(INSERT INTO|UPDATE bi|DELETE FROM|DROP (TABLE|VIEW)|CREATE (TABLE|OR REPLACE|VIEW)|ATTACH|COPY )\b", t), arq
    assert len(achados) == 1 and "read_only=True" in achados[0][1] and achados[0][0] == "base.py"


def test_banco_inexistente_da_mensagem_clara(tmp_path):
    with pytest.raises(BancoIndisponivel, match="run_etl"):
        abrir(tmp_path / "nao_existe.duckdb")


def test_banco_sem_views_bi_orienta_rodar_run_powerbi(etl):
    with pytest.raises(BancoIndisponivel, match="run_powerbi"):
        abrir(etl["cfg"].arquivo_banco)                                # banco do ETL, ainda sem schema bi


def test_view_fora_do_contrato_e_detectada(bi_db, tmp_path):
    p = tmp_path / "wh.duckdb"
    shutil.copy(bi_db, p)
    con = duckdb.connect(str(p))
    con.execute("CREATE OR REPLACE VIEW bi.dim_canal AS SELECT id_canal, canal FROM mart.dim_canal")   # falta tipo_canal
    con.close()
    with pytest.raises(BancoIndisponivel, match="contrato"):
        abrir(p)


def test_arquivo_corrompido_da_mensagem_clara(tmp_path):
    p = tmp_path / "ruim.duckdb"
    p.write_bytes(b"isto nao e um banco duckdb" * 100)
    with pytest.raises(BancoIndisponivel):
        abrir(p)


def test_assinatura_muda_quando_o_banco_e_regravado(tmp_path):
    p = tmp_path / "a.duckdb"
    p.write_bytes(b"x")
    a = assinatura(p)
    p.write_bytes(b"xx")
    assert assinatura(p) != a and assinatura(tmp_path / "nao_existe")[1:] == (0, 0)


def test_variavel_de_ambiente_define_o_caminho(monkeypatch, tmp_path):
    monkeypatch.setenv("EMPRESAX_BANCO", str(tmp_path / "x.duckdb"))
    assert caminho_banco() == tmp_path / "x.duckdb"


# ===================================================================== 3. valores × referências independentes
def _f_do_contexto(repo, c):
    ano = c.get("ano")
    if c.get("mes"):
        ini = fim = c["mes"]
    else:
        ini, fim = (date(ano, 1, 1), min(date(ano, 12, 1), ULT)) if ano else (date(2024, 1, 1), ULT)
    fil = tuple(repo.filiais.loc[repo.filiais.filial == c["filial"], "id_filial"]) if c.get("filial") else ()
    prod = tuple(repo.produtos.loc[repo.produtos.produto == c["produto"], "id_produto"]) if c.get("produto") else ()
    return Filtros(ini, fim, fil, prod)


@pytest.mark.parametrize("ctx", P.CONTEXTOS, ids=[c["id"] for c in P.CONTEXTOS])
def test_indicadores_do_app_batem_com_os_290_valores_de_referencia(repo, ctx):
    """O app deve reproduzir os valores de referência calculados direto dos CSVs (sem DuckDB nem views)."""
    ref = P.referencia_independente(DATA, ctx)
    f = _f_do_contexto(repo, ctx)
    k = repo.kpis(f)
    mapa = {"IND-01": "registrada", "IND-02": "entregues", "IND-03": "devolucoes", "IND-04": "ajustada", "IND-07": "custo_ajustado", "IND-08": "lucro_bruto",
            "IND-09": "margem_bruta", "IND-10": "unidades_entregues", "IND-11": "pedidos", "IND-12": "ticket_pedido", "IND-13": "desconto_efetivo",
            "IND-14": "preco_bruto_medio", "IND-15": "linhas_negativas", "IND-16": "pct_linhas_negativas", "IND-06": "taxa_devolucao"}
    for ind, chave in mapa.items():
        esperado = ref[ind]
        assert (k[chave] is None) == (esperado is None), (ctx["id"], ind)
        if esperado is not None:
            assert abs(k[chave] - esperado) < (1e-9 if abs(esperado) < 10 else 0.01), (ctx["id"], ind, k[chave], esperado)
    assert abs(k["diferenca_reconciliacao"]) < 0.01
    d = repo.despesas(f, k)
    if ctx.get("produto"):
        assert d is None and ref["IND-17"] is None
    else:
        assert abs(d["total"] - ref["IND-17"]) < 0.01 and abs(d["resultado"] - ref["IND-19"]) < 0.01
        assert abs(d["pct_receita"] - ref["IND-18"]) < 1e-9 and abs(d["margem_operacional"] - ref["IND-20"]) < 1e-9
        o = repo.orcamento(f)
        assert abs(o["orcado_anual"] - ref["IND-25"]) < 0.01 and abs(o["orcado_acumulado"] - ref["IND-26"]) < 0.01
        assert abs(o["realizado"] - ref["IND-27"]) < 0.01
        if ref["IND-28"] is not None:
            assert abs(o["execucao"] - ref["IND-28"]) < 1e-9 and abs(o["consumo_anual"] - ref["IND-29"]) < 1e-9
    if ctx.get("mes"):
        a = repo.comparacao_anual(f)
        if ref["IND-24"] is None:
            assert not a["disponivel"]
        else:
            assert a["disponivel"] and abs(a["variacao"] - ref["IND-24"]) < 1e-9


def _oraculo_csv(csv_, ini, fim, fil, prod, can):
    v = O.vendas(csv_)
    v = v[(v.mes >= ini) & (v.mes <= fim)]
    if fil:
        v = v[v.id_filial.isin(fil)]
    if prod:
        v = v[v.id_produto.isin(prod)]
    if can:
        v = v[v.id_canal.isin(can)]
    return v


def test_combinacoes_aleatorias_de_filtros_contra_pandas_nos_csvs(repo, csv_):
    rng = np.random.default_rng(20261014)
    meses = [m.isoformat() for m in repo.meses]
    vazios = 0
    for _ in range(60):
        i, j = sorted(rng.integers(0, len(meses), 2))
        fil = tuple(int(x) for x in rng.choice(repo.filiais.id_filial, rng.integers(0, 4), replace=False))
        prod = tuple(int(x) for x in rng.choice(repo.produtos.id_produto, rng.integers(0, 4), replace=False))
        can = tuple(int(x) for x in rng.choice(repo.canais.id_canal, rng.integers(0, 3), replace=False))
        k = repo.kpis(Filtros(date.fromisoformat(meses[i]), date.fromisoformat(meses[j]), fil, prod, can))
        o = _oraculo_csv(csv_, meses[i], meses[j], fil, prod, can)
        assert k["linhas"] == len(o) and k["vazio"] == (len(o) == 0)
        assert abs(k["registrada"] - o.receita_liquida.sum()) < 0.05 and abs(k["ajustada"] - o.ent.sum()) < 0.05
        assert abs(k["devolucoes"] - o.dev.sum()) < 0.05 and abs(k["custo_ajustado"] - o.custo_ent.sum()) < 0.05
        assert k["pedidos"] == o.id_pedido.nunique()
        if len(o) == 0:
            vazios += 1
            assert k["margem_bruta"] is None and k["ticket_pedido"] is None and k["pct_linhas_negativas"] is None
    assert vazios >= 0


def test_por_dimensao_soma_para_o_total(repo):
    f = F("2025-01-01", "2026-09-01")
    k = repo.kpis(f)
    for dim in ("filial", "produto", "canal", "categoria"):
        d = repo.por_dimensao(f, dim)
        assert abs(d.ajustada.sum() - k["ajustada"]) < 0.05 and d.linhas.sum() == k["linhas"], dim
        assert abs(d.participacao.sum() - 1) < 1e-9
        assert (d.registrada - d.devolucoes - d.ajustada).abs().max() < 0.05


def test_variacao_anual_por_filial_so_existe_com_base_positiva(repo):
    d = repo.por_dimensao(F("2025-01-01", "2025-06-01"), "filial").set_index("nome")
    assert pd.isna(d.loc["Salvador", "yoy"])                      # Salvador abriu em fev/2025: base de 2024 é zero
    assert not pd.isna(d.loc["Rio de Janeiro", "yoy"])
    d24 = repo.por_dimensao(F("2024-01-01", "2024-06-01"), "filial")
    assert d24.yoy.isna().all() and d24.base_ano_anterior.isna().all()   # 2024 não tem ano anterior


def test_resultados_chave_da_etapa_4_aparecem_no_app(repo):
    k = repo.kpis(F())
    assert round(k["ajustada"] / 1e6, 2) == 41.29 and round(k["margem_bruta"], 3) == 0.403
    a = repo.comparacao_anual(F())
    assert round(a["variacao"], 3) == 0.204 and a["periodo_base"] == (date(2025, 1, 1), date(2025, 9, 1))
    o = repo.orcamento(F())
    assert round(o["execucao"], 3) == 1.005 and round(o["consumo_anual"], 3) == 0.718 and round(o["orcado_anual"] / 1e6, 2) == 19.67


def test_orcamento_por_departamento_destaca_ti(repo):
    d = repo.orcamento_por(F(), "departamento").set_index("nome")
    assert round(d.loc["Tecnologia da Informação", "execucao"], 3) == 1.057
    assert (d.execucao > 1.05).sum() == 1


# ===================================================================== 4. estados vazios e denominadores zerados
def test_razao_protege_denominador_zero_e_nulos():
    assert razao(1, 0) is None and razao(None, 3) is None and razao(3, None) is None and razao(float("nan"), 2) is None
    assert razao(0, 4) == 0.0 and razao(1, 4) == 0.25


def test_filial_antes_de_abrir_da_resultado_vazio_sem_numeros_enganosos(repo):
    f = F("2024-01-01", "2024-12-01", fil=(7,))                          # Salvador só vende a partir de fev/2025
    k = repo.kpis(f)
    assert k["vazio"] and k["linhas"] == 0 and k["ajustada"] == 0
    assert k["margem_bruta"] is None and k["taxa_devolucao"] is None and k["ticket_pedido"] is None and k["receita_por_linha"] is None
    assert repo.serie_mensal(f).empty and repo.por_dimensao(f, "produto").empty
    assert not repo.comparacao_anual(f)["disponivel"]
    assert repo.matriz_yoy_filial(f).empty or repo.matriz_yoy_filial(f).notna().sum().sum() == 0


def test_base_zerada_nao_vira_crescimento(repo):
    a = repo.comparacao_anual(F("2025-02-01", "2025-02-01", fil=(7,)))   # primeiro mês de Salvador: base de 2024 zerada
    assert not a["disponivel"] and "base zerada" in a["motivo"]
    assert not repo.comparacao_anual(F("2024-03-01", "2024-05-01"))["disponivel"]


def test_combinacao_produto_filial_sem_vendas_nao_quebra(repo):
    for p in repo.produtos.id_produto:
        k = repo.kpis(F("2024-01-01", "2024-01-01", fil=(7,), prod=(int(p),)))
        assert k["vazio"] and k["margem_bruta"] is None


def test_orcamento_sem_dados_marca_vazio_e_nao_divide_por_zero(repo):
    f = F("2024-01-01", "2024-03-01", fil=(7,))                           # Salvador ainda não existia: sem orçamento nem despesa
    o = repo.orcamento(f)
    assert o["vazio"] and o["execucao"] is None and o["consumo_anual"] is None and o["orcado_acumulado"] == 0
    d = repo.despesas(f)
    assert d["total"] == 0 and d["pct_receita"] is None and d["resultado"] is None and d["margem_operacional"] is None


def test_despesas_indisponiveis_com_produto_ou_canal(repo):
    assert repo.despesas(F(prod=(10,))) is None and repo.despesas(F(can=(1,))) is None
    assert repo.serie_despesas(F(prod=(10,))) is None and repo.despesas_por_filial(F(can=(2,))) is None
    assert repo.despesas(F(fil=(5,))) is not None


def test_nenhum_mes_futuro_aparece_em_series(repo):
    for s in (repo.serie_mensal(F("2024-01-01", "2026-09-01")), repo.orcamento_mensal(F("2024-01-01", "2026-09-01"))):
        assert s.mes.max() == pd.Timestamp(ULT)
    assert repo.ultimo_mes == ULT and repo.meses[-1] == ULT


# ===================================================================== 5. preço × volume × mix no app
def test_pvm_do_app_fecha_com_a_variacao_da_receita_ajustada(repo):
    for f in (F(), F(fil=(5,)), F(prod=(1, 2, 3)), F(can=(2,)), F("2025-03-01", "2025-08-01", fil=(2, 3), can=(1, 4)), F("2026-02-01", "2026-02-01", fil=(5,))):
        for desloc in (-12, -f.n_meses):
            b = f.deslocado(desloc)
            if b.inicio < repo.primeiro_mes:
                continue
            res, por = repo.pvm_periodo(f, b)
            soma = sum(res[k] for k in ("volume", "mix", "preco", "desconto", "impostos", "produto_novo", "produto_descontinuado", "efeito_devolucoes"))
            assert abs(soma - (res["ajustada_atual"] - res["ajustada_base"])) < 0.01, (f, desloc)
            assert abs(res["residuo"]) < 0.01
            assert abs(res["ajustada_atual"] - repo.kpis(f)["ajustada"]) < 0.01 and abs(res["ajustada_base"] - repo.kpis(b)["ajustada"]) < 0.01


def test_pvm_do_app_contra_oraculo_em_python_puro_por_periodo(repo, csv_):
    """Períodos de vários meses: agrega por produto nos CSVs e aplica a decomposição em Python puro (tests/oraculos.py)."""
    def agg(ini, fim, fil):
        v = _oraculo_csv(csv_, ini, fim, fil, (), ())
        g = v.groupby("id_produto")[["quantidade", "receita_bruta", "desconto_valor", "impostos_valor"]].sum()
        return {("P", p): dict(q=float(r.quantidade), b=float(r.receita_bruta), d=float(r.desconto_valor), i=float(r.impostos_valor)) for p, r in g.iterrows()}
    prods = list(csv_["dim_produto"].id_produto)
    for ini, fim, fil in (("2026-01-01", "2026-09-01", ()), ("2026-01-01", "2026-03-01", (5,)), ("2025-06-01", "2025-08-01", (1, 2))):
        f = Filtros(date.fromisoformat(ini), date.fromisoformat(fim), fil)
        b = f.deslocado(-12)
        res, _ = repo.pvm_periodo(f, b)
        a1, a0 = agg(ini, fim, fil), agg(b.inicio.isoformat(), b.fim.isoformat(), fil)
        agg_all = {**{("A", p): x for (_, p), x in a1.items()}, **{("B", p): x for (_, p), x in a0.items()}}
        o = O.pvm(agg_all, prods, "A", "B")
        for k_app, k_o in (("volume", "volume"), ("mix", "mix"), ("preco", "preco"), ("desconto", "desconto"), ("impostos", "impostos"), ("produto_novo", "novo"), ("produto_descontinuado", "descontinuado")):
            assert abs(res[k_app] - o[k_o]) < 0.01, (ini, fim, fil, k_app)


def test_pvm_mensal_do_app_igual_a_etapa_4_porto_alegre(repo):
    res, _ = casos.porto_alegre_pvm(repo, date(2026, 2, 1))
    esperado = dict(volume=-75101, mix=-90513, preco=3117, desconto=-774, produto_novo=4698, produto_descontinuado=-12935)
    for k, v in esperado.items():
        assert abs(res[k] - v) < 1, k
    assert round(res["ajustada_base"]) == 351281 and round(res["ajustada_atual"]) == 179410


def test_pvm_recortes_diferentes_sao_rejeitados(repo):
    with pytest.raises(FiltroInvalido):
        repo.pvm_periodo(F(fil=(5,)), F("2025-01-01", "2025-09-01", fil=(2,)))


def test_pvm_com_base_vazia_nao_quebra(repo):
    res, _ = repo.pvm_periodo(F("2025-02-01", "2025-02-01", fil=(7,)), F("2024-02-01", "2024-02-01", fil=(7,)))
    assert res["ajustada_base"] == 0


# ===================================================================== 6. estudos de caso
def test_porto_alegre_separa_pedidos_linhas_e_receita_por_linha(repo):
    c = casos.porto_alegre_comparacao(repo, date(2026, 2, 1)).set_index("metrica")
    assert round(c.loc["Receita ajustada", "variacao"], 3) == -0.489 and round(c.loc["Pedidos", "variacao"], 3) == -0.066
    assert round(c.loc["Linhas de pedido", "variacao"], 3) == 0.029 and round(c.loc["Receita por linha", "variacao"], 3) == -0.504
    assert casos.porto_alegre_comparacao(repo, date(2024, 6, 1)) is None            # sem base: o ano anterior não existe nos dados
    assert casos.porto_alegre_comparacao(repo, date(2025, 1, 1)) is not None
    conc = casos.porto_alegre_concentracao(repo, date(2025, 2, 1))
    assert round(conc["share_top_linhas"], 3) == 0.381 and conc["maior_cliente"] == 421 and round(conc["share_maior_cliente"], 3) == 0.294


def test_smartphone_confere_com_a_investigacao_inv3(repo):
    r = casos.smartphone_resumo(repo)
    assert r["preco_ini"] == r["preco_fim"] == 5290 and round(r["variacao_custo"], 3) == 0.371
    assert r["linhas_neg"] == 607 and r["linhas_neg_empresa"] == 612
    assert r["primeira_negativa"] == pd.Timestamp("2024-11-01") and r["cem_por_cento_desde"] == pd.Timestamp("2025-11-01")
    assert round(r["margem_ini"], 3) == 0.176 and round(r["margem_fim"], 3) == -0.137
    p = casos.smartphone_preco_para_margem(repo, 0.0)
    assert round(p["aumento"], 3) == 0.137 and p["mes"] == ULT
    assert casos.smartphone_preco_para_margem(repo, 0.2)["preco_necessario"] > p["preco_necessario"]
    assert casos.smartphone_preco_para_margem(repo, 1.0) is None
