-- =====================================================================================================
-- ANÁLISE 03 · PRODUTOS COM MENOR MARGEM
-- Pergunta: quais produtos apresentam menor margem?
-- Margem bruta ajustada = (receita ajustada − custo ajustado) / receita ajustada, onde custo ajustado exclui o custo das
--   devoluções (hipótese PN-DEV-02, NÃO comprovada). Sensibilidade ao lado: margem se o custo devolvido NÃO fosse recuperado.
-- FILTRO EXPLÍCITO: só entram produtos com >= {PISO_LINHAS} linhas ENTREGUES (piso em config.py; 0 = todos). A coluna
--   filtro_aplicado repete o critério em cada linha e 03b informa quantos produtos ficaram de fora.
-- Linhas de margem negativa (custo > receita líquida) são contadas sobre TODAS as linhas do produto (PN-MRG-01).
-- Técnicas: LEFT JOIN, FILTER, CTE, NULLIF (denominador zero), RANK com NULLS LAST.
-- =====================================================================================================

-- @@ 03a_margem_por_produto
WITH p AS (
    SELECT d.id_produto, d.produto, d.categoria,
           count(f.id_venda)                                      AS linhas_total,
           count(f.id_venda) FILTER (WHERE NOT f.eh_devolvida)    AS linhas_entregues,
           count(f.id_venda) FILTER (WHERE f.flag_margem_negativa) AS linhas_margem_negativa,
           coalesce(sum(f.receita_liquida_entregue), 0)           AS receita_ajustada,
           coalesce(sum(f.custo_entregue), 0)                     AS custo_ajustado,
           coalesce(sum(f.custo_total), 0)                        AS custo_total_registrado
    FROM mart.dim_produto d LEFT JOIN mart.fact_vendas f USING (id_produto)
    GROUP BY d.id_produto, d.produto, d.categoria),
m AS (
    SELECT *, receita_ajustada - custo_ajustado AS lucro_bruto_ajustado,
           (receita_ajustada - custo_ajustado)::DOUBLE / nullif(receita_ajustada, 0)        AS margem_bruta_ajustada_pct,
           (receita_ajustada - custo_total_registrado)::DOUBLE / nullif(receita_ajustada, 0) AS margem_se_custo_nao_recuperado_pct,
           linhas_margem_negativa::DOUBLE / nullif(linhas_total, 0)                         AS pct_linhas_margem_negativa
    FROM p WHERE linhas_entregues >= {PISO_LINHAS})
SELECT rank() OVER (ORDER BY margem_bruta_ajustada_pct ASC NULLS LAST, id_produto) AS ranking_menor_margem,
       id_produto, produto, categoria, linhas_entregues, receita_ajustada, custo_ajustado, lucro_bruto_ajustado,
       margem_bruta_ajustada_pct, margem_se_custo_nao_recuperado_pct, linhas_margem_negativa, pct_linhas_margem_negativa,
       CASE WHEN {PISO_LINHAS} = 0 THEN 'sem piso: todos os produtos'
            ELSE 'piso: produtos com >= {PISO_LINHAS} linhas entregues' END AS filtro_aplicado
FROM m ORDER BY ranking_menor_margem;

-- @@ 03b_filtro_piso_resumo
WITH p AS (SELECT d.id_produto, count(f.id_venda) FILTER (WHERE NOT f.eh_devolvida) AS linhas_entregues
           FROM mart.dim_produto d LEFT JOIN mart.fact_vendas f USING (id_produto) GROUP BY d.id_produto)
SELECT {PISO_LINHAS} AS piso_linhas_entregues,
       count(*)                                          AS produtos_no_cadastro,
       count(*) FILTER (WHERE linhas_entregues >= {PISO_LINHAS}) AS produtos_incluidos,
       count(*) FILTER (WHERE linhas_entregues <  {PISO_LINHAS}) AS produtos_excluidos_pelo_piso,
       min(linhas_entregues)                             AS menor_volume_entre_produtos
FROM p;
