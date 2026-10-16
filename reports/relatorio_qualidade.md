# Relatório de qualidade do ETL

Resultado: **APROVADO** — 143 validações OK, 0 erros, 3 observações.

Política de devoluções vigente: `PROVISORIA_EXCLUI_DEVOLVIDAS`

## Registros por camada

| Tabela | raw | stg | mart |
|---|---:|---:|---:|
| dim_calendario | 1,096 | 1,096 | 1,096 |
| dim_canal | 4 | 4 | 4 |
| dim_categoria_despesa | 18 | 18 | 18 |
| dim_cliente | 650 | 650 | 650 |
| dim_departamento | 8 | 8 | 8 |
| dim_filial | 8 | 8 | 8 |
| dim_produto | 39 | 39 | 39 |
| dim_vendedor | 24 | 24 | 24 |
| fact_despesas | 7,075 | 7,075 | 7,075 |
| fact_metas_vendas | 270 | 270 | 270 |
| fact_orcamento | 6,005 | 6,005 | 6,005 |
| fact_rh_mensal | 909 | 909 | 909 |
| fact_vendas | 59,365 | 59,365 | 59,365 |
| kpi_margem_negativa_filial | — | — | 8 |
| kpi_margem_negativa_mes | — | — | 33 |
| kpi_margem_negativa_pedido | — | — | 611 |
| kpi_margem_negativa_produto | — | — | 39 |
| kpi_preco_mes | — | — | 33 |
| kpi_preco_produto_mes | — | — | 1,287 |
| kpi_vendas_mes | — | — | 33 |
| meta_vs_realizado_mensal | — | — | 246 |
| orcado_vs_realizado_acumulado | — | — | 264 |
| orcado_vs_realizado_mensal | — | — | 5,478 |
| periodo_realizado | — | — | 1 |
| ref_comportamentos_sinteticos | — | — | 17 |

## Observações

| Camada | Tabela | Regra | Esperado | Obtido | Ação necessária |
|---|---|---|---|---|---|
| mart | fact_vendas | OBS-1: linhas 'Devolvido' mantidas com valores originais positivos; receita ajustada aplica PN-DEV-01/02/03 | - | 1310 | Nenhuma no ETL: decisão de negócio registrada. Manter o rótulo 'provisória/não oficial' nos KPIs; reabrir se surgir data ou lançamento de estorno. |
| mart | fact_vendas | OBS-2: linhas com margem negativa (custo > receita líquida) preservadas e sinalizadas | - | 612 | Nenhuma no ETL (dado preservado). A investigação por produto/período é tema da análise (Etapas 3 e 4). |
| mart | fact_orcamento | OBS-3: linhas de orçamento posteriores a 2026-09-01 (futuro) excluídas das comparações | - | 527 | Nenhuma: orçamento é prospectivo. O corte avança sozinho quando houver novos meses realizados. |

## Validações aprovadas

| Camada | Tabela | Regra | Esperado | Obtido |
|---|---|---|---|---|
| raw | dim_calendario | registros no raw = registros do CSV | 1096 | 1096 |
| raw | dim_canal | registros no raw = registros do CSV | 4 | 4 |
| raw | dim_categoria_despesa | registros no raw = registros do CSV | 18 | 18 |
| raw | dim_cliente | registros no raw = registros do CSV | 650 | 650 |
| raw | dim_departamento | registros no raw = registros do CSV | 8 | 8 |
| raw | dim_filial | registros no raw = registros do CSV | 8 | 8 |
| raw | dim_produto | registros no raw = registros do CSV | 39 | 39 |
| raw | dim_vendedor | registros no raw = registros do CSV | 24 | 24 |
| raw | fact_despesas | registros no raw = registros do CSV | 7075 | 7075 |
| raw | fact_metas_vendas | registros no raw = registros do CSV | 270 | 270 |
| raw | fact_orcamento | registros no raw = registros do CSV | 6005 | 6005 |
| raw | fact_rh_mensal | registros no raw = registros do CSV | 909 | 909 |
| raw | fact_vendas | registros no raw = registros do CSV | 59365 | 59365 |
| stg | dim_calendario | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_canal | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_categoria_despesa | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_cliente | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_departamento | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_filial | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_produto | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_vendedor | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | fact_despesas | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | fact_metas_vendas | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | fact_orcamento | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | fact_rh_mensal | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | fact_vendas | tipagem e obrigatoriedade das colunas (nenhuma falha) | 0 | 0 |
| stg | dim_calendario | registros stg = raw (nada descartado) | 1096 | 1096 |
| stg | dim_calendario | chave primária única (data) | 0 | 0 |
| stg | dim_calendario | data data: valor convertido = texto original | 0 | 0 |
| stg | dim_calendario | data primeiro_dia_mes: valor convertido = texto original | 0 | 0 |
| stg | dim_canal | registros stg = raw (nada descartado) | 4 | 4 |
| stg | dim_canal | chave primária única (id_canal) | 0 | 0 |
| stg | dim_categoria_despesa | registros stg = raw (nada descartado) | 18 | 18 |
| stg | dim_categoria_despesa | chave primária única (id_categoria_despesa) | 0 | 0 |
| stg | dim_cliente | registros stg = raw (nada descartado) | 650 | 650 |
| stg | dim_cliente | chave primária única (id_cliente) | 0 | 0 |
| stg | dim_cliente | data data_cadastro: valor convertido = texto original | 0 | 0 |
| stg | dim_cliente | data data_primeira_compra: valor convertido = texto original | 0 | 0 |
| stg | dim_departamento | registros stg = raw (nada descartado) | 8 | 8 |
| stg | dim_departamento | chave primária única (id_departamento) | 0 | 0 |
| stg | dim_filial | registros stg = raw (nada descartado) | 8 | 8 |
| stg | dim_filial | chave primária única (id_filial) | 0 | 0 |
| stg | dim_filial | data data_abertura: valor convertido = texto original | 0 | 0 |
| stg | dim_produto | registros stg = raw (nada descartado) | 39 | 39 |
| stg | dim_produto | chave primária única (id_produto) | 0 | 0 |
| stg | dim_produto | soma de preco_lista: raw = stg | 57420.0000 | 57420.0000 |
| stg | dim_produto | soma de custo_unitario_base: raw = stg | 29945.1000 | 29945.1000 |
| stg | dim_produto | soma de margem_lista_pct: raw = stg | 20.9900 | 20.9900 |
| stg | dim_produto | soma de aliquota_imposto: raw = stg | 5.9000 | 5.9000 |
| stg | dim_vendedor | registros stg = raw (nada descartado) | 24 | 24 |
| stg | dim_vendedor | chave primária única (id_vendedor) | 0 | 0 |
| stg | dim_vendedor | data data_admissao: valor convertido = texto original | 0 | 0 |
| stg | fact_despesas | registros stg = raw (nada descartado) | 7075 | 7075 |
| stg | fact_despesas | chave primária única (id_despesa) | 0 | 0 |
| stg | fact_despesas | data data: valor convertido = texto original | 0 | 0 |
| stg | fact_despesas | soma de valor: raw = stg | 45712808.0600 | 45712808.0600 |
| stg | fact_metas_vendas | registros stg = raw (nada descartado) | 270 | 270 |
| stg | fact_metas_vendas | chave primária única (mes, id_filial) | 0 | 0 |
| stg | fact_metas_vendas | data mes: valor convertido = texto original | 0 | 0 |
| stg | fact_metas_vendas | soma de meta_receita_liquida: raw = stg | 157802000.0000 | 157802000.0000 |
| stg | fact_metas_vendas | soma de meta_margem_bruta_pct: raw = stg | 98.2800 | 98.2800 |
| stg | fact_metas_vendas | soma de meta_lucro_bruto: raw = stg | 58099500.0000 | 58099500.0000 |
| stg | fact_orcamento | registros stg = raw (nada descartado) | 6005 | 6005 |
| stg | fact_orcamento | chave primária única (mes, id_departamento, id_categoria_despesa, id_filial) | 0 | 0 |
| stg | fact_orcamento | data mes: valor convertido = texto original | 0 | 0 |
| stg | fact_orcamento | soma de valor_orcado: raw = stg | 51117629.0000 | 51117629.0000 |
| stg | fact_rh_mensal | registros stg = raw (nada descartado) | 909 | 909 |
| stg | fact_rh_mensal | chave primária única (data_referencia, id_departamento, id_filial) | 0 | 0 |
| stg | fact_rh_mensal | data data_referencia: valor convertido = texto original | 0 | 0 |
| stg | fact_vendas | registros stg = raw (nada descartado) | 59365 | 59365 |
| stg | fact_vendas | chave primária única (id_venda) | 0 | 0 |
| stg | fact_vendas | data data: valor convertido = texto original | 0 | 0 |
| stg | fact_vendas | soma de preco_unitario: raw = stg | 73969592.2800 | 73969592.2800 |
| stg | fact_vendas | soma de desconto_pct: raw = stg | 3458.1300 | 3458.1300 |
| stg | fact_vendas | soma de receita_bruta: raw = stg | 170993819.9400 | 170993819.9400 |
| stg | fact_vendas | soma de desconto_valor: raw = stg | 10637755.3400 | 10637755.3400 |
| stg | fact_vendas | soma de impostos_valor: raw = stg | 23850710.2100 | 23850710.2100 |
| stg | fact_vendas | soma de receita_liquida: raw = stg | 136505354.3900 | 136505354.3900 |
| stg | fact_vendas | soma de custo_total: raw = stg | 80501050.3100 | 80501050.3100 |
| stg | fact_vendas | domínio de status ∈ ('Entregue', 'Devolvido') | 0 | 0 |
| stg | fact_vendas | integridade referencial id_cliente -> dim_cliente.id_cliente | 0 | 0 |
| stg | fact_vendas | integridade referencial id_produto -> dim_produto.id_produto | 0 | 0 |
| stg | fact_vendas | integridade referencial id_filial -> dim_filial.id_filial | 0 | 0 |
| stg | fact_vendas | integridade referencial id_vendedor -> dim_vendedor.id_vendedor | 0 | 0 |
| stg | fact_vendas | integridade referencial id_canal -> dim_canal.id_canal | 0 | 0 |
| stg | fact_vendas | integridade referencial data -> dim_calendario.data | 0 | 0 |
| stg | fact_despesas | integridade referencial id_departamento -> dim_departamento.id_departamento | 0 | 0 |
| stg | fact_despesas | integridade referencial id_categoria_despesa -> dim_categoria_despesa.id_categoria_despesa | 0 | 0 |
| stg | fact_despesas | integridade referencial id_filial -> dim_filial.id_filial | 0 | 0 |
| stg | fact_despesas | integridade referencial data -> dim_calendario.data | 0 | 0 |
| stg | fact_orcamento | integridade referencial id_departamento -> dim_departamento.id_departamento | 0 | 0 |
| stg | fact_orcamento | integridade referencial id_categoria_despesa -> dim_categoria_despesa.id_categoria_despesa | 0 | 0 |
| stg | fact_orcamento | integridade referencial id_filial -> dim_filial.id_filial | 0 | 0 |
| stg | fact_orcamento | integridade referencial mes -> dim_calendario.data | 0 | 0 |
| stg | fact_metas_vendas | integridade referencial id_filial -> dim_filial.id_filial | 0 | 0 |
| stg | fact_metas_vendas | integridade referencial mes -> dim_calendario.data | 0 | 0 |
| stg | fact_rh_mensal | integridade referencial id_departamento -> dim_departamento.id_departamento | 0 | 0 |
| stg | fact_rh_mensal | integridade referencial id_filial -> dim_filial.id_filial | 0 | 0 |
| stg | fact_rh_mensal | integridade referencial data_referencia -> dim_calendario.data | 0 | 0 |
| stg | dim_produto | margem_lista_pct entre 0 e 1 | 0 | 0 |
| stg | dim_produto | aliquota_imposto entre 0 e 1 | 0 | 0 |
| stg | fact_vendas | desconto_pct entre 0 e 1 | 0 | 0 |
| stg | fact_metas_vendas | meta_margem_bruta_pct entre 0 e 1 | 0 | 0 |
| stg | fact_vendas | quantidade, preço, receita e custo > 0 | 0 | 0 |
| stg | fact_despesas | valor da despesa > 0 | 0 | 0 |
| stg | fact_vendas | receita_bruta = quantidade x preço (±R$ 0.02) | 0 | 0 |
| stg | fact_vendas | desconto_valor = bruta x desconto_pct (±R$ 0.02) | 0 | 0 |
| stg | fact_vendas | líquida = bruta − desconto − impostos (±R$ 0.02) | 0 | 0 |
| mart | dim_calendario | registros mart = stg | 1096 | 1096 |
| mart | dim_canal | registros mart = stg | 4 | 4 |
| mart | dim_categoria_despesa | registros mart = stg | 18 | 18 |
| mart | dim_cliente | registros mart = stg | 650 | 650 |
| mart | dim_departamento | registros mart = stg | 8 | 8 |
| mart | dim_filial | registros mart = stg | 8 | 8 |
| mart | dim_produto | registros mart = stg | 39 | 39 |
| mart | dim_vendedor | registros mart = stg | 24 | 24 |
| mart | fact_despesas | registros mart = stg | 7075 | 7075 |
| mart | fact_metas_vendas | registros mart = stg | 270 | 270 |
| mart | fact_orcamento | registros mart = stg | 6005 | 6005 |
| mart | fact_rh_mensal | registros mart = stg | 909 | 909 |
| mart | fact_vendas | registros mart = stg | 59365 | 59365 |
| mart | fact_vendas | soma de receita_bruta: stg = mart | 170993819.94 | 170993819.94 |
| mart | fact_vendas | soma de desconto_valor: stg = mart | 10637755.34 | 10637755.34 |
| mart | fact_vendas | soma de impostos_valor: stg = mart | 23850710.21 | 23850710.21 |
| mart | fact_vendas | soma de receita_liquida: stg = mart | 136505354.39 | 136505354.39 |
| mart | fact_vendas | soma de custo_total: stg = mart | 80501050.31 | 80501050.31 |
| mart | fact_vendas | entregue + devolvida = receita líquida total | 136505354.39 | 136505354.39 |
| mart | fact_vendas | custo entregue + devolvido = custo total | 80501050.31 | 80501050.31 |
| mart | fact_vendas | devoluções preservadas (linhas com eh_devolvida) | 1310 | 1310 |
| mart | fact_vendas | devoluções NÃO foram transformadas em valor negativo | 0 | 0 |
| mart | fact_vendas | margens negativas preservadas (linhas sinalizadas) | 612 | 612 |
| mart | fact_vendas | preço praticado preservado (sem alteração) | 0 | 0 |
| mart | periodo_realizado | último mês realizado coerente com dim_calendario | True | True |
| mart | orcado_vs_realizado_mensal | nenhuma linha em meses sem realizado | 0 | 0 |
| mart | orcado_vs_realizado_acumulado | nenhuma linha em meses sem realizado | 0 | 0 |
| mart | meta_vs_realizado_mensal | nenhuma linha em meses sem realizado | 0 | 0 |
| mart | orcado_vs_realizado_mensal | Σ orçado = Σ orçamento até o último mês realizado | 45508644.46 | 45508644.46 |
| mart | orcado_vs_realizado_mensal | Σ realizado = Σ despesas até o último mês realizado | 45712808.06 | 45712808.06 |
| mart | kpi_vendas_mes | Σ vendas entregues + devoluções = Σ receita líquida registrada | 136505354.39 | 136505354.39 |
| mart | kpi_devolucoes_reconciliacao | registrada − entregues − devoluções = 0 (receita) e custo idem | 0 | 0 |
| mart | kpi_devolucoes_pedido | pedidos classificados (sem/parcial/total) = pedidos distintos | 33209 | 33209 |
| mart | ref_premissas_negocio | premissas de devolução PN-DEV-01..04 registradas | 4 | 4 |
| mart | fact_vendas | rastreabilidade: linha_csv_origem preenchida e única | 0 | 0 |
