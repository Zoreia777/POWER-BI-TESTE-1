"""Camada de consumo do Power BI (schema `bi`): contrato, dicionário de indicadores e valores de referência.

IMPORTANTE: as medidas DAX deste módulo NÃO foram executadas no Power BI (este ambiente não o possui). O que existe aqui:
  * views SQL estáveis (testadas contra cálculos independentes em pandas);
  * definições DAX escritas e verificadas por LINT estático (colunas/medidas existem; parênteses balanceados);
  * VALORES DE REFERÊNCIA calculados de forma independente, para o analista conferir no Power BI (checklist em docs/POWERBI_CAMADA_DE_CONSUMO.md).
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from .config import RAIZ
from .consultas import para_csv

PASTA_SQL = RAIZ / "sql" / "powerbi"

# ---------------------------------------------------------------- contrato das views (nomes e ordem das colunas)
CONTRATO: dict[str, list[str]] = {
    "dim_calendario": ["data", "ano", "semestre", "trimestre", "mes_num", "mes_abrev", "ano_mes", "primeiro_dia_mes", "ordem_ano_mes", "dia_util", "realizado"],
    "dim_produto": ["id_produto", "sku", "produto", "categoria", "subcategoria", "preco_lista", "aliquota_imposto"],
    "dim_filial": ["id_filial", "filial", "cidade", "uf", "regiao", "tipo", "concentra_despesas_corporativas"],
    "dim_canal": ["id_canal", "canal", "tipo_canal"],
    "dim_departamento": ["id_departamento", "departamento", "centro_custo", "tipo_area"],
    "dim_categoria_despesa": ["id_categoria_despesa", "categoria_despesa", "grupo_dre", "tipo_custo", "ordem_dre"],
    "dim_cliente": ["id_cliente", "nome_cliente", "segmento", "cidade", "uf", "regiao"],
    "fato_vendas": ["id_venda", "id_pedido", "data", "mes", "id_cliente", "id_produto", "id_filial", "id_vendedor", "id_canal", "status",
                    "quantidade", "preco_unitario", "desconto_pct", "receita_bruta", "desconto_valor", "impostos_valor", "receita_registrada",
                    "receita_ajustada", "devolucao", "custo_registrado", "custo_ajustado", "lucro_bruto_ajustado", "unidades_entregues",
                    "flag_margem_negativa", "flag_devolvida", "linha_csv_origem"],
    "fato_despesas": ["id_despesa", "data", "mes", "id_departamento", "id_categoria_despesa", "id_filial", "fornecedor", "valor"],
    "fato_orcamento": ["mes", "id_departamento", "id_categoria_despesa", "id_filial", "valor_orcado", "mes_realizado"],
    "fato_orcado_realizado_mes": ["mes", "id_departamento", "id_categoria_despesa", "id_filial", "orcado", "realizado", "flag_sem_orcamento", "flag_sem_lancamento"],
    "kpi_empresa_mes": ["mes", "receita_registrada", "vendas_entregues", "devolucoes", "receita_ajustada", "custo_ajustado", "lucro_bruto_ajustado", "despesas",
                        "resultado_operacional_estimado", "margem_bruta_pct", "margem_operacional_estimada_pct", "pedidos", "unidades"],
}

# (tabela_fato, coluna) -> (dimensão, coluna) — relacionamentos do modelo (muitos-para-um, filtro da dimensão para o fato)
RELACIONAMENTOS = [
    ("fato_vendas", "data", "dim_calendario", "data"), ("fato_vendas", "id_produto", "dim_produto", "id_produto"),
    ("fato_vendas", "id_filial", "dim_filial", "id_filial"), ("fato_vendas", "id_canal", "dim_canal", "id_canal"),
    ("fato_vendas", "id_cliente", "dim_cliente", "id_cliente"),
    ("fato_despesas", "data", "dim_calendario", "data"), ("fato_despesas", "id_filial", "dim_filial", "id_filial"),
    ("fato_despesas", "id_departamento", "dim_departamento", "id_departamento"),
    ("fato_despesas", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
    ("fato_orcamento", "mes", "dim_calendario", "data"), ("fato_orcamento", "id_filial", "dim_filial", "id_filial"),
    ("fato_orcamento", "id_departamento", "dim_departamento", "id_departamento"),
    ("fato_orcamento", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
    ("fato_orcado_realizado_mes", "mes", "dim_calendario", "data"), ("fato_orcado_realizado_mes", "id_filial", "dim_filial", "id_filial"),
    ("fato_orcado_realizado_mes", "id_departamento", "dim_departamento", "id_departamento"),
    ("fato_orcado_realizado_mes", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
]

_SEM_PROD = "IF ( ISFILTERED ( dim_produto ) || ISFILTERED ( dim_canal ) || ISFILTERED ( dim_cliente ), BLANK (), {} )"


def _ind(id_, nome, tipo, definicao, dax, grao, filtros, formato, premissa=""):
    return dict(id=id_, nome=nome, tipo=tipo, definicao=definicao, dax=dax, grao=grao, filtros=filtros, formato=formato, premissa=premissa)


INDICADORES = [
    _ind("IND-01", "Receita Registrada", "base", "Receita líquida (bruta − desconto − impostos) de TODAS as linhas, inclusive devolvidas.", "SUM ( fato_vendas[receita_registrada] )",
         "item de pedido", "calendário, filial, produto, canal, cliente", "R$ #,0", "PN-DEV-01/04: indicador separado, sempre reconciliável"),
    _ind("IND-02", "Vendas Entregues", "base", "Receita líquida das linhas com status Entregue.", 'CALCULATE ( SUM ( fato_vendas[receita_registrada] ), fato_vendas[status] = "Entregue" )',
         "item de pedido", "idem IND-01", "R$ #,0"),
    _ind("IND-03", "Devoluções", "base", "Receita líquida das linhas com status Devolvido (devolução integral, PN-DEV-01).", "SUM ( fato_vendas[devolucao] )",
         "item de pedido", "idem IND-01", "R$ #,0", "Sem data de devolução: fica no mês da venda (PN-DEV-03)"),
    _ind("IND-04", "Receita Ajustada", "base", "INDICADOR PRINCIPAL PROVISÓRIO: receita das vendas entregues. Não é reconhecimento contábil definitivo.", "SUM ( fato_vendas[receita_ajustada] )",
         "item de pedido", "idem IND-01", "R$ #,0", "PN-DEV-01 (política PROVISORIA_EXCLUI_DEVOLVIDAS)"),
    _ind("IND-05", "Diferença de Reconciliação", "derivada", "Registrada − Entregues − Devoluções. Deve ser 0,00 em qualquer filtro.", "[Receita Registrada] - [Vendas Entregues] - [Devoluções]",
         "idem", "idem", "R$ #,0.00", "PN-DEV-04"),
    _ind("IND-06", "Taxa de Devolução %", "derivada", "Devoluções ÷ Receita Registrada (razão de somas).", "DIVIDE ( [Devoluções], [Receita Registrada] )", "idem", "idem", "0.0%"),
    _ind("IND-07", "Custo Ajustado", "base", "Custo das linhas entregues (custo devolvido considerado recuperado — hipótese).", "SUM ( fato_vendas[custo_ajustado] )", "item de pedido", "idem", "R$ #,0", "PN-DEV-02 (hipótese não comprovada)"),
    _ind("IND-08", "Lucro Bruto Ajustado", "derivada", "Receita Ajustada − Custo Ajustado.", "[Receita Ajustada] - [Custo Ajustado]", "idem", "idem", "R$ #,0"),
    _ind("IND-09", "Margem Bruta Ajustada %", "derivada", "Lucro Bruto ÷ Receita Ajustada (razão de somas; nunca média de percentuais).", "DIVIDE ( [Lucro Bruto Ajustado], [Receita Ajustada] )", "idem", "idem", "0.0%", "PN-MRG-01"),
    _ind("IND-10", "Unidades Entregues", "base", "Soma das quantidades das linhas entregues.", "SUM ( fato_vendas[unidades_entregues] )", "item de pedido", "idem", "#,0"),
    _ind("IND-11", "Pedidos", "base", "Pedidos distintos (inclui pedidos com linhas devolvidas). Não é aditivo entre cortes.", "DISTINCTCOUNT ( fato_vendas[id_pedido] )", "pedido", "idem", "#,0"),
    _ind("IND-12", "Ticket por Pedido", "derivada", "Receita Ajustada ÷ Pedidos.", "DIVIDE ( [Receita Ajustada], [Pedidos] )", "idem", "idem", "R$ #,0"),
    _ind("IND-13", "Desconto Efetivo %", "derivada", "Σ desconto ÷ Σ receita bruta (todas as linhas).", "DIVIDE ( SUM ( fato_vendas[desconto_valor] ), SUM ( fato_vendas[receita_bruta] ) )", "idem", "idem", "0.0%", "PN-PRC-01: desconto ≠ preço praticado vs lista"),
    _ind("IND-14", "Preço Bruto Médio por Unidade", "derivada", "Σ receita bruta ÷ Σ quantidade (todas as linhas). Só faz sentido por produto.", "DIVIDE ( SUM ( fato_vendas[receita_bruta] ), SUM ( fato_vendas[quantidade] ) )", "idem", "produto", "R$ #,0.00"),
    _ind("IND-15", "Linhas com Margem Negativa", "base", "Linhas em que custo > receita líquida.", "SUM ( fato_vendas[flag_margem_negativa] )", "item de pedido", "idem", "#,0", "PN-MRG-01"),
    _ind("IND-16", "% Linhas com Margem Negativa", "derivada", "Linhas negativas ÷ total de linhas.", "DIVIDE ( [Linhas com Margem Negativa], COUNTROWS ( fato_vendas ) )", "idem", "idem", "0.0%", "PN-MRG-01"),
    _ind("IND-17", "Despesas", "base", "Soma dos lançamentos de despesa. BLANK se o corte incluir produto, canal ou cliente (despesas não têm esses vínculos).",
         _SEM_PROD.format("SUM ( fato_despesas[valor] )"), "lançamento", "calendário, filial, departamento, categoria", "R$ #,0", "Matriz concentra despesas corporativas"),
    _ind("IND-18", "Despesas % da Receita Ajustada", "derivada", "Despesas ÷ Receita Ajustada (por filial, a Matriz não é comparável às demais).", "DIVIDE ( [Despesas], [Receita Ajustada] )", "idem", "calendário, filial", "0.0%"),
    _ind("IND-19", "Resultado Operacional Estimado", "derivada", "Lucro Bruto Ajustado − Despesas. NÃO é lucro líquido contábil.", "IF ( ISBLANK ( [Despesas] ), BLANK (), [Lucro Bruto Ajustado] - [Despesas] )", "idem", "calendário, filial", "R$ #,0", "Rótulo obrigatório: resultado operacional ESTIMADO do dataset"),
    _ind("IND-20", "Margem Operacional Estimada %", "derivada", "Resultado Operacional Estimado ÷ Receita Ajustada.", "DIVIDE ( [Resultado Operacional Estimado], [Receita Ajustada] )", "idem", "calendário, filial", "0.0%"),
    _ind("IND-21", "Receita Ajustada Mês Anterior", "tempo", "Receita Ajustada do mês imediatamente anterior ao filtrado.", "CALCULATE ( [Receita Ajustada], DATEADD ( dim_calendario[data], -1, MONTH ) )", "mês", "calendário (1 mês)", "R$ #,0"),
    _ind("IND-22", "Variação MoM %", "tempo", "Receita Ajustada ÷ mês anterior − 1. BLANK sem base ou base zero (não é 0% nem crescimento).",
         "VAR base = [Receita Ajustada Mês Anterior] RETURN IF ( ISBLANK ( base ) || base = 0, BLANK (), DIVIDE ( [Receita Ajustada] - base, base ) )", "mês", "calendário (1 mês)", "0.0%", "Etapa 3, análise 07"),
    _ind("IND-23", "Receita Ajustada Ano Anterior", "tempo", "Receita Ajustada do mesmo período do ano anterior.", "CALCULATE ( [Receita Ajustada], SAMEPERIODLASTYEAR ( dim_calendario[data] ) )", "mês", "calendário", "R$ #,0"),
    _ind("IND-24", "Variação YoY %", "tempo", "Receita Ajustada ÷ mesmo período do ano anterior − 1. BLANK sem base.",
         "VAR base = [Receita Ajustada Ano Anterior] RETURN IF ( ISBLANK ( base ) || base = 0, BLANK (), DIVIDE ( [Receita Ajustada] - base, base ) )", "mês", "calendário", "0.0%",
         "Para 2026 comparar só meses realizados (use filtro de calendário[realizado] = 1)"),
    _ind("IND-25", "Orçamento Anual", "base", "Orçamento dos 12 meses do(s) ano(s) filtrado(s), inclusive meses futuros.", _SEM_PROD.format("CALCULATE ( SUM ( fato_orcamento[valor_orcado] ), ALLEXCEPT ( dim_calendario, dim_calendario[ano] ) )"),
         "mês × departamento × categoria × filial", "ano, filial, departamento, categoria", "R$ #,0", "PN-ORC-01"),
    _ind("IND-26", "Orçamento Acumulado", "base", "Orçamento dos meses REALIZADOS dentro do filtro de calendário.", _SEM_PROD.format("CALCULATE ( SUM ( fato_orcamento[valor_orcado] ), fato_orcamento[mes_realizado] = 1 )"),
         "idem", "calendário, filial, departamento, categoria", "R$ #,0", "PN-ORC-01"),
    _ind("IND-27", "Realizado Acumulado", "base", "Despesas realizadas nos meses do filtro (tabela orçado × realizado).", _SEM_PROD.format("SUM ( fato_orcado_realizado_mes[realizado] )"),
         "idem", "idem", "R$ #,0", "PN-ORC-01"),
    _ind("IND-28", "Execução do Orçamento %", "derivada", "Realizado Acumulado ÷ Orçamento ACUMULADO (comparação correta).", "DIVIDE ( [Realizado Acumulado], [Orçamento Acumulado] )", "idem", "idem", "0.0%", "PN-ORC-01"),
    _ind("IND-29", "Consumo do Orçamento Anual %", "derivada", "Realizado Acumulado ÷ Orçamento ANUAL. NÃO é execução: ano em curso dá 'economia' falsa.", "DIVIDE ( [Realizado Acumulado], [Orçamento Anual] )", "idem", "idem", "0.0%", "Leitura ingênua (Etapa 3, 06c)"),
]


# ---------------------------------------------------------------- lint estático do DAX
def lint_dax(indicadores=INDICADORES, contrato=CONTRATO) -> list[str]:
    """Erros encontrados (lista vazia = ok). Verifica: parênteses, tabela[coluna] existentes, [Medida] definidas, nomes únicos."""
    erros = []
    nomes = [i["nome"] for i in indicadores]
    if len(set(nomes)) != len(nomes):
        erros.append("nomes de medidas duplicados")
    for i in indicadores:
        d = i["dax"]
        if d.count("(") != d.count(")"):
            erros.append(f"{i['id']}: parênteses desbalanceados")
        for t, c in re.findall(r"\b([a-z_]+)\[([a-z_]+)\]", d):
            if t not in contrato or c not in contrato[t]:
                erros.append(f"{i['id']}: coluna inexistente {t}[{c}]")
        for m in re.findall(r"(?<![\w\]])\[([^\]]+)\]", d):
            if m not in nomes:
                erros.append(f"{i['id']}: medida inexistente [{m}]")
        for k in ("definicao", "dax", "grao", "filtros", "formato"):
            if not i[k]:
                erros.append(f"{i['id']}: campo vazio {k}")
    return erros


# ---------------------------------------------------------------- criação / exportação
def criar_views(con) -> list[str]:
    """Cria o schema `bi` (CREATE OR REPLACE VIEW). Conexão de escrita; não toca nas tabelas do mart."""
    for arq in sorted(PASTA_SQL.glob("*.sql")):
        con.execute(arq.read_text(encoding="utf-8"))
    return [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='bi' ORDER BY 1").fetchall()]


def exportar(con, destino: Path) -> dict[str, int]:
    destino.mkdir(parents=True, exist_ok=True)
    out = {}
    for v in CONTRATO:
        df = con.execute(f"SELECT * FROM bi.{v}").df()
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c] = df[c].dt.strftime("%Y-%m-%d")
        (destino / f"{v}.csv").write_text(para_csv(df), encoding="utf-8", newline="")
        out[v] = len(df)
    return out


# ---------------------------------------------------------------- valores de referência
CONTEXTOS = [
    {"id": "C01", "nome": "Todos os meses realizados (sem filtro)"},
    {"id": "C02", "nome": "Ano 2024", "ano": 2024}, {"id": "C03", "nome": "Ano 2025", "ano": 2025},
    {"id": "C04", "nome": "Ano 2026 (jan–set)", "ano": 2026},
    {"id": "C05", "nome": "Mês set/2026", "ano": 2026, "mes": date(2026, 9, 1)},
    {"id": "C06", "nome": "Mês jan/2026", "ano": 2026, "mes": date(2026, 1, 1)},
    {"id": "C07", "nome": "Porto Alegre, fev/2026", "ano": 2026, "mes": date(2026, 2, 1), "filial": "Porto Alegre"},
    {"id": "C08", "nome": "Matriz, ano 2026", "ano": 2026, "filial": "São Paulo (Matriz)"},
    {"id": "C09", "nome": "Smartphone X Max, ano 2026", "ano": 2026, "produto": "Smartphone X Max"},
    {"id": "C10", "nome": "Notebook Pro 14\", ago/2025", "ano": 2025, "mes": date(2025, 8, 1), "produto": 'Notebook Pro 14"'},
]
ULTIMO = date(2026, 9, 1)


def _meses_ant(mes: date, n: int) -> date:
    t = mes.year * 12 + mes.month - 1 - n
    return date(t // 12, t % 12 + 1, 1)


def _razao(a, b):
    return None if a is None or b in (None, 0) else a / b


def referencia_independente(dados_dir: Path, ctx: dict) -> dict:
    """Valores esperados calculados DIRETO dos CSVs originais (sem DuckDB, sem as views bi)."""
    v = pd.read_csv(dados_dir / "fact_vendas.csv")
    v["mes"] = pd.to_datetime(v.data.str[:7] + "-01").dt.date
    cp = pd.read_csv(dados_dir / "dim_produto.csv")[["id_produto", "produto"]]
    cf = pd.read_csv(dados_dir / "dim_filial.csv")[["id_filial", "filial"]]
    v = v.merge(cp, on="id_produto").merge(cf, on="id_filial")
    d = pd.read_csv(dados_dir / "fact_despesas.csv").merge(cf, on="id_filial")
    d["mes"] = pd.to_datetime(d.data.str[:7] + "-01").dt.date
    o = pd.read_csv(dados_dir / "fact_orcamento.csv").merge(cf, on="id_filial")
    o["mes"] = pd.to_datetime(o.mes).dt.date

    def corte(df, mes_override=None, ano_override=None, usa_produto=True):
        m = df
        ano = ctx.get("ano") if ano_override is None else ano_override
        mes = ctx.get("mes") if mes_override is None else mes_override
        if ano is not None and "mes" in m:
            m = m[m.mes.map(lambda x: x.year) == ano] if mes_override is None else m
        if mes is not None:
            m = m[m.mes == mes]
        if ctx.get("filial"):
            m = m[m.filial == ctx["filial"]]
        if usa_produto and ctx.get("produto"):
            m = m[m.produto == ctx["produto"]]
        return m.assign() if False else m

    def vendas_cortadas(mes=None):
        m = v[v.mes <= ULTIMO]
        if mes is None:
            if ctx.get("ano") is not None:
                m = m[m.mes.map(lambda x: x.year) == ctx["ano"]]
            if ctx.get("mes") is not None:
                m = m[m.mes == ctx["mes"]]
        else:
            m = m[m.mes == mes]
        if ctx.get("filial"):
            m = m[m.filial == ctx["filial"]]
        if ctx.get("produto"):
            m = m[m.produto == ctx["produto"]]
        return m

    def kpi_vendas(m):
        ent = m[m.status == "Entregue"]
        r = dict(receita_registrada=m.receita_liquida.sum(), vendas_entregues=ent.receita_liquida.sum(), devolucoes=m[m.status == "Devolvido"].receita_liquida.sum(),
                 receita_ajustada=ent.receita_liquida.sum(), custo_ajustado=ent.custo_total.sum(), unidades_entregues=ent.quantidade.sum(), pedidos=m.id_pedido.nunique(),
                 linhas_neg=int((m.custo_total > m.receita_liquida).sum()), linhas=len(m), desc=m.desconto_valor.sum(), bruta=m.receita_bruta.sum(), qtd=m.quantidade.sum())
        return r

    k = kpi_vendas(vendas_cortadas())
    res = {"IND-01": k["receita_registrada"], "IND-02": k["vendas_entregues"], "IND-03": k["devolucoes"], "IND-04": k["receita_ajustada"],
           "IND-05": k["receita_registrada"] - k["vendas_entregues"] - k["devolucoes"], "IND-06": _razao(k["devolucoes"], k["receita_registrada"]), "IND-07": k["custo_ajustado"],
           "IND-08": k["receita_ajustada"] - k["custo_ajustado"], "IND-09": _razao(k["receita_ajustada"] - k["custo_ajustado"], k["receita_ajustada"]),
           "IND-10": k["unidades_entregues"], "IND-11": k["pedidos"], "IND-12": _razao(k["receita_ajustada"], k["pedidos"]),
           "IND-13": _razao(k["desc"], k["bruta"]), "IND-14": _razao(k["bruta"], k["qtd"]), "IND-15": k["linhas_neg"], "IND-16": _razao(k["linhas_neg"], k["linhas"])}
    # despesas / resultado (sem produto)
    sem_prod = not ctx.get("produto")
    if sem_prod:
        dd = d[d.mes <= ULTIMO]
        if ctx.get("ano") is not None:
            dd = dd[dd.mes.map(lambda x: x.year) == ctx["ano"]]
        if ctx.get("mes") is not None:
            dd = dd[dd.mes == ctx["mes"]]
        if ctx.get("filial"):
            dd = dd[dd.filial == ctx["filial"]]
        desp = dd.valor.sum()
        res.update({"IND-17": desp, "IND-18": _razao(desp, k["receita_ajustada"]), "IND-19": k["receita_ajustada"] - k["custo_ajustado"] - desp,
                    "IND-20": _razao(k["receita_ajustada"] - k["custo_ajustado"] - desp, k["receita_ajustada"])})
    else:
        res.update({"IND-17": None, "IND-18": None, "IND-19": None, "IND-20": None})
    # tempo (só quando há um mês no contexto)
    if ctx.get("mes") is not None:
        mm = ctx["mes"]
        ant = kpi_vendas(vendas_cortadas(_meses_ant(mm, 1)))["receita_ajustada"] if _meses_ant(mm, 1) >= date(2024, 1, 1) else None
        ya = kpi_vendas(vendas_cortadas(_meses_ant(mm, 12)))["receita_ajustada"] if _meses_ant(mm, 12) >= date(2024, 1, 1) else None
        res["IND-21"], res["IND-23"] = ant, ya
        res["IND-22"] = None if ant in (None, 0) else (k["receita_ajustada"] - ant) / ant
        res["IND-24"] = None if ya in (None, 0) else (k["receita_ajustada"] - ya) / ya
    else:
        res.update({"IND-21": None, "IND-22": None, "IND-23": None, "IND-24": None})
    # orçamento (sem produto)
    if sem_prod:
        oo = o.copy()
        if ctx.get("filial"):
            oo = oo[oo.filial == ctx["filial"]]
        anos = [ctx["ano"]] if ctx.get("ano") is not None else sorted({x.year for x in oo.mes})
        anual = oo[oo.mes.map(lambda x: x.year).isin(anos)].valor_orcado.sum()
        acc = oo[oo.mes <= ULTIMO]
        acc = acc[acc.mes.map(lambda x: x.year).isin(anos)]
        if ctx.get("mes") is not None:
            acc = acc[acc.mes == ctx["mes"]]
        orc_acc = acc.valor_orcado.sum()
        real = res["IND-17"]
        res.update({"IND-25": anual, "IND-26": orc_acc, "IND-27": real, "IND-28": _razao(real, orc_acc), "IND-29": _razao(real, anual)})
    else:
        res.update({"IND-25": None, "IND-26": None, "IND-27": None, "IND-28": None, "IND-29": None})
    return res


def referencia_sql(con, ctx: dict) -> dict:
    """Os mesmos valores, calculados com SQL sobre as views `bi` (é o que o Power BI deveria reproduzir)."""
    def filtro(alias_mes="v.mes", usa_prod=True, mes=None):
        w = [f"{alias_mes} <= DATE '{ULTIMO}'"]
        if ctx.get("ano") is not None and mes is None:
            w.append(f"year({alias_mes}) = {ctx['ano']}")
        m = mes if mes is not None else ctx.get("mes")
        if m is not None:
            w.append(f"{alias_mes} = DATE '{m}'")
        if ctx.get("filial"):
            w.append(f"f.filial = '{ctx['filial']}'")
        if usa_prod and ctx.get("produto"):
            w.append(f"p.produto = '{ctx['produto']}'")
        return " AND ".join(w)

    def vendas(mes=None):
        return con.execute(f"""SELECT coalesce(sum(v.receita_registrada),0), coalesce(sum(v.receita_ajustada),0), coalesce(sum(v.devolucao),0), coalesce(sum(v.custo_ajustado),0),
            coalesce(sum(v.unidades_entregues),0), count(DISTINCT v.id_pedido), coalesce(sum(v.flag_margem_negativa),0), count(*), coalesce(sum(v.desconto_valor),0),
            coalesce(sum(v.receita_bruta),0), coalesce(sum(v.quantidade),0)
            FROM bi.fato_vendas v JOIN bi.dim_filial f USING (id_filial) JOIN bi.dim_produto p USING (id_produto) WHERE {filtro(mes=mes)}""").fetchone()

    reg, aj, dev, cus, un, ped, neg, lin, desc, bru, qtd = [float(x) for x in vendas()]
    res = {"IND-01": reg, "IND-02": reg - dev, "IND-03": dev, "IND-04": aj, "IND-05": reg - (reg - dev) - dev, "IND-06": _razao(dev, reg), "IND-07": cus,
           "IND-08": aj - cus, "IND-09": _razao(aj - cus, aj), "IND-10": un, "IND-11": int(ped), "IND-12": _razao(aj, ped), "IND-13": _razao(desc, bru),
           "IND-14": _razao(bru, qtd), "IND-15": int(neg), "IND-16": _razao(neg, lin)}
    if not ctx.get("produto"):
        desp = float(con.execute(f"""SELECT coalesce(sum(v.valor),0) FROM bi.fato_despesas v JOIN bi.dim_filial f USING (id_filial) WHERE {filtro(usa_prod=False)}""").fetchone()[0])
        res.update({"IND-17": desp, "IND-18": _razao(desp, aj), "IND-19": aj - cus - desp, "IND-20": _razao(aj - cus - desp, aj)})
        anos = f"year(v.mes) = {ctx['ano']}" if ctx.get("ano") is not None else "1=1"
        extra = (f" AND f.filial = '{ctx['filial']}'" if ctx.get("filial") else "")
        anual = float(con.execute(f"SELECT coalesce(sum(v.valor_orcado),0) FROM bi.fato_orcamento v JOIN bi.dim_filial f USING (id_filial) WHERE {anos}{extra}").fetchone()[0])
        mm = f" AND v.mes = DATE '{ctx['mes']}'" if ctx.get("mes") is not None else ""
        acc = float(con.execute(f"SELECT coalesce(sum(v.valor_orcado),0) FROM bi.fato_orcamento v JOIN bi.dim_filial f USING (id_filial) WHERE v.mes_realizado = 1 AND {anos}{extra}{mm}").fetchone()[0])
        rz = float(con.execute(f"SELECT coalesce(sum(v.realizado),0) FROM bi.fato_orcado_realizado_mes v JOIN bi.dim_filial f USING (id_filial) WHERE {filtro(usa_prod=False)}").fetchone()[0])
        res.update({"IND-25": anual, "IND-26": acc, "IND-27": rz, "IND-28": _razao(rz, acc), "IND-29": _razao(rz, anual)})
    else:
        res.update({k: None for k in ("IND-17", "IND-18", "IND-19", "IND-20", "IND-25", "IND-26", "IND-27", "IND-28", "IND-29")})
    if ctx.get("mes") is not None:
        mm = ctx["mes"]
        a1, a12 = _meses_ant(mm, 1), _meses_ant(mm, 12)
        ant = float(vendas(a1)[1]) if a1 >= date(2024, 1, 1) else None
        ya = float(vendas(a12)[1]) if a12 >= date(2024, 1, 1) else None
        res.update({"IND-21": ant, "IND-23": ya, "IND-22": None if ant in (None, 0) else (aj - ant) / ant, "IND-24": None if ya in (None, 0) else (aj - ya) / ya})
    else:
        res.update({"IND-21": None, "IND-22": None, "IND-23": None, "IND-24": None})
    return res


def tabela_referencia(fonte) -> pd.DataFrame:
    """fonte(ctx) -> dict id→valor. Devolve a tabela longa (contexto × indicador)."""
    nome = {i["id"]: i["nome"] for i in INDICADORES}
    linhas = []
    for c in CONTEXTOS:
        r = fonte(c)
        for i in INDICADORES:
            v = r.get(i["id"])
            linhas.append(dict(contexto_id=c["id"], contexto=c["nome"], indicador_id=i["id"], indicador=nome[i["id"]], valor_esperado=None if v is None else float(v)))
    return pd.DataFrame(linhas)
