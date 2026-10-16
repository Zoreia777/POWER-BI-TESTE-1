"""Validações de qualidade e relatório.

Cada validação vira uma `Checagem` com esperado x obtido. Status:
  OK          -> passou
  ERRO        -> falha obrigatória (o pipeline aborta e faz rollback)
  OBSERVACAO  -> fato relevante para o negócio que NÃO é erro (ex.: devoluções preservadas)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from .config import Config
from .schema import DOMINIOS, FKS, SQL_TYPE, TABELAS

REGEX = {  # formatos estritos: o CAST do DuckDB é permissivo demais ('1.0' viraria inteiro 1)
    "INT": r"^-?[0-9]+$",
    "MONEY": r"^-?[0-9]+(\.[0-9]{1,2})?$",
    "PCT": r"^-?[0-9]+(\.[0-9]{1,4})?$",
    "DATE": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
    "DOUBLE": r"^-?[0-9]+(\.[0-9]+)?$",
}


@dataclass
class Checagem:
    camada: str
    tabela: str
    regra: str
    esperado: object
    obtido: object
    status: str = ""
    acao: str = ""          # só para OBSERVACAO: o que (não) precisa ser feito

    def __post_init__(self) -> None:
        if not self.status:
            self.status = "OK" if str(self.esperado) == str(self.obtido) else "ERRO"


def _q(con, sql: str):
    return con.execute(sql).fetchone()[0]


def expr(coluna: str) -> str:
    """Valor bruto normalizado: sem espaços nas pontas e vazio => NULL."""
    return f"NULLIF(TRIM({coluna}), '')"


# ---------------------------------------------------------------- RAW -> STG (antes do CAST)
def checar_conversoes(con: duckdb.DuckDBPyConnection) -> list[Checagem]:
    """Conta, por tabela, valores que NÃO convertem para o tipo do contrato e nulos indevidos."""
    out: list[Checagem] = []
    for nome, tab in TABELAS.items():
        partes, rotulos = [], []
        for c in tab.colunas:
            e = expr(c.nome)
            if not c.anulavel:
                partes.append(f"count(*) FILTER (WHERE {e} IS NULL)")
                rotulos.append(f"{c.nome}: nulo/vazio em coluna obrigatória")
            if c.tipo != "TEXT":
                ruim = f"({e} IS NOT NULL AND (NOT regexp_matches({e}, '{REGEX[c.tipo]}') OR TRY_CAST({e} AS {SQL_TYPE[c.tipo]}) IS NULL))"
                partes.append(f"count(*) FILTER (WHERE {ruim})")
                rotulos.append(f"{c.nome}: valor não conversível para {c.tipo}")
        linha = con.execute(f"SELECT {', '.join(partes)} FROM raw.{nome}").fetchone()
        for rot, n in zip(rotulos, linha):
            if n:                                   # só registra o que falhou (evita 150 linhas 'OK')
                out.append(Checagem("stg", nome, rot, 0, n))
        out.append(Checagem("stg", nome, "tipagem e obrigatoriedade das colunas (nenhuma falha)", 0,
                            sum(linha)))
    return out


# ---------------------------------------------------------------- STG
def checar_staging(con: duckdb.DuckDBPyConnection, cfg: Config) -> list[Checagem]:
    out: list[Checagem] = []
    tol = cfg.tolerancia_rs
    for nome, tab in TABELAS.items():
        n_raw, n_stg = _q(con, f"SELECT count(*) FROM raw.{nome}"), _q(con, f"SELECT count(*) FROM stg.{nome}")
        out.append(Checagem("stg", nome, "registros stg = raw (nada descartado)", n_raw, n_stg))
        pk = ", ".join(tab.pk)
        dup = n_stg - _q(con, f"SELECT count(*) FROM (SELECT DISTINCT {pk} FROM stg.{nome})")
        out.append(Checagem("stg", nome, f"chave primária única ({pk})", 0, dup))
        # datas: reconversão para texto deve ser idêntica ao valor original
        for c in tab.colunas:
            if c.tipo == "DATE":
                dif = _q(con, f"SELECT count(*) FROM raw.{nome} r JOIN stg.{nome} s USING (_linha_origem) "
                              f"WHERE CAST(s.{c.nome} AS VARCHAR) IS DISTINCT FROM {expr('r.' + c.nome)}")
                out.append(Checagem("stg", nome, f"data {c.nome}: valor convertido = texto original", 0, dif))
            if c.tipo in ("MONEY", "PCT"):
                sr = _q(con, f"SELECT coalesce(sum(CAST({expr(c.nome)} AS DECIMAL(24,4))),0) FROM raw.{nome}")
                ss = _q(con, f"SELECT coalesce(sum(CAST({c.nome} AS DECIMAL(24,4))),0) FROM stg.{nome}")
                out.append(Checagem("stg", nome, f"soma de {c.nome}: raw = stg", sr, ss))
    for (t, c), dom in DOMINIOS.items():
        lista = ", ".join(f"'{d}'" for d in dom)
        out.append(Checagem("stg", t, f"domínio de {c} ∈ {dom}", 0,
                            _q(con, f"SELECT count(*) FROM stg.{t} WHERE {c} NOT IN ({lista})")))
    for f, c, d, cd in FKS:
        orf = _q(con, f"SELECT count(*) FROM stg.{f} a LEFT JOIN stg.{d} b ON a.{c} = b.{cd} "
                      f"WHERE a.{c} IS NOT NULL AND b.{cd} IS NULL")
        out.append(Checagem("stg", f, f"integridade referencial {c} -> {d}.{cd}", 0, orf))
    # intervalos plausíveis
    for t in ("dim_produto", "fact_vendas", "fact_metas_vendas"):
        for c in TABELAS[t].colunas:
            if c.tipo == "PCT":
                bad = _q(con, f"SELECT count(*) FROM stg.{t} WHERE {c.nome} < 0 OR {c.nome} > 1")
                out.append(Checagem("stg", t, f"{c.nome} entre 0 e 1", 0, bad))
    out.append(Checagem("stg", "fact_vendas", "quantidade, preço, receita e custo > 0", 0, _q(
        con, "SELECT count(*) FROM stg.fact_vendas WHERE quantidade<=0 OR preco_unitario<=0 OR receita_liquida<=0 OR custo_total<=0")))
    out.append(Checagem("stg", "fact_despesas", "valor da despesa > 0", 0,
                        _q(con, "SELECT count(*) FROM stg.fact_despesas WHERE valor <= 0")))
    # reconciliação financeira linha a linha
    out.append(Checagem("stg", "fact_vendas", f"receita_bruta = quantidade x preço (±R$ {tol})", 0, _q(
        con, f"SELECT count(*) FROM stg.fact_vendas WHERE abs(quantidade*preco_unitario - receita_bruta) > {tol}")))
    out.append(Checagem("stg", "fact_vendas", f"desconto_valor = bruta x desconto_pct (±R$ {tol})", 0, _q(
        con, f"SELECT count(*) FROM stg.fact_vendas WHERE abs(receita_bruta*desconto_pct - desconto_valor) > {tol}")))
    out.append(Checagem("stg", "fact_vendas", f"líquida = bruta − desconto − impostos (±R$ {tol})", 0, _q(
        con, f"SELECT count(*) FROM stg.fact_vendas WHERE abs(receita_bruta-desconto_valor-impostos_valor-receita_liquida) > {tol}")))
    return out


# ---------------------------------------------------------------- MART
def checar_mart(con: duckdb.DuckDBPyConnection, cfg: Config) -> list[Checagem]:
    out: list[Checagem] = []
    for nome in TABELAS:
        out.append(Checagem("mart", nome, "registros mart = stg", _q(con, f"SELECT count(*) FROM stg.{nome}"),
                            _q(con, f"SELECT count(*) FROM mart.{nome}")))
    for c in ("receita_bruta", "desconto_valor", "impostos_valor", "receita_liquida", "custo_total"):
        out.append(Checagem("mart", "fact_vendas", f"soma de {c}: stg = mart",
                            _q(con, f"SELECT sum({c}) FROM stg.fact_vendas"), _q(con, f"SELECT sum({c}) FROM mart.fact_vendas")))
    out.append(Checagem("mart", "fact_vendas", "entregue + devolvida = receita líquida total",
                        _q(con, "SELECT sum(receita_liquida) FROM mart.fact_vendas"),
                        _q(con, "SELECT sum(receita_liquida_entregue + receita_liquida_devolvida) FROM mart.fact_vendas")))
    out.append(Checagem("mart", "fact_vendas", "custo entregue + devolvido = custo total",
                        _q(con, "SELECT sum(custo_total) FROM mart.fact_vendas"),
                        _q(con, "SELECT sum(custo_entregue + custo_devolvido) FROM mart.fact_vendas")))
    dev = _q(con, "SELECT count(*) FROM stg.fact_vendas WHERE status='Devolvido'")
    out.append(Checagem("mart", "fact_vendas", "devoluções preservadas (linhas com eh_devolvida)", dev,
                        _q(con, "SELECT count(*) FROM mart.fact_vendas WHERE eh_devolvida")))
    out.append(Checagem("mart", "fact_vendas", "devoluções NÃO foram transformadas em valor negativo", 0,
                        _q(con, "SELECT count(*) FROM mart.fact_vendas WHERE eh_devolvida AND receita_liquida <= 0")))
    neg = _q(con, "SELECT count(*) FROM stg.fact_vendas WHERE custo_total > receita_liquida")
    out.append(Checagem("mart", "fact_vendas", "margens negativas preservadas (linhas sinalizadas)", neg,
                        _q(con, "SELECT count(*) FROM mart.fact_vendas WHERE flag_margem_negativa")))
    out.append(Checagem("mart", "fact_vendas", "preço praticado preservado (sem alteração)", 0, _q(
        con, "SELECT count(*) FROM mart.fact_vendas m JOIN stg.fact_vendas s USING (id_venda) "
             "WHERE m.preco_unitario <> s.preco_unitario OR m.custo_total <> s.custo_total")))
    # período realizado
    ult = _q(con, "SELECT ultimo_mes_realizado FROM mart.periodo_realizado")
    out.append(Checagem("mart", "periodo_realizado", "último mês realizado coerente com dim_calendario", True,
                        _q(con, "SELECT consistente_com_calendario FROM mart.periodo_realizado")))
    for t in ("orcado_vs_realizado_mensal", "orcado_vs_realizado_acumulado", "meta_vs_realizado_mensal"):
        col = "mes_referencia" if t.endswith("acumulado") else "mes"
        out.append(Checagem("mart", t, "nenhuma linha em meses sem realizado", 0,
                            _q(con, f"SELECT count(*) FROM mart.{t} WHERE {col} > DATE '{ult}'")))
    out.append(Checagem("mart", "orcado_vs_realizado_mensal", "Σ orçado = Σ orçamento até o último mês realizado",
                        _q(con, f"SELECT coalesce(sum(valor_orcado),0) FROM stg.fact_orcamento WHERE mes <= DATE '{ult}'"),
                        _q(con, "SELECT coalesce(sum(orcado),0) FROM mart.orcado_vs_realizado_mensal")))
    out.append(Checagem("mart", "orcado_vs_realizado_mensal", "Σ realizado = Σ despesas até o último mês realizado",
                        _q(con, f"SELECT coalesce(sum(valor),0) FROM stg.fact_despesas WHERE data < DATE '{ult}' + INTERVAL 1 MONTH"),
                        _q(con, "SELECT coalesce(sum(realizado),0) FROM mart.orcado_vs_realizado_mensal")))
    out.append(Checagem("mart", "kpi_vendas_mes", "Σ vendas entregues + devoluções = Σ receita líquida registrada",
                        _q(con, "SELECT sum(receita_liquida_registrada) FROM mart.kpi_vendas_mes"),
                        _q(con, "SELECT sum(vendas_entregues + devolucoes) FROM mart.kpi_vendas_mes")))
    # reconciliação das devoluções (views do mart) e premissas registradas
    out.append(Checagem("mart", "kpi_devolucoes_reconciliacao", "registrada − entregues − devoluções = 0 (receita) e custo idem", 0, _q(
        con, "SELECT count(*) FROM mart.kpi_devolucoes_reconciliacao WHERE diferenca_receita <> 0 OR diferenca_custo <> 0")))
    out.append(Checagem("mart", "kpi_devolucoes_pedido", "pedidos classificados (sem/parcial/total) = pedidos distintos",
                        _q(con, "SELECT count(DISTINCT id_pedido) FROM mart.fact_vendas"),
                        _q(con, "SELECT sum(pedidos) FROM mart.kpi_devolucoes_pedido")))
    out.append(Checagem("mart", "ref_premissas_negocio", "premissas de devolução PN-DEV-01..04 registradas", 4,
                        _q(con, "SELECT count(*) FROM mart.ref_premissas_negocio WHERE id LIKE 'PN-DEV-%'")))
    out.append(Checagem("mart", "fact_vendas", "rastreabilidade: linha_csv_origem preenchida e única", 0, _q(
        con, "SELECT (SELECT count(*) FROM mart.fact_vendas WHERE linha_csv_origem IS NULL) + "
             "(SELECT count(*) - count(DISTINCT linha_csv_origem) FROM mart.fact_vendas)")))
    # observações de negócio (não são erros) — cada uma diz se exige ação
    fut = _q(con, f"SELECT count(*) FROM stg.fact_orcamento WHERE mes > DATE '{ult}'")
    out += [
        Checagem("mart", "fact_vendas", "OBS-1: linhas 'Devolvido' mantidas com valores originais positivos; receita ajustada aplica PN-DEV-01/02/03",
                 "-", dev, "OBSERVACAO",
                 "Nenhuma no ETL: decisão de negócio registrada. Manter o rótulo 'provisória/não oficial' nos KPIs; reabrir se surgir data ou lançamento de estorno."),
        Checagem("mart", "fact_vendas", "OBS-2: linhas com margem negativa (custo > receita líquida) preservadas e sinalizadas",
                 "-", neg, "OBSERVACAO",
                 "Nenhuma no ETL (dado preservado). A investigação por produto/período é tema da análise (Etapas 3 e 4)."),
        Checagem("mart", "fact_orcamento", f"OBS-3: linhas de orçamento posteriores a {ult} (futuro) excluídas das comparações",
                 "-", fut, "OBSERVACAO",
                 "Nenhuma: orçamento é prospectivo. O corte avança sozinho quando houver novos meses realizados."),
    ]
    return out


# ---------------------------------------------------------------- relatório
def gravar_relatorio(checks: list[Checagem], contagens: dict[str, dict[str, int]], destino: Path, cfg: Config) -> None:
    """Relatório determinístico (sem horários): rodar duas vezes gera o mesmo arquivo."""
    n_err = sum(c.status == "ERRO" for c in checks)
    L = ["# Relatório de qualidade do ETL", "",
         f"Resultado: **{'FALHA' if n_err else 'APROVADO'}** — {sum(c.status == 'OK' for c in checks)} validações OK, "
         f"{n_err} erros, {sum(c.status == 'OBSERVACAO' for c in checks)} observações.", "",
         f"Política de devoluções vigente: `{cfg.politica_devolucao}`", "",
         "## Registros por camada", "", "| Tabela | raw | stg | mart |", "|---|---:|---:|---:|"]
    nomes = sorted({t for d in contagens.values() for t in d})
    for t in nomes:
        L.append(f"| {t} | " + " | ".join(f"{contagens[s].get(t, '—'):,}" if isinstance(contagens[s].get(t), int) else "—" for s in ("raw", "stg", "mart")) + " |")
    for titulo, filtro in (("Erros", "ERRO"), ("Observações", "OBSERVACAO")):
        sel = [c for c in checks if c.status == filtro]
        if sel:
            L += ["", f"## {titulo}", "", "| Camada | Tabela | Regra | Esperado | Obtido | Ação necessária |", "|---|---|---|---|---|---|"]
            L += [f"| {c.camada} | {c.tabela} | {c.regra} | {c.esperado} | {c.obtido} | {c.acao or '—'} |" for c in sel]
    L += ["", "## Validações aprovadas", "", "| Camada | Tabela | Regra | Esperado | Obtido |", "|---|---|---|---|---|"]
    L += [f"| {c.camada} | {c.tabela} | {c.regra} | {c.esperado} | {c.obtido} |" for c in checks if c.status == "OK"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(L) + "\n", encoding="utf-8")
