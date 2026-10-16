-- =====================================================================================================
-- ANÁLISE 01 · FATURAMENTO
-- Pergunta: qual o faturamento por mês (e por ano, em base comparável)?
-- Indicador principal: RECEITA AJUSTADA PROVISÓRIA (PN-DEV-01) = receita líquida das vendas 'Entregue'.
--   Sempre ao lado de: receita registrada (todas as linhas), vendas entregues e devoluções.
--   Reconciliação: registrada = entregues + devoluções (coluna diferenca_reconciliacao, deve ser 0).
--   NÃO é receita contábil oficialmente reconhecida. Devoluções são agrupadas pelo MÊS DA VENDA ORIGINAL
--   (não existe data de devolução; PN-DEV-03).
-- Grão: mês (01a) e ano (01b). Fonte: mart.fact_vendas. Período: apenas meses realizados.
-- Técnicas: CTE, LEFT JOIN com calendário (meses sem venda aparecem com 0), GROUP BY, LAG, CASE, FILTER.
-- Comparações: 'sem_base' (não existe período anterior), 'sem_atividade' (0 e 0), 'base_zerada' (base 0 e atual > 0) e
--   'comparavel'. Só 'comparavel' gera percentual: nunca se mostra 0% ou crescimento infinito onde não há base.
-- =====================================================================================================

-- @@ 01a_faturamento_mensal
WITH meses AS (                      -- calendário dos meses REALIZADOS (garante linha mesmo sem vendas)
    SELECT DISTINCT primeiro_dia_mes AS mes
    FROM mart.dim_calendario
    WHERE primeiro_dia_mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)),
v AS (                               -- os 3 componentes reconciliáveis, por mês da venda
    SELECT m.mes,
           coalesce(sum(f.receita_liquida), 0)           AS receita_registrada,
           coalesce(sum(f.receita_liquida_entregue), 0)  AS vendas_entregues,
           coalesce(sum(f.receita_liquida_devolvida), 0) AS devolucoes
    FROM meses m LEFT JOIN mart.fact_vendas f ON f.mes = m.mes
    GROUP BY m.mes),
comp AS (                            -- LAG(1) = mês anterior; LAG(12) = mesmo mês do ano anterior
    SELECT *, vendas_entregues AS receita_ajustada,
           lag(vendas_entregues, 1)  OVER o AS ajustada_mes_anterior,
           lag(vendas_entregues, 12) OVER o AS ajustada_mesmo_mes_ano_anterior
    FROM v WINDOW o AS (ORDER BY mes)),
st AS (                              -- status de comparabilidade antes de calcular qualquer percentual
    SELECT *,
        CASE WHEN ajustada_mes_anterior IS NULL THEN 'sem_base'
             WHEN ajustada_mes_anterior = 0 AND receita_ajustada = 0 THEN 'sem_atividade'
             WHEN ajustada_mes_anterior = 0 THEN 'base_zerada' ELSE 'comparavel' END AS status_mom,
        CASE WHEN ajustada_mesmo_mes_ano_anterior IS NULL THEN 'sem_base'
             WHEN ajustada_mesmo_mes_ano_anterior = 0 AND receita_ajustada = 0 THEN 'sem_atividade'
             WHEN ajustada_mesmo_mes_ano_anterior = 0 THEN 'base_zerada' ELSE 'comparavel' END AS status_yoy
    FROM comp)
SELECT mes,
       receita_registrada, vendas_entregues, devolucoes,
       receita_ajustada,
       receita_registrada - vendas_entregues - devolucoes                      AS diferenca_reconciliacao,
       CASE WHEN receita_registrada <> 0 THEN devolucoes::DOUBLE / receita_registrada END AS taxa_devolucao_pct,
       status_mom,
       CASE WHEN status_mom = 'comparavel' THEN receita_ajustada::DOUBLE / ajustada_mes_anterior - 1 END AS variacao_mom_pct,
       status_yoy,
       CASE WHEN status_yoy = 'comparavel' THEN receita_ajustada::DOUBLE / ajustada_mesmo_mes_ano_anterior - 1 END AS variacao_yoy_pct,
       'receita_ajustada_provisoria (PN-DEV-01/03; nao e receita contabil oficial)' AS indicador_principal
FROM st ORDER BY mes;

-- @@ 01b_faturamento_anual_ytd
-- Ano a ano em BASE COMPARÁVEL: o ano corrente só é comparado com os mesmos meses (1..mês de corte) dos anos anteriores.
WITH corte AS (SELECT month(ultimo_mes_realizado) AS mes_corte FROM mart.periodo_realizado),
v AS (
    SELECT year(mes) AS ano, month(mes) AS mes_num,
           sum(receita_liquida) AS registrada, sum(receita_liquida_entregue) AS entregues, sum(receita_liquida_devolvida) AS devolucoes
    FROM mart.fact_vendas GROUP BY 1, 2),
a AS (
    SELECT ano,
           count(*)                                                         AS meses_realizados_no_ano,
           sum(registrada)                                                  AS receita_registrada_ano_realizado,
           sum(entregues)                                                   AS receita_ajustada_ano_realizado,
           count(*) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS meses_no_ytd,
           sum(registrada) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS receita_registrada_ytd,
           sum(entregues)  FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS receita_ajustada_ytd,
           sum(devolucoes) FILTER (WHERE mes_num <= (SELECT mes_corte FROM corte)) AS devolucoes_ytd
    FROM v GROUP BY ano),
c AS (SELECT *, lag(receita_ajustada_ytd) OVER (ORDER BY ano) AS ajustada_ytd_ano_anterior,
             lag(meses_no_ytd) OVER (ORDER BY ano) AS meses_ytd_ano_anterior FROM a)
SELECT ano, meses_realizados_no_ano, (meses_realizados_no_ano = 12) AS ano_completo,
       receita_registrada_ano_realizado, receita_ajustada_ano_realizado,
       'jan a ' || (SELECT strftime(ultimo_mes_realizado, '%m') FROM mart.periodo_realizado) AS periodo_ytd_comparado,
       receita_registrada_ytd, devolucoes_ytd, receita_ajustada_ytd, ajustada_ytd_ano_anterior,
       CASE WHEN ajustada_ytd_ano_anterior IS NULL THEN 'sem_base'
            WHEN ajustada_ytd_ano_anterior = 0 THEN 'base_zerada'
            WHEN meses_no_ytd <> meses_ytd_ano_anterior THEN 'base_incompleta' ELSE 'comparavel' END AS status_yoy_ytd,
       CASE WHEN ajustada_ytd_ano_anterior > 0 AND meses_no_ytd = meses_ytd_ano_anterior
            THEN receita_ajustada_ytd::DOUBLE / ajustada_ytd_ano_anterior - 1 END AS variacao_yoy_ytd_pct
FROM c ORDER BY ano;
