-- =====================================================================================================
-- ANÁLISE 08 · FATORES DE VARIAÇÃO (decomposição da receita)
-- Pergunta: quais fatores podem explicar variações relevantes?
-- Metodologia completa e exemplos numéricos: docs/METODOLOGIA_DECOMPOSICAO.md. Resumo:
--   Para cada produto i, no período atual (1) e na base (0):  R = bruta − desconto − impostos = Q · P · (1−d) · (1−t)
--   com Q unidades, P preço bruto médio, d desconto efetivo (desconto/bruta) e t imposto efetivo (impostos/(bruta−desconto)).
--   Produtos CONTINUANTES (Q0>0 e Q1>0) recebem os efeitos:
--     volume  = (Q1c − Q0c) · R0_i / Q0c        (o conjunto de continuantes cresce/encolhe na proporção da base)
--     mix     = (Q1_i − Q1c · Q0_i/Q0c) · R0_i/Q0_i   (mudança de composição entre produtos)
--     preço   = Q1_i · (P1−P0) · (1−d0)(1−t0)
--     desconto= −Q1_i · P1 · (d1−d0) · (1−t0)
--     imposto = −Q1_i · P1 · (1−d1) · (t1−t0)
--   Produtos NOVOS (Q0=0, Q1>0): efeito = R1. DESCONTINUADOS (Q0>0, Q1=0): efeito = −R0. Sem vendas nos dois: 0.
--   A soma dos efeitos é IDENTIDADE ALGÉBRICA (telescópica), não ajuste: não existe "outros".
--   Único termo à parte: arredondamento = diferença entre receita_liquida registrada e (bruta − desconto − impostos); aparece
--   explicitamente e NÃO é efeito de negócio (é 0,00 neste dataset).
--   Devoluções: a decomposição é feita sobre a receita REGISTRADA; o efeito devoluções = −(Δ devoluções) leva à receita ajustada (PN-DEV-01).
-- Comparações: MoM (mês anterior) e YoY (mesmo mês do ano anterior), sempre entre meses realizados. Base inexistente = 'sem_base';
--   base realizada sem vendas = 'base_zerada' (percentuais ficam NULL).
-- Técnicas: CTE encadeadas, CROSS JOIN (grade), window SUM() FILTER OVER, TEMP VIEW compartilhada, UNION ALL.
-- Rótulo dos resultados: o fechamento é CONCLUSÃO ARITMÉTICA; atribuir causa a um efeito é HIPÓTESE (ver docs/CONSULTAS_SQL.md).
-- =====================================================================================================

-- @@ setup
CREATE OR REPLACE TEMP VIEW analise_pvm_pares AS
WITH meses AS (SELECT DISTINCT primeiro_dia_mes AS mes FROM mart.dim_calendario
               WHERE primeiro_dia_mes <= (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)),
p AS (SELECT 'MoM' AS tipo_comparacao, mes AS periodo, CAST(mes - INTERVAL 1 MONTH AS DATE) AS periodo_base FROM meses
      UNION ALL SELECT 'YoY', mes, CAST(mes - INTERVAL 12 MONTH AS DATE) FROM meses)
SELECT p.*, (b.mes IS NOT NULL) AS base_no_periodo_realizado
FROM p LEFT JOIN meses b ON b.mes = p.periodo_base;

-- @@ setup
CREATE OR REPLACE TEMP VIEW analise_pvm_produto AS
WITH agg AS (
    SELECT mes, id_produto, sum(quantidade)::DOUBLE AS q, sum(receita_bruta)::DOUBLE AS bruta,
           sum(desconto_valor)::DOUBLE AS desconto, sum(impostos_valor)::DOUBLE AS imposto,
           (sum(receita_bruta) - sum(desconto_valor) - sum(impostos_valor))::DOUBLE AS r
    FROM mart.fact_vendas GROUP BY mes, id_produto),
grade AS (
    SELECT pv.tipo_comparacao, pv.periodo, pv.periodo_base, d.id_produto, d.produto,
           coalesce(a1.q, 0) AS q1, coalesce(a1.bruta, 0) AS b1, coalesce(a1.desconto, 0) AS d1v, coalesce(a1.imposto, 0) AS i1, coalesce(a1.r, 0) AS r1,
           coalesce(a0.q, 0) AS q0, coalesce(a0.bruta, 0) AS b0, coalesce(a0.desconto, 0) AS d0v, coalesce(a0.imposto, 0) AS i0, coalesce(a0.r, 0) AS r0
    FROM analise_pvm_pares pv CROSS JOIN mart.dim_produto d
    LEFT JOIN agg a1 ON a1.mes = pv.periodo      AND a1.id_produto = d.id_produto
    LEFT JOIN agg a0 ON a0.mes = pv.periodo_base AND a0.id_produto = d.id_produto
    WHERE pv.base_no_periodo_realizado),
cls AS (
    SELECT *, CASE WHEN q1 > 0 AND q0 > 0 THEN 'continuante' WHEN q1 > 0 THEN 'novo'
                   WHEN q0 > 0 THEN 'descontinuado' ELSE 'sem_vendas' END AS classe_produto
    FROM grade),
tot AS (
    SELECT *, sum(q0) FILTER (WHERE classe_produto = 'continuante') OVER (PARTITION BY tipo_comparacao, periodo) AS q0c,
              sum(q1) FILTER (WHERE classe_produto = 'continuante') OVER (PARTITION BY tipo_comparacao, periodo) AS q1c
    FROM cls)
SELECT tipo_comparacao, periodo, periodo_base, id_produto, produto, classe_produto, q0, q1, r0, r1,
    CASE WHEN classe_produto = 'continuante' THEN (q1c - q0c) * r0 / q0c ELSE 0 END AS efeito_volume,
    CASE WHEN classe_produto = 'continuante' THEN (q1 - q1c * q0 / q0c) * (r0 / q0) ELSE 0 END AS efeito_mix,
    CASE WHEN classe_produto = 'continuante'
         THEN q1 * (b1 / q1 - b0 / q0) * (1 - d0v / b0) * (1 - i0 / (b0 - d0v)) ELSE 0 END AS efeito_preco,
    CASE WHEN classe_produto = 'continuante'
         THEN -b1 * (d1v / b1 - d0v / b0) * (1 - i0 / (b0 - d0v)) ELSE 0 END AS efeito_desconto,
    CASE WHEN classe_produto = 'continuante'
         THEN -b1 * (1 - d1v / b1) * (i1 / (b1 - d1v) - i0 / (b0 - d0v)) ELSE 0 END AS efeito_impostos,
    CASE WHEN classe_produto = 'novo' THEN r1 ELSE 0 END AS efeito_produto_novo,
    CASE WHEN classe_produto = 'descontinuado' THEN -r0 ELSE 0 END AS efeito_produto_descontinuado
FROM tot;

-- @@ 08a_decomposicao_total
-- Uma linha por (comparação, período). Colunas de "check_*" provam o fechamento; residuo_* devem ser 0.
WITH e AS (
    SELECT tipo_comparacao, periodo, periodo_base, sum(r0) AS r0, sum(r1) AS r1,
           sum(efeito_volume) AS efeito_volume, sum(efeito_mix) AS efeito_mix, sum(efeito_preco) AS efeito_preco,
           sum(efeito_desconto) AS efeito_desconto, sum(efeito_impostos) AS efeito_impostos,
           sum(efeito_produto_novo) AS efeito_produto_novo, sum(efeito_produto_descontinuado) AS efeito_produto_descontinuado,
           count(*) FILTER (WHERE classe_produto = 'novo') AS produtos_novos,
           count(*) FILTER (WHERE classe_produto = 'descontinuado') AS produtos_descontinuados
    FROM analise_pvm_produto GROUP BY tipo_comparacao, periodo, periodo_base),
l AS (SELECT mes, sum(receita_liquida)::DOUBLE AS registrada, sum(receita_liquida_devolvida)::DOUBLE AS devolucoes,
             sum(receita_liquida_entregue)::DOUBLE AS ajustada FROM mart.fact_vendas GROUP BY mes),
j AS (
    SELECT p.tipo_comparacao, p.periodo, p.periodo_base, p.base_no_periodo_realizado AS base_valida,
           coalesce(l1.registrada, 0) AS reg1, coalesce(l0.registrada, 0) AS reg0,
           coalesce(l1.devolucoes, 0) AS dev1, coalesce(l0.devolucoes, 0) AS dev0,
           coalesce(l1.ajustada, 0) AS aj1, coalesce(l0.ajustada, 0) AS aj0,
           e.* EXCLUDE (tipo_comparacao, periodo, periodo_base)
    FROM analise_pvm_pares p
    LEFT JOIN e ON e.tipo_comparacao = p.tipo_comparacao AND e.periodo = p.periodo
    LEFT JOIN l l1 ON l1.mes = p.periodo
    LEFT JOIN l l0 ON l0.mes = p.periodo_base)
SELECT tipo_comparacao, periodo, periodo_base,
       CASE WHEN NOT base_valida THEN 'sem_base' WHEN reg0 = 0 THEN 'base_zerada' ELSE 'comparavel' END AS status_base,
       CASE WHEN base_valida THEN reg0 END AS receita_registrada_base,
       CASE WHEN base_valida THEN reg1 END AS receita_registrada_atual,
       CASE WHEN base_valida THEN efeito_volume END AS efeito_volume,
       CASE WHEN base_valida THEN efeito_mix END AS efeito_mix,
       CASE WHEN base_valida THEN efeito_preco END AS efeito_preco,
       CASE WHEN base_valida THEN efeito_desconto END AS efeito_desconto,
       CASE WHEN base_valida THEN efeito_impostos END AS efeito_impostos,
       CASE WHEN base_valida THEN efeito_produto_novo END AS efeito_produto_novo,
       CASE WHEN base_valida THEN efeito_produto_descontinuado END AS efeito_produto_descontinuado,
       CASE WHEN base_valida THEN (reg1 - r1) - (reg0 - r0) END AS efeito_arredondamento_nao_e_negocio,
       CASE WHEN base_valida THEN reg1 - reg0 END AS variacao_registrada,
       CASE WHEN base_valida THEN reg1 - reg0
              - (efeito_volume + efeito_mix + efeito_preco + efeito_desconto + efeito_impostos + efeito_produto_novo + efeito_produto_descontinuado
                 + (reg1 - r1) - (reg0 - r0)) END AS residuo_registrada,
       CASE WHEN base_valida THEN -(dev1 - dev0) END AS efeito_devolucoes,
       CASE WHEN base_valida THEN aj1 - aj0 END AS variacao_receita_ajustada,
       CASE WHEN base_valida THEN (aj1 - aj0)
              - ((reg1 - reg0) - (dev1 - dev0)) END AS residuo_ajustada,
       CASE WHEN base_valida AND aj0 > 0 THEN (aj1 - aj0) / aj0 END AS variacao_receita_ajustada_pct,
       produtos_novos, produtos_descontinuados,
       'efeitos = identidade algebrica; causa de cada efeito e HIPOTESE' AS leitura
FROM j ORDER BY tipo_comparacao, periodo;

-- @@ 08b_contribuicao_por_dimensao
-- Quanto cada filial / canal / produto contribuiu para a variação da receita ajustada. A participação é NULL quando a variação
-- total é ~0 (denominador zerado) e pode passar de ±100% quando unidades se compensam (ex.: uma sobe, outra cai).
WITH dim AS (
    SELECT 'filial' AS dimensao, id_filial AS chave, filial AS nome FROM mart.dim_filial
    UNION ALL SELECT 'canal', id_canal, canal FROM mart.dim_canal
    UNION ALL SELECT 'produto', id_produto, produto FROM mart.dim_produto),
v AS (
    SELECT mes, 'filial' AS dimensao, id_filial AS chave, sum(receita_liquida_entregue) AS aj FROM mart.fact_vendas GROUP BY mes, id_filial
    UNION ALL SELECT mes, 'canal', id_canal, sum(receita_liquida_entregue) FROM mart.fact_vendas GROUP BY mes, id_canal
    UNION ALL SELECT mes, 'produto', id_produto, sum(receita_liquida_entregue) FROM mart.fact_vendas GROUP BY mes, id_produto),
g AS (
    SELECT p.tipo_comparacao, p.periodo, p.periodo_base, d.dimensao, d.chave, d.nome,
           coalesce(v1.aj, 0)::DOUBLE AS ajustada_atual, coalesce(v0.aj, 0)::DOUBLE AS ajustada_base
    FROM analise_pvm_pares p CROSS JOIN dim d
    LEFT JOIN v v1 ON v1.mes = p.periodo      AND v1.dimensao = d.dimensao AND v1.chave = d.chave
    LEFT JOIN v v0 ON v0.mes = p.periodo_base AND v0.dimensao = d.dimensao AND v0.chave = d.chave
    WHERE p.base_no_periodo_realizado),
t AS (SELECT *, ajustada_atual - ajustada_base AS contribuicao,
             sum(ajustada_atual - ajustada_base) OVER (PARTITION BY tipo_comparacao, periodo, dimensao) AS variacao_total
      FROM g)
SELECT tipo_comparacao, periodo, periodo_base, dimensao, chave, nome, ajustada_base, ajustada_atual, contribuicao, variacao_total,
       CASE WHEN abs(variacao_total) < 0.005 THEN NULL ELSE contribuicao / variacao_total END AS participacao_na_variacao
FROM t ORDER BY tipo_comparacao, periodo, dimensao, chave;

-- @@ 08c_decomposicao_produto_ultimo_mes
-- Efeitos por produto no último mês realizado (MoM e YoY). volume + mix por produto = (Q1−Q0)·R0/Q0.
SELECT tipo_comparacao, periodo, periodo_base, id_produto, produto, classe_produto,
       q0 AS unidades_base, q1 AS unidades_atual, r0 AS receita_registrada_base, r1 AS receita_registrada_atual,
       efeito_volume, efeito_mix, efeito_preco, efeito_desconto, efeito_impostos, efeito_produto_novo, efeito_produto_descontinuado,
       r1 - r0 AS variacao_produto,
       (r1 - r0) - (efeito_volume + efeito_mix + efeito_preco + efeito_desconto + efeito_impostos + efeito_produto_novo + efeito_produto_descontinuado) AS residuo_produto
FROM analise_pvm_produto
WHERE periodo = (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)
ORDER BY tipo_comparacao, abs(r1 - r0) DESC, id_produto;

-- @@ 08d_decomposicao_verificacao
-- Auditoria da própria decomposição: maior resíduo e quantas situações especiais foram tratadas.
SELECT tipo_comparacao,
       count(DISTINCT periodo) AS comparacoes_validas,
       max(abs((r1 - r0) - (efeito_volume + efeito_mix + efeito_preco + efeito_desconto + efeito_impostos
                            + efeito_produto_novo + efeito_produto_descontinuado))) AS maior_residuo_por_produto,
       count(*) FILTER (WHERE classe_produto = 'novo')          AS casos_produto_novo,
       count(*) FILTER (WHERE classe_produto = 'descontinuado') AS casos_produto_descontinuado,
       count(*) FILTER (WHERE classe_produto = 'sem_vendas')    AS casos_produto_sem_vendas_nos_dois_periodos,
       count(*) FILTER (WHERE classe_produto = 'continuante')   AS casos_produto_continuante
FROM analise_pvm_produto GROUP BY tipo_comparacao ORDER BY tipo_comparacao;
