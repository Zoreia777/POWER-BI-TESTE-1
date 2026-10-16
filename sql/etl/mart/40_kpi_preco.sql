-- PREÇO PRATICADO x PREÇO DE LISTA, por produto e mês (todas as linhas: preço é fato da transação).
-- Granularidade: preco_lista vem de dim_produto (um valor por produto, SEM vigência por data); logo a
-- comparação é "preço praticado vs lista cadastrada". A variação é calculada como RAZÃO DE SOMAS
-- ponderada por quantidade (efeito_preco / valor a preço de lista) — nunca média de percentuais por linha.
-- Variação de preço (reajuste) e desconto são medidas DIFERENTES e ficam em colunas separadas:
--   variacao_preco_pct   = receita_bruta / (qtd x preço lista) - 1      (antes do desconto)
--   desconto_pct_efetivo = desconto_valor / receita_bruta               (depois do preço praticado)
CREATE OR REPLACE TABLE mart.kpi_preco_produto_mes AS
SELECT mes, p.id_produto, p.produto,
       sum(quantidade)                                   AS unidades,
       sum(valor_a_preco_lista)                          AS valor_a_preco_lista,
       sum(receita_bruta)                                AS receita_bruta_preco_praticado,
       sum(efeito_preco_valor)                           AS efeito_preco_valor,
       (sum(efeito_preco_valor) / sum(valor_a_preco_lista))::DECIMAL(12,6) AS variacao_preco_pct,
       sum(desconto_valor)                               AS desconto_valor,
       (sum(desconto_valor) / sum(receita_bruta))::DECIMAL(12,6)           AS desconto_pct_efetivo,
       count(*) FILTER (WHERE f.preco_unitario > f.preco_lista) AS linhas_acima_da_lista,
       count(*)                                          AS linhas
FROM mart.fact_vendas f JOIN mart.dim_produto p USING (id_produto)
GROUP BY mes, p.id_produto, p.produto
ORDER BY mes, p.id_produto;

-- Mesmo indicador em grão MENSAL (todos os produtos). Aqui a regra de granularidade pesa de verdade:
-- a variação do mês é a razão das SOMAS (Σ efeito de preço / Σ valor a preço de lista), e não a média
-- das variações dos produtos, que daria o mesmo peso a um produto de R$ 100 e a um de R$ 7.000.
CREATE OR REPLACE TABLE mart.kpi_preco_mes AS
SELECT mes,
       sum(valor_a_preco_lista)                          AS valor_a_preco_lista,
       sum(receita_bruta)                                AS receita_bruta_preco_praticado,
       sum(efeito_preco_valor)                           AS efeito_preco_valor,
       (sum(efeito_preco_valor) / sum(valor_a_preco_lista))::DECIMAL(12,6) AS variacao_preco_pct,
       sum(desconto_valor)                               AS desconto_valor,
       (sum(desconto_valor) / sum(receita_bruta))::DECIMAL(12,6)           AS desconto_pct_efetivo
FROM mart.fact_vendas
GROUP BY mes ORDER BY mes;
