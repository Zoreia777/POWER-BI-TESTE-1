#!/usr/bin/env python3
"""Etapa 4 — executa as 6 investigações analíticas (Python/Pandas/Plotly) e grava reports/executivo/.

    python scripts/run_etl.py && python scripts/run_analises.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from empresax.analise.dados import carregar  # noqa: E402
from empresax.analise.relatorio import executar_todas, gravar  # noqa: E402
from empresax.config import Config  # noqa: E402

if __name__ == "__main__":
    cfg = Config()
    if not cfg.arquivo_banco.exists():
        sys.exit(f"Banco não encontrado: {cfg.arquivo_banco}. Rode antes: python scripts/run_etl.py")
    D = carregar(cfg)
    I = executar_todas(cfg, D)
    h = gravar(I, D, cfg)
    n = sum(len(i.achados) for i in I.values())
    print(f"{len(I)} investigações, {n} achados, {len(h)} arquivos em {cfg.pasta_executivo}")
