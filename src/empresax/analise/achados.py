"""Estruturas do relatório: todo achado tem um TIPO explícito."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

OBSERVACAO = "OBSERVAÇÃO"                    # o que os dados mostram (medido)
CONCLUSAO = "CONCLUSÃO ARITMÉTICA"           # decorre das contas, sem interpretação de causa
HIPOTESE = "HIPÓTESE"                        # explicação possível, NÃO comprovada
PROGRAMADO = "PADRÃO PROGRAMADO"             # criado de propósito no gerador sintético (P-id)
TIPOS = (OBSERVACAO, CONCLUSAO, HIPOTESE, PROGRAMADO)


@dataclass
class Achado:
    id: str
    tipo: str
    texto: str

    def __post_init__(self):
        assert self.tipo in TIPOS, self.tipo


@dataclass
class Investigacao:
    id: str
    titulo: str
    pergunta: str
    metodo: str
    achados: list[Achado] = field(default_factory=list)
    tabelas: dict[str, pd.DataFrame] = field(default_factory=dict)
    limitacoes: list[str] = field(default_factory=list)
    recomendacoes: list[str] = field(default_factory=list)       # sempre condicionais ("se... então...")
    proximas: list[str] = field(default_factory=list)
    metricas: dict = field(default_factory=dict)                  # números-chave (usados em testes e gráficos)

    def add(self, tipo: str, texto: str) -> None:
        self.achados.append(Achado(f"{self.id}.{len(self.achados) + 1}", tipo, texto))
