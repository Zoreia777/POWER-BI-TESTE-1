"""Carga dos dados do mart para DataFrames (banco aberto somente para leitura)."""
from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd

from ..config import Config


@dataclass
class Dados:
    vendas: pd.DataFrame          # mart.fact_vendas (mes como Timestamp)
    produtos: pd.DataFrame
    filiais: pd.DataFrame
    canais: pd.DataFrame
    despesas: pd.DataFrame        # fact_despesas + dim_categoria_despesa (grupo_dre, categoria_despesa)
    orcamento: pd.DataFrame       # mart.orcado_vs_realizado_mensal + categoria/departamento
    orc_acum: pd.DataFrame        # mart.orcado_vs_realizado_acumulado
    orc_plano: pd.DataFrame       # mart.fact_orcamento COMPLETO (inclui meses futuros): base do orçamento ANUAL
    clientes: pd.DataFrame
    ultimo_mes: pd.Timestamp

    @property
    def meses(self) -> list[pd.Timestamp]:
        return list(pd.date_range("2024-01-01", self.ultimo_mes, freq="MS"))


def carregar(cfg: Config | None = None, con=None) -> Dados:
    cfg = cfg or Config()
    fechar = con is None
    if con is None:
        con = duckdb.connect(str(cfg.arquivo_banco), read_only=True)
    try:
        q = lambda s: con.execute(s).df()  # noqa: E731
        v = q("SELECT * FROM mart.fact_vendas")
        v["mes"] = pd.to_datetime(v["mes"])
        v["data"] = pd.to_datetime(v["data"])
        d = q("""SELECT f.*, c.categoria_despesa, c.grupo_dre, dp.departamento
                 FROM mart.fact_despesas f JOIN mart.dim_categoria_despesa c USING (id_categoria_despesa)
                 JOIN mart.dim_departamento dp USING (id_departamento)""")
        d["mes"] = pd.to_datetime(d["mes"])
        o = q("""SELECT o.*, c.categoria_despesa, c.grupo_dre, dp.departamento
                 FROM mart.orcado_vs_realizado_mensal o JOIN mart.dim_categoria_despesa c USING (id_categoria_despesa)
                 JOIN mart.dim_departamento dp USING (id_departamento)""")
        o["mes"] = pd.to_datetime(o["mes"])
        a = q("SELECT * FROM mart.orcado_vs_realizado_acumulado")
        a["mes_referencia"] = pd.to_datetime(a["mes_referencia"])
        pl = q("SELECT mes, valor_orcado FROM mart.fact_orcamento")
        pl["mes"] = pd.to_datetime(pl["mes"])
        ultimo = pd.Timestamp(q("SELECT ultimo_mes_realizado u FROM mart.periodo_realizado").u.iloc[0])
        return Dados(v, q("SELECT * FROM mart.dim_produto"), q("SELECT * FROM mart.dim_filial"), q("SELECT * FROM mart.dim_canal"),
                     d, o, a, pl, q("SELECT id_cliente, segmento FROM mart.dim_cliente"), ultimo)
    finally:
        if fechar:
            con.close()
