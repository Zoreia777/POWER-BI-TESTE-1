-- KPIs DE VENDAS POR MÊS DA VENDA — métricas SEPARADAS e reconciliáveis (premissas PN-DEV-01..04):
--   receita_liquida_registrada : TODAS as linhas (Entregue + Devolvido), valores originais
--   vendas_entregues           : receita líquida das linhas com status 'Entregue'
--   devolucoes                 : receita líquida das linhas 'Devolvido' (positiva, como no dado original)
--   registrada = vendas_entregues + devolucoes  (reconciliação exata)
-- receita_reconhecida_provisoria (= vendas_entregues) é o indicador AJUSTADO do cenário simulado: aplica a premissa
-- "devolução integral cancela a receita da venda" (PN-DEV-01). NÃO é receita contábil oficialmente reconhecida.
-- BASE TEMPORAL: tudo é agrupado pelo MÊS DA VENDA ORIGINAL. Não existe data de devolução; nenhum estorno é
-- atribuído a período específico (PN-DEV-03). 'devolucoes' de um mês = vendas daquele mês marcadas como devolvidas.
-- Custo: premissa PN-DEV-02 (HIPÓTESE do cenário, não comprovada): o produto devolvido volta ao estoque e o custo é
-- recuperável; por isso o custo ajustado exclui custo_devolvido. A coluna lucro_bruto_se_custo_nao_recuperado mostra
-- o efeito se a hipótese fosse falsa.
-- taxa_devolucao_valor_pct = devolucoes / receita registrada (razão de somas, nunca média de percentuais).
CREATE OR REPLACE TABLE mart.kpi_vendas_mes AS
SELECT
    mes,
    count(*)                                              AS linhas,
    count(DISTINCT id_pedido)                             AS pedidos,
    sum(quantidade)                                       AS unidades,
    sum(receita_bruta)                                    AS receita_bruta_registrada,
    sum(desconto_valor)                                   AS desconto_total,
    sum(impostos_valor)                                   AS impostos_total,
    sum(receita_liquida)                                  AS receita_liquida_registrada,
    sum(receita_liquida_entregue)                         AS vendas_entregues,
    sum(receita_liquida_devolvida)                        AS devolucoes,
    count(*) FILTER (WHERE eh_devolvida)                  AS linhas_devolvidas,
    (sum(receita_liquida_devolvida) / sum(receita_liquida))::DECIMAL(12,6) AS taxa_devolucao_valor_pct,
    sum(receita_liquida_entregue)                         AS receita_reconhecida_provisoria,
    sum(custo_total)                                      AS custo_total_registrado,
    sum(custo_devolvido)                                  AS custo_devolvido_hipotese_recuperavel,
    sum(custo_entregue)                                   AS custo_reconhecido_provisorio,
    (sum(receita_liquida_entregue) - sum(custo_entregue)) AS lucro_bruto_provisorio,
    ((sum(receita_liquida_entregue) - sum(custo_entregue)) / nullif(sum(receita_liquida_entregue), 0))::DECIMAL(12,6) AS margem_bruta_provisoria_pct,
    (sum(receita_liquida_entregue) - sum(custo_total))    AS lucro_bruto_se_custo_nao_recuperado,
    count(*) FILTER (WHERE flag_margem_negativa)          AS linhas_margem_negativa,
    sum(custo_total - receita_liquida) FILTER (WHERE flag_margem_negativa) AS prejuizo_bruto_linhas_negativas,
    '{POLITICA}'                                          AS politica_devolucao,
    'PN-DEV-01;PN-DEV-02;PN-DEV-03;PN-DEV-04'             AS premissas_aplicadas,
    'mes da venda original (sem data de devolucao)'       AS base_temporal_devolucao
FROM mart.fact_vendas
GROUP BY mes
ORDER BY mes;
