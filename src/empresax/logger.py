"""Configuração de logs: console + arquivo timestampado em logs/."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def configurar(pasta_logs: Path) -> tuple[logging.Logger, Path]:
    pasta_logs.mkdir(parents=True, exist_ok=True)
    arquivo = pasta_logs / f"etl_{datetime.now():%Y%m%d_%H%M%S_%f}.log"
    log = logging.getLogger("empresax")
    log.setLevel(logging.INFO)
    for h in list(log.handlers):          # evita handlers duplicados em execuções repetidas
        log.removeHandler(h)
        h.close()
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    for h in (logging.FileHandler(arquivo, encoding="utf-8"), logging.StreamHandler()):
        h.setFormatter(fmt)
        log.addHandler(h)
    log.propagate = False
    return log, arquivo
