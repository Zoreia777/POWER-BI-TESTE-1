#!/usr/bin/env python3
"""Executa as análises SQL da Etapa 3 sobre warehouse/empresa_x.duckdb (rode antes scripts/run_etl.py).

    python scripts/run_queries.py        ->  reports/consultas/*.csv + reports/resultados_etapa3.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from empresax.config import Config  # noqa: E402
from empresax.consultas import ConsultaErro, executar_todas, gravar_resumo  # noqa: E402
from empresax.logger import configurar  # noqa: E402

if __name__ == "__main__":
    cfg = Config()
    log, _ = configurar(cfg.pasta_logs)
    try:
        res = executar_todas(cfg, log=log)
    except ConsultaErro as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)
    gravar_resumo(res, cfg.pasta_relatorios / "resultados_etapa3.md")
    print(f"{len(res)} resultados exportados para {cfg.pasta_consultas_saida}")
