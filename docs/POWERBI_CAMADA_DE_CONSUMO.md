# Camada de consumo do Power BI — views, indicadores, DAX e validação

> ⚠️ **Estado de validação:** as medidas DAX abaixo **NÃO foram executadas no Power BI** (o ambiente de desenvolvimento não tem Power BI). O que foi validado: (1) as views SQL, contra cálculos independentes em pandas; (2) as definições DAX, por *lint* estático (colunas e medidas referenciadas existem; parênteses balanceados). O que falta: abrir o modelo no Power BI e conferir os **valores de referência** da seção 5. Este documento é gerado por `scripts/run_powerbi.py`.

## 1. Visão geral

`python scripts/run_etl.py && python scripts/run_powerbi.py` cria o schema `bi` no DuckDB (views estáveis) e exporta cada view para `powerbi/dados/*.csv` (o Power BI Desktop importa CSV sem driver adicional). A receita principal é a **receita ajustada provisória** (PN-DEV-01), sempre ao lado de registrada, entregues e devoluções.
O arquivo `powerbi/medidas_dax.md` (anterior) segue válido como material de apoio; as medidas desta camada seguem a política de devoluções e o contrato de views testado.

## 2. Modelo e relacionamentos (muitos-para-um; filtro vai da dimensão para o fato)

| Fato (coluna) | → | Dimensão (coluna) |
|---|---|---|
| `fato_vendas[data]` | → | `dim_calendario[data]` |
| `fato_vendas[id_produto]` | → | `dim_produto[id_produto]` |
| `fato_vendas[id_filial]` | → | `dim_filial[id_filial]` |
| `fato_vendas[id_canal]` | → | `dim_canal[id_canal]` |
| `fato_vendas[id_cliente]` | → | `dim_cliente[id_cliente]` |
| `fato_despesas[data]` | → | `dim_calendario[data]` |
| `fato_despesas[id_filial]` | → | `dim_filial[id_filial]` |
| `fato_despesas[id_departamento]` | → | `dim_departamento[id_departamento]` |
| `fato_despesas[id_categoria_despesa]` | → | `dim_categoria_despesa[id_categoria_despesa]` |
| `fato_orcamento[mes]` | → | `dim_calendario[data]` |
| `fato_orcamento[id_filial]` | → | `dim_filial[id_filial]` |
| `fato_orcamento[id_departamento]` | → | `dim_departamento[id_departamento]` |
| `fato_orcamento[id_categoria_despesa]` | → | `dim_categoria_despesa[id_categoria_despesa]` |
| `fato_orcado_realizado_mes[mes]` | → | `dim_calendario[data]` |
| `fato_orcado_realizado_mes[id_filial]` | → | `dim_filial[id_filial]` |
| `fato_orcado_realizado_mes[id_departamento]` | → | `dim_departamento[id_departamento]` |
| `fato_orcado_realizado_mes[id_categoria_despesa]` | → | `dim_categoria_despesa[id_categoria_despesa]` |

Dimensão de datas: marcar `dim_calendario` como tabela de datas (coluna `data`). Fatos mensais (`fato_orcamento`, `fato_orcado_realizado_mes`) usam o 1º dia do mês em `mes`.

## 3. Contrato das views (nomes e ordem das colunas — testados)

| View / tabela | Linhas | Colunas |
|---|---:|---|
| `dim_calendario` | 1.096 | `data`, `ano`, `semestre`, `trimestre`, `mes_num`, `mes_abrev`, `ano_mes`, `primeiro_dia_mes`, `ordem_ano_mes`, `dia_util`, `realizado` |
| `dim_produto` | 39 | `id_produto`, `sku`, `produto`, `categoria`, `subcategoria`, `preco_lista`, `aliquota_imposto` |
| `dim_filial` | 8 | `id_filial`, `filial`, `cidade`, `uf`, `regiao`, `tipo`, `concentra_despesas_corporativas` |
| `dim_canal` | 4 | `id_canal`, `canal`, `tipo_canal` |
| `dim_departamento` | 8 | `id_departamento`, `departamento`, `centro_custo`, `tipo_area` |
| `dim_categoria_despesa` | 18 | `id_categoria_despesa`, `categoria_despesa`, `grupo_dre`, `tipo_custo`, `ordem_dre` |
| `dim_cliente` | 650 | `id_cliente`, `nome_cliente`, `segmento`, `cidade`, `uf`, `regiao` |
| `fato_vendas` | 59.365 | `id_venda`, `id_pedido`, `data`, `mes`, `id_cliente`, `id_produto`, `id_filial`, `id_vendedor`, `id_canal`, `status`, `quantidade`, `preco_unitario`, `desconto_pct`, `receita_bruta`, `desconto_valor`, `impostos_valor`, `receita_registrada`, `receita_ajustada`, `devolucao`, `custo_registrado`, `custo_ajustado`, `lucro_bruto_ajustado`, `unidades_entregues`, `flag_margem_negativa`, `flag_devolvida`, `linha_csv_origem` |
| `fato_despesas` | 7.075 | `id_despesa`, `data`, `mes`, `id_departamento`, `id_categoria_despesa`, `id_filial`, `fornecedor`, `valor` |
| `fato_orcamento` | 6.005 | `mes`, `id_departamento`, `id_categoria_despesa`, `id_filial`, `valor_orcado`, `mes_realizado` |
| `fato_orcado_realizado_mes` | 5.478 | `mes`, `id_departamento`, `id_categoria_despesa`, `id_filial`, `orcado`, `realizado`, `flag_sem_orcamento`, `flag_sem_lancamento` |
| `kpi_empresa_mes` | 33 | `mes`, `receita_registrada`, `vendas_entregues`, `devolucoes`, `receita_ajustada`, `custo_ajustado`, `lucro_bruto_ajustado`, `despesas`, `resultado_operacional_estimado`, `margem_bruta_pct`, `margem_operacional_estimada_pct`, `pedidos`, `unidades` |

## 4. Regras de filtro e granularidade

| Regra | Por quê |
|---|---|
| `fato_vendas` tem 1 linha por **item de pedido**; **Pedidos** é contagem distinta e **não soma** entre cortes. | Um pedido pode ter até 4 itens/produtos. |
| Despesas e orçamento **não têm** produto, canal nem cliente: as medidas retornam **vazio** se esses cortes estiverem ativos. | Evita exibir o total da empresa dentro de um produto (leitura enganosa). |
| Por filial, a **Matriz** concentra despesas corporativas: não compare `Despesas % da Receita Ajustada` da Matriz com as demais. | PN-SIN-01/Etapa 3 (análise 04). |
| Percentuais são **razão de somas** (`DIVIDE(SUM, SUM)`), nunca média de percentuais. | Média de percentuais pondera errado. |
| Variação MoM/YoY é **vazia** (BLANK) sem base ou com base zero. | Não é crescimento nem 0%. |
| Em 2026, compare apenas meses realizados (`dim_calendario[realizado] = 1`); o orçamento **anual** inclui meses futuros. | PN-ORC-01. |
| `Resultado Operacional Estimado` deve exibir o rótulo “estimado do dataset; não é lucro líquido contábil”. | Não há impostos sobre lucro, juros de capital etc. |
| `Receita Ajustada` é **provisória**: exibir a nota quando for o KPI principal. | PN-DEV-01..04. |

## 5. Dicionário de indicadores e definições DAX (não executadas no Power BI)

### IND-01 · Receita Registrada

- **Definição:** Receita líquida (bruta − desconto − impostos) de TODAS as linhas, inclusive devolvidas.
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** calendário, filial, produto, canal, cliente · **Formato:** `R$ #,0`
- **Premissa/observação:** PN-DEV-01/04: indicador separado, sempre reconciliável

```dax
Receita Registrada =
    SUM ( fato_vendas[receita_registrada] )
```

### IND-02 · Vendas Entregues

- **Definição:** Receita líquida das linhas com status Entregue.
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** idem IND-01 · **Formato:** `R$ #,0`

```dax
Vendas Entregues =
    CALCULATE ( SUM ( fato_vendas[receita_registrada] ), fato_vendas[status] = "Entregue" )
```

### IND-03 · Devoluções

- **Definição:** Receita líquida das linhas com status Devolvido (devolução integral, PN-DEV-01).
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** idem IND-01 · **Formato:** `R$ #,0`
- **Premissa/observação:** Sem data de devolução: fica no mês da venda (PN-DEV-03)

```dax
Devoluções =
    SUM ( fato_vendas[devolucao] )
```

### IND-04 · Receita Ajustada

- **Definição:** INDICADOR PRINCIPAL PROVISÓRIO: receita das vendas entregues. Não é reconhecimento contábil definitivo.
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** idem IND-01 · **Formato:** `R$ #,0`
- **Premissa/observação:** PN-DEV-01 (política PROVISORIA_EXCLUI_DEVOLVIDAS)

```dax
Receita Ajustada =
    SUM ( fato_vendas[receita_ajustada] )
```

### IND-05 · Diferença de Reconciliação

- **Definição:** Registrada − Entregues − Devoluções. Deve ser 0,00 em qualquer filtro.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `R$ #,0.00`
- **Premissa/observação:** PN-DEV-04

```dax
Diferença de Reconciliação =
    [Receita Registrada] - [Vendas Entregues] - [Devoluções]
```

### IND-06 · Taxa de Devolução %

- **Definição:** Devoluções ÷ Receita Registrada (razão de somas).
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `0.0%`

```dax
Taxa de Devolução % =
    DIVIDE ( [Devoluções], [Receita Registrada] )
```

### IND-07 · Custo Ajustado

- **Definição:** Custo das linhas entregues (custo devolvido considerado recuperado — hipótese).
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** idem · **Formato:** `R$ #,0`
- **Premissa/observação:** PN-DEV-02 (hipótese não comprovada)

```dax
Custo Ajustado =
    SUM ( fato_vendas[custo_ajustado] )
```

### IND-08 · Lucro Bruto Ajustado

- **Definição:** Receita Ajustada − Custo Ajustado.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `R$ #,0`

```dax
Lucro Bruto Ajustado =
    [Receita Ajustada] - [Custo Ajustado]
```

### IND-09 · Margem Bruta Ajustada %

- **Definição:** Lucro Bruto ÷ Receita Ajustada (razão de somas; nunca média de percentuais).
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `0.0%`
- **Premissa/observação:** PN-MRG-01

```dax
Margem Bruta Ajustada % =
    DIVIDE ( [Lucro Bruto Ajustado], [Receita Ajustada] )
```

### IND-10 · Unidades Entregues

- **Definição:** Soma das quantidades das linhas entregues.
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** idem · **Formato:** `#,0`

```dax
Unidades Entregues =
    SUM ( fato_vendas[unidades_entregues] )
```

### IND-11 · Pedidos

- **Definição:** Pedidos distintos (inclui pedidos com linhas devolvidas). Não é aditivo entre cortes.
- **Tipo:** base · **Grão:** pedido · **Filtros válidos:** idem · **Formato:** `#,0`

```dax
Pedidos =
    DISTINCTCOUNT ( fato_vendas[id_pedido] )
```

### IND-12 · Ticket por Pedido

- **Definição:** Receita Ajustada ÷ Pedidos.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `R$ #,0`

```dax
Ticket por Pedido =
    DIVIDE ( [Receita Ajustada], [Pedidos] )
```

### IND-13 · Desconto Efetivo %

- **Definição:** Σ desconto ÷ Σ receita bruta (todas as linhas).
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `0.0%`
- **Premissa/observação:** PN-PRC-01: desconto ≠ preço praticado vs lista

```dax
Desconto Efetivo % =
    DIVIDE ( SUM ( fato_vendas[desconto_valor] ), SUM ( fato_vendas[receita_bruta] ) )
```

### IND-14 · Preço Bruto Médio por Unidade

- **Definição:** Σ receita bruta ÷ Σ quantidade (todas as linhas). Só faz sentido por produto.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** produto · **Formato:** `R$ #,0.00`

```dax
Preço Bruto Médio por Unidade =
    DIVIDE ( SUM ( fato_vendas[receita_bruta] ), SUM ( fato_vendas[quantidade] ) )
```

### IND-15 · Linhas com Margem Negativa

- **Definição:** Linhas em que custo > receita líquida.
- **Tipo:** base · **Grão:** item de pedido · **Filtros válidos:** idem · **Formato:** `#,0`
- **Premissa/observação:** PN-MRG-01

```dax
Linhas com Margem Negativa =
    SUM ( fato_vendas[flag_margem_negativa] )
```

### IND-16 · % Linhas com Margem Negativa

- **Definição:** Linhas negativas ÷ total de linhas.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `0.0%`
- **Premissa/observação:** PN-MRG-01

```dax
% Linhas com Margem Negativa =
    DIVIDE ( [Linhas com Margem Negativa], COUNTROWS ( fato_vendas ) )
```

### IND-17 · Despesas

- **Definição:** Soma dos lançamentos de despesa. BLANK se o corte incluir produto, canal ou cliente (despesas não têm esses vínculos).
- **Tipo:** base · **Grão:** lançamento · **Filtros válidos:** calendário, filial, departamento, categoria · **Formato:** `R$ #,0`
- **Premissa/observação:** Matriz concentra despesas corporativas

```dax
Despesas =
    IF ( ISFILTERED ( dim_produto ) || ISFILTERED ( dim_canal ) || ISFILTERED ( dim_cliente ), BLANK (), SUM ( fato_despesas[valor] ) )
```

### IND-18 · Despesas % da Receita Ajustada

- **Definição:** Despesas ÷ Receita Ajustada (por filial, a Matriz não é comparável às demais).
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** calendário, filial · **Formato:** `0.0%`

```dax
Despesas % da Receita Ajustada =
    DIVIDE ( [Despesas], [Receita Ajustada] )
```

### IND-19 · Resultado Operacional Estimado

- **Definição:** Lucro Bruto Ajustado − Despesas. NÃO é lucro líquido contábil.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** calendário, filial · **Formato:** `R$ #,0`
- **Premissa/observação:** Rótulo obrigatório: resultado operacional ESTIMADO do dataset

```dax
Resultado Operacional Estimado =
    IF ( ISBLANK ( [Despesas] ), BLANK (), [Lucro Bruto Ajustado] - [Despesas] )
```

### IND-20 · Margem Operacional Estimada %

- **Definição:** Resultado Operacional Estimado ÷ Receita Ajustada.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** calendário, filial · **Formato:** `0.0%`

```dax
Margem Operacional Estimada % =
    DIVIDE ( [Resultado Operacional Estimado], [Receita Ajustada] )
```

### IND-21 · Receita Ajustada Mês Anterior

- **Definição:** Receita Ajustada do mês imediatamente anterior ao filtrado.
- **Tipo:** tempo · **Grão:** mês · **Filtros válidos:** calendário (1 mês) · **Formato:** `R$ #,0`

```dax
Receita Ajustada Mês Anterior =
    CALCULATE ( [Receita Ajustada], DATEADD ( dim_calendario[data], -1, MONTH ) )
```

### IND-22 · Variação MoM %

- **Definição:** Receita Ajustada ÷ mês anterior − 1. BLANK sem base ou base zero (não é 0% nem crescimento).
- **Tipo:** tempo · **Grão:** mês · **Filtros válidos:** calendário (1 mês) · **Formato:** `0.0%`
- **Premissa/observação:** Etapa 3, análise 07

```dax
Variação MoM % =
    VAR base = [Receita Ajustada Mês Anterior] RETURN IF ( ISBLANK ( base ) || base = 0, BLANK (), DIVIDE ( [Receita Ajustada] - base, base ) )
```

### IND-23 · Receita Ajustada Ano Anterior

- **Definição:** Receita Ajustada do mesmo período do ano anterior.
- **Tipo:** tempo · **Grão:** mês · **Filtros válidos:** calendário · **Formato:** `R$ #,0`

```dax
Receita Ajustada Ano Anterior =
    CALCULATE ( [Receita Ajustada], SAMEPERIODLASTYEAR ( dim_calendario[data] ) )
```

### IND-24 · Variação YoY %

- **Definição:** Receita Ajustada ÷ mesmo período do ano anterior − 1. BLANK sem base.
- **Tipo:** tempo · **Grão:** mês · **Filtros válidos:** calendário · **Formato:** `0.0%`
- **Premissa/observação:** Para 2026 comparar só meses realizados (use filtro de calendário[realizado] = 1)

```dax
Variação YoY % =
    VAR base = [Receita Ajustada Ano Anterior] RETURN IF ( ISBLANK ( base ) || base = 0, BLANK (), DIVIDE ( [Receita Ajustada] - base, base ) )
```

### IND-25 · Orçamento Anual

- **Definição:** Orçamento dos 12 meses do(s) ano(s) filtrado(s), inclusive meses futuros.
- **Tipo:** base · **Grão:** mês × departamento × categoria × filial · **Filtros válidos:** ano, filial, departamento, categoria · **Formato:** `R$ #,0`
- **Premissa/observação:** PN-ORC-01

```dax
Orçamento Anual =
    IF ( ISFILTERED ( dim_produto ) || ISFILTERED ( dim_canal ) || ISFILTERED ( dim_cliente ), BLANK (), CALCULATE ( SUM ( fato_orcamento[valor_orcado] ), ALLEXCEPT ( dim_calendario, dim_calendario[ano] ) ) )
```

### IND-26 · Orçamento Acumulado

- **Definição:** Orçamento dos meses REALIZADOS dentro do filtro de calendário.
- **Tipo:** base · **Grão:** idem · **Filtros válidos:** calendário, filial, departamento, categoria · **Formato:** `R$ #,0`
- **Premissa/observação:** PN-ORC-01

```dax
Orçamento Acumulado =
    IF ( ISFILTERED ( dim_produto ) || ISFILTERED ( dim_canal ) || ISFILTERED ( dim_cliente ), BLANK (), CALCULATE ( SUM ( fato_orcamento[valor_orcado] ), fato_orcamento[mes_realizado] = 1 ) )
```

### IND-27 · Realizado Acumulado

- **Definição:** Despesas realizadas nos meses do filtro (tabela orçado × realizado).
- **Tipo:** base · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `R$ #,0`
- **Premissa/observação:** PN-ORC-01

```dax
Realizado Acumulado =
    IF ( ISFILTERED ( dim_produto ) || ISFILTERED ( dim_canal ) || ISFILTERED ( dim_cliente ), BLANK (), SUM ( fato_orcado_realizado_mes[realizado] ) )
```

### IND-28 · Execução do Orçamento %

- **Definição:** Realizado Acumulado ÷ Orçamento ACUMULADO (comparação correta).
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `0.0%`
- **Premissa/observação:** PN-ORC-01

```dax
Execução do Orçamento % =
    DIVIDE ( [Realizado Acumulado], [Orçamento Acumulado] )
```

### IND-29 · Consumo do Orçamento Anual %

- **Definição:** Realizado Acumulado ÷ Orçamento ANUAL. NÃO é execução: ano em curso dá 'economia' falsa.
- **Tipo:** derivada · **Grão:** idem · **Filtros válidos:** idem · **Formato:** `0.0%`
- **Premissa/observação:** Leitura ingênua (Etapa 3, 06c)

```dax
Consumo do Orçamento Anual % =
    DIVIDE ( [Realizado Acumulado], [Orçamento Anual] )
```

## 6. Checklist de validação no Power BI (valores de referência)

Calculados **de forma independente** direto dos 13 CSVs (pandas) e iguais ao SQL sobre as views `bi` (`scripts/run_powerbi.py` interrompe se divergirem). Para cada contexto, aplique os filtros indicados e confira a medida; tolerância R$ 0,01 (valores) / 0,01 p.p. (percentuais). Arquivo completo: `powerbi/referencia/valores_referencia.csv`.

| Contexto | Receita Registrada | Devoluções | Receita Ajustada | Margem Bruta Ajustada % | Despesas | Resultado Operacional Estimado | Variação YoY % | Orçamento Acumulado | Execução do Orçamento % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **C01** Todos os meses realizados (sem filtro) | 136.505.354 | 2.990.527 | 133.514.827 | 41,25% | 45.712.808 | 9.365.294 | (vazio) | 45.508.644 | 100,45% |
| **C02** Ano 2024 | 41.766.867 | 964.792 | 40.802.075 | 42,25% | 14.114.037 | 3.123.302 | (vazio) | 14.060.255 | 100,38% |
| **C03** Ano 2025 | 52.576.979 | 1.156.564 | 51.420.415 | 41,27% | 17.474.510 | 3.745.150 | (vazio) | 17.387.829 | 100,50% |
| **C04** Ano 2026 (jan–set) | 42.161.509 | 869.171 | 41.292.338 | 40,25% | 14.124.260 | 2.496.843 | (vazio) | 14.060.560 | 100,45% |
| **C05** Mês set/2026 | 5.410.974 | 109.190 | 5.301.784 | 39,72% | 1.709.308 | 396.406 | 14,08% | 1.693.440 | 100,94% |
| **C06** Mês jan/2026 | 4.324.699 | 81.953 | 4.242.746 | 40,56% | 1.441.683 | 279.094 | 33,38% | 1.414.790 | 101,90% |
| **C07** Porto Alegre, fev/2026 | 182.901 | 3.491 | 179.410 | 40,26% | 82.270 | -10.033 | -48,93% | 87.433 | 94,09% |
| **C08** Matriz, ano 2026 | 12.530.304 | 250.450 | 12.279.853 | 41,34% | 6.897.972 | -1.821.825 | (vazio) | 6.912.627 | 99,79% |
| **C09** Smartphone X Max, ano 2026 | 3.273.434 | 58.040 | 3.215.394 | -9,92% | (vazio) | (vazio) | (vazio) | (vazio) | (vazio) |
| **C10** Notebook Pro 14", ago/2025 | 12.312 | 0 | 12.312 | 16,99% | (vazio) | (vazio) | -95,41% | (vazio) | (vazio) |

**Como registrar o resultado:** marque cada linha conferida; qualquer divergência deve ser reportada com o contexto e a medida. Só depois disso o texto “validado no Power BI” pode ser usado.
