-- DEMAIS FATOS: cópia tipada do staging (+ coluna `mes`, primeiro dia do mês, nas tabelas diárias).
CREATE OR REPLACE TABLE mart.fact_despesas AS
SELECT * EXCLUDE (_linha_origem), date_trunc('month', data)::DATE AS mes FROM stg.fact_despesas ORDER BY id_despesa;
CREATE OR REPLACE TABLE mart.fact_orcamento AS
SELECT * EXCLUDE (_linha_origem) FROM stg.fact_orcamento ORDER BY mes, id_departamento, id_categoria_despesa, id_filial;
CREATE OR REPLACE TABLE mart.fact_metas_vendas AS
SELECT * EXCLUDE (_linha_origem) FROM stg.fact_metas_vendas ORDER BY mes, id_filial;
CREATE OR REPLACE TABLE mart.fact_rh_mensal AS
SELECT * EXCLUDE (_linha_origem), date_trunc('month', data_referencia)::DATE AS mes FROM stg.fact_rh_mensal
ORDER BY data_referencia, id_departamento, id_filial;
