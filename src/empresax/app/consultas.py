"""Consultas do aplicativo sobre as views `bi` (conexão somente leitura, SQL parametrizado).

Regras de negócio preservadas (PN-DEV-01..03): receita ajustada = vendas entregues; registrada = entregues + devoluções;
devoluções ficam no mês da venda (não existe data de devolução); custo devolvido tratado como recuperado (hipótese).
Razões são sempre razão de somas; denominador zero → None (nunca 0% nem infinito).
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from ..analise import pvm
from .filtros import Filtros, FiltroInvalido  # noqa: F401  (reexport)

_SENT_ATUAL, _SENT_BASE = pd.Timestamp("2100-01-01"), pd.Timestamp("2099-01-01")


def razao(a, b):
    """a/b com None quando faltar dado ou o denominador for 0."""
    if a is None or b is None:
        return None
    try:
        if pd.isna(a) or pd.isna(b) or float(b) == 0:
            return None
    except (TypeError, ValueError):
        return None
    return float(a) / float(b)


def _f(x):
    return 0.0 if x is None else float(x)


def _d(x) -> date:
    return x.date() if hasattr(x, "date") else x


class Repositorio:
    """Consultas de leitura. Cada chamada usa um cursor próprio (seguro para várias sessões do Streamlit)."""

    def __init__(self, con):
        self.con = con
        q = lambda s: self._q(s)  # noqa: E731
        self.filiais = q("SELECT id_filial, filial, tipo FROM bi.dim_filial ORDER BY id_filial")
        self.produtos = q("SELECT id_produto, produto, categoria FROM bi.dim_produto ORDER BY categoria, produto")
        self.canais = q("SELECT id_canal, canal FROM bi.dim_canal ORDER BY id_canal")
        self.ultimo_mes: date = _d(self.con.cursor().execute("SELECT max(primeiro_dia_mes) FROM bi.dim_calendario WHERE realizado = 1").fetchone()[0])
        self.primeiro_mes: date = _d(self.con.cursor().execute("SELECT min(mes) FROM bi.fato_vendas").fetchone()[0])
        self.meses: list[date] = [_d(x) for x in pd.date_range(self.primeiro_mes, self.ultimo_mes, freq="MS")]

    # ------------------------------------------------------------------ infraestrutura
    def _q(self, sql: str, par=None) -> pd.DataFrame:
        cur = self.con.cursor()
        try:
            return cur.execute(sql, par or []).df()
        finally:
            cur.close()

    def validar(self, f: Filtros) -> Filtros:
        return f.validar(self.ultimo_mes, self.primeiro_mes, {"filiais": self.filiais.id_filial, "produtos": self.produtos.id_produto, "canais": self.canais.id_canal})

    def fonte(self) -> dict:
        """Metadados exibidos no rodapé: período dos dados e última execução bem-sucedida do ETL."""
        ex = None
        try:
            r = self.con.cursor().execute("SELECT finalizado_em FROM ops.execucoes WHERE status = 'SUCESSO' ORDER BY finalizado_em DESC LIMIT 1").fetchone()
            ex = r[0] if r else None
        except Exception:  # noqa: BLE001 — metadado opcional
            ex = None
        return dict(primeiro_mes=self.primeiro_mes, ultimo_mes=self.ultimo_mes, ultima_carga=ex)

    # ------------------------------------------------------------------ indicadores
    def kpis(self, f: Filtros) -> dict:
        f = self.validar(f)
        w, p = f.sql()
        r = self.con.cursor().execute(f"""
            SELECT count(*), count(DISTINCT id_pedido),
                   sum(receita_registrada), sum(receita_registrada) FILTER (WHERE status = 'Entregue'), sum(devolucao), sum(receita_ajustada),
                   sum(custo_ajustado), sum(unidades_entregues), sum(quantidade), sum(receita_bruta), sum(desconto_valor), sum(flag_margem_negativa)
            FROM bi.fato_vendas WHERE {w}""", p).fetchone()
        linhas = int(r[0])
        reg, ent, dev, aj, cus, un, qtd, bru, desc, neg = (_f(x) for x in r[2:])
        k = dict(vazio=linhas == 0, linhas=linhas, pedidos=int(r[1]), registrada=reg, entregues=ent, devolucoes=dev, ajustada=aj, custo_ajustado=cus,
                 unidades_entregues=un, quantidade=qtd, bruta=bru, desconto=desc, linhas_negativas=int(neg))
        k["diferenca_reconciliacao"] = round(reg - ent - dev, 2)
        k["lucro_bruto"] = aj - cus
        k["margem_bruta"] = razao(aj - cus, aj)
        k["taxa_devolucao"] = razao(dev, reg)
        k["ticket_pedido"] = razao(aj, k["pedidos"])
        k["receita_por_linha"] = razao(aj, linhas)
        k["desconto_efetivo"] = razao(desc, bru)
        k["pct_linhas_negativas"] = razao(neg, linhas)
        k["preco_bruto_medio"] = razao(bru, qtd)
        return k

    def despesas(self, f: Filtros, kp: dict | None = None) -> dict | None:
        """None quando o corte inclui produto/canal (despesas não têm esses vínculos): evita um número enganoso."""
        f = self.validar(f)
        if f.tem_produto_ou_canal:
            return None
        w, p = f.sql(col_produto=None, col_canal=None)
        total = _f(self.con.cursor().execute(f"SELECT sum(valor) FROM bi.fato_despesas WHERE {w}", p).fetchone()[0])
        kp = kp or self.kpis(f)
        out = dict(total=total, pct_receita=razao(total, kp["ajustada"]), resultado=None, margem_operacional=None)
        if not kp["vazio"]:
            out["resultado"] = kp["lucro_bruto"] - total
            out["margem_operacional"] = razao(out["resultado"], kp["ajustada"])
        return out

    def comparacao_anual(self, f: Filtros) -> dict:
        """Período equivalente do ano anterior (mesmos meses, mesmos filtros). Sem base ou base zero → indisponível, com o motivo."""
        base_f = f.deslocado(-12)
        if base_f.inicio < self.primeiro_mes:
            return dict(disponivel=False, motivo="O período equivalente do ano anterior começa antes de jan/2024 (início dos dados).")
        k0, k1 = self.kpis(base_f), self.kpis(f)
        if k0["vazio"] or k0["ajustada"] == 0:
            return dict(disponivel=False, motivo="Não há vendas no período equivalente do ano anterior para este recorte (base zerada: não é crescimento nem queda).")
        return dict(disponivel=True, base=k0["ajustada"], atual=k1["ajustada"], variacao=k1["ajustada"] / k0["ajustada"] - 1,
                    margem_base=k0["margem_bruta"], margem_atual=k1["margem_bruta"], periodo_base=(base_f.inicio, base_f.fim))

    # ------------------------------------------------------------------ séries e recortes
    def serie_mensal(self, f: Filtros) -> pd.DataFrame:
        f = self.validar(f)
        w, p = f.sql()
        df = self._q(f"""SELECT mes, sum(receita_registrada) AS registrada, sum(receita_ajustada) AS ajustada, sum(devolucao) AS devolucoes,
                                sum(custo_ajustado) AS custo_ajustado, count(*) AS linhas, count(DISTINCT id_pedido) AS pedidos, sum(unidades_entregues) AS unidades
                         FROM bi.fato_vendas WHERE {w} GROUP BY mes ORDER BY mes""", p)
        df["mes"] = pd.to_datetime(df["mes"])
        df["lucro_bruto"] = df.ajustada - df.custo_ajustado
        df["margem_bruta"] = df.lucro_bruto / df.ajustada.where(df.ajustada != 0)
        return df

    def serie_despesas(self, f: Filtros) -> pd.DataFrame | None:
        f = self.validar(f)
        if f.tem_produto_ou_canal:
            return None
        w, p = f.sql(col_produto=None, col_canal=None)
        df = self._q(f"SELECT mes, sum(valor) AS despesas FROM bi.fato_despesas WHERE {w} GROUP BY mes ORDER BY mes", p)
        df["mes"] = pd.to_datetime(df["mes"])
        return df

    _DIM = {"filial": ("id_filial", "bi.dim_filial", "filial"), "produto": ("id_produto", "bi.dim_produto", "produto"),
            "canal": ("id_canal", "bi.dim_canal", "canal"), "categoria": ("id_produto", "bi.dim_produto", "categoria")}

    def por_dimensao(self, f: Filtros, dim: str) -> pd.DataFrame:
        """Indicadores por filial/produto/canal/categoria no período, já com a variação anual (período equivalente) quando existe base."""
        f = self.validar(f)
        chave, tabela, nome = self._DIM[dim]
        grupo = "d.categoria" if dim == "categoria" else f"d.{chave}, d.{nome}"
        sel = "d.categoria AS nome" if dim == "categoria" else f"d.{chave} AS chave, d.{nome} AS nome"

        def agreg(ff: Filtros) -> pd.DataFrame:
            w, p = ff.sql(col_mes="v.mes", col_filial="v.id_filial", col_produto="v.id_produto", col_canal="v.id_canal")
            return self._q(f"""SELECT {sel}, sum(v.receita_registrada) AS registrada, sum(v.receita_ajustada) AS ajustada, sum(v.devolucao) AS devolucoes,
                                      sum(v.custo_ajustado) AS custo_ajustado, count(*) AS linhas, count(DISTINCT v.id_pedido) AS pedidos,
                                      sum(v.unidades_entregues) AS unidades, sum(v.flag_margem_negativa) AS linhas_negativas,
                                      sum(v.desconto_valor) AS desconto, sum(v.receita_bruta) AS bruta
                               FROM bi.fato_vendas v JOIN {tabela} d USING ({chave}) WHERE {w} GROUP BY {grupo}""", p)
        a = agreg(f)
        a["lucro_bruto"] = a.ajustada - a.custo_ajustado
        a["margem_bruta"] = a.lucro_bruto / a.ajustada.where(a.ajustada != 0)
        a["taxa_devolucao"] = a.devolucoes / a.registrada.where(a.registrada != 0)
        a["pct_linhas_negativas"] = a.linhas_negativas / a.linhas.where(a.linhas != 0)
        a["desconto_efetivo"] = a.desconto / a.bruta.where(a.bruta != 0)
        a["participacao"] = a.ajustada / a.ajustada.sum() if a.ajustada.sum() else float("nan")
        base_f = f.deslocado(-12)
        a["base_ano_anterior"] = float("nan")
        a["yoy"] = float("nan")
        if base_f.inicio >= self.primeiro_mes:
            b = agreg(base_f)
            k = "nome" if dim == "categoria" else "chave"
            m = b.set_index(k).ajustada
            a["base_ano_anterior"] = a[k].map(m)
            ok = a.base_ano_anterior.notna() & (a.base_ano_anterior != 0)
            a.loc[ok, "yoy"] = a.ajustada[ok] / a.base_ano_anterior[ok] - 1
        return a.sort_values("ajustada", ascending=False).reset_index(drop=True)

    def despesas_por_filial(self, f: Filtros) -> pd.DataFrame | None:
        f = self.validar(f)
        if f.tem_produto_ou_canal:
            return None
        w, p = f.sql(col_mes="x.mes", col_filial="x.id_filial", col_produto=None, col_canal=None)
        return self._q(f"""SELECT d.filial AS nome, sum(x.valor) AS despesas FROM bi.fato_despesas x JOIN bi.dim_filial d USING (id_filial)
                           WHERE {w} GROUP BY d.filial""", p)

    def matriz_yoy_filial(self, f: Filtros) -> pd.DataFrame:
        """Filial × mês: variação anual da receita ajustada (vazio onde não há base comparável)."""
        f = self.validar(f)
        w, p = f.sql(periodo=False, col_filial="id_filial", col_produto="id_produto", col_canal="id_canal")
        df = self._q(f"""SELECT d.filial, v.mes, sum(v.receita_ajustada) AS r FROM bi.fato_vendas v JOIN bi.dim_filial d USING (id_filial)
                         WHERE {w} GROUP BY d.filial, v.mes""".replace("TRUE", "TRUE"), p)
        df["mes"] = pd.to_datetime(df["mes"])
        piv = df.pivot(index="filial", columns="mes", values="r").reindex(columns=pd.to_datetime(self.meses))
        yoy = piv / piv.shift(12, axis=1).where(piv.shift(12, axis=1) > 0) - 1
        cols = [c for c in yoy.columns if pd.Timestamp(f.inicio) <= c <= pd.Timestamp(f.fim)]
        return yoy[cols].dropna(how="all")

    # ------------------------------------------------------------------ orçamento
    def orcamento(self, f: Filtros) -> dict:
        """Orçado × realizado. Orçamento só tem filial: produto/canal NÃO se aplicam (avisado na página)."""
        f = self.validar(f)
        w, p = f.sql(col_filial="o.id_filial", col_mes="o.mes", col_produto=None, col_canal=None)
        r = self.con.cursor().execute(f"SELECT sum(o.orcado), sum(o.realizado) FROM bi.fato_orcado_realizado_mes o WHERE {w}", p).fetchone()
        orc_acum, real = _f(r[0]), _f(r[1])
        wf, pf = f.sql(periodo=False, col_produto=None, col_canal=None)
        anual = _f(self.con.cursor().execute(f"SELECT sum(valor_orcado) FROM bi.fato_orcamento WHERE {wf} AND year(mes) BETWEEN ? AND ?", pf + [f.inicio.year, f.fim.year]).fetchone()[0])
        return dict(orcado_acumulado=orc_acum, realizado=real, orcado_anual=anual, execucao=razao(real, orc_acum), consumo_anual=razao(real, anual),
                    desvio=real - orc_acum, vazio=orc_acum == 0 and real == 0)

    def orcamento_por(self, f: Filtros, dim: str) -> pd.DataFrame:
        f = self.validar(f)
        tabela, chave, nome = {"departamento": ("bi.dim_departamento", "id_departamento", "departamento"),
                               "categoria": ("bi.dim_categoria_despesa", "id_categoria_despesa", "categoria_despesa")}[dim]
        w, p = f.sql(col_filial="o.id_filial", col_mes="o.mes", col_produto=None, col_canal=None)
        df = self._q(f"""SELECT d.{nome} AS nome, sum(o.orcado) AS orcado, sum(o.realizado) AS realizado
                         FROM bi.fato_orcado_realizado_mes o JOIN {tabela} d USING ({chave}) WHERE {w} GROUP BY d.{nome}""", p)
        df["execucao"] = df.realizado / df.orcado.where(df.orcado != 0)
        df["desvio"] = df.realizado - df.orcado
        return df.sort_values("desvio", ascending=False).reset_index(drop=True)

    def orcamento_mensal(self, f: Filtros) -> pd.DataFrame:
        f = self.validar(f)
        w, p = f.sql(col_filial="o.id_filial", col_mes="o.mes", col_produto=None, col_canal=None)
        df = self._q(f"SELECT o.mes, sum(o.orcado) AS orcado, sum(o.realizado) AS realizado FROM bi.fato_orcado_realizado_mes o WHERE {w} GROUP BY o.mes ORDER BY o.mes", p)
        df["mes"] = pd.to_datetime(df["mes"])
        return df

    # ------------------------------------------------------------------ preço × volume × mix
    def pvm_periodo(self, atual: Filtros, base: Filtros) -> tuple[dict, pd.DataFrame]:
        """Decomposição entre dois PERÍODOS (cada um agregado por produto; mesma metodologia de docs/METODOLOGIA_DECOMPOSICAO.md).
        `atual` e `base` devem ter o mesmo recorte (filiais/produtos/canais); só o período muda."""
        atual, base = self.validar(atual), self.validar(base)
        if (atual.filiais, atual.produtos, atual.canais) != (base.filiais, base.produtos, base.canais):
            raise FiltroInvalido("atual e base precisam ter o mesmo recorte de filial/produto/canal")
        linhas = []
        for fl, sent in ((atual, _SENT_ATUAL), (base, _SENT_BASE)):
            w, p = fl.sql()
            df = self._q(f"""SELECT id_produto, sum(quantidade) AS quantidade, sum(receita_bruta) AS receita_bruta, sum(desconto_valor) AS desconto_valor,
                                    sum(impostos_valor) AS impostos_valor, sum(devolucao) AS receita_liquida_devolvida
                             FROM bi.fato_vendas WHERE {w} GROUP BY id_produto""", p)
            df["mes"] = sent
            linhas.append(df)
        v = pd.concat(linhas, ignore_index=True)
        for c in ("quantidade", "receita_bruta", "desconto_valor", "impostos_valor", "receita_liquida_devolvida"):
            v[c] = v[c].astype(float)
        resumo, por = pvm.decompor(v, _SENT_ATUAL, _SENT_BASE)
        resumo["ajustada_base"] = resumo["receita_base"] - float(v[v.mes == _SENT_BASE].receita_liquida_devolvida.sum())
        resumo["ajustada_atual"] = resumo["receita_atual"] - float(v[v.mes == _SENT_ATUAL].receita_liquida_devolvida.sum())
        nomes = self.produtos.set_index("id_produto").produto
        por = por.assign(produto=por.index.map(nomes))
        return resumo, por.reset_index(drop=True)
