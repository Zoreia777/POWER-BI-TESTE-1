-- DEVOLUÇÕES: reconciliação, classificação de pedidos e premissas de negócio.
-- São VIEWS (sempre consistentes com mart.fact_vendas; não duplicam dados).

-- (a) Reconciliação por ano da venda e total: registrada = entregues + devoluções (diferença deve ser 0).
CREATE OR REPLACE VIEW mart.kpi_devolucoes_reconciliacao AS
WITH base AS (
    SELECT CAST(year(mes) AS VARCHAR) AS periodo_venda, * FROM mart.fact_vendas
    UNION ALL BY NAME
    SELECT 'TOTAL' AS periodo_venda, * FROM mart.fact_vendas)
SELECT periodo_venda,
       count(*)                                         AS linhas,
       count(*) FILTER (WHERE NOT eh_devolvida)         AS linhas_entregues,
       count(*) FILTER (WHERE eh_devolvida)             AS linhas_devolvidas,
       sum(receita_liquida)                             AS receita_registrada,
       sum(receita_liquida_entregue)                    AS vendas_entregues,
       sum(receita_liquida_devolvida)                   AS devolucoes,
       sum(receita_liquida) - sum(receita_liquida_entregue) - sum(receita_liquida_devolvida) AS diferenca_receita,
       sum(custo_total)                                 AS custo_registrado,
       sum(custo_entregue)                              AS custo_entregue,
       sum(custo_devolvido)                             AS custo_devolvido_hipotese_recuperavel,
       sum(custo_total) - sum(custo_entregue) - sum(custo_devolvido) AS diferenca_custo,
       (sum(receita_liquida_devolvida) / sum(receita_liquida))::DECIMAL(12,6) AS taxa_devolucao_valor_pct
FROM base GROUP BY periodo_venda ORDER BY periodo_venda;

-- (b) Pedidos por tipo de devolução. O status existe por LINHA (item); não há devolução parcial de quantidade.
CREATE OR REPLACE VIEW mart.kpi_devolucoes_pedido AS
WITH p AS (
    SELECT id_pedido, count(*) AS linhas, count(*) FILTER (WHERE eh_devolvida) AS linhas_dev,
           sum(receita_liquida) AS registrada, sum(receita_liquida_devolvida) AS devolvida
    FROM mart.fact_vendas GROUP BY id_pedido)
SELECT CASE WHEN linhas_dev = 0 THEN 'sem_devolucao' WHEN linhas_dev = linhas THEN 'devolucao_total' ELSE 'devolucao_parcial' END AS tipo_pedido,
       count(*) AS pedidos, sum(linhas) AS linhas, sum(linhas_dev) AS linhas_devolvidas,
       sum(registrada) AS receita_registrada, sum(devolvida) AS devolucoes
FROM p GROUP BY 1 ORDER BY 1;

-- (c) Premissas de negócio aprovadas (rastreáveis). Tipo: DECISÃO | HIPÓTESE (não comprovada pelos dados) | LIMITAÇÃO.
CREATE OR REPLACE VIEW mart.ref_premissas_negocio AS
SELECT * FROM (VALUES
 ('PN-DEV-01','DECISÃO DE NEGÓCIO','Uma devolução integral cancela a receita da venda. Aplicada por linha (item de pedido): não há devolução parcial de quantidade nos dados. Os valores originais permanecem preservados.','Aprovado pelo usuário em 14/10/2026','receita_reconhecida_provisoria = vendas_entregues'),
 ('PN-DEV-02','HIPÓTESE DO CENÁRIO (não comprovada pelos dados)','O produto devolvido retorna ao estoque em condições de revenda e seu custo é recuperável. Não há dado que comprove isto.','Aprovado pelo usuário em 14/10/2026','custo ajustado exclui custo_devolvido; sensibilidade em lucro_bruto_se_custo_nao_recuperado'),
 ('PN-DEV-03','LIMITAÇÃO DOS DADOS','Não existe data da devolução. Nenhuma data é inventada e nenhum estorno é atribuído a período específico: os indicadores usam o mês da venda original. O indicador ajustado NÃO é receita contábil oficialmente reconhecida.','Aprovado pelo usuário em 14/10/2026','toda série mensal de devoluções = mês da venda'),
 ('PN-DEV-04','DECISÃO DE NEGÓCIO','Receita registrada, vendas entregues e devoluções são indicadores separados e reconciliáveis: registrada = entregues + devoluções.','Aprovado pelo usuário em 14/10/2026','mart.kpi_devolucoes_reconciliacao'),
 ('PN-MRG-01','DECISÃO DE NEGÓCIO','Linhas com margem negativa são preservadas e sinalizadas; custos e preços não são alterados.','Aprovado pelo usuário em 14/10/2026','flag_margem_negativa; kpi_margem_negativa_*'),
 ('PN-ORC-01','DECISÃO DE NEGÓCIO','Comparações orçado/meta x realizado ficam limitadas ao período com dados realizados; meses futuros não são lidos como desempenho abaixo do orçamento.','Aprovado pelo usuário em 14/10/2026','mart.periodo_realizado; orcado_vs_realizado_*'),
 ('PN-PRC-01','DECISÃO DE NEGÓCIO','Preços praticados são preservados. Variação de preço vs lista e desconto são indicadores distintos, calculados como razão de somas.','Aprovado pelo usuário em 14/10/2026','kpi_preco_produto_mes; kpi_preco_mes'),
 ('PN-SIN-01','LIMITAÇÃO DOS DADOS','Os dados são fictícios. Padrões como sazonalidade foram programados no gerador e não são evidência sobre o mercado real.','Aprovado pelo usuário em 14/10/2026','mart.ref_comportamentos_sinteticos')
) AS t(id, tipo, premissa, origem, onde_se_aplica);
