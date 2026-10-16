-- DIMENSÕES: cópia tipada do staging (sem a coluna técnica _linha_origem).
-- Nenhuma regra de negócio aqui: as dimensões já chegam validadas (PK única, sem órfãos).
CREATE OR REPLACE TABLE mart.dim_calendario        AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_calendario        ORDER BY data;
CREATE OR REPLACE TABLE mart.dim_canal             AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_canal             ORDER BY id_canal;
CREATE OR REPLACE TABLE mart.dim_categoria_despesa AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_categoria_despesa ORDER BY id_categoria_despesa;
CREATE OR REPLACE TABLE mart.dim_cliente           AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_cliente           ORDER BY id_cliente;
CREATE OR REPLACE TABLE mart.dim_departamento      AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_departamento      ORDER BY id_departamento;
CREATE OR REPLACE TABLE mart.dim_filial            AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_filial            ORDER BY id_filial;
CREATE OR REPLACE TABLE mart.dim_produto           AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_produto           ORDER BY id_produto;
CREATE OR REPLACE TABLE mart.dim_vendedor          AS SELECT * EXCLUDE (_linha_origem) FROM stg.dim_vendedor          ORDER BY id_vendedor;
