"""Camada STG: tipagem, padronização e validação (sem descartar nenhum registro).

Padronização aplicada a todo valor: TRIM nas pontas; texto vazio => NULL; conversão
estrita para o tipo do contrato (schema.py). Os valores NÃO são alterados além disso:
preços, custos e status permanecem exatamente como vieram do CSV.
"""
from __future__ import annotations

import logging

import duckdb

from .errors import QualidadeErro
from .quality import Checagem, checar_conversoes, expr
from .schema import SQL_TYPE, TABELAS


def construir_staging(con: duckdb.DuckDBPyConnection, log: logging.Logger) -> list[Checagem]:
    con.execute("CREATE SCHEMA IF NOT EXISTS stg")
    checks = checar_conversoes(con)
    falhas = [c for c in checks if c.status == "ERRO"]
    if falhas:
        for c in falhas:
            log.error("conversão falhou: %s %s (%s ocorrências)", c.tabela, c.regra, c.obtido)
        raise QualidadeErro("Dados brutos não convertem para o contrato de tipos: "
                            + "; ".join(f"{c.tabela}.{c.regra} ({c.obtido})" for c in falhas if ":" in c.regra))
    for nome, tab in TABELAS.items():
        cols = ", ".join(
            (f"CAST({expr(c.nome)} AS {SQL_TYPE[c.tipo]})" if c.tipo != "TEXT" else expr(c.nome)) + f" AS {c.nome}"
            for c in tab.colunas)
        con.execute(f"CREATE OR REPLACE TABLE stg.{nome} AS SELECT _linha_origem, {cols} FROM raw.{nome} ORDER BY _linha_origem")
        log.info("stg.%-22s %8d linhas", nome, con.execute(f"SELECT count(*) FROM stg.{nome}").fetchone()[0])
    return checks
