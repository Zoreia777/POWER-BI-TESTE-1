"""Testes da Etapa 2: verificam o COMPORTAMENTO das transformações contra um oráculo em pandas,
e a reação do pipeline a dados ruins (injeção de falhas). Nenhum teste apenas checa existência de arquivo."""
import hashlib
from decimal import Decimal

import duckdb
import pandas as pd
import pytest

from conftest import DATA, cfg_tmp, copia_dados, impressao_digital
from empresax.errors import ArquivoAusenteErro, EstruturaInvalidaErro, QualidadeErro
from empresax.pipeline import executar
from empresax.schema import FKS, TABELAS

CENT = Decimal("0.01")


def q(con, sql):
    return con.execute(sql).fetchall()


def soma(con, sql):
    return Decimal(str(con.execute(sql).fetchone()[0]))


# ===================================================== 1. quantidade de registros por tabela
@pytest.mark.parametrize("tabela", list(TABELAS))
def test_registros_por_camada_igual_ao_csv(etl, csv_, tabela):
    esperado = len(csv_[tabela])
    for camada in ("raw", "stg", "mart"):
        assert q(etl["con"], f"SELECT count(*) FROM {camada}.{tabela}")[0][0] == esperado, f"{camada}.{tabela}"


def test_total_de_registros_do_projeto(etl):
    assert q(etl["con"], "SELECT count(*) FROM mart.fact_vendas")[0][0] == 59_365
    assert q(etl["con"], "SELECT count(*) FROM mart.fact_despesas")[0][0] == 7_075


# ===================================================== 2. integridade das chaves primárias
@pytest.mark.parametrize("tabela", list(TABELAS))
def test_chave_primaria_unica_e_nao_nula(etl, tabela):
    pk = ", ".join(TABELAS[tabela].pk)
    n, distintos = q(etl["con"], f"SELECT count(*), count(DISTINCT ({pk})) FROM mart.{tabela}")[0]
    assert n == distintos
    for c in TABELAS[tabela].pk:
        assert q(etl["con"], f"SELECT count(*) FROM mart.{tabela} WHERE {c} IS NULL")[0][0] == 0


def test_pipeline_rejeita_chave_duplicada(tmp_path):
    dados = copia_dados(tmp_path / "d")
    df = pd.read_csv(dados / "dim_filial.csv")
    pd.concat([df, df.iloc[[0]]]).to_csv(dados / "dim_filial.csv", index=False)
    with pytest.raises(QualidadeErro, match="chave primária"):
        executar(cfg_tmp(tmp_path, dados))


# ===================================================== 3. integridade referencial
@pytest.mark.parametrize("f,c,d,cd", FKS)
def test_sem_orfaos_no_mart(etl, f, c, d, cd):
    orf = q(etl["con"], f"SELECT count(*) FROM mart.{f} a LEFT JOIN mart.{d} b ON a.{c}=b.{cd} WHERE b.{cd} IS NULL")
    assert orf[0][0] == 0


def test_pipeline_rejeita_registro_orfao(tmp_path):
    dados = copia_dados(tmp_path / "d")
    v = pd.read_csv(dados / "fact_vendas.csv")
    v.loc[10, "id_cliente"] = 999_999
    v.to_csv(dados / "fact_vendas.csv", index=False)
    with pytest.raises(QualidadeErro, match="integridade referencial"):
        executar(cfg_tmp(tmp_path, dados))


# ===================================================== 4. conversão correta das datas
def test_tipos_das_colunas_de_data(etl):
    for nome, tab in TABELAS.items():
        for c in tab.colunas:
            if c.tipo == "DATE":
                tipo = q(etl["con"], f"SELECT data_type FROM information_schema.columns WHERE table_schema='mart' "
                                     f"AND table_name='{nome}' AND column_name='{c.nome}'")[0][0]
                assert tipo == "DATE", f"{nome}.{c.nome} = {tipo}"


def test_valores_de_data_batem_com_pandas(etl, csv_):
    esp = pd.to_datetime(csv_["fact_vendas"].set_index("id_venda").data)
    got = etl["con"].execute("SELECT id_venda, data, mes FROM mart.fact_vendas").df().set_index("id_venda")
    assert (pd.to_datetime(got.data) == esp.reindex(got.index)).all()
    assert (pd.to_datetime(got.mes) == esp.reindex(got.index).dt.to_period("M").dt.to_timestamp()).all()
    cal = pd.to_datetime(csv_["dim_calendario"].data)
    assert pd.to_datetime(etl["con"].execute("SELECT data FROM mart.dim_calendario ORDER BY data").df().data).equals(cal)


@pytest.mark.parametrize("ruim", ["2024-13-45", "2024-1-5", "01/02/2024", "texto"])
def test_data_invalida_aborta_pipeline(tmp_path, ruim):
    dados = copia_dados(tmp_path / "d")
    e = pd.read_csv(dados / "fact_despesas.csv", dtype=str)
    e.loc[3, "data"] = ruim
    e.to_csv(dados / "fact_despesas.csv", index=False)
    with pytest.raises(QualidadeErro, match="data"):
        executar(cfg_tmp(tmp_path, dados))


# ===================================================== 5. reconciliação dos valores financeiros
@pytest.mark.parametrize("col", ["receita_bruta", "desconto_valor", "impostos_valor", "receita_liquida", "custo_total"])
def test_totais_de_vendas_batem_com_csv(etl, csv_, col):
    esp = Decimal(str(round(csv_["fact_vendas"][col].sum(), 2)))
    assert abs(soma(etl["con"], f"SELECT sum({col}) FROM mart.fact_vendas") - esp) <= CENT


def test_totais_de_despesa_orcamento_e_metas(etl, csv_):
    for tab, col in (("fact_despesas", "valor"), ("fact_orcamento", "valor_orcado"), ("fact_metas_vendas", "meta_receita_liquida")):
        esp = Decimal(str(round(csv_[tab][col].sum(), 2)))
        assert abs(soma(etl["con"], f"SELECT sum({col}) FROM mart.{tab}") - esp) <= CENT, tab


def test_identidade_financeira_linha_a_linha_no_mart(etl):
    ruins = q(etl["con"], "SELECT count(*) FROM mart.fact_vendas WHERE abs(receita_bruta - desconto_valor - impostos_valor - receita_liquida) > 0.02 "
                          "OR abs(quantidade*preco_unitario - receita_bruta) > 0.02")
    assert ruins[0][0] == 0


def test_pipeline_detecta_inconsistencia_financeira(tmp_path):
    dados = copia_dados(tmp_path / "d")
    v = pd.read_csv(dados / "fact_vendas.csv")
    v.loc[5, "receita_liquida"] += 100.0          # quebra bruta - desconto - imposto = líquida
    v.to_csv(dados / "fact_vendas.csv", index=False)
    with pytest.raises(QualidadeErro, match="líquida"):
        executar(cfg_tmp(tmp_path, dados))


# ===================================================== 6. preservação das devoluções
def test_devolucoes_preservadas_sem_virar_negativas(etl, csv_):
    v = csv_["fact_vendas"]
    dev = v[v.status == "Devolvido"]
    assert len(dev) == 1310
    got = etl["con"].execute("SELECT id_venda, receita_liquida, receita_liquida_devolvida, receita_liquida_entregue, eh_devolvida "
                             "FROM mart.fact_vendas WHERE eh_devolvida ORDER BY id_venda").df()
    assert list(got.id_venda) == list(dev.sort_values("id_venda").id_venda)
    assert (got.receita_liquida > 0).all()                                     # continua positiva
    assert (got.receita_liquida == got.receita_liquida_devolvida).all()        # componente devolvido
    assert (got.receita_liquida_entregue == 0).all()                           # e não conta como entregue
    assert abs(soma(etl["con"], "SELECT sum(receita_liquida_devolvida) FROM mart.fact_vendas") - Decimal(str(round(dev.receita_liquida.sum(), 2)))) <= CENT


def test_entregue_mais_devolvido_fecha_com_total(etl):
    d = q(etl["con"], "SELECT count(*) FROM mart.fact_vendas WHERE receita_liquida_entregue + receita_liquida_devolvida <> receita_liquida "
                      "OR custo_entregue + custo_devolvido <> custo_total")
    assert d[0][0] == 0


def test_pedidos_parcialmente_devolvidos_mantem_status_por_linha(etl, csv_):
    v = csv_["fact_vendas"]
    esp = (v.groupby("id_pedido").status.nunique() > 1).sum()
    got = q(etl["con"], "SELECT count(*) FROM (SELECT id_pedido FROM mart.fact_vendas GROUP BY 1 HAVING count(DISTINCT status) > 1)")[0][0]
    assert got == esp == 915


def test_pipeline_nao_aceita_status_desconhecido(tmp_path):
    dados = copia_dados(tmp_path / "d")
    v = pd.read_csv(dados / "fact_vendas.csv")
    v.loc[0, "status"] = "Cancelado"
    v.to_csv(dados / "fact_vendas.csv", index=False)
    with pytest.raises(QualidadeErro, match="domínio"):
        executar(cfg_tmp(tmp_path, dados))


# ===================================================== 7. preservação das margens negativas
def test_margens_negativas_preservadas_e_identificadas(etl, csv_):
    v = csv_["fact_vendas"]
    esp = set(v[v.custo_total > v.receita_liquida].id_venda)
    assert len(esp) == 612
    got = set(etl["con"].execute("SELECT id_venda FROM mart.fact_vendas WHERE flag_margem_negativa").df().id_venda)
    assert got == esp


def test_precos_e_custos_nao_foram_alterados(etl, csv_):
    got = etl["con"].execute("SELECT id_venda, preco_unitario, custo_total, receita_liquida, desconto_pct FROM mart.fact_vendas ORDER BY id_venda").df()
    esp = csv_["fact_vendas"].sort_values("id_venda")
    for c in ("preco_unitario", "custo_total", "receita_liquida", "desconto_pct"):
        assert (got[c].astype(float).round(4).values == esp[c].round(4).values).all(), c


def test_indicadores_de_margem_negativa_por_dimensao(etl, csv_):
    con, v = etl["con"], csv_["fact_vendas"]
    neg = v[v.custo_total > v.receita_liquida]
    assert q(con, "SELECT sum(linhas_margem_negativa) FROM mart.kpi_margem_negativa_produto")[0][0] == 612
    assert q(con, "SELECT sum(linhas_margem_negativa) FROM mart.kpi_margem_negativa_filial")[0][0] == 612
    assert q(con, "SELECT sum(linhas_margem_negativa) FROM mart.kpi_margem_negativa_mes")[0][0] == 612
    assert q(con, "SELECT sum(linhas_margem_negativa) FROM mart.kpi_margem_negativa_pedido")[0][0] == 612
    assert q(con, "SELECT count(*) FROM mart.kpi_margem_negativa_pedido")[0][0] == neg.id_pedido.nunique()
    prej = Decimal(str(round((neg.custo_total - neg.receita_liquida).sum(), 2)))
    assert abs(soma(con, "SELECT sum(prejuizo_bruto) FROM mart.kpi_margem_negativa_produto") - prej) <= CENT
    top = q(con, "SELECT produto FROM mart.kpi_margem_negativa_produto ORDER BY linhas_margem_negativa DESC, id_produto LIMIT 1")[0][0]
    esp_top = neg.merge(csv_["dim_produto"], on="id_produto").produto.value_counts().idxmax()
    assert top == esp_top


# ===================================================== 8. períodos sem realizado
def test_periodo_realizado_derivado_dos_fatos(etl, csv_):
    ult, completo, coerente = q(etl["con"], "SELECT ultimo_mes_realizado, ultimo_mes_completo, consistente_com_calendario FROM mart.periodo_realizado")[0]
    assert str(ult) == "2026-09-01" and completo and coerente


def test_comparacoes_nao_incluem_meses_futuros(etl, csv_):
    con = etl["con"]
    assert q(con, "SELECT count(*) FROM mart.orcado_vs_realizado_mensal WHERE mes > DATE '2026-09-01'")[0][0] == 0
    assert q(con, "SELECT count(*) FROM mart.orcado_vs_realizado_acumulado WHERE mes_referencia > DATE '2026-09-01'")[0][0] == 0
    assert q(con, "SELECT count(*) FROM mart.meta_vs_realizado_mensal WHERE mes > DATE '2026-09-01'")[0][0] == 0
    o = csv_["fact_orcamento"]
    futuro = o[o.mes > "2026-09-01"]
    assert len(futuro) == 527 and futuro.valor_orcado.sum() > 0
    # o orçamento futuro existe no mart (fato), mas NÃO vira "abaixo do orçamento"
    assert q(con, "SELECT count(*) FROM mart.fact_orcamento WHERE mes > DATE '2026-09-01'")[0][0] == 527


def test_orcado_vs_realizado_reconcilia_com_csv(etl, csv_):
    o, e = csv_["fact_orcamento"], csv_["fact_despesas"]
    orc = Decimal(str(round(o[o.mes <= "2026-09-01"].valor_orcado.sum(), 2)))
    rea = Decimal(str(round(e.valor.sum(), 2)))
    con = etl["con"]
    assert abs(soma(con, "SELECT sum(orcado) FROM mart.orcado_vs_realizado_mensal") - orc) <= CENT
    assert abs(soma(con, "SELECT sum(realizado) FROM mart.orcado_vs_realizado_mensal") - rea) <= CENT
    # 10 linhas orçadas sem nenhum lançamento: realizado = 0 (não some da comparação)
    assert q(con, "SELECT count(*) FROM mart.orcado_vs_realizado_mensal WHERE sem_lancamento_no_mes")[0][0] == 10


def test_orcamento_anual_acumulado_e_realizado_acumulado(etl, csv_):
    con, o, e = etl["con"], csv_["fact_orcamento"], csv_["fact_despesas"]
    o26, e26 = o[o.mes.str[:4] == "2026"], e[e.data.str[:4] == "2026"]
    anual = Decimal(str(round(o26.valor_orcado.sum(), 2)))
    acum = Decimal(str(round(o26[o26.mes <= "2026-09-01"].valor_orcado.sum(), 2)))
    real = Decimal(str(round(e26.valor.sum(), 2)))
    got = q(con, "SELECT sum(orcamento_anual), sum(orcamento_acumulado), sum(realizado_acumulado) FROM mart.orcado_vs_realizado_acumulado "
                 "WHERE mes_referencia = DATE '2026-09-01'")[0]
    assert abs(Decimal(str(got[0])) - anual) <= CENT and abs(Decimal(str(got[1])) - acum) <= CENT and abs(Decimal(str(got[2])) - real) <= CENT
    assert anual > acum                       # o anual inclui out-dez; o acumulado não
    # a comparação justa (acumulado x acumulado) difere da ingênua (realizado x anual)
    assert abs(real / acum - Decimal(1)) < abs(real / anual - Decimal(1))


def test_acumulado_cresce_e_reinicia_a_cada_ano(etl):
    df = etl["con"].execute("SELECT ano, mes_referencia, id_departamento, orcamento_acumulado, realizado_acumulado "
                            "FROM mart.orcado_vs_realizado_acumulado ORDER BY id_departamento, mes_referencia").df()
    for _, g in df.groupby(["id_departamento", "ano"]):
        assert g.realizado_acumulado.is_monotonic_increasing and g.orcamento_acumulado.is_monotonic_increasing
    jan = df[df.mes_referencia.astype(str).str[5:7] == "01"]
    assert (jan.orcamento_acumulado.astype(float) < df.groupby(["id_departamento", "ano"]).orcamento_acumulado.transform("max").loc[jan.index].astype(float) + 1e-9).all()


def test_ultimo_mes_realizado_acompanha_os_dados(tmp_path, csv_):
    """Se o último mês deixa de existir nos fatos, o corte recua sozinho (nada está 'hardcoded')."""
    dados = copia_dados(tmp_path / "d")
    for arq, col in (("fact_vendas", "data"), ("fact_despesas", "data")):
        d = pd.read_csv(dados / f"{arq}.csv")
        d[d[col] < "2026-09-01"].to_csv(dados / f"{arq}.csv", index=False)
    cal = pd.read_csv(dados / "dim_calendario.csv")
    cal.loc[cal.data >= "2026-09-01", ["realizado", "status_periodo"]] = [0, "Projetado"]
    cal.to_csv(dados / "dim_calendario.csv", index=False)
    r = executar(cfg_tmp(tmp_path, dados))
    con = duckdb.connect(str(cfg_tmp(tmp_path, dados).arquivo_banco), read_only=True)
    assert str(q(con, "SELECT ultimo_mes_realizado FROM mart.periodo_realizado")[0][0]) == "2026-08-01"
    assert q(con, "SELECT count(*) FROM mart.orcado_vs_realizado_mensal WHERE mes >= DATE '2026-09-01'")[0][0] == 0
    con.close()


# ===================================================== 9. ausência de duplicação após reexecução
def test_reexecucao_e_idempotente(tmp_path):
    cfg = cfg_tmp(tmp_path)
    executar(cfg)
    con = duckdb.connect(str(cfg.arquivo_banco))
    antes = impressao_digital(con)
    exec_antes = con.execute("SELECT count(*) FROM ops.execucoes").fetchone()[0]
    rel_antes = (cfg.pasta_relatorios / "relatorio_qualidade.md").read_text(encoding="utf-8")
    con.close()
    executar(cfg)
    con = duckdb.connect(str(cfg.arquivo_banco))
    depois = impressao_digital(con)
    assert len(antes) == 13 + 13 + 25          # 13 raw + 13 stg + 25 mart
    assert antes == depois                     # mesmas linhas e mesmo conteúdo
    assert con.execute("SELECT count(*) FROM ops.execucoes").fetchone()[0] == exec_antes + 1   # só o histórico cresce
    assert (cfg.pasta_relatorios / "relatorio_qualidade.md").read_text(encoding="utf-8") == rel_antes
    con.close()


def test_falha_faz_rollback_e_preserva_ultimo_estado_valido(tmp_path):
    dados = copia_dados(tmp_path / "d")
    cfg = cfg_tmp(tmp_path, dados)
    executar(cfg)
    con = duckdb.connect(str(cfg.arquivo_banco)); bom = impressao_digital(con); con.close()
    v = pd.read_csv(dados / "fact_vendas.csv"); v.loc[0, "id_cliente"] = 999_999; v.to_csv(dados / "fact_vendas.csv", index=False)
    with pytest.raises(QualidadeErro):
        executar(cfg)
    con = duckdb.connect(str(cfg.arquivo_banco))
    assert impressao_digital(con) == bom
    assert con.execute("SELECT status FROM ops.execucoes ORDER BY iniciado_em DESC LIMIT 1").fetchone()[0] == "FALHA"
    con.close()


def test_csvs_originais_nao_sao_modificados(etl):
    assert etl["csv_inalterados"]
    sha = dict(etl["con"].execute("SELECT arquivo, sha256 FROM ops.arquivos_origem").fetchall())
    for p in DATA.glob("*.csv"):
        assert sha[p.name] == hashlib.sha256(p.read_bytes()).hexdigest()


def test_erros_de_estrutura(tmp_path):
    dados = copia_dados(tmp_path / "d")
    (dados / "dim_canal.csv").unlink()
    with pytest.raises(ArquivoAusenteErro):
        executar(cfg_tmp(tmp_path / "a", dados))
    dados2 = copia_dados(tmp_path / "d2")
    c = pd.read_csv(dados2 / "dim_canal.csv").rename(columns={"canal": "nome_canal"})
    c.to_csv(dados2 / "dim_canal.csv", index=False)
    with pytest.raises(EstruturaInvalidaErro):
        executar(cfg_tmp(tmp_path / "b", dados2))


# ===================================================== 10. consistência dos KPIs
def test_kpi_vendas_mes_bate_com_pandas(etl, csv_):
    v = csv_["fact_vendas"].assign(mes=lambda d: d.data.str[:7] + "-01")
    esp = v.groupby("mes").apply(lambda g: pd.Series({
        "registrada": g.receita_liquida.sum(),
        "entregue": g[g.status == "Entregue"].receita_liquida.sum(),
        "devolvida": g[g.status == "Devolvido"].receita_liquida.sum(),
        "custo_ent": g[g.status == "Entregue"].custo_total.sum(),
        "neg": (g.custo_total > g.receita_liquida).sum(),
        "pedidos": g.id_pedido.nunique()}), include_groups=False)
    got = etl["con"].execute("SELECT strftime(mes,'%Y-%m-%d') m, receita_liquida_registrada r, vendas_entregues e, devolucoes d, "
                             "custo_reconhecido_provisorio c, linhas_margem_negativa n, pedidos p FROM mart.kpi_vendas_mes ORDER BY mes").df().set_index("m")
    assert len(got) == 33
    for a, b in (("r", "registrada"), ("e", "entregue"), ("d", "devolvida"), ("c", "custo_ent")):
        assert (got[a].astype(float) - esp[b].reindex(got.index)).abs().max() < 0.02, a
    assert (got.n == esp.neg.reindex(got.index)).all() and (got.p == esp.pedidos.reindex(got.index)).all()


def test_taxa_de_devolucao_e_razao_de_somas(etl, csv_):
    v = csv_["fact_vendas"]
    esp = v[v.status == "Devolvido"].receita_liquida.sum() / v.receita_liquida.sum()
    ponderada = float(q(etl["con"], "SELECT sum(devolucoes)/sum(receita_liquida_registrada) FROM mart.kpi_vendas_mes")[0][0])
    assert ponderada == pytest.approx(esp, rel=1e-9) and 0.0218 < ponderada < 0.0220   # ~2,19%
    media_simples = float(q(etl["con"], "SELECT avg(taxa_devolucao_valor_pct) FROM mart.kpi_vendas_mes")[0][0])
    assert media_simples != pytest.approx(ponderada, rel=1e-6)      # a média simples de % seria diferente (e errada)


def test_politica_de_devolucao_provisoria_esta_explicita(etl):
    pol = q(etl["con"], "SELECT DISTINCT politica_devolucao FROM mart.kpi_vendas_mes")
    assert pol == [("PROVISORIA_EXCLUI_DEVOLVIDAS",)]
    cols = [r[0] for r in q(etl["con"], "SELECT column_name FROM information_schema.columns WHERE table_name='kpi_vendas_mes' AND table_schema='mart'")]
    assert {"vendas_entregues", "devolucoes", "receita_liquida_registrada", "receita_reconhecida_provisoria"} <= set(cols)


def test_variacao_de_preco_e_ponderada_e_separada_do_desconto(etl, csv_):
    v = csv_["fact_vendas"].merge(csv_["dim_produto"][["id_produto", "preco_lista", "produto"]], on="id_produto")
    v["mes"] = v.data.str[:7] + "-01"
    g = v.assign(lista=v.quantidade * v.preco_lista, bruta=v.quantidade * v.preco_unitario).groupby(["mes", "produto"]).agg(
        lista=("lista", "sum"), bruta=("bruta", "sum"), desc=("desconto_valor", "sum")).reset_index()
    g["var"] = g.bruta / g.lista - 1
    g["desc_pct"] = g.desc / g.bruta
    got = etl["con"].execute("SELECT strftime(mes,'%Y-%m-%d') mes, produto, variacao_preco_pct v, desconto_pct_efetivo d, "
                             "efeito_preco_valor e, valor_a_preco_lista l, receita_bruta_preco_praticado b FROM mart.kpi_preco_produto_mes").df()
    m = got.merge(g, on=["mes", "produto"])
    assert len(m) == len(got) == len(g)
    assert (m.v.astype(float) - m["var"]).abs().max() < 1e-5 and (m.d.astype(float) - m.desc_pct).abs().max() < 1e-5
    assert ((m.l.astype(float) + m.e.astype(float)) - m.b.astype(float)).abs().max() < 0.02    # lista + efeito-preço = bruta


def test_variacao_de_preco_mensal_e_razao_de_somas_nao_media_de_percentuais(etl, csv_):
    v = csv_["fact_vendas"].merge(csv_["dim_produto"][["id_produto", "preco_lista"]], on="id_produto")
    v["mes"] = v.data.str[:7] + "-01"
    v["lista"], v["efeito"] = v.quantidade * v.preco_lista, v.quantidade * (v.preco_unitario - v.preco_lista)
    g = v.groupby("mes")[["lista", "efeito"]].sum()
    esp = g.efeito / g.lista
    got = etl["con"].execute("SELECT strftime(mes,'%Y-%m-%d') m, variacao_preco_pct FROM mart.kpi_preco_mes ORDER BY mes").df().set_index("m")
    assert len(got) == 33 and (got.variacao_preco_pct.astype(float) - esp.reindex(got.index)).abs().max() < 1e-5
    # a armadilha: média simples dos percentuais produto-mês dá outro número
    media = etl["con"].execute("SELECT mes, avg(variacao_preco_pct) a FROM mart.kpi_preco_produto_mes GROUP BY mes ORDER BY mes").df()
    assert (media.a.astype(float).values - got.variacao_preco_pct.astype(float).values).__abs__().max() > 1e-3


def test_preco_fixo_com_desconto_prova_que_sao_medidas_distintas(etl):
    """Smartphone X Max tem preço praticado = preço de lista (variação 0), mas recebe desconto."""
    df = etl["con"].execute("SELECT variacao_preco_pct v, desconto_pct_efetivo d FROM mart.kpi_preco_produto_mes WHERE produto='Smartphone X Max'").df()
    assert (df.v.astype(float) == 0).all() and (df.d.astype(float) > 0.01).all()
    gen = etl["con"].execute("SELECT max(variacao_preco_pct) FROM mart.kpi_preco_produto_mes").fetchone()[0]
    assert 0.0 < float(gen) < 0.07


def test_variacao_de_preco_por_linha_respeita_granularidade(etl, csv_):
    got = etl["con"].execute("SELECT id_venda, preco_unitario, preco_lista, variacao_preco_vs_lista_pct v, efeito_preco_valor e, quantidade FROM mart.fact_vendas").df()
    assert ((got.preco_unitario.astype(float) / got.preco_lista.astype(float) - 1) - got.v.astype(float)).abs().max() < 1e-5
    assert (got.e.astype(float) - got.quantidade * (got.preco_unitario.astype(float) - got.preco_lista.astype(float))).abs().max() < 0.02


def test_metas_x_realizado_so_ate_ultimo_mes_e_atingimento_correto(etl, csv_):
    m = csv_["fact_metas_vendas"]; v = csv_["fact_vendas"]
    a = m[(m.mes == "2026-09-01") & (m.id_filial == 1)].meta_receita_liquida.iloc[0]
    ent = v[(v.data.str[:7] == "2026-09") & (v.id_filial == 1) & (v.status == "Entregue")].receita_liquida.sum()
    got = float(q(etl["con"], "SELECT atingimento_provisorio_pct FROM mart.meta_vs_realizado_mensal WHERE mes = DATE '2026-09-01' AND id_filial = 1")[0][0])
    assert got == pytest.approx(ent / a, abs=1e-5)


def test_relatorio_de_qualidade_aprovado_e_logs(etl):
    rel = (etl["cfg"].pasta_relatorios / "relatorio_qualidade.md").read_text(encoding="utf-8")
    assert "Resultado: **APROVADO**" in rel and "0 erros" in rel
    assert etl["res"].arquivo_log.exists() and "ETL SUCESSO" in etl["res"].arquivo_log.read_text(encoding="utf-8")
    assert q(etl["con"], "SELECT count(*) FROM ops.qualidade_checks WHERE status='ERRO'")[0][0] == 0
