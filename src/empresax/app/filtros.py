"""Filtros do aplicativo: validação estrita e geração de SQL PARAMETRIZADO (nenhum valor do usuário entra no texto do SQL)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

PRIMEIRO_MES = date(2024, 1, 1)


class FiltroInvalido(ValueError):
    pass


def _mes(d) -> date:
    if not isinstance(d, date) or hasattr(d, "hour"):
        raise FiltroInvalido(f"data inválida: {d!r}")
    return d.replace(day=1)


def _ids(valores, nome) -> tuple[int, ...]:
    out = []
    for x in valores:
        if isinstance(x, bool) or not isinstance(x, int):
            raise FiltroInvalido(f"{nome}: identificador inválido {x!r} (esperado inteiro)")
        out.append(int(x))
    return tuple(sorted(set(out)))


@dataclass(frozen=True)
class Filtros:
    """Período (1º dia dos meses, inclusive) + seleção de filiais/produtos/canais. Tupla vazia = TODOS."""

    inicio: date
    fim: date
    filiais: tuple = ()
    produtos: tuple = ()
    canais: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "inicio", _mes(self.inicio))
        object.__setattr__(self, "fim", _mes(self.fim))
        object.__setattr__(self, "filiais", _ids(self.filiais, "filiais"))
        object.__setattr__(self, "produtos", _ids(self.produtos, "produtos"))
        object.__setattr__(self, "canais", _ids(self.canais, "canais"))
        if self.inicio > self.fim:
            raise FiltroInvalido("o mês inicial é posterior ao mês final")

    def validar(self, ultimo_mes: date, primeiro_mes: date = PRIMEIRO_MES, ids_validos: dict | None = None) -> "Filtros":
        """Garante: período dentro dos meses REALIZADOS (nunca meses futuros) e ids existentes nas dimensões."""
        if self.inicio < primeiro_mes or self.fim > ultimo_mes:
            raise FiltroInvalido(f"período fora dos meses realizados ({primeiro_mes:%m/%Y} a {ultimo_mes:%m/%Y})")
        for nome, dados in (ids_validos or {}).items():
            desconhecidos = set(getattr(self, nome)) - set(dados)
            if desconhecidos:
                raise FiltroInvalido(f"{nome}: identificadores inexistentes {sorted(desconhecidos)}")
        return self

    @property
    def tem_produto_ou_canal(self) -> bool:
        return bool(self.produtos or self.canais)

    @property
    def n_meses(self) -> int:
        return (self.fim.year - self.inicio.year) * 12 + self.fim.month - self.inicio.month + 1

    def deslocado(self, meses: int) -> "Filtros":
        """Mesmo recorte, período deslocado (ex.: -12 = período equivalente do ano anterior)."""
        def d(x):
            t = x.year * 12 + x.month - 1 + meses
            return date(t // 12, t % 12 + 1, 1)
        return replace(self, inicio=d(self.inicio), fim=d(self.fim))

    def sql(self, col_mes="mes", col_filial="id_filial", col_produto="id_produto", col_canal="id_canal", periodo=True):
        """(texto, parâmetros). Só aparecem colunas fixas no texto; os valores vão como parâmetros."""
        partes, par = [], []
        if periodo:
            partes.append(f"{col_mes} BETWEEN ? AND ?")
            par += [self.inicio, self.fim]
        for sel, col in ((self.filiais, col_filial), (self.produtos, col_produto), (self.canais, col_canal)):
            if sel and col:
                partes.append(f"list_contains(?, {col})")
                par.append(list(sel))
        return (" AND ".join(partes) or "TRUE"), par
