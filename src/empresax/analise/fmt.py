"""Formatação pt-BR dos números que aparecem nos textos do relatório."""
from __future__ import annotations


def _sep(s: str) -> str:
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def brl(x: float, casas: int = 0) -> str:
    sinal = "-" if x < 0 else ""
    return f"{sinal}R$ {_sep(f'{abs(x):,.{casas}f}')}"


def mil(x: float) -> str:
    """R$ em milhares (ex.: R$ 171,9 mil) ou milhões."""
    a = abs(x)
    s = "-" if x < 0 else ""
    if a >= 1e6:
        return f"{s}R$ {_sep(f'{a / 1e6:,.2f}')} mi"
    return f"{s}R$ {_sep(f'{a / 1e3:,.1f}')} mil"


def pct(x: float, casas: int = 1) -> str:
    return f"{_sep(f'{x * 100:,.{casas}f}')}%"


def var(x: float, casas: int = 1) -> str:
    """Variação percentual SEMPRE com sinal (+2,9% / -6,6%)."""
    return f"{'+' if x >= 0 else '-'}{_sep(f'{abs(x) * 100:,.{casas}f}')}%"


def pp(x: float, casas: int = 1) -> str:
    return f"{'+' if x >= 0 else '-'}{_sep(f'{abs(x) * 100:,.{casas}f}')} p.p."


def num(x: float, casas: int = 0) -> str:
    s = f"{x:,.{casas}f}"
    if float(s.replace(",", "")) == 0:
        s = s.lstrip("-")
    return _sep(s)


def mes(ts) -> str:
    nomes = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    return f"{nomes[ts.month - 1]}/{str(ts.year)[2:]}"
