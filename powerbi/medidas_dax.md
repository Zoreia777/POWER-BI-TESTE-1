# Medidas DAX · Empresa X

Cole as medidas em **Modelagem → Nova medida**. Crie uma tabela vazia chamada `_Medidas`
(*Inserir dados → tabela com 1 coluna vazia*) e guarde todas lá, em pastas de exibição
(*Painel de modelo → Pasta de exibição*) com os nomes dos blocos abaixo.

> **Regra de ouro do modelo:** receita e CMV só contam vendas com `status = "Entregue"`.
> Devoluções ficam fora (aparecem só na medida de taxa de devolução).

---

## 1. Base e controle de período

```dax
Última Data Realizada =
CALCULATE (
    MAX ( dim_calendario[data] ),
    dim_calendario[realizado] = 1,
    ALL ( dim_calendario )
)
```

```dax
Período Realizado? =
-- 1 quando o período filtrado já tem dados reais; útil para esconder visuais "projetados"
IF ( MIN ( dim_calendario[data] ) <= [Última Data Realizada], 1, 0 )
```

---

## 2. Vendas e lucratividade

```dax
Receita Bruta =
CALCULATE ( SUM ( fact_vendas[receita_bruta] ), fact_vendas[status] = "Entregue" )

Descontos =
CALCULATE ( SUM ( fact_vendas[desconto_valor] ), fact_vendas[status] = "Entregue" )

Impostos =
CALCULATE ( SUM ( fact_vendas[impostos_valor] ), fact_vendas[status] = "Entregue" )

Receita Líquida =
CALCULATE ( SUM ( fact_vendas[receita_liquida] ), fact_vendas[status] = "Entregue" )

CMV =
CALCULATE ( SUM ( fact_vendas[custo_total] ), fact_vendas[status] = "Entregue" )

Lucro Bruto = [Receita Líquida] - [CMV]

Margem Bruta % = DIVIDE ( [Lucro Bruto], [Receita Líquida] )

Desconto Médio % = DIVIDE ( [Descontos], [Receita Bruta] )

Pedidos =
CALCULATE ( DISTINCTCOUNT ( fact_vendas[id_pedido] ), fact_vendas[status] = "Entregue" )

Itens Vendidos =
CALCULATE ( SUM ( fact_vendas[quantidade] ), fact_vendas[status] = "Entregue" )

Ticket Médio = DIVIDE ( [Receita Líquida], [Pedidos] )

Taxa de Devolução % =
DIVIDE (
    CALCULATE ( SUM ( fact_vendas[receita_bruta] ), fact_vendas[status] = "Devolvido" ),
    SUM ( fact_vendas[receita_bruta] )
)
```

---

## 3. Despesas, resultado e DRE

```dax
Despesas Totais = SUM ( fact_despesas[valor] )

Despesas com Pessoal =
CALCULATE ( [Despesas Totais], dim_categoria_despesa[grupo_dre] = "Despesas com Pessoal" )

Despesas Comerciais =
CALCULATE ( [Despesas Totais], dim_categoria_despesa[grupo_dre] = "Despesas Comerciais" )

Despesas Operacionais =
CALCULATE ( [Despesas Totais], dim_categoria_despesa[grupo_dre] = "Despesas Operacionais" )

Despesas Administrativas =
CALCULATE ( [Despesas Totais], dim_categoria_despesa[grupo_dre] = "Despesas Administrativas" )

Despesas Financeiras =
CALCULATE ( [Despesas Totais], dim_categoria_despesa[grupo_dre] = "Despesas Financeiras" )

Resultado Operacional = [Lucro Bruto] - [Despesas Totais]

Margem Operacional % = DIVIDE ( [Resultado Operacional], [Receita Líquida] )

Despesas % da Receita = DIVIDE ( [Despesas Totais], [Receita Líquida] )
```

**Cascata (waterfall) do DRE** — crie a tabela de apoio e a medida de seleção:

```dax
tbl_dre =
DATATABLE (
    "Linha", STRING, "Ordem", INTEGER,
    {
        { "Receita Bruta", 1 },
        { "(-) Descontos", 2 },
        { "(-) Impostos", 3 },
        { "(-) CMV", 4 },
        { "(-) Pessoal", 5 },
        { "(-) Comerciais", 6 },
        { "(-) Operacionais", 7 },
        { "(-) Administrativas", 8 },
        { "(-) Financeiras", 9 },
        { "Resultado Operacional", 10 }
    }
)

Valor DRE =
SWITCH (
    SELECTEDVALUE ( tbl_dre[Linha] ),
    "Receita Bruta", [Receita Bruta],
    "(-) Descontos", -[Descontos],
    "(-) Impostos", -[Impostos],
    "(-) CMV", -[CMV],
    "(-) Pessoal", -[Despesas com Pessoal],
    "(-) Comerciais", -[Despesas Comerciais],
    "(-) Operacionais", -[Despesas Operacionais],
    "(-) Administrativas", -[Despesas Administrativas],
    "(-) Financeiras", -[Despesas Financeiras],
    "Resultado Operacional", [Resultado Operacional]
)
```

No gráfico de cascata: Categoria = `tbl_dre[Linha]` (ordenar por `Ordem`), Y = `[Valor DRE]`.
Marque "Resultado Operacional" como **total** nas opções de formato.

---

## 4. Inteligência de tempo

```dax
Receita Líquida LY =
CALCULATE ( [Receita Líquida], SAMEPERIODLASTYEAR ( dim_calendario[data] ) )

Receita Líquida LY (comparável) =
-- compara só até o mesmo ponto do ano passado (evita comparar 9 meses de 2026 com 12 de 2025)
VAR _ultima = [Última Data Realizada]
RETURN
    CALCULATE (
        [Receita Líquida],
        SAMEPERIODLASTYEAR ( dim_calendario[data] ),
        dim_calendario[data] <= EDATE ( _ultima, -12 )
    )

Var. YoY % =
DIVIDE ( [Receita Líquida] - [Receita Líquida LY (comparável)], [Receita Líquida LY (comparável)] )

Receita Líquida Mês Anterior =
CALCULATE ( [Receita Líquida], DATEADD ( dim_calendario[data], -1, MONTH ) )

Var. MoM % =
DIVIDE ( [Receita Líquida] - [Receita Líquida Mês Anterior], [Receita Líquida Mês Anterior] )

Receita YTD =
TOTALYTD ( [Receita Líquida], dim_calendario[data] )

Receita 12M Móvel =
CALCULATE (
    [Receita Líquida],
    DATESINPERIOD ( dim_calendario[data], MAX ( dim_calendario[data] ), -12, MONTH )
)

Receita Média Móvel 3M =
DIVIDE (
    CALCULATE (
        [Receita Líquida],
        DATESINPERIOD ( dim_calendario[data], MAX ( dim_calendario[data] ), -3, MONTH )
    ),
    3
)

Resultado Operacional LY (comparável) =
VAR _ultima = [Última Data Realizada]
RETURN
    CALCULATE (
        [Resultado Operacional],
        SAMEPERIODLASTYEAR ( dim_calendario[data] ),
        dim_calendario[data] <= EDATE ( _ultima, -12 )
    )
```

---

## 5. Metas e projeção

```dax
Meta Receita = SUM ( fact_metas_vendas[meta_receita_liquida] )

Meta Receita (realizado) =
CALCULATE ( [Meta Receita], KEEPFILTERS ( dim_calendario[realizado] = 1 ) )

Atingimento da Meta % = DIVIDE ( [Receita Líquida], [Meta Receita (realizado)] )

Gap para Meta = [Receita Líquida] - [Meta Receita (realizado)]

Projeção de Receita do Ano =
-- realizado até hoje + meta dos meses restantes ajustada pelo ritmo de atingimento
VAR _ultima = [Última Data Realizada]
VAR _ano = YEAR ( _ultima )
VAR _real =
    CALCULATE ( [Receita Líquida], dim_calendario[ano] = _ano, dim_calendario[data] <= _ultima )
VAR _metaReal =
    CALCULATE ( [Meta Receita], dim_calendario[ano] = _ano, dim_calendario[realizado] = 1 )
VAR _metaResto =
    CALCULATE ( [Meta Receita], dim_calendario[ano] = _ano, dim_calendario[realizado] = 0 )
RETURN
    _real + _metaResto * DIVIDE ( _real, _metaReal )
```

---

## 6. Orçamento × Realizado

```dax
Despesa Orçada = SUM ( fact_orcamento[valor_orcado] )

Despesa Orçada (realizado) =
CALCULATE ( [Despesa Orçada], KEEPFILTERS ( dim_calendario[realizado] = 1 ) )

Variação vs Orçado (R$) = [Despesas Totais] - [Despesa Orçada (realizado)]

Variação vs Orçado % = DIVIDE ( [Variação vs Orçado (R$)], [Despesa Orçada (realizado)] )

Execução do Orçamento % = DIVIDE ( [Despesas Totais], [Despesa Orçada (realizado)] )

Cor do Orçamento =
-- use em Formatação condicional → Cor da fonte/preenchimento → Valor do campo
SWITCH (
    TRUE (),
    ISBLANK ( [Execução do Orçamento %] ), BLANK (),
    [Execução do Orçamento %] > 1.10, "#F85149",   -- estourou mais de 10%
    [Execução do Orçamento %] > 1.00, "#D29922",   -- acima do orçado
    "#3FB950"                                      -- dentro do orçado
)

Ícone do Orçamento =
SWITCH (
    TRUE (),
    [Execução do Orçamento %] > 1.10, "▲▲",
    [Execução do Orçamento %] > 1.00, "▲",
    "●"
)
```

> `fact_orcamento[mes]` guarda o **primeiro dia do mês**. Compare sempre em eixos
> mensais (`mes_ano`, `ano_mes`), não em eixo diário.

---

## 7. Clientes, vendedores e Pareto

```dax
Clientes Ativos =
CALCULATE ( DISTINCTCOUNT ( fact_vendas[id_cliente] ), fact_vendas[status] = "Entregue" )

Novos Clientes =
VAR _ini = MIN ( dim_calendario[data] )
VAR _fim = MAX ( dim_calendario[data] )
RETURN
    COUNTROWS (
        FILTER (
            dim_cliente,
            dim_cliente[data_primeira_compra] >= _ini
                && dim_cliente[data_primeira_compra] <= _fim
        )
    )

Receita por Cliente = DIVIDE ( [Receita Líquida], [Clientes Ativos] )

% Acumulado Clientes =
-- usar com eixo = dim_cliente[nome_cliente] ordenado por Receita Líquida (decrescente)
VAR _atual = [Receita Líquida]
VAR _tabela =
    ADDCOLUMNS ( ALLSELECTED ( dim_cliente[nome_cliente] ), "@rec", [Receita Líquida] )
VAR _acum = SUMX ( FILTER ( _tabela, [@rec] >= _atual ), [@rec] )
VAR _total = SUMX ( _tabela, [@rec] )
RETURN
    DIVIDE ( _acum, _total )

Classe ABC =
VAR _p = [% Acumulado Clientes]
RETURN
    SWITCH ( TRUE (), ISBLANK ( [Receita Líquida] ), BLANK (), _p <= 0.8, "A", _p <= 0.95, "B", "C" )

Ranking Vendedor =
RANKX ( ALLSELECTED ( dim_vendedor[nome_vendedor] ), [Receita Líquida], , DESC, DENSE )

Ranking Produto =
RANKX ( ALLSELECTED ( dim_produto[produto] ), [Lucro Bruto], , DESC, DENSE )
```

---

## 8. Pessoas

`fact_rh_mensal[data_referencia]` é o **último dia do mês** (foto do quadro).

```dax
Headcount (fim do período) =
CALCULATE (
    SUM ( fact_rh_mensal[headcount] ),
    LASTNONBLANK (
        dim_calendario[data],
        CALCULATE ( COUNTROWS ( fact_rh_mensal ) )
    )
)

Headcount Médio =
AVERAGEX ( VALUES ( dim_calendario[ano_mes] ), CALCULATE ( SUM ( fact_rh_mensal[headcount] ) ) )

Admissões = SUM ( fact_rh_mensal[admissoes] )

Desligamentos = SUM ( fact_rh_mensal[desligamentos] )

Turnover % = DIVIDE ( [Desligamentos], [Headcount Médio] )

Custo de Pessoal por Funcionário =
DIVIDE ( [Despesas com Pessoal], [Headcount Médio] )

Receita por Funcionário = DIVIDE ( [Receita Líquida], [Headcount Médio] )

Vagas em Aberto =
-- planejado − real, no fim do período
CALCULATE (
    SUM ( fact_rh_mensal[headcount_planejado] ) - SUM ( fact_rh_mensal[headcount] ),
    LASTNONBLANK ( dim_calendario[data], CALCULATE ( COUNTROWS ( fact_rh_mensal ) ) )
)
```

---

## 9. Métrica dinâmica (um botão, vários gráficos)

Crie a tabela desconectada:

```dax
sel_metrica =
DATATABLE (
    "metrica", STRING, "ordem", INTEGER,
    {
        { "Receita Líquida", 1 },
        { "Lucro Bruto", 2 },
        { "Resultado Operacional", 3 },
        { "Despesas", 4 },
        { "Margem Bruta %", 5 }
    }
)
```

Ordene `metrica` por `ordem`. Depois a medida:

```dax
Métrica Dinâmica =
SWITCH (
    SELECTEDVALUE ( sel_metrica[metrica], "Receita Líquida" ),
    "Receita Líquida", [Receita Líquida],
    "Lucro Bruto", [Lucro Bruto],
    "Resultado Operacional", [Resultado Operacional],
    "Despesas", [Despesas Totais],
    "Margem Bruta %", [Margem Bruta %]
)
```

**Formato dinâmico:** selecione a medida → *Formato → Formato dinâmico* e use:

```dax
SWITCH (
    SELECTEDVALUE ( sel_metrica[metrica], "Receita Líquida" ),
    "Margem Bruta %", "0.0%",
    "R$ #,0"
)
```

Use `sel_metrica[metrica]` como **segmentação (botões)** e `[Métrica Dinâmica]` no eixo Y dos gráficos.

**Título dinâmico:**

```dax
Título da Visão =
SELECTEDVALUE ( sel_metrica[metrica], "Receita Líquida" )
    & " · "
    & FORMAT ( MIN ( dim_calendario[data] ), "mmm/yy" )
    & " a "
    & FORMAT ( MIN ( MAX ( dim_calendario[data] ), [Última Data Realizada] ), "mmm/yy" )
```

(Visual → Formato → Título → fx → *Valor do campo* → `[Título da Visão]`.)

---

## 10. Simulador de cenários (what-if)

Crie três parâmetros com `GENERATESERIES` (ou *Modelagem → Novo parâmetro*):

```dax
par_preco   = GENERATESERIES ( -0.10, 0.10, 0.01 )
par_volume  = GENERATESERIES ( -0.20, 0.20, 0.01 )
par_custo   = GENERATESERIES ( -0.10, 0.15, 0.01 )
par_despesa = GENERATESERIES ( -0.15, 0.15, 0.01 )
```

Cada tabela vira uma segmentação (barra deslizante) com a coluna `[Value]`.

```dax
Δ Preço    = SELECTEDVALUE ( par_preco[Value], 0 )
Δ Volume   = SELECTEDVALUE ( par_volume[Value], 0 )
Δ Custo    = SELECTEDVALUE ( par_custo[Value], 0 )
Δ Despesas = SELECTEDVALUE ( par_despesa[Value], 0 )

Receita Líquida (Cenário) = [Receita Líquida] * ( 1 + [Δ Volume] ) * ( 1 + [Δ Preço] )

CMV (Cenário) = [CMV] * ( 1 + [Δ Volume] ) * ( 1 + [Δ Custo] )

Despesas (Cenário) =
-- só a parte variável acompanha o volume; a fixa não muda
VAR _var =
    CALCULATE ( [Despesas Totais], dim_categoria_despesa[tipo_custo] = "Variável" )
VAR _fix =
    CALCULATE ( [Despesas Totais], dim_categoria_despesa[tipo_custo] = "Fixa" )
RETURN
    ( _var * ( 1 + [Δ Volume] ) + _fix ) * ( 1 + [Δ Despesas] )

Resultado (Cenário) =
[Receita Líquida (Cenário)] - [CMV (Cenário)] - [Despesas (Cenário)]

Δ Resultado vs Base = [Resultado (Cenário)] - [Resultado Operacional]

Margem Operacional (Cenário) =
DIVIDE ( [Resultado (Cenário)], [Receita Líquida (Cenário)] )
```

> Simplificação: impostos e comissões acompanham a receita proporcionalmente.
> É um simulador de decisão rápida, não uma projeção contábil.

---

## 11. Textos inteligentes (storytelling)

```dax
Texto Destaque =
VAR _rec = [Receita Líquida]
VAR _yoy = [Var. YoY %]
VAR _marg = [Margem Operacional %]
RETURN
    "Receita de " & FORMAT ( _rec / 1000000, "R$ 0.0" ) & " mi, "
        & IF ( _yoy >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( _yoy ), "0.0%" ) & " vs mesmo período do ano anterior. "
        & "Margem operacional de " & FORMAT ( _marg, "0.0%" ) & "."

Melhor Filial =
VAR _t = ADDCOLUMNS ( VALUES ( dim_filial[filial] ), "@r", [Receita Líquida] )
RETURN
    MAXX ( TOPN ( 1, _t, [@r], DESC ), dim_filial[filial] )

Pior Atingimento de Meta =
VAR _t = ADDCOLUMNS ( VALUES ( dim_filial[filial] ), "@a", [Atingimento da Meta %] )
RETURN
    MAXX ( TOPN ( 1, _t, [@a], ASC ), dim_filial[filial] )
```
