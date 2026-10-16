"""Decomposição preço × volume × mix × desconto × imposto em pandas.

Mesma metodologia de docs/METODOLOGIA_DECOMPOSICAO.md e de sql/analise/08_fatores_variacao.sql, mas aplicável a QUALQUER
recorte (filial, canal, categoria…). Os testes conferem esta implementação contra o SQL (empresa inteira) e contra um
oráculo em Python puro, de modo que a versão em pandas e a versão em SQL se validam mutuamente.
"""
from __future__ import annotations

import pandas as pd

EFEITOS = ["volume", "mix", "preco", "desconto", "impostos", "produto_novo", "produto_descontinuado"]


def agregar(v: pd.DataFrame, mes: pd.Timestamp) -> pd.DataFrame:
    """Q, bruta, desconto, imposto e receita registrada por produto num mês."""
    x = v[v["mes"] == mes].groupby("id_produto").agg(
        q=("quantidade", "sum"), b=("receita_bruta", "sum"), d=("desconto_valor", "sum"), i=("impostos_valor", "sum"),
        dev=("receita_liquida_devolvida", "sum"))
    x = x.astype(float)
    x["r"] = x.b - x.d - x.i
    return x


def decompor(v: pd.DataFrame, atual: pd.Timestamp, base: pd.Timestamp) -> tuple[dict, pd.DataFrame]:
    """Devolve (resumo, por_produto). `v` já vem filtrado para o recorte desejado."""
    a1, a0 = agregar(v, atual), agregar(v, base)
    ids = a1.index.union(a0.index)
    a1, a0 = a1.reindex(ids, fill_value=0.0), a0.reindex(ids, fill_value=0.0)
    cont = (a1.q > 0) & (a0.q > 0)
    q0c, q1c = a0.q[cont].sum(), a1.q[cont].sum()
    out = pd.DataFrame(0.0, index=ids, columns=EFEITOS)
    if cont.any():
        c1, c0 = a1[cont], a0[cont]
        P1, P0 = c1.b / c1.q, c0.b / c0.q
        d1, d0 = c1.d / c1.b, c0.d / c0.b
        t1, t0 = c1.i / (c1.b - c1.d), c0.i / (c0.b - c0.d)
        out.loc[cont, "volume"] = (q1c - q0c) * c0.r / q0c
        out.loc[cont, "mix"] = (c1.q - q1c * c0.q / q0c) * (c0.r / c0.q)
        out.loc[cont, "preco"] = c1.q * (P1 - P0) * (1 - d0) * (1 - t0)
        out.loc[cont, "desconto"] = -c1.q * P1 * (d1 - d0) * (1 - t0)
        out.loc[cont, "impostos"] = -c1.q * P1 * (1 - d1) * (t1 - t0)
    novo, desc = (a1.q > 0) & (a0.q == 0), (a0.q > 0) & (a1.q == 0)
    out.loc[novo, "produto_novo"] = a1.r[novo]
    out.loc[desc, "produto_descontinuado"] = -a0.r[desc]
    out["variacao"] = a1.r - a0.r
    out["residuo"] = out["variacao"] - out[EFEITOS].sum(axis=1)
    out["r0"], out["r1"], out["q0"], out["q1"] = a0.r, a1.r, a0.q, a1.q
    resumo = {k: float(out[k].sum()) for k in EFEITOS}
    resumo.update(receita_base=float(a0.r.sum()), receita_atual=float(a1.r.sum()), variacao_registrada=float(out.variacao.sum()),
                  residuo=float(out.residuo.sum()), efeito_devolucoes=-float(a1.dev.sum() - a0.dev.sum()),
                  variacao_ajustada=float(out.variacao.sum() - (a1.dev.sum() - a0.dev.sum())))
    return resumo, out


def serie(v: pd.DataFrame, meses: list[pd.Timestamp], tipo: str = "YoY") -> pd.DataFrame:
    """Decomposição para cada mês com base realizada (MoM = mês anterior; YoY = 12 meses antes)."""
    lag = 1 if tipo == "MoM" else 12
    linhas = []
    conj = set(meses)
    for m in meses:
        b = m - pd.DateOffset(months=lag)
        if b in conj:
            r, _ = decompor(v, m, b)
            linhas.append({"periodo": m, "periodo_base": b, **r})
    return pd.DataFrame(linhas)
