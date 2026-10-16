"""Uso:  python -m empresax [--dados PASTA] [--banco ARQUIVO.duckdb]   (com PYTHONPATH=src)"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config
from .errors import PipelineErro
from .pipeline import executar


def main() -> int:
    ap = argparse.ArgumentParser(description="ETL da Empresa X: CSV -> DuckDB (raw, stg, mart)")
    ap.add_argument("--dados", type=Path, help="pasta com os CSVs (padrão: data/)")
    ap.add_argument("--banco", type=Path, help="arquivo DuckDB de saída (padrão: warehouse/empresa_x.duckdb)")
    a = ap.parse_args()
    kw = {}
    if a.dados:
        kw["pasta_dados"] = a.dados
    if a.banco:
        kw["arquivo_banco"] = a.banco
    try:
        r = executar(Config(**kw))
    except PipelineErro as e:
        print(f"\nERRO: {e}", file=sys.stderr)
        return 1
    print("\nContagens por camada:")
    for camada, tabs in r.contagens.items():
        print(f"  {camada}: {sum(tabs.values()):,} registros em {len(tabs)} tabelas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
