"""Estudos de caso do aplicativo (Porto Alegre e Smartphone X Max), calculados sobre as views `bi`.

Escopo FIXO: não dependem dos filtros da barra lateral (o recorte faz parte do caso). Atividade (pedidos, linhas, unidades) usa
todas as linhas, como na investigação INV1; receita usa a receita ajustada provisória (PN-DEV-01).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from ..config import RAIZ
from .consultas import Repositorio, razao
from .filtros import Filtros

FILIAL_CASO = "Porto Alegre"
PRODUTO_CASO = "Smartphone X Max"
PASTA_EVIDENCIAS = RAIZ / "reports" / "executivo" / "evidencias"


def _id(df, col_id, col_nome, nome) -> int:
    x = df.loc[df[col_nome] == nome, col_id]
    if x.empty:
        raise LookupError(f"{nome!r} não existe no cadastro")
    return int(x.iloc[0])


def porto_alegre_serie(repo: Repositorio) -> pd.DataFrame:
    fid = _id(repo.filiais, "id_filial", "filial", FILIAL_CASO)
    df = repo._q("""SELECT mes, sum(receita_ajustada) AS ajustada, count(DISTINCT id_pedido) AS pedidos, count(*) AS linhas, sum(quantidade) AS unidades
                    FROM bi.fato_vendas WHERE id_filial = ? GROUP BY mes ORDER BY mes""", [fid])
    df["mes"] = pd.to_datetime(df["mes"])
    df = df.set_index("mes").reindex(pd.to_datetime(repo.meses)).rename_axis("mes")
    df["receita_por_linha"] = df.ajustada / df.linhas.where(df.linhas != 0)
    df["yoy"] = df.ajustada / df.ajustada.shift(12).where(df.ajustada.shift(12) > 0) - 1
    return df.reset_index()


def porto_alegre_comparacao(repo: Repositorio, mes: date) -> pd.DataFrame | None:
    """Mês × mesmo mês do ano anterior: separa quantas ordens, quantas linhas e quanto vale cada linha. None sem base."""
    s = porto_alegre_serie(repo).set_index("mes")
    atual, base = pd.Timestamp(mes), pd.Timestamp(mes) - pd.DateOffset(years=1)
    if base not in s.index or pd.isna(s.loc[base, "linhas"]) or s.loc[base, "linhas"] == 0:
        return None
    linhas = []
    for nome, col in (("Receita ajustada", "ajustada"), ("Pedidos", "pedidos"), ("Linhas de pedido", "linhas"), ("Unidades", "unidades"), ("Receita por linha", "receita_por_linha")):
        b, a = float(s.loc[base, col]), float(s.loc[atual, col])
        linhas.append(dict(metrica=nome, base=b, atual=a, variacao=razao(a - b, b)))
    return pd.DataFrame(linhas)


def porto_alegre_pvm(repo: Repositorio, mes: date):
    fid = _id(repo.filiais, "id_filial", "filial", FILIAL_CASO)
    return repo.pvm_periodo(Filtros(mes, mes, (fid,)), Filtros(mes, mes, (fid,)).deslocado(-12))


def porto_alegre_concentracao(repo: Repositorio, mes: date, topn: int = 5) -> dict:
    """Quanto da receita do mês vem das N maiores linhas e do maior cliente (concentração da base)."""
    fid = _id(repo.filiais, "id_filial", "filial", FILIAL_CASO)
    d = repo._q("SELECT id_cliente, receita_ajustada AS r FROM bi.fato_vendas WHERE id_filial = ? AND mes = ?", [fid, mes])
    tot = float(d.r.sum())
    if d.empty or tot == 0:
        return dict(disponivel=False)
    top = float(d.r.nlargest(topn).sum())
    cli = d.groupby("id_cliente").r.sum().sort_values(ascending=False)
    return dict(disponivel=True, receita=tot, topn=topn, share_top_linhas=top / tot, maior_cliente=int(cli.index[0]), share_maior_cliente=float(cli.iloc[0]) / tot)


def smartphone_serie(repo: Repositorio) -> pd.DataFrame:
    pid = _id(repo.produtos, "id_produto", "produto", PRODUTO_CASO)
    df = repo._q("""SELECT mes, count(*) AS linhas, sum(flag_margem_negativa) AS linhas_negativas, sum(quantidade) AS unidades,
                           sum(receita_bruta) AS bruta, sum(receita_registrada) AS liquida, sum(custo_registrado) AS custo
                    FROM bi.fato_vendas WHERE id_produto = ? GROUP BY mes ORDER BY mes""", [pid])
    df["mes"] = pd.to_datetime(df["mes"])
    df["preco_bruto_un"] = df.bruta / df.unidades
    df["preco_liquido_un"] = df.liquida / df.unidades
    df["custo_un"] = df.custo / df.unidades
    df["margem_bruta"] = 1 - df.custo / df.liquida
    df["pct_linhas_negativas"] = df.linhas_negativas / df.linhas
    return df


def smartphone_resumo(repo: Repositorio) -> dict:
    s = smartphone_serie(repo)
    pid = _id(repo.produtos, "id_produto", "produto", PRODUTO_CASO)
    tot = repo._q("SELECT sum(flag_margem_negativa) AS n FROM bi.fato_vendas").n.iloc[0]
    primeiro_neg = s.loc[s.linhas_negativas > 0, "mes"]
    cem = s.loc[s.pct_linhas_negativas == 1, "mes"]
    return dict(preco_ini=float(s.preco_bruto_un.iloc[0]), preco_fim=float(s.preco_bruto_un.iloc[-1]), custo_ini=float(s.custo_un.iloc[0]), custo_fim=float(s.custo_un.iloc[-1]),
                margem_ini=float(s.margem_bruta.iloc[0]), margem_fim=float(s.margem_bruta.iloc[-1]), linhas_neg=int(s.linhas_negativas.sum()), linhas_neg_empresa=int(tot),
                primeira_negativa=primeiro_neg.iloc[0] if len(primeiro_neg) else None, cem_por_cento_desde=cem.iloc[0] if len(cem) else None,
                variacao_custo=float(s.custo_un.iloc[-1] / s.custo_un.iloc[0] - 1), variacao_preco=float(s.preco_bruto_un.iloc[-1] / s.preco_bruto_un.iloc[0] - 1), id_produto=pid)


def smartphone_preco_para_margem(repo: Repositorio, margem_alvo: float) -> dict | None:
    """Conta aritmética (NÃO é recomendação de preço): preço bruto por unidade para atingir a margem-alvo no ÚLTIMO mês, mantendo
    desconto efetivo e imposto efetivo observados e o custo por unidade. Ignora elasticidade (efeito do preço sobre a quantidade)."""
    s = smartphone_serie(repo).iloc[-1]
    pid = _id(repo.produtos, "id_produto", "produto", PRODUTO_CASO)
    r = repo.con.cursor().execute("SELECT sum(receita_bruta), sum(desconto_valor), sum(impostos_valor) FROM bi.fato_vendas WHERE id_produto = ? AND mes = ?", [pid, s.mes.date()]).fetchone()
    bruta, desc, imp = (float(x) for x in r)
    d_ef, t_ef = desc / bruta, imp / (bruta - desc)
    fator = (1 - d_ef) * (1 - t_ef) * (1 - margem_alvo)
    if fator <= 0:
        return None
    preco = float(s.custo_un) / fator
    return dict(margem_alvo=margem_alvo, preco_necessario=preco, preco_atual=float(s.preco_bruto_un), aumento=preco / float(s.preco_bruto_un) - 1, mes=s.mes.date())


def achados_gerados(inv: str) -> list[dict]:
    """Achados rotulados (OBSERVAÇÃO / CONCLUSÃO ARITMÉTICA / HIPÓTESE / PADRÃO PROGRAMADO) gerados por scripts/run_analises.py.
    Lista vazia se o relatório ainda não foi gerado (a página avisa)."""
    arq = Path(PASTA_EVIDENCIAS) / f"{inv}_achados.json"
    if not arq.exists():
        return []
    return json.loads(arq.read_text(encoding="utf-8"))
