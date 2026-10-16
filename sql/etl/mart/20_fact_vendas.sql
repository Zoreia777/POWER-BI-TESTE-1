-- FATO DE VENDAS (grão: 1 linha = 1 item de pedido; 59.365 linhas, nenhuma removida)
--
-- Colunas originais preservadas SEM alteração (preço, custo, desconto, status).
-- Colunas derivadas:
--  * Devoluções  : eh_devolvida e a divisão da receita/custo em *_entregue / *_devolvido.
--                  A receita das devolvidas continua POSITIVA (valores originais preservados; sem estorno inventado).
--                  Premissas PN-DEV-01..04 (mart.ref_premissas_negocio).
--  * Margem      : lucro_bruto_linha, margem_bruta_pct_linha, flag_margem_negativa
--                  (custo_total > receita_liquida). Não altera custo nem preço.
--  * Preço       : preco_lista (dim_produto), variacao_preco_vs_lista_pct, efeito_preco_valor.
--                  receita_bruta já está a PREÇO PRATICADO; desconto_valor é uma coluna separada.
--                  Variação de preço (reajuste sobre a lista) NÃO é desconto.
CREATE OR REPLACE TABLE mart.fact_vendas AS
SELECT
    v.* EXCLUDE (_linha_origem),
    v._linha_origem                                                          AS linha_csv_origem,  -- rastreia o registro até data/fact_vendas.csv (cabeçalho = linha 1)
    date_trunc('month', v.data)::DATE                                        AS mes,
    (v.status = 'Devolvido')                                                 AS eh_devolvida,
    CASE WHEN v.status = 'Entregue'  THEN v.receita_liquida ELSE 0 END::DECIMAL(14,2) AS receita_liquida_entregue,
    CASE WHEN v.status = 'Devolvido' THEN v.receita_liquida ELSE 0 END::DECIMAL(14,2) AS receita_liquida_devolvida,
    CASE WHEN v.status = 'Entregue'  THEN v.custo_total     ELSE 0 END::DECIMAL(14,2) AS custo_entregue,
    CASE WHEN v.status = 'Devolvido' THEN v.custo_total     ELSE 0 END::DECIMAL(14,2) AS custo_devolvido,
    (v.receita_liquida - v.custo_total)::DECIMAL(14,2)                       AS lucro_bruto_linha,
    ((v.receita_liquida - v.custo_total) / v.receita_liquida)::DECIMAL(12,6) AS margem_bruta_pct_linha,
    (v.custo_total > v.receita_liquida)                                      AS flag_margem_negativa,
    p.preco_lista,
    (v.preco_unitario / p.preco_lista - 1)::DECIMAL(12,6)                    AS variacao_preco_vs_lista_pct,
    (v.quantidade * p.preco_lista)::DECIMAL(18,2)                            AS valor_a_preco_lista,
    (v.receita_bruta - v.quantidade * p.preco_lista)::DECIMAL(18,2)          AS efeito_preco_valor
FROM stg.fact_vendas v
LEFT JOIN stg.dim_produto p USING (id_produto)
ORDER BY v.id_venda;
