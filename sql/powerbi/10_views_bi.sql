-- =====================================================================================================
-- CAMADA DE CONSUMO DO POWER BI (schema `bi`) — Etapa 4
-- Contrato estável: nomes e ordem das colunas estão em src/empresax/powerbi.py (CONTRATO) e são testados.
-- Regras: só colunas necessárias; flags como 0/1; valores monetários em DECIMAL; datas de mês = 1º dia do mês.
-- Receita principal = receita_ajustada (PROVISÓRIA, PN-DEV-01). receita_registrada = entregues + devoluções.
-- Não altera nenhuma tabela do mart; só cria views.
-- =====================================================================================================
CREATE SCHEMA IF NOT EXISTS bi;

CREATE OR REPLACE VIEW bi.dim_calendario AS
SELECT data, ano, semestre, trimestre, mes_num, mes_abrev, ano_mes, primeiro_dia_mes, ordem_ano_mes, dia_util, realizado
FROM mart.dim_calendario;

CREATE OR REPLACE VIEW bi.dim_produto AS
SELECT id_produto, sku, produto, categoria, subcategoria, preco_lista, aliquota_imposto FROM mart.dim_produto;

CREATE OR REPLACE VIEW bi.dim_filial AS
SELECT id_filial, filial, cidade, uf, regiao, tipo, (tipo = 'Matriz')::INTEGER AS concentra_despesas_corporativas FROM mart.dim_filial;

CREATE OR REPLACE VIEW bi.dim_canal AS SELECT id_canal, canal, tipo_canal FROM mart.dim_canal;

CREATE OR REPLACE VIEW bi.dim_departamento AS SELECT id_departamento, departamento, centro_custo, tipo_area FROM mart.dim_departamento;

CREATE OR REPLACE VIEW bi.dim_categoria_despesa AS
SELECT id_categoria_despesa, categoria_despesa, grupo_dre, tipo_custo, ordem_dre FROM mart.dim_categoria_despesa;

CREATE OR REPLACE VIEW bi.dim_cliente AS SELECT id_cliente, nome_cliente, segmento, cidade, uf, regiao FROM mart.dim_cliente;

-- Grão: 1 linha = 1 item de pedido (59.365 linhas). Base de todas as medidas de vendas.
CREATE OR REPLACE VIEW bi.fato_vendas AS
SELECT id_venda, id_pedido, data, mes, id_cliente, id_produto, id_filial, id_vendedor, id_canal, status,
       quantidade, preco_unitario, desconto_pct, receita_bruta, desconto_valor, impostos_valor,
       receita_liquida                                   AS receita_registrada,
       receita_liquida_entregue                          AS receita_ajustada,
       receita_liquida_devolvida                         AS devolucao,
       custo_total                                       AS custo_registrado,
       custo_entregue                                    AS custo_ajustado,
       receita_liquida_entregue - custo_entregue         AS lucro_bruto_ajustado,
       CASE WHEN eh_devolvida THEN 0 ELSE quantidade END AS unidades_entregues,
       flag_margem_negativa::INTEGER                     AS flag_margem_negativa,
       eh_devolvida::INTEGER                             AS flag_devolvida,
       linha_csv_origem
FROM mart.fact_vendas;

-- Grão: 1 linha = 1 lançamento de despesa. Sem vínculo com produto/canal/cliente.
CREATE OR REPLACE VIEW bi.fato_despesas AS
SELECT id_despesa, data, mes, id_departamento, id_categoria_despesa, id_filial, fornecedor, valor FROM mart.fact_despesas;

-- Grão: mês × departamento × categoria × filial. INCLUI meses futuros (base do orçamento ANUAL).
CREATE OR REPLACE VIEW bi.fato_orcamento AS
SELECT o.mes, o.id_departamento, o.id_categoria_despesa, o.id_filial, o.valor_orcado,
       (o.mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado))::INTEGER AS mes_realizado
FROM mart.fact_orcamento o;

-- Grão: mês × departamento × categoria × filial, só meses realizados: orçado e realizado lado a lado.
CREATE OR REPLACE VIEW bi.fato_orcado_realizado_mes AS
SELECT mes, id_departamento, id_categoria_despesa, id_filial, orcado, realizado,
       sem_orcamento::INTEGER AS flag_sem_orcamento, sem_lancamento_no_mes::INTEGER AS flag_sem_lancamento
FROM mart.orcado_vs_realizado_mensal;

-- Grão: 1 linha por mês realizado (empresa). Valores de REFERÊNCIA para conferir as medidas DAX.
CREATE OR REPLACE VIEW bi.kpi_empresa_mes AS
WITH v AS (SELECT mes, sum(receita_liquida) AS receita_registrada, sum(receita_liquida_entregue) AS vendas_entregues,
                  sum(receita_liquida_devolvida) AS devolucoes, sum(custo_entregue) AS custo_ajustado,
                  count(DISTINCT id_pedido) AS pedidos, sum(quantidade) AS unidades FROM mart.fact_vendas GROUP BY mes),
d AS (SELECT mes, sum(valor) AS despesas FROM mart.fact_despesas GROUP BY mes)
SELECT c.primeiro_dia_mes AS mes,
       v.receita_registrada, v.vendas_entregues, v.devolucoes, v.vendas_entregues AS receita_ajustada, v.custo_ajustado,
       v.vendas_entregues - v.custo_ajustado AS lucro_bruto_ajustado,
       coalesce(d.despesas, 0) AS despesas,
       v.vendas_entregues - v.custo_ajustado - coalesce(d.despesas, 0) AS resultado_operacional_estimado,
       (v.vendas_entregues - v.custo_ajustado)::DOUBLE / nullif(v.vendas_entregues, 0) AS margem_bruta_pct,
       (v.vendas_entregues - v.custo_ajustado - coalesce(d.despesas, 0))::DOUBLE / nullif(v.vendas_entregues, 0) AS margem_operacional_estimada_pct,
       v.pedidos, v.unidades
FROM (SELECT DISTINCT primeiro_dia_mes FROM mart.dim_calendario
      WHERE primeiro_dia_mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)) c
LEFT JOIN v ON v.mes = c.primeiro_dia_mes LEFT JOIN d ON d.mes = c.primeiro_dia_mes
ORDER BY 1;
