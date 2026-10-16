#!/usr/bin/env python3
"""Atalho: python scripts/run_etl.py  (não exige configurar PYTHONPATH)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from empresax.__main__ import main  # noqa: E402

sys.exit(main())
