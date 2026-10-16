-- =====================================================================================================
-- ANÁLISE 04 · DESPESAS POR FILIAL
-- Pergunta: quais filiais apresentam maiores despesas?
-- Despesas = lançamentos de mart.fact_despesas no período realizado (não incluem o custo das mercadorias).
-- CUIDADO DE LEITURA: a Matriz (São Paulo) concentra as despesas corporativas; por isso o valor absoluto e a razão
--   despesa/receita NÃO são medida de eficiência isolada. A coluna nota_leitura destaca a Matriz. Comparar filiais entre si
--   (tipo = 'Filial') é mais justo que comparar a Matriz com elas.
-- Relação despesa/receita = despesas / receita ajustada (PN-DEV-01) da mesma unidade e período (razão de somas).
-- Técnicas: JOIN em 3 tabelas, GROUP BY, window SUM() OVER (participação), RANK, CASE.
-- =====================================================================================================

-- @@ 04a_despesas_por_filial
WITH d AS (SELECT id_filial, sum(valor) AS despesas FROM mart.fact_despesas
           WHERE mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado) GROUP BY id_filial),
r AS (SELECT id_filial, sum(receita_liquida_entregue) AS receita_ajustada FROM mart.fact_vendas GROUP BY id_filial)
SELECT rank() OVER (ORDER BY d.despesas DESC, f.id_filial) AS ranking_despesas,
       f.id_filial, f.filial, f.tipo,
       d.despesas,
       d.despesas::DOUBLE / sum(d.despesas) OVER ()           AS participacao_nas_despesas_pct,
       r.receita_ajustada,
       d.despesas::DOUBLE / nullif(r.receita_ajustada, 0)     AS despesas_sobre_receita_ajustada_pct,
       CASE WHEN f.tipo = 'Matriz' THEN 'Matriz concentra despesas corporativas: nao usar a razao despesa/receita como medida de eficiencia isolada'
            ELSE '' END AS nota_leitura
FROM mart.dim_filial f JOIN d USING (id_filial) LEFT JOIN r USING (id_filial)
ORDER BY ranking_despesas;

-- @@ 04b_despesas_filial_por_grupo
WITH d AS (
    SELECT f.id_filial, f.filial, f.tipo, g.grupo_dre, sum(x.valor) AS despesas
    FROM mart.fact_despesas x
    JOIN mart.dim_filial f USING (id_filial)
    JOIN mart.dim_categoria_despesa g USING (id_categoria_despesa)
    WHERE x.mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)
    GROUP BY f.id_filial, f.filial, f.tipo, g.grupo_dre),
r AS (SELECT id_filial, sum(receita_liquida_entregue) AS receita_ajustada FROM mart.fact_vendas GROUP BY id_filial)
SELECT d.id_filial, d.filial, d.tipo, d.grupo_dre, d.despesas,
       d.despesas::DOUBLE / sum(d.despesas) OVER (PARTITION BY d.id_filial) AS participacao_na_filial_pct,
       d.despesas::DOUBLE / sum(d.despesas) OVER ()                         AS participacao_no_total_pct,
       d.despesas::DOUBLE / nullif(r.receita_ajustada, 0)                   AS grupo_sobre_receita_ajustada_pct
FROM d LEFT JOIN r USING (id_filial)
ORDER BY d.id_filial, d.grupo_dre;
