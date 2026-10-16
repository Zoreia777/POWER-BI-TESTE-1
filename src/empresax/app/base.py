"""Conexão SOMENTE LEITURA com o warehouse e verificação do contrato das views `bi`."""
from __future__ import annotations

import os
from pathlib import Path

import duckdb

from ..config import Config
from ..powerbi import CONTRATO

VAR_AMBIENTE = "EMPRESAX_BANCO"


class BancoIndisponivel(Exception):
    """Erro 'amigável': a mensagem já diz ao usuário o que fazer."""


def caminho_banco(cfg: Config | None = None) -> Path:
    env = os.environ.get(VAR_AMBIENTE)
    return Path(env) if env else (cfg or Config()).arquivo_banco


def assinatura(caminho: Path) -> tuple[str, int, int]:
    """(caminho, mtime_ns, tamanho): muda quando o ETL regrava o banco → invalida os caches do app."""
    try:
        s = Path(caminho).stat()
    except OSError:
        return (str(caminho), 0, 0)
    return (str(caminho), s.st_mtime_ns, s.st_size)


def abrir(caminho: Path) -> duckdb.DuckDBPyConnection:
    """Abre o banco com read_only=True (nenhuma escrita é possível) e confere se as views `bi` existem com as colunas do contrato."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise BancoIndisponivel(f"Banco de dados não encontrado em {caminho}. Rode no terminal: python scripts/run_etl.py e depois python scripts/run_powerbi.py")
    try:
        con = duckdb.connect(str(caminho), read_only=True)
    except duckdb.Error as e:  # arquivo corrompido, bloqueado por outro processo…
        raise BancoIndisponivel(f"Não foi possível abrir o banco {caminho} em modo leitura ({e}). Feche outros processos que o usem ou refaça: python scripts/run_etl.py") from e
    try:
        cols = {}
        for v, c in con.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'bi'").fetchall():
            cols.setdefault(v, set()).add(c)
        faltam = [v for v in CONTRATO if v not in cols]
        if faltam:
            raise BancoIndisponivel(f"As views do schema `bi` não existem no banco ({', '.join(faltam[:3])}…). Rode no terminal: python scripts/run_powerbi.py")
        ruins = [v for v, lista in CONTRATO.items() if not set(lista) <= cols[v]]
        if ruins:
            raise BancoIndisponivel(f"As views {', '.join(ruins)} estão fora do contrato esperado. Rode: python scripts/run_etl.py e python scripts/run_powerbi.py")
    except BancoIndisponivel:
        con.close()
        raise
    return con
