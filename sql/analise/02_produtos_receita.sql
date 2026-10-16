-- =====================================================================================================
-- ANÁLISE 02 · PRODUTOS COM MAIOR RECEITA
-- Pergunta: quais produtos têm maior receita?
-- Métrica: receita ajustada provisória (PN-DEV-01), com registrada e devoluções ao lado. Período: todo o realizado.
-- Curva ABC: a classe usa a participação acumulada ANTES de incluir o próprio produto (A < 80%, B < 95%, C resto);
--   assim o produto que cruza a linha dos 80% ainda é A. Desempate do ranking: id_produto (resultado determinístico).
-- Técnicas: JOIN, GROUP BY, window SUM() OVER, ROW_NUMBER, CASE.
-- =====================================================================================================

-- @@ 02a_ranking_produtos_receita
WITH p AS (
    SELECT d.id_produto, d.produto, d.categoria,
           coalesce(sum(f.receita_liquida_entregue), 0)  AS receita_ajustada,
           coalesce(sum(f.receita_liquida), 0)           AS receita_registrada,
           coalesce(sum(f.receita_liquida_devolvida), 0) AS devolucoes
    FROM mart.dim_produto d LEFT JOIN mart.fact_vendas f USING (id_produto)   -- LEFT: produto sem venda também aparece
    GROUP BY d.id_produto, d.produto, d.categoria),
r AS (SELECT *, receita_ajustada::DOUBLE / sum(receita_ajustada) OVER () AS participacao_pct FROM p),
a AS (SELECT *, sum(participacao_pct) OVER (ORDER BY receita_ajustada DESC, id_produto) AS participacao_acumulada_pct FROM r)
SELECT row_number() OVER (ORDER BY receita_ajustada DESC, id_produto) AS ranking,
       id_produto, produto, categoria,
       receita_ajustada, receita_registrada, devolucoes,
       participacao_pct, participacao_acumulada_pct,
       CASE WHEN participacao_acumulada_pct - participacao_pct < 0.80 THEN 'A'
            WHEN participacao_acumulada_pct - participacao_pct < 0.95 THEN 'B' ELSE 'C' END AS classe_abc,
       'receita_ajustada_provisoria (PN-DEV-01/03)' AS indicador_principal
FROM a ORDER BY ranking;

-- @@ 02b_receita_por_categoria
SELECT d.categoria,
       count(DISTINCT d.id_produto)                         AS produtos,
       sum(f.receita_liquida_entregue)                      AS receita_ajustada,
       sum(f.receita_liquida)                               AS receita_registrada,
       sum(f.receita_liquida_devolvida)                     AS devolucoes,
       sum(f.receita_liquida_entregue)::DOUBLE / sum(sum(f.receita_liquida_entregue)) OVER () AS participacao_pct
FROM mart.fact_vendas f JOIN mart.dim_produto d USING (id_produto)
GROUP BY d.categoria ORDER BY receita_ajustada DESC, d.categoria;
