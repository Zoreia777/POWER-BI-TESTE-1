#!/usr/bin/env python3
"""Etapa 4 — camada de consumo do Power BI: cria as views `bi`, exporta CSVs e gera valores de referência + documentação.

    python scripts/run_etl.py && python scripts/run_powerbi.py

Gera: powerbi/dados/*.csv (git-ignorado), powerbi/referencia/{valores_referencia,dicionario_indicadores,contrato_views}.csv e
docs/POWERBI_CAMADA_DE_CONSUMO.md, docs/POWERBI_ROTEIRO_DE_CONSTRUCAO.md e powerbi/referencia/checklist_validacao.csv. NENHUMA medida DAX é executada aqui.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import duckdb  # noqa: E402
import pandas as pd  # noqa: E402

from empresax import powerbi as P  # noqa: E402
from empresax.config import RAIZ, Config  # noqa: E402
from empresax.consultas import para_csv  # noqa: E402
from empresax.powerbi_doc import gerar_documento, gerar_roteiro, tabela_checklist  # noqa: E402

if __name__ == "__main__":
    cfg = Config()
    erros = P.lint_dax()
    if erros:
        sys.exit("Lint DAX falhou:\n" + "\n".join(erros))
    if not cfg.arquivo_banco.exists():
        sys.exit(f"Banco não encontrado: {cfg.arquivo_banco}. Rode antes: python scripts/run_etl.py")
    con = duckdb.connect(str(cfg.arquivo_banco))
    try:
        views = P.criar_views(con)
        n = P.exportar(con, RAIZ / "powerbi" / "dados")
        ref = P.tabela_referencia(lambda c: P.referencia_sql(con, c))
    finally:
        con.close()
    indep = P.tabela_referencia(lambda c: P.referencia_independente(cfg.pasta_dados, c))
    a, b = ref.valor_esperado.fillna(-9e99), indep.valor_esperado.fillna(-9e99)
    if ((a - b).abs() > 0.01).any():
        sys.exit("Divergência entre SQL (views bi) e cálculo independente — não grave valores de referência.")
    saida = RAIZ / "powerbi" / "referencia"
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "valores_referencia.csv").write_text(para_csv(indep), encoding="utf-8", newline="")
    (saida / "dicionario_indicadores.csv").write_text(para_csv(pd.DataFrame(P.INDICADORES)), encoding="utf-8", newline="")
    (saida / "contrato_views.csv").write_text(para_csv(pd.DataFrame([{"view": v, "ordem": i + 1, "coluna": c} for v, cs in P.CONTRATO.items() for i, c in enumerate(cs)])), encoding="utf-8", newline="")
    (saida / "checklist_validacao.csv").write_text(para_csv(tabela_checklist(indep)), encoding="utf-8", newline="")
    (RAIZ / "docs" / "POWERBI_CAMADA_DE_CONSUMO.md").write_text(gerar_documento(indep, n), encoding="utf-8")
    (RAIZ / "docs" / "POWERBI_ROTEIRO_DE_CONSTRUCAO.md").write_text(gerar_roteiro(indep, n), encoding="utf-8")
    print(f"{len(views)} views bi, {sum(n.values())} linhas exportadas, {len(indep)} valores de referência (SQL = independente)")
