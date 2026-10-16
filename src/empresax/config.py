"""Configuração centralizada do pipeline ETL da Empresa X.

Tudo que muda de um ambiente para outro (pastas, nome do banco, política de
devoluções) fica aqui. Os caminhos são sempre relativos à raiz do repositório,
descoberta a partir da localização deste arquivo, então o pipeline roda igual
em qualquer máquina (inclusive Windows).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Política de tratamento das devoluções (status = 'Devolvido').
# A evidência disponível NÃO permite determinar o tratamento contábil correto
# (ver docs/DEVOLUCOES.md). Enquanto o negócio não decidir, os KPIs expõem os
# três componentes separados e a "receita reconhecida" é PROVISÓRIA.
POLITICA_DEVOLUCAO = "PROVISORIA_EXCLUI_DEVOLVIDAS"
DESCRICAO_POLITICA_DEVOLUCAO = (
    "PROVISÓRIA: receita reconhecida = vendas com status 'Entregue'. Convenção herdada de "
    "sql/views.sql, sem confirmação contábil. Decisão de negócio pendente (docs/DEVOLUCOES.md)."
)


@dataclass(frozen=True)
class Config:
    """Caminhos e parâmetros de uma execução. Os testes criam instâncias com pastas temporárias."""

    pasta_dados: Path = RAIZ / "data"
    arquivo_banco: Path = RAIZ / "warehouse" / "empresa_x.duckdb"
    pasta_sql: Path = RAIZ / "sql" / "etl" / "mart"
    pasta_logs: Path = RAIZ / "logs"
    pasta_relatorios: Path = RAIZ / "reports"
    # Tolerância (R$) usada nas reconciliações de arredondamento por linha.
    tolerancia_rs: float = 0.02
    # ---- Etapa 3: parâmetros das análises SQL (substituem {PLACEHOLDERS} em sql/analise/*.sql)
    pasta_analise: Path = RAIZ / "sql" / "analise"
    pasta_consultas_saida: Path = RAIZ / "reports" / "consultas"
    limiar_queda_mom: float = -0.15      # queda mês a mês: variação <= -15%
    limiar_queda_yoy: float = -0.10      # queda ano a ano: variação <= -10%
    piso_linhas_margem: int = 200        # mínimo de linhas ENTREGUES para entrar no ranking de margem; 0 = todos
    tolerancia_orcamento_pct: float = 0.05   # faixa "dentro do orçado": execução entre 95% e 105%
    # ---- Etapa 4: investigação analítica (Python)
    pasta_executivo: Path = RAIZ / "reports" / "executivo"
    queda_persistente_meses: int = 3     # queda YoY em >= N meses consecutivos é considerada "persistente"
    politica_devolucao: str = field(default=POLITICA_DEVOLUCAO)
