"""Fixtures compartilhadas. O pipeline roda UMA vez por sessão em pastas temporárias;
os testes comparam o banco com um 'oráculo' calculado direto dos CSVs via pandas."""
import shutil
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from empresax.config import Config  # noqa: E402
from empresax.pipeline import executar  # noqa: E402

DATA = RAIZ / "data"


def cfg_tmp(base: Path, dados: Path = DATA) -> Config:
    return Config(pasta_dados=dados, arquivo_banco=base / "w.duckdb",
                  pasta_logs=base / "logs", pasta_relatorios=base / "rel")


def copia_dados(destino: Path) -> Path:
    shutil.copytree(DATA, destino)
    return destino


def impressao_digital(con, schemas=("raw", "stg", "mart")) -> dict:
    """(linhas, hash do conteúdo) de cada tabela — independe da ordem das linhas."""
    out = {}
    for s, t in con.execute("SELECT table_schema, table_name FROM information_schema.tables "
                            "WHERE table_schema IN ('raw','stg','mart') AND table_type='BASE TABLE'").fetchall():
        out[f"{s}.{t}"] = con.execute(f'SELECT count(*), sum(hash(x)::HUGEINT) FROM {s}."{t}" x').fetchone()
    return out


@pytest.fixture(scope="session")
def csv_():
    """Todos os CSVs como DataFrames (oráculo)."""
    return {p.stem: pd.read_csv(p) for p in sorted(DATA.glob("*.csv"))}


@pytest.fixture(scope="session")
def etl(tmp_path_factory):
    base = tmp_path_factory.mktemp("etl")
    antes = {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in DATA.glob("*.csv")}
    cfg = cfg_tmp(base)
    res = executar(cfg)
    depois = {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in DATA.glob("*.csv")}
    con = duckdb.connect(str(cfg.arquivo_banco), read_only=True)
    yield {"cfg": cfg, "res": res, "con": con, "csv_inalterados": antes == depois}
    con.close()


@pytest.fixture(scope="session")
def bi_db(etl, tmp_path_factory):
    """Cópia do banco do ETL com as views `bi` criadas (o aplicativo só lê dessa cópia)."""
    from empresax import powerbi as P
    p = tmp_path_factory.mktemp("appdb") / "wh.duckdb"
    shutil.copy(etl["cfg"].arquivo_banco, p)
    con = duckdb.connect(str(p))
    P.criar_views(con)
    con.close()
    return p
