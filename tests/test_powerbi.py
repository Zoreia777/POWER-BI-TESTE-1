"""Etapa 4 — testes da camada de consumo do Power BI (schema `bi`).

IMPORTANTE: estes testes NÃO executam DAX no Power BI. Validam as views SQL, o contrato, os valores de referência
(SQL × cálculo independente nos CSVs) e o lint estático das definições DAX.
"""
import re
import shutil
from dataclasses import replace
from datetime import date

import duckdb
import pandas as pd
import pytest

from empresax import powerbi as P
from empresax.config import Config
from empresax.consultas import para_csv
from empresax.pipeline import executar
from empresax.powerbi_doc import gerar_documento

from conftest import DATA, RAIZ, cfg_tmp, impressao_digital


@pytest.fixture(scope="module")
def bi(etl, tmp_path_factory):
    """Cópia gravável do banco do ETL com as views `bi` criadas."""
    p = tmp_path_factory.mktemp("bi") / "wh.duckdb"
    shutil.copy(etl["cfg"].arquivo_banco, p)
    con = duckdb.connect(str(p))
    views = P.criar_views(con)
    yield {"con": con, "views": views, "arquivo": p}
    con.close()


# ================================================================ 1. contrato e contagens
def test_contrato_das_views_colunas_e_ordem_exatas(bi):
    assert sorted(bi["views"]) == sorted(P.CONTRATO)
    for v, cols in P.CONTRATO.items():
        reais = [r[0] for r in bi["con"].execute(f"DESCRIBE bi.{v}").fetchall()]
        assert reais == cols, v


def test_contagens_das_views_batem_com_mart_e_csv(bi, csv_):
    c = bi["con"]
    n = lambda q: c.execute(q).fetchone()[0]
    assert n("SELECT count(*) FROM bi.fato_vendas") == len(csv_["fact_vendas"]) == n("SELECT count(*) FROM mart.fact_vendas")
    assert n("SELECT count(*) FROM bi.fato_despesas") == len(csv_["fact_despesas"])
    assert n("SELECT count(*) FROM bi.fato_orcamento") == len(csv_["fact_orcamento"])
    assert n("SELECT count(*) FROM bi.dim_produto") == len(csv_["dim_produto"])
    assert n("SELECT count(*) FROM bi.dim_filial") == len(csv_["dim_filial"])
    assert n("SELECT count(*) FROM bi.dim_cliente") == len(csv_["dim_cliente"])
    assert n("SELECT count(*) FROM bi.dim_canal") == len(csv_["dim_canal"])


def test_chaves_unicas_nas_dimensoes_e_fatos(bi):
    c = bi["con"]
    for v, k in [("dim_produto", "id_produto"), ("dim_filial", "id_filial"), ("dim_canal", "id_canal"), ("dim_cliente", "id_cliente"),
                 ("dim_departamento", "id_departamento"), ("dim_categoria_despesa", "id_categoria_despesa"), ("dim_calendario", "data"),
                 ("fato_vendas", "id_venda"), ("fato_despesas", "id_despesa")]:
        assert c.execute(f"SELECT count(*) - count(DISTINCT {k}) FROM bi.{v}").fetchone()[0] == 0, v


def test_relacionamentos_do_modelo_nao_tem_orfaos(bi):
    c = bi["con"]
    for f, col, d, dc in P.RELACIONAMENTOS:
        o = c.execute(f"SELECT count(*) FROM bi.{f} x WHERE x.{col} IS NOT NULL AND x.{col} NOT IN (SELECT {dc} FROM bi.{d})").fetchone()[0]
        assert o == 0, (f, col, d)


# ================================================================ 2. reconciliação
def test_reconciliacao_linha_a_linha_registrada_igual_ajustada_mais_devolucao(bi):
    r = bi["con"].execute("SELECT count(*) FROM bi.fato_vendas WHERE abs(receita_registrada - receita_ajustada - devolucao) > 0.005").fetchone()[0]
    assert r == 0


def test_receita_ajustada_so_vem_de_entregues_e_devolucao_so_de_devolvidas(bi):
    c = bi["con"]
    assert c.execute("SELECT count(*) FROM bi.fato_vendas WHERE status='Devolvido' AND receita_ajustada <> 0").fetchone()[0] == 0
    assert c.execute("SELECT count(*) FROM bi.fato_vendas WHERE status='Entregue' AND devolucao <> 0").fetchone()[0] == 0


def test_kpi_empresa_mes_contra_pandas_direto_dos_csvs(bi, csv_):
    v = csv_["fact_vendas"].assign(mes=lambda d: d.data.str[:7])
    d = csv_["fact_despesas"].assign(mes=lambda d: d.data.str[:7])
    k = bi["con"].execute("SELECT * FROM bi.kpi_empresa_mes ORDER BY mes").df()
    k["m"] = pd.to_datetime(k.mes).dt.strftime("%Y-%m")
    for _, r in k.iterrows():
        x = v[v.mes == r.m]
        ent = x[x.status == "Entregue"]
        assert abs(r.receita_registrada - x.receita_liquida.sum()) < 0.05
        assert abs(r.receita_ajustada - ent.receita_liquida.sum()) < 0.05
        assert abs(r.devolucoes - x[x.status == "Devolvido"].receita_liquida.sum()) < 0.05
        assert abs(r.custo_ajustado - ent.custo_total.sum()) < 0.05
        assert abs(r.despesas - d[d.mes == r.m].valor.sum()) < 0.05
        assert abs(r.resultado_operacional_estimado - (r.lucro_bruto_ajustado - r.despesas)) < 0.05
        assert abs(r.margem_bruta_pct - r.lucro_bruto_ajustado / r.receita_ajustada) < 1e-9
        assert r.pedidos == x.id_pedido.nunique()


# ================================================================ 3. valores de referência
def test_referencia_sql_igual_a_independente_em_todos_os_contextos(bi):
    sql = P.tabela_referencia(lambda c: P.referencia_sql(bi["con"], c))
    ind = P.tabela_referencia(lambda c: P.referencia_independente(DATA, c))
    assert len(sql) == len(ind) == len(P.CONTEXTOS) * len(P.INDICADORES)
    assert list(sql.contexto_id) == list(ind.contexto_id) and list(sql.indicador_id) == list(ind.indicador_id)
    assert sql.valor_esperado.isna().tolist() == ind.valor_esperado.isna().tolist()
    dif = (sql.valor_esperado.fillna(0) - ind.valor_esperado.fillna(0)).abs()
    assert dif.max() < 0.01, sql.loc[dif.idxmax()].to_dict()


def test_referencia_regras_de_nulidade(bi):
    t = P.tabela_referencia(lambda c: P.referencia_sql(bi["con"], c)).set_index(["contexto_id", "indicador_id"]).valor_esperado
    for ctx in ("C09", "C10"):                                   # produto filtrado → despesas/orçamento não se aplicam
        for i in ("IND-17", "IND-19", "IND-25", "IND-28"):
            assert pd.isna(t[(ctx, i)]), (ctx, i)
    for i in ("IND-21", "IND-22", "IND-23", "IND-24"):           # sem mês único → sem MoM/YoY
        assert pd.isna(t[("C01", i)])
    assert not pd.isna(t[("C05", "IND-22")]) and not pd.isna(t[("C05", "IND-24")])


def test_referencia_reconcilia_indicadores_entre_si(bi):
    for c in P.CONTEXTOS:
        r = P.referencia_sql(bi["con"], c)
        assert abs(r["IND-01"] - r["IND-03"] - r["IND-04"]) < 0.01, c["id"]       # registrada = ajustada + devoluções
        assert abs(r["IND-05"]) < 0.01
        assert abs(r["IND-08"] - (r["IND-04"] - r["IND-07"])) < 0.01


def test_execucao_ingenua_difere_da_correta_e_a_correta_usa_orcamento_acumulado(bi):
    r = P.referencia_sql(bi["con"], P.CONTEXTOS[3])      # 2026
    assert r["IND-29"] < 0.75 < r["IND-28"]
    assert r["IND-26"] < r["IND-25"]


# ================================================================ 4. mutação das views SQL
def test_mutacao_sql_receita_ajustada_trocada_por_liquida_e_detectada(bi, tmp_path, monkeypatch):
    pasta = tmp_path / "sql"
    pasta.mkdir()
    for f in P.PASTA_SQL.glob("*.sql"):
        t = f.read_text(encoding="utf-8")
        antigo = "receita_liquida_entregue                          AS receita_ajustada"
        assert antigo in t
        (pasta / f.name).write_text(t.replace(antigo, "receita_liquida                                   AS receita_ajustada"), encoding="utf-8")
    p = tmp_path / "mut.duckdb"
    shutil.copy(bi["arquivo"], p)
    con = duckdb.connect(str(p))
    monkeypatch.setattr(P, "PASTA_SQL", pasta)
    P.criar_views(con)
    quebrou = con.execute("SELECT count(*) FROM bi.fato_vendas WHERE abs(receita_registrada - receita_ajustada - devolucao) > 0.005").fetchone()[0]
    assert quebrou > 0                                              # a reconciliação linha a linha pega o erro
    r = P.referencia_sql(con, P.CONTEXTOS[0])
    ok = P.referencia_independente(DATA, P.CONTEXTOS[0])
    assert abs(r["IND-04"] - ok["IND-04"]) > 1000                   # e a referência independente também
    con.close()


# ================================================================ 5. lint do DAX
def test_lint_dax_passa_no_original():
    assert P.lint_dax() == []


def _ind_com(dax):
    base = dict(P.INDICADORES[0])
    base["dax"] = dax
    return [base]


def test_lint_dax_detecta_coluna_inexistente():
    e = P.lint_dax(_ind_com("SUM ( fato_vendas[coluna_que_nao_existe] )"))
    assert any("coluna inexistente" in x for x in e)


def test_lint_dax_detecta_medida_inexistente():
    e = P.lint_dax(_ind_com("DIVIDE ( [Medida Fantasma], 2 )"))
    assert any("medida inexistente" in x for x in e)


def test_lint_dax_detecta_parenteses_desbalanceados():
    e = P.lint_dax(_ind_com("SUM ( fato_vendas[receita_ajustada] "))
    assert any("parênteses" in x for x in e)


def test_lint_dax_detecta_nome_duplicado_e_campo_vazio():
    a = dict(P.INDICADORES[0])
    assert any("duplicados" in x for x in P.lint_dax([a, dict(a)]))
    b = dict(a)
    b["definicao"] = ""
    assert any("campo vazio" in x for x in P.lint_dax([b]))


def test_dicionario_completo_ids_unicos_e_sequenciais():
    ids = [i["id"] for i in P.INDICADORES]
    assert ids == [f"IND-{n:02d}" for n in range(1, len(ids) + 1)] and len(ids) == 29
    for i in P.INDICADORES:
        assert all(i[k] for k in ("id", "nome", "tipo", "definicao", "dax", "grao", "filtros", "formato"))


def test_toda_medida_de_vendas_ignora_dimensoes_inaplicaveis_em_despesas():
    for i in P.INDICADORES:
        if i["id"] in ("IND-17", "IND-25", "IND-26", "IND-27"):
            assert "ISFILTERED ( dim_produto )" in i["dax"], i["id"]


# ================================================================ 6. idempotência, exportação, ETL, documento
def test_criar_views_e_idempotente(bi):
    antes = bi["con"].execute("SELECT sum(receita_ajustada) FROM bi.fato_vendas").fetchone()
    assert P.criar_views(bi["con"]) == bi["views"]
    assert bi["con"].execute("SELECT sum(receita_ajustada) FROM bi.fato_vendas").fetchone() == antes


def test_exportacao_deterministica_e_com_contagens(bi, tmp_path):
    a = P.exportar(bi["con"], tmp_path / "a")
    b = P.exportar(bi["con"], tmp_path / "b")
    assert a == b and set(a) == set(P.CONTRATO)
    for v in P.CONTRATO:
        assert (tmp_path / "a" / f"{v}.csv").read_bytes() == (tmp_path / "b" / f"{v}.csv").read_bytes()
        assert len((tmp_path / "a" / f"{v}.csv").read_text(encoding="utf-8").splitlines()) == a[v] + 1


def test_etl_reexecutado_com_schema_bi_presente_nao_quebra_nem_altera_o_mart(bi, etl, tmp_path):
    p = tmp_path / "re.duckdb"
    shutil.copy(bi["arquivo"], p)
    cfg = replace(cfg_tmp(tmp_path), arquivo_banco=p)
    executar(cfg)
    con = duckdb.connect(str(p))
    try:
        assert impressao_digital(con) == impressao_digital(etl["con"])
        P.criar_views(con)                                   # as views voltam a ser criadas sobre o mart reconstruído
        assert con.execute("SELECT count(*) FROM bi.fato_vendas").fetchone()[0] == bi["con"].execute("SELECT count(*) FROM bi.fato_vendas").fetchone()[0]
    finally:
        con.close()


def test_documento_gerado_declara_que_dax_nao_foi_executado(bi):
    ref = P.tabela_referencia(lambda c: P.referencia_sql(bi["con"], c))
    linhas = {v: bi["con"].execute(f"SELECT count(*) FROM bi.{v}").fetchone()[0] for v in P.CONTRATO}
    doc = gerar_documento(ref, linhas)
    assert "NÃO foram executadas no Power BI" in doc
    for v in P.CONTRATO:
        assert v in doc
    assert all(i["id"] in doc for i in P.INDICADORES)
    assert "59.365" in doc                                    # milhar em pt-BR


def test_documento_versionado_no_repositorio_tem_o_aviso():
    t = (RAIZ / "docs" / "POWERBI_CAMADA_DE_CONSUMO.md").read_text(encoding="utf-8")
    assert "NÃO foram executadas no Power BI" in t


def test_csvs_originais_continuam_inalterados(etl):
    assert etl["csv_inalterados"] is True


# ================================================================ 7. roteiro de construção e checklist (Etapa 5)
def _roteiro_e_ref(bi):
    from empresax.powerbi_doc import gerar_roteiro
    ref = P.tabela_referencia(lambda c: P.referencia_independente(DATA, c))
    n = {v: bi["con"].execute(f"SELECT count(*) FROM bi.{v}").fetchone()[0] for v in P.CONTRATO}
    return gerar_roteiro(ref, n), ref


def test_roteiro_cita_views_relacionamentos_medidas_e_os_290_valores(bi):
    doc, ref = _roteiro_e_ref(bi)
    assert len(ref) == 290
    for v in P.CONTRATO:
        assert f"`{v}.csv`" in doc
    for a, b, c, d in P.RELACIONAMENTOS:
        assert f"`{a}[{b}]` | → | `{c}[{d}]`" in doc
    for i in P.INDICADORES:
        assert f"{i['nome']} =" in doc and i["dax"] in doc
    assert "290 valores" in doc and "checklist_validacao.csv" in doc
    for p in ("Visão Geral", "Filiais", "Produtos e Margem", "Orçamento", "Investigações"):
        assert f"### " in doc and p in doc


def test_roteiro_declara_dax_nao_executado_e_nao_afirma_validacao(bi):
    doc, _ = _roteiro_e_ref(bi)
    assert "nenhuma medida DAX foi executada no Power BI" in doc
    assert "Só quando os 290 valores conferirem" in doc
    assert not re.search(r"medidas? (foram|estão) validadas", doc.lower())


def test_medidas_do_roteiro_so_dependem_de_medidas_anteriores():
    vistos = set()
    for i in P.INDICADORES:
        for m in re.findall(r"(?<![\w\]])\[([^\]]+)\]", i["dax"]):
            assert m in vistos, (i["id"], m)
        vistos.add(i["nome"])


def test_checklist_tem_290_linhas_com_colunas_de_resposta_em_branco(bi, tmp_path):
    from empresax.powerbi_doc import tabela_checklist
    ref = P.tabela_referencia(lambda c: P.referencia_independente(DATA, c))
    t = tabela_checklist(ref)
    assert len(t) == 290 and (t.valor_powerbi == "").all() and (t.confere == "").all()
    assert t.filtros_a_aplicar.str.contains("realizado").all()
    arq = RAIZ / "powerbi" / "referencia" / "checklist_validacao.csv"
    gravado = pd.read_csv(arq, dtype=str, keep_default_na=False)
    assert len(gravado) == 290 and list(gravado.columns) == list(t.columns)
    assert gravado.valor_esperado.map(lambda x: x == "" or float(x) == float(x)).all()


def test_roteiro_versionado_confere_com_o_gerador(bi):
    doc, _ = _roteiro_e_ref(bi)
    assert (RAIZ / "docs" / "POWERBI_ROTEIRO_DE_CONSTRUCAO.md").read_text(encoding="utf-8") == doc


def test_roteiro_guiado_tem_criterios_de_aprovacao_ferramenta_e_contagens(bi):
    doc, _ = _roteiro_e_ref(bi)
    for a in ("A1", "A2", "A3", "A4", "A5", "A6"):
        assert f"| {a} |" in doc
    assert "scripts\\conferir_powerbi.py" in doc and "checklist_preenchido.csv" in doc
    assert "Unidades de exibição = Nenhum" in doc and "Inglês (Estados Unidos)" in doc and "Marcar como tabela de datas" in doc
    assert "59.365" in doc  # contagem esperada de fato_vendas
    assert "NÃO VALIDADAS" in doc and "ainda não foi executado no Power BI Desktop" in doc
