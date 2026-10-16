"""Modelo semântico (TMSL / model.bim) do Power BI da Empresa X.

Gera tabelas (Power Query M lendo os CSVs), relacionamentos em estrela,
tabela de datas marcada e todas as medidas DAX organizadas em pastas.
"""
import uuid

NS = uuid.UUID("6f1c2b9e-5d1a-4f7a-9a51-2f0f4c1e7a10")


def tag(*parts):
    """lineageTag determinístico (mesmo nome -> mesmo GUID a cada geração)."""
    return str(uuid.uuid5(NS, "/".join(parts)))


# ---------------------------------------------------------------------------
# Formatos
# ---------------------------------------------------------------------------
MOEDA = '"R$" #,0;-"R$" #,0;"R$" #,0'
MOEDA2 = '"R$" #,0.00;-"R$" #,0.00;"R$" #,0.00'
PCT = "0.0%;-0.0%;0.0%"
INT = "#,0"
DEC1 = "#,0.0"

# ---------------------------------------------------------------------------
# Tabelas vindas dos CSVs: (coluna, tipo M, tipo TOM, opções)
# opções: hidden, sort, fmt, cat (dataCategory), summ
# ---------------------------------------------------------------------------
T = "type text"
I = "Int64.Type"
N = "type number"
D = "type date"

CSV_TABLES = {
    "dim_calendario": [
        ("data", D, {}),
        ("ano", I, {}),
        ("semestre", T, {}),
        ("trimestre", T, {}),
        ("mes_num", I, {"hidden": True}),
        ("mes_nome", T, {"sort": "mes_num"}),
        ("mes_abrev", T, {"sort": "mes_num"}),
        ("ano_mes", T, {"sort": "ordem_ano_mes"}),
        ("mes_ano", T, {"sort": "ordem_ano_mes"}),
        ("ordem_ano_mes", I, {"hidden": True}),
        ("dia", I, {}),
        ("dia_semana_num", I, {"hidden": True}),
        ("dia_semana", T, {"sort": "dia_semana_num"}),
        ("dia_semana_abrev", T, {"sort": "dia_semana_num"}),
        ("semana_do_ano", I, {}),
        ("fim_de_semana", I, {}),
        ("feriado", T, {}),
        ("dia_util", I, {}),
        ("realizado", I, {}),
        ("status_periodo", T, {}),
        ("primeiro_dia_mes", D, {}),
    ],
    "dim_filial": [
        ("id_filial", I, {"hidden": True}),
        ("filial", T, {}),
        ("cidade", T, {"cat": "City"}),
        ("uf", T, {"cat": "StateOrProvince"}),
        ("regiao", T, {}),
        ("tipo", T, {}),
        ("data_abertura", D, {}),
        ("latitude", N, {"cat": "Latitude", "hidden": True}),
        ("longitude", N, {"cat": "Longitude", "hidden": True}),
    ],
    "dim_produto": [
        ("id_produto", I, {"hidden": True}),
        ("sku", T, {}),
        ("produto", T, {}),
        ("categoria", T, {}),
        ("subcategoria", T, {}),
        ("preco_lista", N, {"fmt": MOEDA2}),
        ("custo_unitario_base", N, {"fmt": MOEDA2}),
        ("margem_lista_pct", N, {"fmt": PCT}),
        ("aliquota_imposto", N, {"fmt": PCT}),
    ],
    "dim_cliente": [
        ("id_cliente", I, {"hidden": True}),
        ("nome_cliente", T, {}),
        ("segmento", T, {}),
        ("cidade", T, {"cat": "City"}),
        ("uf", T, {"cat": "StateOrProvince"}),
        ("regiao", T, {}),
        ("data_cadastro", D, {}),
        ("data_primeira_compra", D, {}),
    ],
    "dim_vendedor": [
        ("id_vendedor", I, {"hidden": True}),
        ("nome_vendedor", T, {}),
        ("equipe", T, {}),
        ("cargo", T, {}),
        ("data_admissao", D, {}),
    ],
    "dim_canal": [
        ("id_canal", I, {"hidden": True}),
        ("canal", T, {}),
        ("tipo_canal", T, {}),
    ],
    "dim_departamento": [
        ("id_departamento", I, {"hidden": True}),
        ("departamento", T, {}),
        ("centro_custo", T, {}),
        ("responsavel", T, {}),
        ("tipo_area", T, {}),
    ],
    "dim_categoria_despesa": [
        ("id_categoria_despesa", I, {"hidden": True}),
        ("categoria_despesa", T, {}),
        ("grupo_dre", T, {"sort": "ordem_dre"}),
        ("tipo_custo", T, {}),
        ("ordem_dre", I, {"hidden": True}),
    ],
    "fact_vendas": [
        ("id_venda", I, {"hidden": True}),
        ("id_pedido", T, {"hidden": True}),
        ("data", D, {"hidden": True}),
        ("id_cliente", I, {"hidden": True}),
        ("id_produto", I, {"hidden": True}),
        ("id_filial", I, {"hidden": True}),
        ("id_vendedor", I, {"hidden": True}),
        ("id_canal", I, {"hidden": True}),
        ("quantidade", I, {"hidden": True}),
        ("preco_unitario", N, {"hidden": True, "fmt": MOEDA2}),
        ("desconto_pct", N, {"hidden": True, "fmt": PCT}),
        ("receita_bruta", N, {"hidden": True, "fmt": MOEDA2}),
        ("desconto_valor", N, {"hidden": True, "fmt": MOEDA2}),
        ("impostos_valor", N, {"hidden": True, "fmt": MOEDA2}),
        ("receita_liquida", N, {"hidden": True, "fmt": MOEDA2}),
        ("custo_total", N, {"hidden": True, "fmt": MOEDA2}),
        ("forma_pagamento", T, {}),
        ("status", T, {}),
    ],
    "fact_despesas": [
        ("id_despesa", I, {"hidden": True}),
        ("data", D, {"hidden": True}),
        ("id_departamento", I, {"hidden": True}),
        ("id_categoria_despesa", I, {"hidden": True}),
        ("id_filial", I, {"hidden": True}),
        ("fornecedor", T, {}),
        ("valor", N, {"hidden": True, "fmt": MOEDA2}),
    ],
    "fact_orcamento": [
        ("mes", D, {"hidden": True}),
        ("id_departamento", I, {"hidden": True}),
        ("id_categoria_despesa", I, {"hidden": True}),
        ("id_filial", I, {"hidden": True}),
        ("valor_orcado", N, {"hidden": True, "fmt": MOEDA2}),
    ],
    "fact_metas_vendas": [
        ("mes", D, {"hidden": True}),
        ("id_filial", I, {"hidden": True}),
        ("meta_receita_liquida", N, {"hidden": True, "fmt": MOEDA2}),
        ("meta_margem_bruta_pct", N, {"hidden": True, "fmt": PCT}),
        ("meta_lucro_bruto", N, {"hidden": True, "fmt": MOEDA2}),
    ],
    "fact_rh_mensal": [
        ("data_referencia", D, {"hidden": True}),
        ("id_departamento", I, {"hidden": True}),
        ("id_filial", I, {"hidden": True}),
        ("headcount", I, {"hidden": True}),
        ("headcount_planejado", I, {"hidden": True}),
        ("admissoes", I, {"hidden": True}),
        ("desligamentos", I, {"hidden": True}),
    ],
}

# colunas extras calculadas no Power Query do calendário
CAL_EXTRA = [
    ("ano_tri", T, {"sort": "ordem_ano_tri"}),
    ("ordem_ano_tri", I, {"hidden": True}),
]

TOM_TYPE = {T: "string", I: "int64", N: "double", D: "dateTime"}


def m_csv(table, cols, extra_steps=None):
    tipos = ", ".join('{"%s", %s}' % (c, t) for c, t, _ in cols)
    lines = [
        "let",
        f'    Fonte = Csv.Document(File.Contents(PastaDados & "{table}.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),",
        f'    Tipos = Table.TransformColumnTypes(Cabecalhos, {{{tipos}}}, "en-US")' + ("," if extra_steps else ""),
    ]
    last = "Tipos"
    if extra_steps:
        for i, (name, expr) in enumerate(extra_steps):
            sep = "," if i < len(extra_steps) - 1 else ""
            lines.append(f"    {name} = {expr}{sep}")
            last = name
    lines += ["in", f"    {last}"]
    return lines


def column(table, name, mtype, opts):
    col = {
        "name": name,
        "dataType": TOM_TYPE[mtype],
        "sourceColumn": name,
        "lineageTag": tag(table, name),
        "summarizeBy": "none",
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}],
    }
    if mtype == D:
        col["formatString"] = "dd/mm/yyyy"
        col["annotations"].append({"name": "UnderlyingDateTimeDataType", "value": "Date"})
    elif mtype == I:
        col["formatString"] = "0"
    elif mtype == N:
        col["formatString"] = opts.get("fmt", "#,0.00")
    if opts.get("fmt") and mtype != N:
        col["formatString"] = opts["fmt"]
    if opts.get("hidden"):
        col["isHidden"] = True
    if opts.get("sort"):
        col["sortByColumn"] = opts["sort"]
    if opts.get("cat"):
        col["dataCategory"] = opts["cat"]
    return col


def table_from_csv(name, cols, extra_cols=None, extra_steps=None, description=None):
    allcols = cols + (extra_cols or [])
    t = {
        "name": name,
        "lineageTag": tag(name),
        "columns": [column(name, c, t_, o) for c, t_, o in allcols],
        "partitions": [
            {
                "name": name,
                "mode": "import",
                "source": {"type": "m", "expression": m_csv(name, cols, extra_steps)},
            }
        ],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
    }
    if description:
        t["description"] = description
    return t


def table_from_m(name, cols, m_lines, hidden=False, description=None):
    t = {
        "name": name,
        "lineageTag": tag(name),
        "columns": [column(name, c, t_, o) for c, t_, o in cols],
        "partitions": [
            {"name": name, "mode": "import", "source": {"type": "m", "expression": m_lines}}
        ],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
    }
    if hidden:
        t["isHidden"] = True
    if description:
        t["description"] = description
    return t


# ---------------------------------------------------------------------------
# Medidas DAX
# ---------------------------------------------------------------------------
VERDE, VERDE_BG = "#15803D", "#DCFCE7"
VERMELHO, VERMELHO_BG = "#B91C1C", "#FEE2E2"
NEUTRO_BG = "#F1F5F9"

MEASURES = []  # (pasta, nome, dax, formato, descricao)


def M(folder, name, dax, fmt=None, desc=None):
    MEASURES.append((folder, name, dax.strip("\n"), fmt, desc))


ENTREGUE = 'fact_vendas[status] = "Entregue"'

# 1. Vendas -----------------------------------------------------------------
F = "1. Vendas"
M(F, "Receita Bruta", f"CALCULATE ( SUM ( fact_vendas[receita_bruta] ), {ENTREGUE} )", MOEDA,
  "Faturamento bruto das vendas entregues (devoluções ficam fora).")
M(F, "Descontos", f"CALCULATE ( SUM ( fact_vendas[desconto_valor] ), {ENTREGUE} )", MOEDA)
M(F, "Impostos", f"CALCULATE ( SUM ( fact_vendas[impostos_valor] ), {ENTREGUE} )", MOEDA)
M(F, "Receita Líquida", f"CALCULATE ( SUM ( fact_vendas[receita_liquida] ), {ENTREGUE} )", MOEDA,
  "Receita bruta - descontos - impostos, só vendas entregues.")
M(F, "CMV", f"CALCULATE ( SUM ( fact_vendas[custo_total] ), {ENTREGUE} )", MOEDA,
  "Custo da mercadoria vendida.")
M(F, "Lucro Bruto", "[Receita Líquida] - [CMV]", MOEDA)
M(F, "Margem Bruta %", "DIVIDE ( [Lucro Bruto], [Receita Líquida] )", PCT)
M(F, "Desconto Médio %", "DIVIDE ( [Descontos], [Receita Bruta] )", PCT)
M(F, "Pedidos", f"CALCULATE ( DISTINCTCOUNT ( fact_vendas[id_pedido] ), {ENTREGUE} )", INT)
M(F, "Itens Vendidos", f"CALCULATE ( SUM ( fact_vendas[quantidade] ), {ENTREGUE} )", INT)
M(F, "Ticket Médio", "DIVIDE ( [Receita Líquida], [Pedidos] )", MOEDA2)
M(F, "Taxa de Devolução %", """
DIVIDE (
    CALCULATE ( SUM ( fact_vendas[receita_bruta] ), fact_vendas[status] = "Devolvido" ),
    SUM ( fact_vendas[receita_bruta] )
)""", PCT)
M(F, "Clientes Ativos", f"CALCULATE ( DISTINCTCOUNT ( fact_vendas[id_cliente] ), {ENTREGUE} )", INT)
M(F, "Receita por Cliente", "DIVIDE ( [Receita Líquida], [Clientes Ativos] )", MOEDA)

# 2. Despesas & resultado ---------------------------------------------------
F = "2. Despesas e Resultado"
M(F, "Despesas Totais", "SUM ( fact_despesas[valor] )", MOEDA)
for grupo, nome in [
    ("Despesas com Pessoal", "Despesas com Pessoal"),
    ("Despesas Comerciais", "Despesas Comerciais"),
    ("Despesas Operacionais", "Despesas Operacionais"),
    ("Despesas Administrativas", "Despesas Administrativas"),
    ("Despesas Financeiras", "Despesas Financeiras"),
]:
    M(F, nome, f'CALCULATE ( [Despesas Totais], dim_categoria_despesa[grupo_dre] = "{grupo}" )', MOEDA)
M(F, "Resultado Operacional", "[Lucro Bruto] - [Despesas Totais]", MOEDA,
  "Lucro bruto menos todas as despesas (EBIT simplificado).")
M(F, "Margem Operacional %", "DIVIDE ( [Resultado Operacional], [Receita Líquida] )", PCT)
M(F, "Despesas % da Receita", "DIVIDE ( [Despesas Totais], [Receita Líquida] )", PCT)

# 3. Orçamento --------------------------------------------------------------
F = "3. Orçamento"
M(F, "Despesa Orçada", "SUM ( fact_orcamento[valor_orcado] )", MOEDA)
M(F, "Despesa Orçada (realizado)",
  "CALCULATE ( [Despesa Orçada], KEEPFILTERS ( dim_calendario[realizado] = 1 ) )", MOEDA,
  "Orçamento só dos meses que já aconteceram - base justa de comparação.")
M(F, "Variação vs Orçado (R$)", """
IF (
    ISBLANK ( [Despesa Orçada (realizado)] ),
    BLANK (),
    [Despesas Totais] - [Despesa Orçada (realizado)]
)""", MOEDA)
M(F, "Variação vs Orçado %", "DIVIDE ( [Variação vs Orçado (R$)], [Despesa Orçada (realizado)] )", PCT)
M(F, "Execução do Orçamento %", "DIVIDE ( [Despesas Totais], [Despesa Orçada (realizado)] )", PCT)
M(F, "Cor do Orçamento", f"""
SWITCH (
    TRUE (),
    ISBLANK ( [Execução do Orçamento %] ), "#94A3B8",
    [Execução do Orçamento %] > 1.05, "#DC2626",
    [Execução do Orçamento %] > 1.00, "#F59E0B",
    "#0F766E"
)""")

# 4. Metas ------------------------------------------------------------------
F = "4. Metas"
M(F, "Meta Receita", "SUM ( fact_metas_vendas[meta_receita_liquida] )", MOEDA)
M(F, "Meta Receita (realizado)",
  "CALCULATE ( [Meta Receita], KEEPFILTERS ( dim_calendario[realizado] = 1 ) )", MOEDA)
M(F, "Atingimento da Meta %", "DIVIDE ( [Receita Líquida], [Meta Receita (realizado)] )", PCT)
M(F, "Gap para Meta", "[Receita Líquida] - [Meta Receita (realizado)]", MOEDA)
M(F, "Máximo do Medidor", "MAX ( [Meta Receita (realizado)], [Receita Líquida] ) * 1.15", MOEDA)
M(F, "Cor Atingimento", """
SWITCH (
    TRUE (),
    ISBLANK ( [Atingimento da Meta %] ), "#94A3B8",
    [Atingimento da Meta %] >= 1, "#0F766E",
    [Atingimento da Meta %] >= 0.95, "#F59E0B",
    "#DC2626"
)""")
M(F, "Projeção de Receita do Ano", """
VAR _ultima = [Última Data Realizada]
VAR _ano = YEAR ( _ultima )
VAR _real =
    CALCULATE ( [Receita Líquida], dim_calendario[ano] = _ano, dim_calendario[data] <= _ultima )
VAR _metaReal =
    CALCULATE ( [Meta Receita], dim_calendario[ano] = _ano, dim_calendario[realizado] = 1 )
VAR _metaResto =
    CALCULATE ( [Meta Receita], dim_calendario[ano] = _ano, dim_calendario[realizado] = 0 )
RETURN
    _real + _metaResto * DIVIDE ( _real, _metaReal )""", MOEDA,
  "Realizado do ano + meta dos meses restantes ajustada pelo ritmo atual de atingimento.")
M(F, "Meta do Ano Corrente", """
VAR _ano = YEAR ( [Última Data Realizada] )
RETURN
    CALCULATE ( [Meta Receita], dim_calendario[ano] = _ano )""", MOEDA)

# 5. Tempo ------------------------------------------------------------------
F = "5. Comparação no tempo"
M(F, "Última Data Realizada", """
CALCULATE (
    MAX ( dim_calendario[data] ),
    dim_calendario[realizado] = 1,
    ALL ( dim_calendario )
)""", "dd/mm/yyyy")


def ly(base):
    return f"""
VAR _ultima = [Última Data Realizada]
RETURN
    CALCULATE (
        [{base}],
        SAMEPERIODLASTYEAR ( dim_calendario[data] ),
        dim_calendario[data] <= EDATE ( _ultima, -12 )
    )"""


for base, fmt in [
    ("Receita Líquida", MOEDA),
    ("Lucro Bruto", MOEDA),
    ("Despesas Totais", MOEDA),
    ("Resultado Operacional", MOEDA),
    ("Pedidos", INT),
    ("Ticket Médio", MOEDA2),
    ("Itens Vendidos", INT),
    ("Receita Bruta", MOEDA),
    ("CMV", MOEDA),
    ("Clientes Ativos", INT),
    ("Receita por Cliente", MOEDA),
    ("Headcount (fim do período)", INT),
    ("Receita por Funcionário", MOEDA),
    ("Custo de Pessoal por Funcionário", MOEDA),
    ("Despesa Orçada (realizado)", MOEDA),
]:
    M(F, f"{base} AA", ly(base), fmt, f"{base} no mesmo período do ano anterior (até o mesmo dia).")

for base in ["Margem Bruta %", "Margem Operacional %", "Desconto Médio %", "Taxa de Devolução %",
             "Turnover %", "Despesas % da Receita", "Execução do Orçamento %"]:
    M(F, f"{base} AA", ly(base), PCT)

M(F, "Var. Receita a/a %", "DIVIDE ( [Receita Líquida] - [Receita Líquida AA], [Receita Líquida AA] )", PCT)
M(F, "Receita Acumulada no Ano", "TOTALYTD ( [Receita Líquida], dim_calendario[data] )", MOEDA)
M(F, "Receita Média Móvel 3M", """
DIVIDE (
    CALCULATE (
        [Receita Líquida],
        DATESINPERIOD ( dim_calendario[data], MAX ( dim_calendario[data] ), -3, MONTH )
    ),
    3
)""", MOEDA)

# 6. Clientes ---------------------------------------------------------------
F = "6. Clientes"
M(F, "Novos Clientes", """
VAR _ini = MIN ( dim_calendario[data] )
VAR _fim = MIN ( MAX ( dim_calendario[data] ), [Última Data Realizada] )
RETURN
    COUNTROWS (
        FILTER (
            ALL ( dim_cliente[id_cliente], dim_cliente[data_primeira_compra] ),
            dim_cliente[data_primeira_compra] >= _ini
                && dim_cliente[data_primeira_compra] <= _fim
        )
    )""", INT, "Clientes cuja primeira compra caiu no período filtrado.")
M(F, "Ranking Cliente", """
IF (
    ISBLANK ( [Receita Líquida] ),
    BLANK (),
    RANKX ( ALLSELECTED ( dim_cliente[nome_cliente] ), [Receita Líquida], , DESC, DENSE )
)""", INT)
M(F, "% Acumulado Clientes", """
VAR _atual = [Receita Líquida]
VAR _tabela =
    CALCULATETABLE (
        ADDCOLUMNS ( VALUES ( dim_cliente[id_cliente] ), "@rec", [Receita Líquida] ),
        ALLSELECTED ( dim_cliente )
    )
VAR _acum = SUMX ( FILTER ( _tabela, [@rec] >= _atual ), [@rec] )
VAR _total = SUMX ( _tabela, [@rec] )
RETURN
    IF (
        HASONEVALUE ( dim_cliente[nome_cliente] ) && NOT ISBLANK ( _atual ),
        DIVIDE ( _acum, _total )
    )""", PCT, "Participação acumulada na receita, do maior para o menor cliente (curva ABC).")
M(F, "Receita Top 20 Clientes", "IF ( [Ranking Cliente] <= 20, [Receita Líquida] )", MOEDA)
M(F, "% Acumulado (Top 20)", "IF ( [Ranking Cliente] <= 20, [% Acumulado Clientes] )", PCT)
M(F, "Concentração Top 20 %", """
VAR _t =
    ADDCOLUMNS ( VALUES ( dim_cliente[nome_cliente] ), "@rec", [Receita Líquida] )
RETURN
    DIVIDE ( SUMX ( TOPN ( 20, _t, [@rec], DESC ), [@rec] ), SUMX ( _t, [@rec] ) )""", PCT,
  "Quanto da receita vem dos 20 maiores clientes.")
M(F, "Classe ABC", """
VAR _p = [% Acumulado Clientes]
RETURN
    SWITCH ( TRUE (), ISBLANK ( _p ), BLANK (), _p <= 0.8, "A", _p <= 0.95, "B", "C" )""")
M(F, "Ranking Vendedor", """
IF (
    ISBLANK ( [Receita Líquida] ),
    BLANK (),
    RANKX ( ALLSELECTED ( dim_vendedor[nome_vendedor] ), [Receita Líquida], , DESC, DENSE )
)""", INT)

# 7. Pessoas ----------------------------------------------------------------
F = "7. Pessoas"
M(F, "Headcount Mensal", "SUM ( fact_rh_mensal[headcount] )", INT)
M(F, "Headcount (fim do período)", """
CALCULATE (
    SUM ( fact_rh_mensal[headcount] ),
    LASTNONBLANK ( dim_calendario[data], CALCULATE ( COUNTROWS ( fact_rh_mensal ) ) )
)""", INT)
M(F, "Headcount Médio", """
AVERAGEX (
    VALUES ( dim_calendario[ano_mes] ),
    CALCULATE ( SUM ( fact_rh_mensal[headcount] ) )
)""", DEC1)
M(F, "Total de Admissões", "SUM ( fact_rh_mensal[admissoes] )", INT)
M(F, "Total de Desligamentos", "SUM ( fact_rh_mensal[desligamentos] )", INT)
M(F, "Turnover %", "DIVIDE ( [Total de Desligamentos], [Headcount Médio] )", PCT)
M(F, "Custo de Pessoal por Funcionário", "DIVIDE ( [Despesas com Pessoal], [Headcount Médio] )", MOEDA)
M(F, "Receita por Funcionário", "DIVIDE ( [Receita Líquida], [Headcount Médio] )", MOEDA)
M(F, "Vagas em Aberto", """
CALCULATE (
    SUM ( fact_rh_mensal[headcount_planejado] ) - SUM ( fact_rh_mensal[headcount] ),
    LASTNONBLANK ( dim_calendario[data], CALCULATE ( COUNTROWS ( fact_rh_mensal ) ) )
)""", INT)

# 8. DRE e simulador --------------------------------------------------------
F = "8. DRE e Simulador"
M(F, "Valor DRE", """
SWITCH (
    SELECTEDVALUE ( tbl_dre[Linha] ),
    "Receita bruta", [Receita Bruta],
    "Descontos", - [Descontos],
    "Impostos", - [Impostos],
    "CMV", - [CMV],
    "Pessoal", - [Despesas com Pessoal],
    "Comerciais", - [Despesas Comerciais],
    "Operacionais", - [Despesas Operacionais],
    "Administrativas", - [Despesas Administrativas],
    "Financeiras", - [Despesas Financeiras]
)""", MOEDA)
M(F, "Δ Preço", "SELECTEDVALUE ( par_preco[Variação de Preço], 0 )", PCT)
M(F, "Δ Volume", "SELECTEDVALUE ( par_volume[Variação de Volume], 0 )", PCT)
M(F, "Δ Custo", "SELECTEDVALUE ( par_custo[Variação do Custo], 0 )", PCT)
M(F, "Δ Despesas", "SELECTEDVALUE ( par_despesa[Variação das Despesas], 0 )", PCT)
M(F, "Despesas Variáveis", 'CALCULATE ( [Despesas Totais], dim_categoria_despesa[tipo_custo] = "Variável" )', MOEDA)
M(F, "Despesas Fixas", 'CALCULATE ( [Despesas Totais], dim_categoria_despesa[tipo_custo] = "Fixa" )', MOEDA)
M(F, "Receita Líquida (Cenário)", "[Receita Líquida] * ( 1 + [Δ Volume] ) * ( 1 + [Δ Preço] )", MOEDA)
M(F, "CMV (Cenário)", "[CMV] * ( 1 + [Δ Volume] ) * ( 1 + [Δ Custo] )", MOEDA)
M(F, "Despesas (Cenário)",
  "( [Despesas Variáveis] * ( 1 + [Δ Volume] ) + [Despesas Fixas] ) * ( 1 + [Δ Despesas] )", MOEDA)
M(F, "Resultado (Cenário)", "[Receita Líquida (Cenário)] - [CMV (Cenário)] - [Despesas (Cenário)]", MOEDA)
M(F, "Δ Resultado vs Atual", "[Resultado (Cenário)] - [Resultado Operacional]", MOEDA)
M(F, "Margem Operacional (Cenário)", "DIVIDE ( [Resultado (Cenário)], [Receita Líquida (Cenário)] )", PCT)
M(F, "Valor Alavanca", """
VAR _rl = [Receita Líquida]
VAR _cmv = [CMV]
VAR _dv = [Despesas Variáveis]
VAR _df = [Despesas Fixas]
VAR _v = [Δ Volume]
VAR _p = [Δ Preço]
VAR _c = [Δ Custo]
VAR _d = [Δ Despesas]
VAR _r0 = _rl - _cmv - ( _dv + _df )
VAR _r1 = _rl * ( 1 + _v ) - _cmv * ( 1 + _v ) - ( _dv * ( 1 + _v ) + _df )
VAR _r2 = _rl * ( 1 + _v ) * ( 1 + _p ) - _cmv * ( 1 + _v ) - ( _dv * ( 1 + _v ) + _df )
VAR _r3 = _rl * ( 1 + _v ) * ( 1 + _p ) - _cmv * ( 1 + _v ) * ( 1 + _c ) - ( _dv * ( 1 + _v ) + _df )
VAR _r4 = _r3 + ( _dv * ( 1 + _v ) + _df ) - ( _dv * ( 1 + _v ) + _df ) * ( 1 + _d )
RETURN
    SWITCH (
        SELECTEDVALUE ( tbl_alavancas[Etapa] ),
        "Resultado atual", _r0,
        "Volume", _r1 - _r0,
        "Preço", _r2 - _r1,
        "Custo (CMV)", _r3 - _r2,
        "Despesas", _r4 - _r3
    )""", MOEDA)

# 9. Textos, selos e cores (para os cartões e destaques) ---------------------
F = "9. Textos e Cores"


def badge(nome, atual, anterior, tipo="pct", bom="sobe"):
    """Cria 3 medidas para o selo de variação de um KPI:
    texto (▲ 8,2% a/a), valor numérico (para regra de cor) e cor de fundo."""
    if tipo == "pct":
        var = f"DIVIDE ( _a - _b, ABS ( _b ) )"
        txt = 'FORMAT ( ABS ( _v ), "0.0%" ) & " a/a"'
    else:  # pontos percentuais
        var = "_a - _b"
        txt = 'FORMAT ( ABS ( _v ) * 100, "0.0" ) & " p.p."'
    M(F, f"Var {nome}", f"""
VAR _a = [{atual}]
VAR _b = [{anterior}]
RETURN
    IF ( ISBLANK ( _a ) || ISBLANK ( _b ), BLANK (), {var} )""", PCT if tipo == "pct" else "0.0%")
    M(F, f"Selo {nome}", f"""
VAR _v = [Var {nome}]
RETURN
    IF ( ISBLANK ( _v ), "sem base a/a", IF ( _v >= 0, "▲ ", "▼ " ) & {txt} )""")
    if bom == "sobe":
        cond_bom = "_v >= 0"
    else:
        cond_bom = "_v <= 0"
    M(F, f"Fundo Selo {nome}", f"""
VAR _v = [Var {nome}]
RETURN
    IF ( ISBLANK ( _v ), "{NEUTRO_BG}", IF ( {cond_bom}, "{VERDE_BG}", "{VERMELHO_BG}" ) )""")


BADGES = [
    # nome do selo, medida atual, medida ano anterior, tipo, bom quando
    ("Receita", "Receita Líquida", "Receita Líquida AA", "pct", "sobe"),
    ("Lucro Bruto", "Lucro Bruto", "Lucro Bruto AA", "pct", "sobe"),
    ("Despesas", "Despesas Totais", "Despesas Totais AA", "pct", "desce"),
    ("Resultado", "Resultado Operacional", "Resultado Operacional AA", "pct", "sobe"),
    ("Margem Op", "Margem Operacional %", "Margem Operacional % AA", "pp", "sobe"),
    ("Pedidos", "Pedidos", "Pedidos AA", "pct", "sobe"),
    ("Ticket", "Ticket Médio", "Ticket Médio AA", "pct", "sobe"),
    ("Itens", "Itens Vendidos", "Itens Vendidos AA", "pct", "sobe"),
    ("Desconto", "Desconto Médio %", "Desconto Médio % AA", "pp", "desce"),
    ("Devolução", "Taxa de Devolução %", "Taxa de Devolução % AA", "pp", "desce"),
    ("Receita Bruta", "Receita Bruta", "Receita Bruta AA", "pct", "sobe"),
    ("CMV", "CMV", "CMV AA", "pct", "desce"),
    ("Margem Bruta", "Margem Bruta %", "Margem Bruta % AA", "pp", "sobe"),
    ("Clientes", "Clientes Ativos", "Clientes Ativos AA", "pct", "sobe"),
    ("Receita Cliente", "Receita por Cliente", "Receita por Cliente AA", "pct", "sobe"),
    ("Headcount", "Headcount (fim do período)", "Headcount (fim do período) AA", "pct", "sobe"),
    ("Turnover", "Turnover %", "Turnover % AA", "pp", "desce"),
    ("Custo Pessoal", "Custo de Pessoal por Funcionário", "Custo de Pessoal por Funcionário AA", "pct", "desce"),
    ("Receita Func", "Receita por Funcionário", "Receita por Funcionário AA", "pct", "sobe"),
    ("Orçado", "Despesa Orçada (realizado)", "Despesa Orçada (realizado) AA", "pct", "desce"),
    ("Desp Receita", "Despesas % da Receita", "Despesas % da Receita AA", "pp", "desce"),
]
for b in BADGES:
    badge(*b)

M(F, "Selo Meta", """
VAR _a = [Atingimento da Meta %]
RETURN
    IF ( ISBLANK ( _a ), "sem meta", IF ( _a >= 1, "▲ ", "▼ " ) & FORMAT ( _a, "0%" ) & " da meta" )""")
M(F, "Var Meta", "[Atingimento da Meta %] - 1", PCT)
M(F, "Fundo Selo Meta", f"""
VAR _a = [Atingimento da Meta %]
RETURN
    IF ( ISBLANK ( _a ), "{NEUTRO_BG}", IF ( _a >= 1, "{VERDE_BG}", "{VERMELHO_BG}" ) )""")
M(F, "Selo Execução", """
VAR _e = [Execução do Orçamento %]
RETURN
    IF ( ISBLANK ( _e ), "sem orçamento", IF ( _e <= 1, "● dentro do orçado", "▲ acima do orçado" ) )""")
M(F, "Var Execução", "1 - [Execução do Orçamento %]", PCT)
M(F, "Fundo Selo Execução", f"""
VAR _e = [Execução do Orçamento %]
RETURN
    IF ( ISBLANK ( _e ), "{NEUTRO_BG}", IF ( _e <= 1, "{VERDE_BG}", "{VERMELHO_BG}" ) )""")
M(F, "Selo Cenário", """
VAR _d = [Δ Resultado vs Atual]
RETURN
    IF ( _d = 0, "● igual ao atual", IF ( _d > 0, "▲ ", "▼ " ) & FORMAT ( ABS ( _d ) / 1000000, "0.0" ) & " mi vs atual" )""")
M(F, "Var Cenário", "[Δ Resultado vs Atual]", MOEDA)
M(F, "Fundo Selo Cenário", f"""
VAR _d = [Δ Resultado vs Atual]
RETURN
    IF ( _d = 0, "{NEUTRO_BG}", IF ( _d > 0, "{VERDE_BG}", "{VERMELHO_BG}" ) )""")

M(F, "Melhor Filial", """
VAR _t = ADDCOLUMNS ( VALUES ( dim_filial[filial] ), "@r", [Receita Líquida] )
RETURN
    MAXX ( TOPN ( 1, FILTER ( _t, NOT ISBLANK ( [@r] ) ), [@r], DESC ), dim_filial[filial] )""")
M(F, "Filial em Atenção", """
VAR _t =
    FILTER (
        ADDCOLUMNS ( VALUES ( dim_filial[filial] ), "@a", [Atingimento da Meta %] ),
        NOT ISBLANK ( [@a] )
    )
RETURN
    MAXX ( TOPN ( 1, _t, [@a], ASC ), dim_filial[filial] )""")
M(F, "Canal que Mais Cresce", """
VAR _t =
    FILTER (
        ADDCOLUMNS ( VALUES ( dim_canal[canal] ), "@g", [Var Receita] ),
        NOT ISBLANK ( [@g] )
    )
RETURN
    MAXX ( TOPN ( 1, _t, [@g], DESC ), dim_canal[canal] )""")
M(F, "Título Período", """
VAR _anos = CONCATENATEX ( VALUES ( dim_calendario[ano] ), dim_calendario[ano], ", ", dim_calendario[ano], ASC )
VAR _filiais =
    IF (
        ISFILTERED ( dim_filial[filial] ),
        CONCATENATEX ( VALUES ( dim_filial[filial] ), dim_filial[filial], ", " ),
        "todas as filiais"
    )
RETURN
    "Período: " & _anos & "  •  " & _filiais & "  •  dados até "
        & FORMAT ( [Última Data Realizada], "dd/mm/yyyy" )""")


# ---------------------------------------------------------------------------
# Tabelas auxiliares (Power Query)
# ---------------------------------------------------------------------------
def aux_tables():
    tabs = []
    tabs.append(table_from_m(
        "_Medidas",
        [("Coluna", T, {"hidden": True})],
        ["let", "    Fonte = #table(type table [Coluna = text], {})", "in", "    Fonte"],
        description="Tabela só para guardar as medidas.",
    ))
    tabs.append(table_from_m(
        "tbl_dre",
        [("Linha", T, {"sort": "Ordem"}), ("Ordem", I, {"hidden": True})],
        [
            "let",
            "    Fonte = #table(type table [Linha = text, Ordem = Int64.Type], {",
            '        {"Receita bruta", 1}, {"Descontos", 2}, {"Impostos", 3}, {"CMV", 4},',
            '        {"Pessoal", 5}, {"Comerciais", 6}, {"Operacionais", 7},',
            '        {"Administrativas", 8}, {"Financeiras", 9}',
            "    })",
            "in",
            "    Fonte",
        ],
        description="Linhas da DRE em cascata (o total do gráfico é o Resultado Operacional).",
    ))
    tabs.append(table_from_m(
        "tbl_alavancas",
        [("Etapa", T, {"sort": "Ordem"}), ("Ordem", I, {"hidden": True})],
        [
            "let",
            "    Fonte = #table(type table [Etapa = text, Ordem = Int64.Type], {",
            '        {"Resultado atual", 1}, {"Volume", 2}, {"Preço", 3}, {"Custo (CMV)", 4}, {"Despesas", 5}',
            "    })",
            "in",
            "    Fonte",
        ],
    ))
    for tname, col, vals in [
        ("par_preco", "Variação de Preço", "-0.10, -0.05, 0, 0.05, 0.10"),
        ("par_volume", "Variação de Volume", "-0.20, -0.10, 0, 0.10, 0.20"),
        ("par_custo", "Variação do Custo", "-0.05, 0, 0.05, 0.10, 0.15"),
        ("par_despesa", "Variação das Despesas", "-0.10, -0.05, 0, 0.05, 0.10"),
    ]:
        tabs.append(table_from_m(
            tname,
            [(col, N, {"fmt": "+0%;-0%;0%"})],
            [
                "let",
                f"    Lista = {{{vals}}},",
                f'    Tabela = Table.FromList(Lista, Splitter.SplitByNothing(), {{"{col}"}}),',
                f'    Tipos = Table.TransformColumnTypes(Tabela, {{{{"{col}", type number}}}})',
                "in",
                "    Tipos",
            ],
            description="Parâmetro do simulador de cenários.",
        ))
    return tabs


RELATIONSHIPS = [
    ("fact_vendas", "data", "dim_calendario", "data"),
    ("fact_despesas", "data", "dim_calendario", "data"),
    ("fact_orcamento", "mes", "dim_calendario", "data"),
    ("fact_metas_vendas", "mes", "dim_calendario", "data"),
    ("fact_rh_mensal", "data_referencia", "dim_calendario", "data"),
    ("fact_vendas", "id_filial", "dim_filial", "id_filial"),
    ("fact_despesas", "id_filial", "dim_filial", "id_filial"),
    ("fact_orcamento", "id_filial", "dim_filial", "id_filial"),
    ("fact_metas_vendas", "id_filial", "dim_filial", "id_filial"),
    ("fact_rh_mensal", "id_filial", "dim_filial", "id_filial"),
    ("fact_vendas", "id_cliente", "dim_cliente", "id_cliente"),
    ("fact_vendas", "id_produto", "dim_produto", "id_produto"),
    ("fact_vendas", "id_vendedor", "dim_vendedor", "id_vendedor"),
    ("fact_vendas", "id_canal", "dim_canal", "id_canal"),
    ("fact_despesas", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_despesas", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
    ("fact_orcamento", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_orcamento", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
    ("fact_rh_mensal", "id_departamento", "dim_departamento", "id_departamento"),
]


def build_model(pasta_dados):
    tables = []
    for name, cols in CSV_TABLES.items():
        if name == "dim_calendario":
            t = table_from_csv(
                name, cols, extra_cols=CAL_EXTRA,
                extra_steps=[
                    ("AnoTri", 'Table.AddColumn(Tipos, "ano_tri", each Text.From([ano]) & " " & [trimestre], type text)'),
                    ("OrdemAnoTri", 'Table.AddColumn(AnoTri, "ordem_ano_tri", each [ano] * 10 + Number.From(Text.End([trimestre], 1)), Int64.Type)'),
                ],
                description="Calendário (tabela de datas marcada).",
            )
            t["dataCategory"] = "Time"
            for c in t["columns"]:
                if c["name"] == "data":
                    c["isKey"] = True
        elif name == "dim_categoria_despesa":
            t = table_from_csv(
                name, cols, extra_cols=[("grupo", T, {"sort": "ordem_dre"})],
                extra_steps=[("Grupo", 'Table.AddColumn(Tipos, "grupo", each Text.Replace(Text.Replace([grupo_dre], "Despesas com ", ""), "Despesas ", ""), type text)')],
            )
        else:
            t = table_from_csv(name, cols)
        tables.append(t)
    tables += aux_tables()

    # medidas na tabela _Medidas
    medidas = next(t for t in tables if t["name"] == "_Medidas")
    medidas["measures"] = []
    seen = set()
    for folder, name, dax, fmt, desc in MEASURES:
        assert name not in seen, f"medida duplicada: {name}"
        seen.add(name)
        m = {
            "name": name,
            "expression": dax.split("\n") if "\n" in dax else dax,
            "displayFolder": folder,
            "lineageTag": tag("_Medidas", name),
        }
        if fmt:
            m["formatString"] = fmt
        if desc:
            m["description"] = desc
        medidas["measures"].append(m)

    rels = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rels.append({
            "name": tag("rel", ft, fc, tt, tc),
            "fromTable": ft,
            "fromColumn": fc,
            "toTable": tt,
            "toColumn": tc,
        })

    query_order = ["PastaDados"] + [t["name"] for t in tables]
    model = {
        "name": "EmpresaX",
        "compatibilityLevel": 1600,
        "model": {
            "culture": "pt-BR",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "discourageImplicitMeasures": True,
            "sourceQueryCulture": "pt-BR",
            "tables": tables,
            "relationships": rels,
            "expressions": [
                {
                    "name": "PastaDados",
                    "kind": "m",
                    "expression": f'"{pasta_dados}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
                    "lineageTag": tag("PastaDados"),
                    "description": "Pasta onde estão os CSVs (com a barra no final).",
                    "annotations": [{"name": "PBI_ResultType", "value": "Text"}],
                }
            ],
            "annotations": [
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
                {"name": "PBI_QueryOrder", "value": str(query_order).replace("'", '"')},
                {"name": "PBI_ProTooling", "value": '["DevMode"]'},
            ],
        },
    }
    return model


def check_dax_balance():
    """Checagem simples: parênteses/aspas balanceados e referências a medidas existentes."""
    import re
    names = {n for _, n, _, _, _ in MEASURES}
    problems = []
    for _, n, dax, _, _ in MEASURES:
        s = re.sub(r'"[^"]*"', '""', dax)
        if s.count("(") != s.count(")"):
            problems.append(f"{n}: parênteses desbalanceados")
        if dax.count('"') % 2:
            problems.append(f"{n}: aspas ímpares")
        for ref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", s):
            if ref.startswith("@"):
                continue
            if ref not in names:
                # pode ser coluna qualificada (tabela[coluna]) - essas têm prefixo
                problems.append(f"{n}: referência [{ref}] não é medida")
    return problems
