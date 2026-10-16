"""Executor das análises SQL (Etapa 3).

Cada arquivo de `sql/analise/` é dividido em blocos por linhas `-- @@ nome`:
  * `-- @@ setup`   -> executa sem exportar (ex.: TEMP VIEW compartilhada entre blocos)
  * `-- @@ 01a_xxx` -> um SELECT; o resultado vira `reports/consultas/01a_xxx.csv`
Os parâmetros do `Config` entram como {PLACEHOLDERS}. O banco é aberto só para leitura.
Exportações são determinísticas: ordenação vem do SQL, decimais viram texto fixo, floats são arredondados.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from .config import Config
from .errors import PipelineErro

MARCADOR = re.compile(r"^-- @@ (\S+)\s*$", re.MULTILINE)


class ConsultaErro(PipelineErro):
    """Falha ao executar uma análise SQL."""


@dataclass
class Resultado:
    nome: str
    arquivo_sql: str
    df: pd.DataFrame
    sha256: str = ""


def parametros(cfg: Config) -> dict[str, str]:
    return {
        "{LIMIAR_MOM}": repr(float(cfg.limiar_queda_mom)),
        "{LIMIAR_YOY}": repr(float(cfg.limiar_queda_yoy)),
        "{PISO_LINHAS}": str(int(cfg.piso_linhas_margem)),
        "{TOL_ORC}": repr(float(cfg.tolerancia_orcamento_pct)),
    }


def blocos(texto: str) -> list[tuple[str, str]]:
    partes = MARCADOR.split(texto)           # [cabeçalho, nome1, sql1, nome2, sql2, ...]
    return [(partes[i], partes[i + 1]) for i in range(1, len(partes), 2)]


def executar_arquivo(con, caminho: Path, cfg: Config) -> list[Resultado]:
    texto = caminho.read_text(encoding="utf-8")
    con.execute("SET threads = 1")      # ordem de soma fixa => floats idênticos a cada execução (determinismo)
    for k, v in parametros(cfg).items():
        texto = texto.replace(k, v)
    saida = []
    for nome, sql in blocos(texto):
        try:
            if nome == "setup":
                con.execute(sql)
                continue
            df = con.execute(sql).df()
        except duckdb.Error as e:
            raise ConsultaErro(f"{caminho.name} [{nome}]: {e}") from e
        saida.append(Resultado(nome, caminho.name, df))
    return saida


def para_csv(df: pd.DataFrame) -> str:
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].round(6) + 0.0          # "+ 0.0" troca -0.0 por 0.0 (ruído de sinal em somas de ponto flutuante)
    return d.to_csv(index=False, lineterminator="\n", float_format="%.6f")


def executar_todas(cfg: Config | None = None, con=None, log: logging.Logger | None = None) -> list[Resultado]:
    cfg = cfg or Config()
    log = log or logging.getLogger("empresax")
    fechar = con is None
    if con is None:
        if not cfg.arquivo_banco.exists():
            raise ConsultaErro(f"Banco não encontrado: {cfg.arquivo_banco}. Rode antes: python scripts/run_etl.py")
        con = duckdb.connect(str(cfg.arquivo_banco), read_only=True)
    try:
        arquivos = sorted(cfg.pasta_analise.glob("[0-9][0-9]_*.sql"))
        if not arquivos:
            raise ConsultaErro(f"Nenhuma análise em {cfg.pasta_analise}")
        resultados: list[Resultado] = []
        for a in arquivos:
            resultados += executar_arquivo(con, a, cfg)
    finally:
        if fechar:
            con.close()
    cfg.pasta_consultas_saida.mkdir(parents=True, exist_ok=True)
    for antigo in cfg.pasta_consultas_saida.glob("*.csv"):
        antigo.unlink()
    for r in resultados:
        texto = para_csv(r.df)
        (cfg.pasta_consultas_saida / f"{r.nome}.csv").write_text(texto, encoding="utf-8", newline="")
        r.sha256 = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        log.info("%-34s %6d linhas | sha256 %s", r.nome, len(r.df), r.sha256[:12])
    return resultados


def gravar_resumo(resultados: list[Resultado], destino: Path) -> None:
    L = ["# Resultados das análises SQL (Etapa 3)", "",
         "Gerado por `scripts/run_queries.py`. Conteúdo determinístico: o hash prova que duas execuções geram o mesmo resultado.", "",
         "| Resultado | Arquivo SQL | Linhas | SHA-256 (CSV) |", "|---|---|---:|---|"]
    L += [f"| `{r.nome}` | {r.arquivo_sql} | {len(r.df)} | `{r.sha256[:16]}…` |" for r in resultados]
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(L) + "\n", encoding="utf-8")
