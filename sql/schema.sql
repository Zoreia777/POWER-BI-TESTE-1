-- =====================================================================
-- EMPRESA X · Esquema do banco (modelo estrela)
-- Compatível com SQLite. Para PostgreSQL/SQL Server, troque TEXT por
-- DATE/VARCHAR e REAL por NUMERIC(14,2) conforme a necessidade.
-- Datas são guardadas em formato ISO (AAAA-MM-DD).
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------------------------- DIMENSÕES ------------------------------
CREATE TABLE dim_calendario (
    data              TEXT PRIMARY KEY,
    ano               INTEGER NOT NULL,
    semestre          TEXT    NOT NULL,
    trimestre         TEXT    NOT NULL,
    mes_num           INTEGER NOT NULL,
    mes_nome          TEXT    NOT NULL,
    mes_abrev         TEXT    NOT NULL,
    ano_mes           TEXT    NOT NULL,
    mes_ano           TEXT    NOT NULL,
    ordem_ano_mes     INTEGER NOT NULL,
    dia               INTEGER NOT NULL,
    dia_semana_num    INTEGER NOT NULL,
    dia_semana        TEXT    NOT NULL,
    dia_semana_abrev  TEXT    NOT NULL,
    semana_do_ano     INTEGER NOT NULL,
    fim_de_semana     INTEGER NOT NULL,
    feriado           TEXT,
    dia_util          INTEGER NOT NULL,
    realizado         INTEGER NOT NULL,
    status_periodo    TEXT    NOT NULL,
    primeiro_dia_mes  TEXT    NOT NULL
);

CREATE TABLE dim_filial (
    id_filial      INTEGER PRIMARY KEY,
    filial         TEXT NOT NULL,
    cidade         TEXT NOT NULL,
    uf             TEXT NOT NULL,
    regiao         TEXT NOT NULL,
    tipo           TEXT NOT NULL,
    data_abertura  TEXT NOT NULL,
    latitude       REAL,
    longitude      REAL
);

CREATE TABLE dim_produto (
    id_produto           INTEGER PRIMARY KEY,
    sku                  TEXT NOT NULL UNIQUE,
    produto              TEXT NOT NULL,
    categoria            TEXT NOT NULL,
    subcategoria         TEXT NOT NULL,
    preco_lista          REAL NOT NULL,
    custo_unitario_base  REAL NOT NULL,
    margem_lista_pct     REAL NOT NULL,
    aliquota_imposto     REAL NOT NULL
);

CREATE TABLE dim_cliente (
    id_cliente            INTEGER PRIMARY KEY,
    nome_cliente          TEXT NOT NULL UNIQUE,
    segmento              TEXT NOT NULL,
    cidade                TEXT NOT NULL,
    uf                    TEXT NOT NULL,
    regiao                TEXT NOT NULL,
    data_cadastro         TEXT NOT NULL,
    data_primeira_compra  TEXT
);

CREATE TABLE dim_vendedor (
    id_vendedor    INTEGER PRIMARY KEY,
    nome_vendedor  TEXT NOT NULL,
    equipe         TEXT NOT NULL,
    cargo          TEXT NOT NULL,
    data_admissao  TEXT NOT NULL
);

CREATE TABLE dim_canal (
    id_canal    INTEGER PRIMARY KEY,
    canal       TEXT NOT NULL,
    tipo_canal  TEXT NOT NULL
);

CREATE TABLE dim_departamento (
    id_departamento  INTEGER PRIMARY KEY,
    departamento     TEXT NOT NULL,
    centro_custo     TEXT NOT NULL,
    responsavel      TEXT NOT NULL,
    tipo_area        TEXT NOT NULL
);

CREATE TABLE dim_categoria_despesa (
    id_categoria_despesa  INTEGER PRIMARY KEY,
    categoria_despesa     TEXT NOT NULL,
    grupo_dre             TEXT NOT NULL,
    tipo_custo            TEXT NOT NULL,
    ordem_dre             INTEGER NOT NULL
);

-- ------------------------------ FATOS --------------------------------
CREATE TABLE fact_vendas (
    id_venda         INTEGER PRIMARY KEY,
    id_pedido        TEXT    NOT NULL,
    data             TEXT    NOT NULL REFERENCES dim_calendario(data),
    id_cliente       INTEGER NOT NULL REFERENCES dim_cliente(id_cliente),
    id_produto       INTEGER NOT NULL REFERENCES dim_produto(id_produto),
    id_filial        INTEGER NOT NULL REFERENCES dim_filial(id_filial),
    id_vendedor      INTEGER NOT NULL REFERENCES dim_vendedor(id_vendedor),
    id_canal         INTEGER NOT NULL REFERENCES dim_canal(id_canal),
    quantidade       INTEGER NOT NULL,
    preco_unitario   REAL    NOT NULL,
    desconto_pct     REAL    NOT NULL,
    receita_bruta    REAL    NOT NULL,
    desconto_valor   REAL    NOT NULL,
    impostos_valor   REAL    NOT NULL,
    receita_liquida  REAL    NOT NULL,
    custo_total      REAL    NOT NULL,
    forma_pagamento  TEXT    NOT NULL,
    status           TEXT    NOT NULL CHECK (status IN ('Entregue', 'Devolvido'))
);

CREATE TABLE fact_despesas (
    id_despesa            INTEGER PRIMARY KEY,
    data                  TEXT    NOT NULL REFERENCES dim_calendario(data),
    id_departamento       INTEGER NOT NULL REFERENCES dim_departamento(id_departamento),
    id_categoria_despesa  INTEGER NOT NULL REFERENCES dim_categoria_despesa(id_categoria_despesa),
    id_filial             INTEGER NOT NULL REFERENCES dim_filial(id_filial),
    fornecedor            TEXT    NOT NULL,
    valor                 REAL    NOT NULL
);

CREATE TABLE fact_orcamento (
    mes                   TEXT    NOT NULL REFERENCES dim_calendario(data),
    id_departamento       INTEGER NOT NULL REFERENCES dim_departamento(id_departamento),
    id_categoria_despesa  INTEGER NOT NULL REFERENCES dim_categoria_despesa(id_categoria_despesa),
    id_filial             INTEGER NOT NULL REFERENCES dim_filial(id_filial),
    valor_orcado          REAL    NOT NULL,
    PRIMARY KEY (mes, id_departamento, id_categoria_despesa, id_filial)
);

CREATE TABLE fact_metas_vendas (
    mes                    TEXT    NOT NULL REFERENCES dim_calendario(data),
    id_filial              INTEGER NOT NULL REFERENCES dim_filial(id_filial),
    meta_receita_liquida   REAL    NOT NULL,
    meta_margem_bruta_pct  REAL    NOT NULL,
    meta_lucro_bruto       REAL    NOT NULL,
    PRIMARY KEY (mes, id_filial)
);

CREATE TABLE fact_rh_mensal (
    data_referencia      TEXT    NOT NULL REFERENCES dim_calendario(data),
    id_departamento      INTEGER NOT NULL REFERENCES dim_departamento(id_departamento),
    id_filial            INTEGER NOT NULL REFERENCES dim_filial(id_filial),
    headcount            INTEGER NOT NULL,
    headcount_planejado  INTEGER NOT NULL,
    admissoes            INTEGER NOT NULL,
    desligamentos        INTEGER NOT NULL,
    PRIMARY KEY (data_referencia, id_departamento, id_filial)
);

-- ------------------------------ ÍNDICES ------------------------------
CREATE INDEX ix_vendas_data     ON fact_vendas (data);
CREATE INDEX ix_vendas_cliente  ON fact_vendas (id_cliente);
CREATE INDEX ix_vendas_produto  ON fact_vendas (id_produto);
CREATE INDEX ix_vendas_filial   ON fact_vendas (id_filial);
CREATE INDEX ix_vendas_pedido   ON fact_vendas (id_pedido);
CREATE INDEX ix_despesas_data   ON fact_despesas (data);
CREATE INDEX ix_despesas_cat    ON fact_despesas (id_categoria_despesa);
CREATE INDEX ix_despesas_filial ON fact_despesas (id_filial);
