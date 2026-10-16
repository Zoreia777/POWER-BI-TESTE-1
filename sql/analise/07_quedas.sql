-- =====================================================================================================
-- ANÁLISE 07 · PERÍODOS COM QUEDA DE DESEMPENHO
-- Pergunta: quais períodos apresentam queda?
-- Métrica: receita ajustada provisória (PN-DEV-01). Limiares configuráveis (config.py): mês a mês <= {LIMIAR_MOM}; ano a ano <= {LIMIAR_YOY}.
-- Níveis: empresa, filial e produto, sobre uma grade completa (todo mês realizado × toda unidade), de modo que:
--   'sem_base'      = não existe o período de comparação (início da série)
--   'sem_atividade' = base 0 e atual 0 (ex.: filial antes de abrir)
--   'base_zerada'   = base 0 e atual > 0 (ex.: 1º mês de uma filial/produto): NÃO é crescimento nem queda
--   'comparavel'    = base > 0: só aqui existe percentual e a classificação 'queda_relevante' / 'sem_queda_relevante'.
-- MoM é muito afetado por sazonalidade; YoY compara o mesmo mês e a elimina em boa parte. Por isso os dois aparecem lado a lado.
-- Técnicas: grade com CROSS JOIN, LAG(1) e LAG(12) por partição, CASE, UNION ALL, FILTER.
-- =====================================================================================================

-- @@ setup
CREATE OR REPLACE TEMP VIEW analise_quedas AS
WITH cal AS (SELECT DISTINCT primeiro_dia_mes AS mes FROM mart.dim_calendario
             WHERE primeiro_dia_mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)),
niveis AS (SELECT 'empresa' AS nivel, 0 AS chave, 'Empresa' AS nome
           UNION ALL SELECT 'filial', id_filial, filial FROM mart.dim_filial
           UNION ALL SELECT 'produto', id_produto, produto FROM mart.dim_produto),
v AS (SELECT 'empresa' AS nivel, 0 AS chave, mes, sum(receita_liquida_entregue) AS valor FROM mart.fact_vendas GROUP BY mes
      UNION ALL SELECT 'filial', id_filial, mes, sum(receita_liquida_entregue) FROM mart.fact_vendas GROUP BY id_filial, mes
      UNION ALL SELECT 'produto', id_produto, mes, sum(receita_liquida_entregue) FROM mart.fact_vendas GROUP BY id_produto, mes),
grade AS (SELECT n.nivel, n.chave, n.nome, c.mes, coalesce(v.valor, 0) AS valor
          FROM niveis n CROSS JOIN cal c LEFT JOIN v ON v.nivel = n.nivel AND v.chave = n.chave AND v.mes = c.mes),
comp AS (SELECT *, lag(valor, 1) OVER w AS base_mom, lag(valor, 12) OVER w AS base_yoy
         FROM grade WINDOW w AS (PARTITION BY nivel, chave ORDER BY mes)),
st AS (SELECT *,
        CASE WHEN base_mom IS NULL THEN 'sem_base' WHEN base_mom = 0 AND valor = 0 THEN 'sem_atividade'
             WHEN base_mom = 0 THEN 'base_zerada' ELSE 'comparavel' END AS status_mom,
        CASE WHEN base_yoy IS NULL THEN 'sem_base' WHEN base_yoy = 0 AND valor = 0 THEN 'sem_atividade'
             WHEN base_yoy = 0 THEN 'base_zerada' ELSE 'comparavel' END AS status_yoy
       FROM comp),
pc AS (SELECT *,
        CASE WHEN status_mom = 'comparavel' THEN valor::DOUBLE / base_mom - 1 END AS variacao_mom_pct,
        CASE WHEN status_yoy = 'comparavel' THEN valor::DOUBLE / base_yoy - 1 END AS variacao_yoy_pct
       FROM st)
SELECT *,
       CASE WHEN status_mom <> 'comparavel' THEN status_mom WHEN variacao_mom_pct <= {LIMIAR_MOM} THEN 'queda_relevante' ELSE 'sem_queda_relevante' END AS classificacao_mom,
       CASE WHEN status_yoy <> 'comparavel' THEN status_yoy WHEN variacao_yoy_pct <= {LIMIAR_YOY} THEN 'queda_relevante' ELSE 'sem_queda_relevante' END AS classificacao_yoy
FROM pc;

-- @@ 07a_quedas_empresa
SELECT mes, valor AS receita_ajustada, base_mom, status_mom, variacao_mom_pct, classificacao_mom,
       base_yoy, status_yoy, variacao_yoy_pct, classificacao_yoy,
       {LIMIAR_MOM} AS limiar_mom, {LIMIAR_YOY} AS limiar_yoy
FROM analise_quedas WHERE nivel = 'empresa' ORDER BY mes;

-- @@ 07b_quedas_filial
-- Linhas em que a filial teve queda relevante MoM ou YoY (as demais ficam fora; veja 07d para as contagens).
SELECT nome AS filial, mes, valor AS receita_ajustada, variacao_mom_pct, classificacao_mom, variacao_yoy_pct, classificacao_yoy,
       CASE WHEN classificacao_yoy = 'queda_relevante' THEN base_yoy - valor END AS queda_yoy_em_reais
FROM analise_quedas
WHERE nivel = 'filial' AND (classificacao_mom = 'queda_relevante' OR classificacao_yoy = 'queda_relevante')
ORDER BY queda_yoy_em_reais DESC NULLS LAST, filial, mes;

-- @@ 07c_quedas_produto_yoy
-- Por produto só YoY (a variação mês a mês de um produto é muito ruidosa). Ordenado pelo valor da queda em reais.
SELECT nome AS produto, mes, valor AS receita_ajustada, base_yoy AS receita_mesmo_mes_ano_anterior, variacao_yoy_pct,
       base_yoy - valor AS queda_yoy_em_reais
FROM analise_quedas
WHERE nivel = 'produto' AND classificacao_yoy = 'queda_relevante'
ORDER BY queda_yoy_em_reais DESC, produto, mes;

-- @@ 07d_resumo_quedas_por_nivel
SELECT nivel, 'MoM' AS comparacao, count(*) FILTER (WHERE classificacao_mom = 'queda_relevante') AS quedas_relevantes,
       count(*) FILTER (WHERE classificacao_mom = 'sem_queda_relevante') AS sem_queda_relevante,
       count(*) FILTER (WHERE classificacao_mom IN ('sem_base', 'sem_atividade', 'base_zerada')) AS nao_comparaveis
FROM analise_quedas GROUP BY nivel
UNION ALL
SELECT nivel, 'YoY', count(*) FILTER (WHERE classificacao_yoy = 'queda_relevante'),
       count(*) FILTER (WHERE classificacao_yoy = 'sem_queda_relevante'),
       count(*) FILTER (WHERE classificacao_yoy IN ('sem_base', 'sem_atividade', 'base_zerada'))
FROM analise_quedas GROUP BY nivel
ORDER BY nivel, comparacao;
