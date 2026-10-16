"""Camada RAW: cópia fiel dos CSVs.

Regras: tudo entra como texto (nenhuma conversão), células vazias continuam vazias,
nenhuma linha é filtrada. Cada linha ganha `_linha_origem` (número da linha no CSV,
cabeçalho = 1) para permitir auditoria até o arquivo original. Os CSVs nunca são alterados.
"""
from __future__ import annotations

import csv
import hashlib
import logging

import duckdb
import pandas as pd

from .config import Config
from .errors import ArquivoAusenteErro, EstruturaInvalidaErro
from .quality import Checagem
from .schema import TABELAS


def _linhas_de_dados(caminho) -> int:
    """Conta registros com o módulo csv (parser independente do pandas, usado na reconciliação)."""
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def carregar_raw(con: duckdb.DuckDBPyConnection, cfg: Config, log: logging.Logger) -> list[Checagem]:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE OR REPLACE TABLE ops.arquivos_origem (arquivo VARCHAR, bytes BIGINT, sha256 VARCHAR, registros BIGINT)")
    checks: list[Checagem] = []
    for nome, tab in TABELAS.items():
        caminho = cfg.pasta_dados / f"{nome}.csv"
        if not caminho.is_file():
            raise ArquivoAusenteErro(f"Arquivo esperado não encontrado: {caminho.name} (pasta {cfg.pasta_dados})")
        df = pd.read_csv(caminho, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if list(df.columns) != tab.nomes:
            raise EstruturaInvalidaErro(
                f"{caminho.name}: colunas {list(df.columns)} diferem do contrato {tab.nomes}")
        esperado = _linhas_de_dados(caminho)
        df.insert(0, "_linha_origem", range(2, len(df) + 2))
        con.register("_df_raw", df)
        con.execute(f"CREATE OR REPLACE TABLE raw.{nome} AS SELECT * FROM _df_raw")
        con.unregister("_df_raw")
        obtido = con.execute(f"SELECT count(*) FROM raw.{nome}").fetchone()[0]
        sha = hashlib.sha256(caminho.read_bytes()).hexdigest()
        con.execute("INSERT INTO ops.arquivos_origem VALUES (?,?,?,?)",
                    [caminho.name, caminho.stat().st_size, sha, obtido])
        checks.append(Checagem("raw", nome, "registros no raw = registros do CSV", esperado, obtido))
        log.info("raw.%-22s %8d linhas", nome, obtido)
    return checks
