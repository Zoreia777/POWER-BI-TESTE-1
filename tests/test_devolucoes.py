"""Testes das premissas de devolução aprovadas em 14/10/2026 (PN-DEV-01..04).

Cada teste verifica comportamento: valores contra o CSV original (oráculo em pandas/csv),
reconciliações exatas e reação do pipeline quando os dados mudam.
"""
import csv
from decimal import Decimal

import duckdb
import pandas as pd
import pytest

from conftest import DATA, cfg_tmp, copia_dados
from empresax.pipeline import executar

CENT = Decimal("0.01")


def q(con, sql):
    return con.execute(sql).fetchall()


def dec(x):
    return Decimal(str(x))


# ---------------------------------------------------------------- PN-DEV-01: devolução cancela a receita
def test_receita_ajustada_cancela_exatamente_as_linhas_devolvidas(etl, csv_):
    v = csv_["fact_vendas"].assign(mes=lambda d: d.data.str[:7] + "-01")
    esp = v[v.status == "Entregue"].groupby("mes").receita_liquida.sum()
    got = etl["con"].execute("SELECT strftime(mes,'%Y-%m-%d') m, receita_reconhecida_provisoria r FROM mart.kpi_vendas_mes").df().set_index("m").r.astype(float)
    assert (got - esp.reindex(got.index)).abs().max() < 0.02
    # nenhuma linha devolvida contribui para a receita ajustada
    assert q(etl["con"], "SELECT sum(receita_liquida_entregue) FROM mart.fact_vendas WHERE eh_devolvida")[0][0] == 0


def test_valores_originais_das_linhas_devolvidas_ficam_intactos(etl, csv_):
    v = csv_["fact_vendas"]; dev = v[v.status == "Devolvido"].sort_values("id_venda")
    got = etl["con"].execute("SELECT id_venda, quantidade, preco_unitario, desconto_valor, impostos_valor, receita_bruta, receita_liquida, custo_total, data "
                             "FROM mart.fact_vendas WHERE eh_devolvida ORDER BY id_venda").df()
    for c in ("quantidade", "preco_unitario", "desconto_valor", "impostos_valor", "receita_bruta", "receita_liquida", "custo_total"):
        assert (got[c].astype(float).values == dev[c].values).all(), c
    assert list(got.data.astype(str)) == list(dev.data)           # data da VENDA original, nunca alterada


def test_mudanca_no_status_e_refletida_nos_indicadores(tmp_path, csv_):
    """Comportamento: se 3 linhas Entregue virarem Devolvido, a receita ajustada cai exatamente o valor delas."""
    dados = copia_dados(tmp_path / "d")
    v = pd.read_csv(dados / "fact_vendas.csv")
    alvo = v[v.status == "Entregue"].head(3)
    v.loc[alvo.index, "status"] = "Devolvido"
    v.to_csv(dados / "fact_vendas.csv", index=False)
    cfg = cfg_tmp(tmp_path, dados); executar(cfg)
    con = duckdb.connect(str(cfg.arquivo_banco), read_only=True)
    base = csv_["fact_vendas"]
    esp_ajustada = dec(round(base[base.status == "Entregue"].receita_liquida.sum() - alvo.receita_liquida.sum(), 2))
    got = dec(q(con, "SELECT sum(receita_reconhecida_provisoria) FROM mart.kpi_vendas_mes")[0][0])
    assert abs(got - esp_ajustada) <= CENT
    assert q(con, "SELECT linhas_devolvidas FROM mart.kpi_devolucoes_reconciliacao WHERE periodo_venda='TOTAL'")[0][0] == 1313
    assert q(con, "SELECT count(*) FROM mart.kpi_devolucoes_reconciliacao WHERE diferenca_receita <> 0 OR diferenca_custo <> 0")[0][0] == 0
    con.close()


# ---------------------------------------------------------------- PN-DEV-02: custo recuperável (hipótese)
def test_custo_ajustado_exclui_custo_das_devolvidas_e_sensibilidade_existe(etl, csv_):
    v = csv_["fact_vendas"]
    custo_dev = dec(round(v[v.status == "Devolvido"].custo_total.sum(), 2))
    custo_ent = dec(round(v[v.status == "Entregue"].custo_total.sum(), 2))
    rec_ent = dec(round(v[v.status == "Entregue"].receita_liquida.sum(), 2))
    r = q(etl["con"], "SELECT sum(custo_reconhecido_provisorio), sum(custo_devolvido_hipotese_recuperavel), sum(custo_total_registrado), "
                      "sum(lucro_bruto_provisorio), sum(lucro_bruto_se_custo_nao_recuperado) FROM mart.kpi_vendas_mes")[0]
    ajust, dev, reg, lucro, lucro_pior = map(dec, r)
    assert abs(ajust - custo_ent) <= CENT and abs(dev - custo_dev) <= CENT
    assert abs(ajust + dev - reg) <= CENT                                  # custo reconcilia
    assert abs(lucro - (rec_ent - custo_ent)) <= CENT
    assert abs((lucro - lucro_pior) - custo_dev) <= CENT                   # a hipótese vale exatamente o custo devolvido
    assert custo_dev > 0


def test_hipotese_de_custo_esta_identificada_como_nao_comprovada(etl):
    linhas = dict(q(etl["con"], "SELECT id, tipo FROM mart.ref_premissas_negocio WHERE id LIKE 'PN-DEV-%'"))
    assert linhas["PN-DEV-02"].startswith("HIPÓTESE") and "não comprovada" in linhas["PN-DEV-02"]
    assert linhas["PN-DEV-01"].startswith("DECISÃO") and linhas["PN-DEV-03"].startswith("LIMITAÇÃO")


# ---------------------------------------------------------------- PN-DEV-03: sem data de devolução
def test_nenhuma_data_de_devolucao_ou_estorno_foi_criada(etl):
    for tabela in ("fact_vendas", "kpi_vendas_mes", "kpi_devolucoes_reconciliacao", "kpi_devolucoes_pedido", "meta_vs_realizado_mensal"):
        cols = [r[0].lower() for r in q(etl["con"], f"SELECT column_name FROM information_schema.columns WHERE table_schema='mart' AND table_name='{tabela}'")]
        assert not [c for c in cols if "estorno" in c or "data_devolucao" in c or "dt_devolucao" in c], (tabela, cols)
    assert q(etl["con"], "SELECT count(*) FROM mart.fact_vendas WHERE receita_liquida < 0 OR receita_bruta < 0 OR custo_total < 0")[0][0] == 0


def test_devolucoes_mensais_seguem_o_mes_da_venda_original(etl, csv_):
    v = csv_["fact_vendas"].assign(mes=lambda d: d.data.str[:7] + "-01")
    esp = v[v.status == "Devolvido"].groupby("mes").receita_liquida.sum()
    got = etl["con"].execute("SELECT strftime(mes,'%Y-%m-%d') m, devolucoes d, base_temporal_devolucao b FROM mart.kpi_vendas_mes").df().set_index("m")
    assert (got.d.astype(float) - esp.reindex(got.index).fillna(0)).abs().max() < 0.02
    assert set(got.b) == {"mes da venda original (sem data de devolucao)"}


def test_indicador_ajustado_nunca_e_chamado_de_oficial(etl):
    con = etl["con"]
    cols = q(con, "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='mart'")
    for t, c in cols:                            # qualquer coluna 'reconhecida' precisa dizer que é provisória
        if "reconhecid" in c:
            assert c.endswith("provisoria") or c.endswith("provisorio"), (t, c)
    cm = dict(q(con, "SELECT column_name, comment FROM duckdb_columns() WHERE schema_name='mart' AND table_name='kpi_vendas_mes' AND comment IS NOT NULL"))
    assert "NÃO oficial" in cm["receita_reconhecida_provisoria"] and "PN-DEV-01" in cm["receita_reconhecida_provisoria"]
    assert "PN-DEV-03" in cm["devolucoes"]
    pol = q(con, "SELECT DISTINCT politica_devolucao, premissas_aplicadas FROM mart.kpi_vendas_mes")
    assert pol == [("PROVISORIA_EXCLUI_DEVOLVIDAS", "PN-DEV-01;PN-DEV-02;PN-DEV-03;PN-DEV-04")]


# ---------------------------------------------------------------- PN-DEV-04: separadas e reconciliáveis
def test_reconciliacao_por_ano_fecha_em_zero(etl, csv_):
    v = csv_["fact_vendas"]
    rows = etl["con"].execute("SELECT periodo_venda, linhas, linhas_devolvidas, receita_registrada, vendas_entregues, devolucoes, diferenca_receita, diferenca_custo "
                              "FROM mart.kpi_devolucoes_reconciliacao ORDER BY 1").df()
    assert list(rows.periodo_venda) == ["2024", "2025", "2026", "TOTAL"]
    assert (rows.diferenca_receita.astype(float) == 0).all() and (rows.diferenca_custo.astype(float) == 0).all()
    tot = rows[rows.periodo_venda == "TOTAL"].iloc[0]
    assert tot.linhas == len(v) and tot.linhas_devolvidas == 1310
    assert abs(float(tot.receita_registrada) - v.receita_liquida.sum()) < 0.02
    assert abs(float(tot.devolucoes) - v[v.status == "Devolvido"].receita_liquida.sum()) < 0.02
    anos = rows[rows.periodo_venda != "TOTAL"]
    assert abs(float(anos.devolucoes.astype(float).sum()) - float(tot.devolucoes)) < 0.02          # anos somam o total


def test_pedidos_por_tipo_de_devolucao(etl, csv_):
    v = csv_["fact_vendas"]
    por_pedido = v.groupby("id_pedido").status.apply(lambda s: (s == "Devolvido").mean())
    esp = {"sem_devolucao": (por_pedido == 0).sum(), "devolucao_parcial": ((por_pedido > 0) & (por_pedido < 1)).sum(), "devolucao_total": (por_pedido == 1).sum()}
    got = dict(q(etl["con"], "SELECT tipo_pedido, pedidos FROM mart.kpi_devolucoes_pedido"))
    assert got == esp == {"sem_devolucao": 31922, "devolucao_parcial": 915, "devolucao_total": 372}
    assert sum(got.values()) == v.id_pedido.nunique()


# ---------------------------------------------------------------- rastreabilidade
def test_cada_linha_do_mart_aponta_para_a_linha_original_do_csv(etl):
    with open(DATA / "fact_vendas.csv", newline="", encoding="utf-8") as f:
        linhas = {i: (int(r[0]), r[-1]) for i, r in enumerate(csv.reader(f), start=1) if i > 1}
    got = etl["con"].execute("SELECT id_venda, status, linha_csv_origem FROM mart.fact_vendas").fetchall()
    assert len(got) == len(linhas) == 59_365
    assert all(linhas[lin] == (idv, st) for idv, st, lin in got)           # mesma venda e mesmo status na linha apontada
    assert len({lin for _, _, lin in got}) == 59_365 and min(l for _, _, l in got) == 2


# ---------------------------------------------------------------- observações de qualidade
def test_tres_observacoes_documentadas_e_com_acao(etl):
    obs = etl["res"].checagens
    obs = [c for c in obs if c.status == "OBSERVACAO"]
    assert len(obs) == 3 and all(c.acao for c in obs)
    rel = (etl["cfg"].pasta_relatorios / "relatorio_qualidade.md").read_text(encoding="utf-8")
    assert "Ação necessária" in rel and rel.count("OBS-") == 3
    assert "Resultado: **APROVADO**" in rel
