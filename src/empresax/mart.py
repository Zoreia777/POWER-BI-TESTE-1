"""Camada MART: executa, em ordem, os arquivos sql/etl/mart/*.sql e carrega o registro de comportamentos."""
from __future__ import annotations

import logging
import re

import duckdb

from .comportamentos import COMPORTAMENTOS
from .config import Config


def construir_mart(con: duckdb.DuckDBPyConnection, cfg: Config, log: logging.Logger) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS mart")
    arquivos = sorted(cfg.pasta_sql.glob("*.sql"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo SQL em {cfg.pasta_sql}")
    for arq in arquivos:
        sql = arq.read_text(encoding="utf-8").replace("{POLITICA}", cfg.politica_devolucao)
        con.execute(sql)
        for tabela in re.findall(r"CREATE OR REPLACE (?:TABLE|VIEW) (mart\.\w+)", sql):
            n = con.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
            log.info("%s -> %-40s %8d linhas", arq.name, tabela, n)
    con.execute("CREATE OR REPLACE TABLE mart.ref_comportamentos_sinteticos "
                "(id VARCHAR, comportamento VARCHAR, parametro_no_gerador VARCHAR, linha_gerador INTEGER, "
                "tabela_afetada VARCHAR, origem VARCHAR)")
    con.executemany("INSERT INTO mart.ref_comportamentos_sinteticos VALUES (?,?,?,?,?, 'PROGRAMADO no gerador (dado fictício)')",
                    [list(c) for c in COMPORTAMENTOS])
