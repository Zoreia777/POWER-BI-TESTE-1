-- =====================================================================================================
-- ANÁLISE 05 · EVOLUÇÃO DA LUCRATIVIDADE
-- Pergunta: como evolui a lucratividade?
-- RESULTADO OPERACIONAL ESTIMADO DO DATASET = lucro bruto ajustado − despesas realizadas.
--   NÃO é lucro líquido contábil: não há IR/CSLL, depreciação, resultado financeiro separado nem ajustes contábeis.
--   Lucro bruto ajustado = receita ajustada (PN-DEV-01) − custo ajustado (PN-DEV-02, hipótese). A coluna
--   resultado_se_custo_nao_recuperado mostra o resultado se a hipótese do custo falhar.
-- A média móvel de 3 meses é uma RAZÃO DE SOMAS (Σ resultado / Σ receita), nunca média de percentuais, e só existe com 3 meses completos.
-- Técnicas: CTE, LEFT JOIN com calendário, window SUM() OVER com ROWS BETWEEN, PARTITION BY ano (acumulado), NULLIF.
-- =====================================================================================================

-- @@ 05a_resultado_operacional_mensal
WITH meses AS (SELECT DISTINCT primeiro_dia_mes AS mes FROM mart.dim_calendario
               WHERE primeiro_dia_mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)),
v AS (SELECT mes, sum(receita_liquida_entregue) AS receita_ajustada, sum(custo_entregue) AS custo_ajustado, sum(custo_total) AS custo_total_registrado
      FROM mart.fact_vendas GROUP BY mes),
d AS (SELECT mes, sum(valor) AS despesas FROM mart.fact_despesas GROUP BY mes),
m AS (SELECT meses.mes, coalesce(v.receita_ajustada, 0) AS receita_ajustada, coalesce(v.custo_ajustado, 0) AS custo_ajustado,
             coalesce(v.custo_total_registrado, 0) AS custo_total_registrado, coalesce(d.despesas, 0) AS despesas
      FROM meses LEFT JOIN v USING (mes) LEFT JOIN d USING (mes)),
x AS (SELECT *, receita_ajustada - custo_ajustado AS lucro_bruto_ajustado,
             receita_ajustada - custo_ajustado - despesas AS resultado_operacional_estimado,
             receita_ajustada - custo_total_registrado - despesas AS resultado_se_custo_nao_recuperado
      FROM m)
SELECT mes, receita_ajustada, custo_ajustado, lucro_bruto_ajustado, despesas, resultado_operacional_estimado,
       lucro_bruto_ajustado::DOUBLE / nullif(receita_ajustada, 0)           AS margem_bruta_ajustada_pct,
       resultado_operacional_estimado::DOUBLE / nullif(receita_ajustada, 0) AS margem_operacional_estimada_pct,
       CASE WHEN count(*) OVER w3 = 3
            THEN sum(resultado_operacional_estimado) OVER w3::DOUBLE / nullif(sum(receita_ajustada) OVER w3, 0) END AS margem_operacional_media_movel_3m_pct,
       sum(resultado_operacional_estimado) OVER (PARTITION BY year(mes) ORDER BY mes) AS resultado_acumulado_no_ano,
       resultado_se_custo_nao_recuperado,
       'resultado operacional ESTIMADO do dataset (lucro bruto ajustado - despesas); nao e lucro liquido contabil' AS rotulo
FROM x WINDOW w3 AS (ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
ORDER BY mes;

-- @@ 05b_resultado_anual_ytd
WITH corte AS (SELECT month(ultimo_mes_realizado) AS mes_corte FROM mart.periodo_realizado),
v AS (SELECT mes, sum(receita_liquida_entregue) AS receita_ajustada, sum(custo_entregue) AS custo_ajustado FROM mart.fact_vendas GROUP BY mes),
d AS (SELECT mes, sum(valor) AS despesas FROM mart.fact_despesas GROUP BY mes),
m AS (SELECT year(mes) AS ano, month(mes) AS mes_num, v.receita_ajustada, v.custo_ajustado, coalesce(d.despesas, 0) AS despesas
      FROM v LEFT JOIN d USING (mes)),
a AS (SELECT ano, count(*) AS meses_realizados,
             sum(receita_ajustada) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS receita_ajustada_ytd,
             sum(receita_ajustada - custo_ajustado) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS lucro_bruto_ytd,
             sum(despesas) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS despesas_ytd,
             count(*) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS meses_no_ytd
      FROM m GROUP BY ano)
SELECT ano, meses_realizados, meses_no_ytd, receita_ajustada_ytd, lucro_bruto_ytd, despesas_ytd,
       lucro_bruto_ytd - despesas_ytd AS resultado_operacional_estimado_ytd,
       (lucro_bruto_ytd - despesas_ytd)::DOUBLE / nullif(receita_ajustada_ytd, 0) AS margem_operacional_estimada_ytd_pct,
       lucro_bruto_ytd::DOUBLE / nullif(receita_ajustada_ytd, 0)                  AS margem_bruta_ytd_pct,
       'resultado operacional ESTIMADO do dataset; nao e lucro liquido contabil' AS rotulo
FROM a ORDER BY ano;
