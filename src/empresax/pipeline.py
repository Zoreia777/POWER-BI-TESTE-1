"""Orquestração do ETL: raw -> stg -> mart, tudo em UMA transação.

Idempotência: cada tabela é recriada com CREATE OR REPLACE a partir dos CSVs; rodar duas vezes
com os mesmos arquivos produz exatamente o mesmo conteúdo. Se qualquer etapa falhar, a transação
sofre ROLLBACK e o banco permanece no último estado válido. Só `ops.execucoes` (histórico de
execuções) cresce a cada rodada, por design.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

import duckdb

from . import quality
from .config import Config
from .errors import PipelineErro, QualidadeErro
from .logger import configurar
from .mart import construir_mart
from .raw import carregar_raw
from .staging import construir_staging


@dataclass
class Resultado:
    run_id: str
    checagens: list
    contagens: dict
    arquivo_log: object


def _contagens(con) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for schema, tabela in con.execute(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_schema IN ('raw','stg','mart') AND table_type='BASE TABLE' ORDER BY 1,2").fetchall():
        out.setdefault(schema, {})[tabela] = con.execute(f'SELECT count(*) FROM {schema}."{tabela}"').fetchone()[0]
    return out


def executar(cfg: Config | None = None) -> Resultado:
    cfg = cfg or Config()
    log, arquivo_log = configurar(cfg.pasta_logs)
    cfg.arquivo_banco.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    inicio = datetime.now()
    con = duckdb.connect(str(cfg.arquivo_banco))
    con.execute("CREATE SCHEMA IF NOT EXISTS ops")
    con.execute("CREATE TABLE IF NOT EXISTS ops.execucoes (run_id VARCHAR, iniciado_em TIMESTAMP, finalizado_em TIMESTAMP, "
                "status VARCHAR, mensagem VARCHAR, validacoes_ok INTEGER, validacoes_erro INTEGER)")
    checks: list = []
    contagens: dict = {}
    status, mensagem = "SUCESSO", ""
    log.info("ETL iniciado | run=%s | dados=%s | banco=%s", run_id, cfg.pasta_dados, cfg.arquivo_banco)
    try:
        con.execute("BEGIN TRANSACTION")
        con.execute("CREATE SCHEMA IF NOT EXISTS ops")
        checks += carregar_raw(con, cfg, log)
        checks += construir_staging(con, log)
        checks += quality.checar_staging(con, cfg)
        erros = [c for c in checks if c.status == "ERRO"]
        if erros:
            raise QualidadeErro(f"{len(erros)} validação(ões) obrigatória(s) falharam no staging: "
                                + "; ".join(f"{c.tabela}: {c.regra} (esperado {c.esperado}, obtido {c.obtido})" for c in erros[:5]))
        construir_mart(con, cfg, log)
        checks += quality.checar_mart(con, cfg)
        erros = [c for c in checks if c.status == "ERRO"]
        if erros:
            raise QualidadeErro(f"{len(erros)} validação(ões) obrigatória(s) falharam no mart: "
                                + "; ".join(f"{c.tabela}: {c.regra} (esperado {c.esperado}, obtido {c.obtido})" for c in erros[:5]))
        con.execute("COMMIT")
        contagens = _contagens(con)
    except Exception as e:           # qualquer falha: desfaz tudo e registra
        try:
            con.execute("ROLLBACK")
        except duckdb.Error:
            pass
        status, mensagem = "FALHA", f"{type(e).__name__}: {e}"
        log.error("ETL falhou (rollback aplicado): %s", mensagem)
        contagens = _contagens(con)
        raise_depois = e
    else:
        raise_depois = None
    # persistência de auditoria (fora da transação principal)
    con.execute("CREATE OR REPLACE TABLE ops.qualidade_checks (camada VARCHAR, tabela VARCHAR, regra VARCHAR, esperado VARCHAR, obtido VARCHAR, status VARCHAR)")
    if checks:      # falhas muito cedo (arquivo ausente, cabeçalho inválido) ainda não produzem validações
        con.executemany("INSERT INTO ops.qualidade_checks VALUES (?,?,?,?,?,?)",
                        [[c.camada, c.tabela, c.regra, str(c.esperado), str(c.obtido), c.status] for c in checks])
    con.execute("INSERT INTO ops.execucoes VALUES (?,?,?,?,?,?,?)",
                [run_id, inicio, datetime.now(), status, mensagem,
                 sum(c.status == "OK" for c in checks), sum(c.status == "ERRO" for c in checks)])
    quality.gravar_relatorio(checks, contagens, cfg.pasta_relatorios / "relatorio_qualidade.md", cfg)
    con.close()
    log.info("ETL %s | validações OK=%d erro=%d | log=%s", status, sum(c.status == "OK" for c in checks),
             sum(c.status == "ERRO" for c in checks), arquivo_log.name)
    if raise_depois is not None:
        if isinstance(raise_depois, PipelineErro):
            raise raise_depois
        raise PipelineErro(f"Falha inesperada: {raise_depois}") from raise_depois
    return Resultado(run_id, checks, contagens, arquivo_log)
