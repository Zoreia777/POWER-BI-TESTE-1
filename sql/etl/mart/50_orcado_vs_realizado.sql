-- ORÇADO x REALIZADO — SOMENTE no período em que existem dados realizados (mart.periodo_realizado).
-- Meses futuros NÃO são lidos como "abaixo do orçamento": simplesmente não entram nestas tabelas.
--
-- Três conceitos (ver docs/ETL.md):
--   orçamento ANUAL      = soma do orçamento dos 12 meses do ano (inclui meses futuros)
--   orçamento ACUMULADO  = soma do orçamento de jan até o mês de referência (YTD)
--   realizado ACUMULADO  = soma das despesas de jan até o mês de referência (YTD)
-- Comparar realizado acumulado com o orçamento ANUAL mostraria "economia" falsa; a comparação justa
-- é realizado acumulado x orçamento acumulado.

-- (a) mensal, no grão do orçamento (mês x departamento x categoria x filial)
CREATE OR REPLACE TABLE mart.orcado_vs_realizado_mensal AS
WITH orc AS (
    SELECT mes, id_departamento, id_categoria_despesa, id_filial, sum(valor_orcado) AS orcado
    FROM mart.fact_orcamento GROUP BY ALL),
rea AS (
    SELECT mes, id_departamento, id_categoria_despesa, id_filial, sum(valor) AS realizado, count(*) AS lancamentos
    FROM mart.fact_despesas GROUP BY ALL)
SELECT mes, id_departamento, id_categoria_despesa, id_filial,
       coalesce(orc.orcado, 0)::DECIMAL(18,2)       AS orcado,
       coalesce(rea.realizado, 0)::DECIMAL(18,2)    AS realizado,
       (coalesce(rea.realizado, 0) - coalesce(orc.orcado, 0))::DECIMAL(18,2) AS variacao,
       (rea.realizado / nullif(orc.orcado, 0))::DECIMAL(12,6)  AS execucao_pct,
       coalesce(rea.lancamentos, 0)                 AS lancamentos,
       (orc.orcado IS NULL)                         AS sem_orcamento,
       (rea.realizado IS NULL)                      AS sem_lancamento_no_mes
FROM orc FULL OUTER JOIN rea USING (mes, id_departamento, id_categoria_despesa, id_filial)
WHERE mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)
ORDER BY mes, id_departamento, id_categoria_despesa, id_filial;

-- (b) acumulado no ano, por departamento (um ponto por mês realizado)
CREATE OR REPLACE TABLE mart.orcado_vs_realizado_acumulado AS
WITH meses AS (
    SELECT DISTINCT primeiro_dia_mes AS mes_referencia FROM mart.dim_calendario
    WHERE primeiro_dia_mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)),
grade AS (SELECT m.mes_referencia, d.id_departamento, d.departamento FROM meses m CROSS JOIN mart.dim_departamento d),
mensal AS (
    SELECT mes, id_departamento, sum(orcado) AS orcado, sum(realizado) AS realizado
    FROM mart.orcado_vs_realizado_mensal GROUP BY ALL),
anual AS (
    SELECT year(mes) AS ano, id_departamento, sum(valor_orcado) AS orcamento_anual
    FROM mart.fact_orcamento GROUP BY ALL),
base AS (
    SELECT year(g.mes_referencia) AS ano, g.mes_referencia, g.id_departamento, g.departamento,
           coalesce(m.orcado, 0) AS orcado_mes, coalesce(m.realizado, 0) AS realizado_mes
    FROM grade g LEFT JOIN mensal m ON m.mes = g.mes_referencia AND m.id_departamento = g.id_departamento)
SELECT b.ano, b.mes_referencia, b.id_departamento, b.departamento,
       coalesce(a.orcamento_anual, 0)::DECIMAL(18,2) AS orcamento_anual,
       (sum(b.orcado_mes)    OVER w)::DECIMAL(18,2)  AS orcamento_acumulado,
       (sum(b.realizado_mes) OVER w)::DECIMAL(18,2)  AS realizado_acumulado,
       ((sum(b.realizado_mes) OVER w) - (sum(b.orcado_mes) OVER w))::DECIMAL(18,2) AS variacao_acumulada,
       ((sum(b.realizado_mes) OVER w) / nullif(sum(b.orcado_mes) OVER w, 0))::DECIMAL(12,6) AS execucao_acumulada_pct,
       ((sum(b.realizado_mes) OVER w) / nullif(a.orcamento_anual, 0))::DECIMAL(12,6)        AS consumo_orcamento_anual_pct
FROM base b LEFT JOIN anual a ON a.ano = b.ano AND a.id_departamento = b.id_departamento
WINDOW w AS (PARTITION BY b.ano, b.id_departamento ORDER BY b.mes_referencia)
ORDER BY b.ano, b.mes_referencia, b.id_departamento;

-- (c) meta de receita x receita (mês x filial), também limitada ao período realizado.
-- Usa a receita reconhecida PROVISÓRIA (vendas entregues) e mostra os demais componentes.
CREATE OR REPLACE TABLE mart.meta_vs_realizado_mensal AS
WITH v AS (
    SELECT mes, id_filial, sum(receita_liquida_entregue) AS vendas_entregues,
           sum(receita_liquida_devolvida) AS devolucoes, sum(receita_liquida) AS receita_liquida_registrada
    FROM mart.fact_vendas GROUP BY ALL)
SELECT mes, id_filial,
       m.meta_receita_liquida,
       coalesce(v.vendas_entregues, 0)::DECIMAL(18,2)           AS vendas_entregues,
       coalesce(v.devolucoes, 0)::DECIMAL(18,2)                 AS devolucoes,
       coalesce(v.receita_liquida_registrada, 0)::DECIMAL(18,2) AS receita_liquida_registrada,
       (coalesce(v.vendas_entregues, 0) / nullif(m.meta_receita_liquida, 0))::DECIMAL(12,6) AS atingimento_provisorio_pct,
       (m.meta_receita_liquida IS NULL)                         AS sem_meta,
       '{POLITICA}'                                             AS politica_devolucao,
       'PN-DEV-01;PN-DEV-03'                                    AS premissas_aplicadas
FROM mart.fact_metas_vendas m FULL OUTER JOIN v USING (mes, id_filial)
WHERE mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)
ORDER BY mes, id_filial;
