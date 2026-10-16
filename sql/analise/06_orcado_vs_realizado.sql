-- =====================================================================================================
-- ANÁLISE 06 · ORÇADO × REALIZADO
-- Pergunta: qual a diferença entre orçamento e realizado?
-- Só o período realizado (PN-ORC-01). Três conceitos que NÃO se misturam:
--   orçamento ANUAL      = 12 meses do ano (inclui meses futuros)
--   orçamento ACUMULADO  = jan até o mês de referência (YTD)
--   realizado ACUMULADO  = despesas de jan até o mês de referência
-- Comparação correta: realizado acumulado ÷ orçamento ACUMULADO. A leitura ingênua (÷ anual) cria "economia" falsa (06c).
-- Faixa de tolerância configurável (±{TOL_ORC}): execução > 1+tol = 'acima_do_orcado'; < 1−tol = 'abaixo_do_orcado'; senão 'dentro_da_faixa'.
-- Técnicas: reaproveita as tabelas do mart (FULL OUTER JOIN já resolvido no ETL), CTE, window RANK, CASE.
-- =====================================================================================================

-- @@ 06a_orcado_realizado_departamento_ytd
SELECT a.ano, a.mes_referencia, a.departamento,
       a.orcamento_anual, a.orcamento_acumulado, a.realizado_acumulado, a.variacao_acumulada,
       a.execucao_acumulada_pct, a.consumo_orcamento_anual_pct,
       CASE WHEN a.orcamento_acumulado = 0 THEN 'sem_orcamento'
            WHEN a.execucao_acumulada_pct > 1 + {TOL_ORC} THEN 'acima_do_orcado'
            WHEN a.execucao_acumulada_pct < 1 - {TOL_ORC} THEN 'abaixo_do_orcado' ELSE 'dentro_da_faixa' END AS situacao,
       rank() OVER (ORDER BY a.variacao_acumulada DESC, a.id_departamento) AS ranking_estouro
FROM mart.orcado_vs_realizado_acumulado a
WHERE a.mes_referencia = (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)
ORDER BY ranking_estouro;

-- @@ 06b_orcado_realizado_categoria_ytd
WITH u AS (SELECT ultimo_mes_realizado AS ultimo, date_trunc('year', ultimo_mes_realizado)::DATE AS inicio FROM mart.periodo_realizado),
c AS (
    SELECT g.categoria_despesa, g.grupo_dre, sum(o.orcado) AS orcado_ytd, sum(o.realizado) AS realizado_ytd,
           count(*) FILTER (WHERE o.sem_lancamento_no_mes) AS meses_orcados_sem_lancamento
    FROM mart.orcado_vs_realizado_mensal o JOIN mart.dim_categoria_despesa g USING (id_categoria_despesa)
    WHERE o.mes BETWEEN (SELECT inicio FROM u) AND (SELECT ultimo FROM u)
    GROUP BY g.categoria_despesa, g.grupo_dre)
SELECT rank() OVER (ORDER BY realizado_ytd - orcado_ytd DESC, categoria_despesa) AS ranking_estouro,
       categoria_despesa, grupo_dre, orcado_ytd, realizado_ytd, realizado_ytd - orcado_ytd AS variacao_ytd,
       realizado_ytd::DOUBLE / nullif(orcado_ytd, 0) AS execucao_pct,
       CASE WHEN orcado_ytd = 0 THEN 'sem_orcamento'
            WHEN realizado_ytd::DOUBLE / orcado_ytd > 1 + {TOL_ORC} THEN 'acima_do_orcado'
            WHEN realizado_ytd::DOUBLE / orcado_ytd < 1 - {TOL_ORC} THEN 'abaixo_do_orcado' ELSE 'dentro_da_faixa' END AS situacao,
       meses_orcados_sem_lancamento
FROM c ORDER BY ranking_estouro;

-- @@ 06c_leitura_ingenua_vs_correta
-- Para cada ano: o último mês realizado do ano. Em 2026 (parcial) a diferença entre as duas leituras é enorme.
WITH ult AS (SELECT ano, max(mes_referencia) AS mes_ref FROM mart.orcado_vs_realizado_acumulado GROUP BY ano),
t AS (SELECT a.ano, a.mes_referencia, sum(a.orcamento_anual) AS orcamento_anual, sum(a.orcamento_acumulado) AS orcamento_acumulado,
             sum(a.realizado_acumulado) AS realizado_acumulado
      FROM mart.orcado_vs_realizado_acumulado a JOIN ult u ON u.ano = a.ano AND u.mes_ref = a.mes_referencia GROUP BY a.ano, a.mes_referencia)
SELECT ano, mes_referencia, orcamento_anual, orcamento_acumulado, realizado_acumulado,
       realizado_acumulado::DOUBLE / nullif(orcamento_acumulado, 0) AS execucao_correta_acumulado_sobre_acumulado,
       realizado_acumulado::DOUBLE / nullif(orcamento_anual, 0)     AS leitura_ingenua_acumulado_sobre_anual
FROM t ORDER BY ano;
