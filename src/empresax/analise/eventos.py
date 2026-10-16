"""Eventos PROGRAMADOS no gerador que têm janela de tempo e escopo (ver mart.ref_comportamentos_sinteticos).
Usados só para ROTULAR coincidências; nunca para afirmar causa em dado real."""
import pandas as pd

T = pd.Timestamp
# (id, descrição, id_filial|None, id_produto|None, início, fim, sentido)
EVENTOS = [
    ("P09", "Ruptura de estoque do Notebook Pro 14", None, 1, T("2025-08-01"), T("2025-08-01"), "queda"),
    ("P10", "Concorrente em Porto Alegre (-18%)", 5, None, T("2025-06-01"), T("2025-08-01"), "queda"),
    ("P10", "Chuvas no Rio de Janeiro (-22%)", 2, None, T("2025-03-01"), T("2025-03-01"), "queda"),
    ("P10", "Contrato público em Brasília (+18%)", 6, None, T("2026-03-01"), T("2026-06-01"), "alta"),
    ("P11", "Rampa de vendas da filial nova (Recife)", 8, None, T("2024-06-01"), T("2025-05-01"), "alta"),
    ("P11", "Rampa de vendas da filial nova (Salvador)", 7, None, T("2025-02-01"), T("2026-01-01"), "alta"),
]


def rotular(mes, id_filial=None, id_produto=None) -> str:
    """Eventos programados cuja janela contém `mes` e cujo escopo bate; '' se nenhum."""
    achou = []
    for eid, desc, f, p, ini, fim, _ in EVENTOS:
        if ini <= mes <= fim and (f is None or f == id_filial) and (p is None or p == id_produto) \
                and (f is not None or p is not None):
            achou.append(f"{eid}: {desc}")
    return "; ".join(achou)
