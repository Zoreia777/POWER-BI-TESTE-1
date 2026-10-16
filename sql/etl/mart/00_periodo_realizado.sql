-- PERÍODO REALIZADO
-- Define até quando existem dados realizados. É DERIVADO dos fatos (menor entre o último dia de
-- venda e o último dia de despesa) e conferido contra a coluna `realizado` de dim_calendario.
-- Todas as comparações orçado/meta x realizado usam esta tabela para ignorar meses futuros.
CREATE OR REPLACE TABLE mart.periodo_realizado AS
WITH f AS (
    SELECT LEAST((SELECT max(data) FROM stg.fact_vendas), (SELECT max(data) FROM stg.fact_despesas)) AS ultimo_dia
)
SELECT
    f.ultimo_dia                                   AS ultimo_dia_realizado,
    date_trunc('month', f.ultimo_dia)::DATE        AS ultimo_mes_realizado,
    (f.ultimo_dia = last_day(f.ultimo_dia))        AS ultimo_mes_completo,
    (SELECT max(data) FROM stg.dim_calendario WHERE realizado = 1) AS ultimo_dia_calendario_realizado,
    (f.ultimo_dia = (SELECT max(data) FROM stg.dim_calendario WHERE realizado = 1)) AS consistente_com_calendario
FROM f;
