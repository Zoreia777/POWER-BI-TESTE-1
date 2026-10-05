-- =====================================================================
-- EMPRESA X · Views analíticas
-- Servem para consultar direto no banco ou como fonte "achatada" no BI.
-- Regra: vendas com status 'Devolvido' ficam fora da receita (simplificação).
-- =====================================================================

-- 1) Vendas detalhadas (tabelão para quem prefere uma tabela só)
CREATE VIEW vw_vendas_detalhada AS
SELECT
    v.id_venda, v.id_pedido, v.data,
    c.ano, c.trimestre, c.mes_num, c.ano_mes,
    f.filial, f.uf, f.regiao,
    p.produto, p.categoria, p.subcategoria,
    cl.nome_cliente, cl.segmento,
    vd.nome_vendedor, ca.canal,
    v.quantidade, v.preco_unitario, v.desconto_pct,
    v.receita_bruta, v.desconto_valor, v.impostos_valor, v.receita_liquida,
    v.custo_total AS cmv,
    (v.receita_liquida - v.custo_total) AS lucro_bruto,
    v.forma_pagamento, v.status
FROM fact_vendas v
JOIN dim_calendario c ON c.data = v.data
JOIN dim_filial     f ON f.id_filial = v.id_filial
JOIN dim_produto    p ON p.id_produto = v.id_produto
JOIN dim_cliente   cl ON cl.id_cliente = v.id_cliente
JOIN dim_vendedor  vd ON vd.id_vendedor = v.id_vendedor
JOIN dim_canal     ca ON ca.id_canal = v.id_canal;

-- 2) DRE mensal (receita → lucro bruto → despesas por grupo → resultado)
CREATE VIEW vw_dre_mensal AS
WITH v AS (
    SELECT substr(data, 1, 7) AS ano_mes,
           SUM(receita_bruta)   AS receita_bruta,
           SUM(desconto_valor)  AS descontos,
           SUM(impostos_valor)  AS impostos,
           SUM(receita_liquida) AS receita_liquida,
           SUM(custo_total)     AS cmv
    FROM fact_vendas
    WHERE status = 'Entregue'
    GROUP BY 1
), d AS (
    SELECT substr(f.data, 1, 7) AS ano_mes,
           SUM(CASE WHEN c.grupo_dre = 'Despesas com Pessoal'        THEN f.valor ELSE 0 END) AS desp_pessoal,
           SUM(CASE WHEN c.grupo_dre = 'Despesas Comerciais'         THEN f.valor ELSE 0 END) AS desp_comerciais,
           SUM(CASE WHEN c.grupo_dre = 'Despesas Operacionais'       THEN f.valor ELSE 0 END) AS desp_operacionais,
           SUM(CASE WHEN c.grupo_dre = 'Despesas Administrativas'    THEN f.valor ELSE 0 END) AS desp_administrativas,
           SUM(CASE WHEN c.grupo_dre = 'Despesas Financeiras'        THEN f.valor ELSE 0 END) AS desp_financeiras,
           SUM(f.valor) AS despesas_totais
    FROM fact_despesas f
    JOIN dim_categoria_despesa c USING (id_categoria_despesa)
    GROUP BY 1
)
SELECT
    v.ano_mes,
    ROUND(v.receita_bruta, 2)                                   AS receita_bruta,
    ROUND(v.descontos, 2)                                       AS descontos,
    ROUND(v.impostos, 2)                                        AS impostos,
    ROUND(v.receita_liquida, 2)                                 AS receita_liquida,
    ROUND(v.cmv, 2)                                             AS cmv,
    ROUND(v.receita_liquida - v.cmv, 2)                         AS lucro_bruto,
    ROUND((v.receita_liquida - v.cmv) / v.receita_liquida, 4)   AS margem_bruta_pct,
    ROUND(d.desp_pessoal, 2)          AS desp_pessoal,
    ROUND(d.desp_comerciais, 2)       AS desp_comerciais,
    ROUND(d.desp_operacionais, 2)     AS desp_operacionais,
    ROUND(d.desp_administrativas, 2)  AS desp_administrativas,
    ROUND(d.desp_financeiras, 2)      AS desp_financeiras,
    ROUND(d.despesas_totais, 2)       AS despesas_totais,
    ROUND(v.receita_liquida - v.cmv - d.despesas_totais, 2)                       AS resultado_operacional,
    ROUND((v.receita_liquida - v.cmv - d.despesas_totais) / v.receita_liquida, 4) AS margem_operacional_pct
FROM v
LEFT JOIN d USING (ano_mes)
ORDER BY v.ano_mes;

-- 3) Orçado × Realizado por mês, departamento e categoria
CREATE VIEW vw_orcado_vs_realizado AS
WITH r AS (
    SELECT substr(data, 1, 7) AS ano_mes, id_departamento, id_categoria_despesa, id_filial,
           SUM(valor) AS realizado
    FROM fact_despesas GROUP BY 1, 2, 3, 4
), o AS (
    SELECT substr(mes, 1, 7) AS ano_mes, id_departamento, id_categoria_despesa, id_filial,
           SUM(valor_orcado) AS orcado
    FROM fact_orcamento GROUP BY 1, 2, 3, 4
), chaves AS (
    SELECT ano_mes, id_departamento, id_categoria_despesa, id_filial FROM r
    UNION
    SELECT ano_mes, id_departamento, id_categoria_despesa, id_filial FROM o
)
SELECT k.ano_mes,
       dp.departamento, ct.categoria_despesa, ct.grupo_dre, fl.filial,
       ROUND(COALESCE(o.orcado, 0), 2)    AS orcado,
       ROUND(COALESCE(r.realizado, 0), 2) AS realizado,
       ROUND(COALESCE(r.realizado, 0) - COALESCE(o.orcado, 0), 2) AS variacao
FROM chaves k
LEFT JOIN r ON r.ano_mes = k.ano_mes AND r.id_departamento = k.id_departamento
           AND r.id_categoria_despesa = k.id_categoria_despesa AND r.id_filial = k.id_filial
LEFT JOIN o ON o.ano_mes = k.ano_mes AND o.id_departamento = k.id_departamento
           AND o.id_categoria_despesa = k.id_categoria_despesa AND o.id_filial = k.id_filial
JOIN dim_departamento       dp ON dp.id_departamento = k.id_departamento
JOIN dim_categoria_despesa  ct ON ct.id_categoria_despesa = k.id_categoria_despesa
JOIN dim_filial             fl ON fl.id_filial = k.id_filial;

-- 4) Desempenho por filial: receita × meta
CREATE VIEW vw_meta_vs_realizado_filial AS
WITH r AS (
    SELECT substr(data, 1, 7) AS ano_mes, id_filial,
           SUM(receita_liquida) AS receita_liquida,
           SUM(receita_liquida - custo_total) AS lucro_bruto
    FROM fact_vendas WHERE status = 'Entregue' GROUP BY 1, 2
)
SELECT m.mes, substr(m.mes, 1, 7) AS ano_mes, f.filial,
       m.meta_receita_liquida,
       ROUND(COALESCE(r.receita_liquida, 0), 2) AS receita_liquida,
       ROUND(COALESCE(r.receita_liquida, 0) / m.meta_receita_liquida, 4) AS atingimento_pct,
       m.meta_lucro_bruto,
       ROUND(COALESCE(r.lucro_bruto, 0), 2) AS lucro_bruto
FROM fact_metas_vendas m
JOIN dim_filial f ON f.id_filial = m.id_filial
LEFT JOIN r ON r.ano_mes = substr(m.mes, 1, 7) AND r.id_filial = m.id_filial
ORDER BY m.mes, f.filial;

-- 5) Curva ABC de clientes (acumulado de receita líquida)
CREATE VIEW vw_curva_abc_clientes AS
WITH t AS (
    SELECT c.id_cliente, c.nome_cliente, c.segmento,
           SUM(v.receita_liquida) AS receita
    FROM fact_vendas v JOIN dim_cliente c USING (id_cliente)
    WHERE v.status = 'Entregue'
    GROUP BY 1, 2, 3
), r AS (
    SELECT *, SUM(receita) OVER (ORDER BY receita DESC
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS acumulado,
           SUM(receita) OVER () AS total
    FROM t
)
SELECT id_cliente, nome_cliente, segmento, ROUND(receita, 2) AS receita,
       ROUND(acumulado / total, 4) AS pct_acumulado,
       CASE WHEN acumulado / total <= 0.80 THEN 'A'
            WHEN acumulado / total <= 0.95 THEN 'B'
            ELSE 'C' END AS classe_abc
FROM r
ORDER BY receita DESC;
