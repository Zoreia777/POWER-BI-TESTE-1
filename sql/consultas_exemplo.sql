-- =====================================================================
-- EMPRESA X · Consultas de exemplo (rode no SQLite: sqlite3 database/empresa_x.db)
-- =====================================================================

-- 1) Receita líquida, lucro bruto e margem por ano
SELECT substr(data, 1, 4) AS ano,
       ROUND(SUM(receita_liquida) / 1e6, 2)                          AS receita_mi,
       ROUND(SUM(receita_liquida - custo_total) / 1e6, 2)            AS lucro_bruto_mi,
       ROUND(1 - SUM(custo_total) / SUM(receita_liquida), 3)         AS margem_bruta
FROM fact_vendas
WHERE status = 'Entregue'
GROUP BY 1;

-- 2) Ranking de filiais por receita no último trimestre realizado
SELECT f.filial, ROUND(SUM(v.receita_liquida), 0) AS receita
FROM fact_vendas v JOIN dim_filial f USING (id_filial)
WHERE v.status = 'Entregue' AND v.data BETWEEN '2026-07-01' AND '2026-09-30'
GROUP BY 1 ORDER BY receita DESC;

-- 3) Quem mais estourou o orçamento em 2026 (categoria × departamento)
SELECT departamento, categoria_despesa,
       ROUND(SUM(orcado), 0) AS orcado, ROUND(SUM(realizado), 0) AS realizado,
       ROUND(SUM(realizado) / SUM(orcado) - 1, 3) AS estouro_pct
FROM vw_orcado_vs_realizado
WHERE ano_mes BETWEEN '2026-01' AND '2026-09'
GROUP BY 1, 2
HAVING SUM(orcado) > 0
ORDER BY estouro_pct DESC
LIMIT 10;

-- 4) Produtos com margem baixa (< 10%) e volume relevante
SELECT produto, categoria,
       ROUND(SUM(receita_liquida), 0)                      AS receita,
       ROUND(1 - SUM(cmv) / SUM(receita_liquida), 3)       AS margem_bruta
FROM vw_vendas_detalhada
WHERE status = 'Entregue'
GROUP BY 1, 2
HAVING margem_bruta < 0.10
ORDER BY receita DESC;

-- 5) Evolução da participação dos canais por trimestre
SELECT substr(data, 1, 4) || '-T' || ((CAST(substr(data, 6, 2) AS INTEGER) - 1) / 3 + 1) AS trimestre,
       canal,
       ROUND(100.0 * SUM(receita_liquida) /
             SUM(SUM(receita_liquida)) OVER (PARTITION BY substr(data, 1, 4) || ((CAST(substr(data, 6, 2) AS INTEGER) - 1) / 3)), 1) AS pct_receita
FROM vw_vendas_detalhada
WHERE status = 'Entregue'
GROUP BY 1, 2
ORDER BY 1, 2;

-- 6) DRE mensal completo
SELECT * FROM vw_dre_mensal ORDER BY ano_mes;

-- 7) Taxa de devolução por produto
SELECT produto,
       ROUND(100.0 * SUM(CASE WHEN status = 'Devolvido' THEN receita_bruta ELSE 0 END) / SUM(receita_bruta), 1) AS devolucao_pct
FROM vw_vendas_detalhada
GROUP BY 1 ORDER BY devolucao_pct DESC LIMIT 5;
