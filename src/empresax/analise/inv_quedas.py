"""Investigação 2 — Quedas ano a ano por filial e por produto: quais merecem atenção?"""
from __future__ import annotations

import pandas as pd

from . import pvm
from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, Investigacao
from .dados import Dados
from .eventos import rotular
from .fmt import mes as fm, mil, pct, var
from ..config import Config


def _serie_yoy(base: pd.DataFrame, lim: float) -> pd.DataFrame:
    """base: índice mês, colunas = unidades. Devolve long com yoy, queda e extensão da sequência de quedas."""
    out = []
    for col in base.columns:
        s = base[col]
        b = s.shift(12)
        yoy = (s / b - 1).where(b > 0)
        queda = (yoy <= lim).fillna(False)
        run = []
        n = 0
        for q in queda:
            n = n + 1 if q else 0
            run.append(n)
        # comprimento total da sequência a que cada mês pertence
        seq = pd.Series(run, index=s.index)
        total = seq.copy()
        i = len(seq) - 1
        while i >= 0:
            if seq.iloc[i] > 0:
                j = i
                while j >= 0 and seq.iloc[j] > 0:
                    j -= 1
                total.iloc[j + 1:i + 1] = seq.iloc[i]
                i = j
            else:
                i -= 1
        out.append(pd.DataFrame({"chave": col, "mes": s.index, "valor": s.values, "base": b.values, "yoy_pct": yoy.values,
                                 "queda": queda.values, "sequencia": total.values}))
    return pd.concat(out, ignore_index=True)


def executar(D: Dados, cfg: Config | None = None) -> Investigacao:
    cfg = cfg or Config()
    lim, persist = cfg.limiar_queda_yoy, cfg.queda_persistente_meses
    v = D.vendas
    inv = Investigacao(
        "INV2", "Quedas ano a ano por filial e por produto",
        "Entre as quedas anuais (≤ -10%) de filiais e produtos, quais são relevantes em reais, persistentes e não explicadas por eventos programados?",
        f"Grade completa mês × unidade; queda = variação anual ≤ {pct(lim, 0)}; persistente = ≥ {persist} meses seguidos; "
        "decomposição volume/mix/preço de cada queda de filial; produto líder da queda; rótulo de coincidência com eventos programados (P09–P11).")
    nome_f = D.filiais.set_index("id_filial").filial
    nome_p = D.produtos.set_index("id_produto").produto

    # ---------------- filiais
    mf = v.groupby(["mes", "id_filial"]).receita_liquida_entregue.sum().unstack().reindex(D.meses, fill_value=0.0)
    lf = _serie_yoy(mf, lim)
    inv.tabelas["matriz_yoy_filial"] = lf.pivot(index="mes", columns="chave", values="yoy_pct").rename(columns=nome_f).reset_index()
    quedas_f = lf[lf.queda].copy()
    linhas = v.groupby(["id_filial", "mes"]).size()
    pedidos = v.groupby(["id_filial", "mes"]).id_pedido.nunique()
    reg = []
    for _, r in quedas_f.iterrows():
        f, m = int(r.chave), r.mes
        base_m = m - pd.DateOffset(months=12)
        res, por = pvm.decompor(v[v.id_filial == f], m, base_m)
        top = por.variacao.idxmin()
        reg.append(dict(filial=nome_f[f], mes=m, receita_ajustada=r.valor, receita_ano_anterior=r.base, yoy_pct=r.yoy_pct,
                        queda_rs=r.base - r.valor, linhas_base=int(linhas.get((f, base_m), 0)), linhas_atual=int(linhas.get((f, m), 0)),
                        pedidos_base=int(pedidos.get((f, base_m), 0)), pedidos_atual=int(pedidos.get((f, m), 0)),
                        efeito_volume_mix=res["volume"] + res["mix"], efeito_preco_desconto=res["preco"] + res["desconto"] + res["impostos"],
                        produto_lider=nome_p[top], share_produto_lider=por.variacao[top] / res["variacao_registrada"] if res["variacao_registrada"] else float("nan"),
                        sequencia_meses=int(r.sequencia), programado=rotular(m, id_filial=f)))
    tf = pd.DataFrame(reg).sort_values("queda_rs", ascending=False).reset_index(drop=True)
    inv.tabelas["quedas_filial_yoy"] = tf
    inv.metricas.update(n_quedas_filial=len(tf), n_filial_persistentes=int((tf.sequencia_meses >= persist).sum()),
                        n_filial_programadas=int((tf.programado != "").sum()), queda_total_filial=float(tf.queda_rs.sum()))
    top3 = tf.head(3)
    inv.add(OBSERVACAO, f"{len(tf)} quedas anuais (≤ {pct(lim, 0)}) em mês×filial, somando {mil(tf.queda_rs.sum())} de receita a menos que no mesmo mês do ano anterior. "
                        f"As três maiores: " + "; ".join(f"{r.filial} {fm(r.mes)} ({var(r.yoy_pct)}, {mil(-r.queda_rs)})" for r in top3.itertuples()) + ".")
    pers = tf[tf.sequencia_meses >= persist]
    inv.add(OBSERVACAO, f"Persistência: {len(pers)} das {len(tf)} quedas fazem parte de sequências de {persist}+ meses seguidos"
                        + (f" ({', '.join(sorted(set(pers.filial)))})." if len(pers) else ".") +
                        f" As demais ({len(tf) - len(pers)}) são episódios curtos.")
    vol = (tf.efeito_volume_mix.abs() > tf.efeito_preco_desconto.abs()).mean()
    inv.add(CONCLUSAO, f"Em {pct(vol, 0)} das quedas de filial, o efeito volume+mix é maior (em módulo) que o efeito preço+desconto+imposto: "
                       "as quedas anuais são, aritmeticamente, de quantidade/composição de produtos, não de preço.")
    prog = tf[tf.programado != ""]
    if len(prog):
        inv.add(PROGRAMADO, f"{len(prog)} quedas de filial coincidem com a janela de um evento programado: "
                            + "; ".join(f"{r.filial} {fm(r.mes)} ({r.programado})" for r in prog.head(6).itertuples()) + ".")
    nao = tf[(tf.programado == "") & (tf.sequencia_meses < persist)]
    inv.add(HIPOTESE, f"As {len(nao)} quedas curtas e sem evento programado podem refletir variação natural de pedidos grandes (ver INV1 — Porto Alegre) "
                      "e de calendário (dias úteis); isso não foi testado causa a causa.")

    # ---------------- produtos
    mp = v.groupby(["mes", "id_produto"]).receita_liquida_entregue.sum().unstack().reindex(D.meses, fill_value=0.0)
    lp = _serie_yoy(mp, lim)
    qp = lp[lp.queda].copy()
    lin_p = v.groupby(["id_produto", "mes"]).size()
    reg = []
    for _, r in qp.iterrows():
        p, m = int(r.chave), r.mes
        base_m = m - pd.DateOffset(months=12)
        reg.append(dict(produto=nome_p[p], id_produto=p, mes=m, receita_ajustada=r.valor, receita_ano_anterior=r.base, yoy_pct=r.yoy_pct,
                        queda_rs=r.base - r.valor, linhas_base=int(lin_p.get((p, base_m), 0)), linhas_atual=int(lin_p.get((p, m), 0)),
                        sequencia_meses=int(r.sequencia), programado=rotular(m, id_produto=p)))
    tp = pd.DataFrame(reg).sort_values("queda_rs", ascending=False).reset_index(drop=True)
    tp["persistente"] = tp.sequencia_meses >= persist
    inv.tabelas["quedas_produto_yoy"] = tp
    por_prod = tp.groupby("produto").agg(meses_em_queda=("mes", "count"), queda_total_rs=("queda_rs", "sum"),
                                         maior_sequencia=("sequencia_meses", "max")).sort_values("queda_total_rs", ascending=False)
    inv.tabelas["quedas_produto_resumo"] = por_prod.reset_index()
    top10 = tp.head(10).queda_rs.sum() / tp.queda_rs.sum()
    inv.metricas.update(n_quedas_produto=len(tp), n_prod_persistentes=int(tp.persistente.sum()), queda_total_produto=float(tp.queda_rs.sum()),
                        top10_share=float(top10), n_prod_distintos=int(tp.produto.nunique()), n_prod_programadas=int((tp.programado != "").sum()))
    inv.add(OBSERVACAO, f"{len(tp)} quedas anuais (≤ {pct(lim, 0)}) em produto×mês, em {tp.produto.nunique()} dos {len(D.produtos)} produtos; "
                        f"as 10 maiores concentram {pct(top10, 0)} do valor perdido ({mil(tp.queda_rs.sum())} no total).")
    inv.add(OBSERVACAO, f"Persistência: {int(tp.persistente.sum())} das {len(tp)} quedas pertencem a sequências de {persist}+ meses; "
                        f"{len(tp) - int(tp.persistente.sum())} são episódios curtos.")
    maior = tp.iloc[0]
    inv.add(OBSERVACAO, f"Maior queda: {maior.produto} em {fm(maior.mes)} ({var(maior.yoy_pct)}; {mil(-maior.queda_rs)}).")
    if (tp.programado != "").any():
        pg = tp[tp.programado != ""].iloc[0]
        inv.add(PROGRAMADO, f"{pg.produto} em {fm(pg.mes)} coincide com {pg.programado} (fator 0,10× no gerador) — causa conhecida; "
                            "em dado real equivaleria a uma ruptura de estoque a confirmar.")
    ranking = por_prod.head(5)
    inv.add(OBSERVACAO, "Produtos com maior valor acumulado de quedas anuais: " + "; ".join(
        f"{n} ({int(r.meses_em_queda)} meses, {mil(-r.queda_total_rs)})" for n, r in ranking.iterrows()) + ".")
    inv.add(HIPOTESE, f"Como {len(tp) - int(tp.persistente.sum())} de {len(tp)} quedas de produto são episódios curtos, a explicação mais compatível é variação pontual "
                      "de pedidos (e, no caso do P09, ruptura), e não perda estrutural de demanda. É hipótese: não foi testada produto a produto.")
    inv.limitacoes = ["A grade usa receita ajustada (entregue); devoluções ficam no mês da venda (sem data de devolução).",
                      "Limiares (-10% YoY, 3 meses) são parâmetros de gestão, não verdades estatísticas.",
                      "Dados sintéticos: não há sazonalidade de mercado real, apenas a programada (P01–P05)."]
    inv.recomendacoes = [
        f"Se a gestão priorizar poucas frentes, acompanhar primeiro as {int(tp.persistente.sum())} quedas de produto persistentes e as {len(pers)} de filial persistentes; as curtas só merecem investigação se envolverem grandes valores.",
        "Se uma queda coincidir com ruptura de estoque confirmada, tratar como problema de abastecimento (não de demanda) antes de mexer em preço ou promoção.",
        "Usar média móvel de 3 meses ao lado da variação anual do mês para reduzir falsos alarmes de pedidos grandes."]
    inv.proximas = ["Quais quedas persistentes têm causa operacional documentada (estoque, equipe, concorrente)?",
                    "Os produtos em queda perderam clientes ou foram substituídos por outros da mesma categoria?",
                    "Qual a margem dos produtos em queda: perder esse volume custa muito ou pouco lucro?"]
    return inv
