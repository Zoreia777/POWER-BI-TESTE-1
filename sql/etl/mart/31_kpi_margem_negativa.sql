-- MARGEM NEGATIVA: onde (produto, filial, mês, pedido) o custo supera a receita líquida.
-- Linha com margem negativa = custo_total > receita_liquida (flag_margem_negativa). As linhas
-- são PRESERVADAS; aqui só medimos. Inclui linhas Entregue e Devolvido (colunas separadas).
CREATE OR REPLACE TABLE mart.kpi_margem_negativa_produto AS
SELECT p.id_produto, p.produto, p.categoria,
       count(*)                                               AS linhas,
       count(*) FILTER (WHERE f.flag_margem_negativa)         AS linhas_margem_negativa,
       (count(*) FILTER (WHERE f.flag_margem_negativa))::DECIMAL(18,6) / count(*) AS pct_linhas_margem_negativa,
       coalesce(sum(f.custo_total - f.receita_liquida) FILTER (WHERE f.flag_margem_negativa), 0) AS prejuizo_bruto,
       count(*) FILTER (WHERE f.flag_margem_negativa AND f.eh_devolvida) AS linhas_negativas_devolvidas
FROM mart.fact_vendas f JOIN mart.dim_produto p USING (id_produto)
GROUP BY ALL ORDER BY linhas_margem_negativa DESC, p.id_produto;

CREATE OR REPLACE TABLE mart.kpi_margem_negativa_filial AS
SELECT d.id_filial, d.filial,
       count(*)                                               AS linhas,
       count(*) FILTER (WHERE f.flag_margem_negativa)         AS linhas_margem_negativa,
       (count(*) FILTER (WHERE f.flag_margem_negativa))::DECIMAL(18,6) / count(*) AS pct_linhas_margem_negativa,
       coalesce(sum(f.custo_total - f.receita_liquida) FILTER (WHERE f.flag_margem_negativa), 0) AS prejuizo_bruto
FROM mart.fact_vendas f JOIN mart.dim_filial d USING (id_filial)
GROUP BY ALL ORDER BY d.id_filial;

CREATE OR REPLACE TABLE mart.kpi_margem_negativa_mes AS
SELECT mes,
       count(*)                                               AS linhas,
       count(*) FILTER (WHERE flag_margem_negativa)           AS linhas_margem_negativa,
       (count(*) FILTER (WHERE flag_margem_negativa))::DECIMAL(18,6) / count(*) AS pct_linhas_margem_negativa,
       coalesce(sum(custo_total - receita_liquida) FILTER (WHERE flag_margem_negativa), 0) AS prejuizo_bruto
FROM mart.fact_vendas GROUP BY mes ORDER BY mes;

-- Pedidos com pelo menos uma linha de margem negativa. `pedido_margem_negativa` indica se o
-- PEDIDO como um todo (soma das linhas) também ficou no prejuízo.
CREATE OR REPLACE TABLE mart.kpi_margem_negativa_pedido AS
SELECT id_pedido, min(data) AS data, min(id_filial) AS id_filial,
       count(*)                                         AS linhas_pedido,
       count(*) FILTER (WHERE flag_margem_negativa)     AS linhas_margem_negativa,
       sum(receita_liquida)                             AS receita_liquida_pedido,
       sum(custo_total)                                 AS custo_pedido,
       sum(lucro_bruto_linha)                           AS lucro_bruto_pedido,
       (sum(lucro_bruto_linha) < 0)                     AS pedido_margem_negativa
FROM mart.fact_vendas
GROUP BY id_pedido HAVING count(*) FILTER (WHERE flag_margem_negativa) > 0
ORDER BY id_pedido;
