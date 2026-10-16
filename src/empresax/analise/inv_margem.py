"""Investigação 4 — Evolução da margem bruta e do resultado operacional estimado."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, Investigacao
from .dados import Dados
from .fmt import mes as fm, mil, num, pct, pp, var

ROTULO = "resultado operacional ESTIMADO do dataset (receita ajustada − custo ajustado − despesas); não é lucro líquido contábil"


def ytd(D: Dados, ano: int) -> pd.DataFrame:
    """Vendas e despesas de jan até o mês de referência do ano `ano` (mesmo número de meses nos 3 anos)."""
    lim = D.ultimo_mes.month
    v = D.vendas[(D.vendas.mes.dt.year == ano) & (D.vendas.mes.dt.month <= lim)]
    return v


def decompor_margem(v1: pd.DataFrame, v0: pd.DataFrame, chave: str = "id_produto") -> tuple[dict, pd.DataFrame]:
    """ΔMargem = mix (Σ(w1−w0)·(m0−M0)) + taxa (Σ w1·(m1−m0)) + entradas/saídas, com w = peso do produto na receita ajustada."""
    def tab(v):
        g = v.groupby(chave).agg(r=("receita_liquida_entregue", "sum"), c=("custo_entregue", "sum"))
        g["w"] = g.r / g.r.sum()
        g["m"] = np.where(g.r > 0, 1 - g.c / g.r.where(g.r > 0), np.nan)
        return g
    a, b = tab(v1), tab(v0)
    ids = a.index.union(b.index)
    a, b = a.reindex(ids), b.reindex(ids)
    cont = (a.r > 0) & (b.r > 0)
    novo, sai = (a.r > 0) & ~(b.r > 0), (b.r > 0) & ~(a.r > 0)
    out = pd.DataFrame(index=ids)
    out["peso_base"], out["peso_atual"] = b.w.fillna(0), a.w.fillna(0)
    out["margem_base"], out["margem_atual"] = b.m, a.m
    M1 = 1 - a.c.sum() / a.r.sum()
    M0 = 1 - b.c.sum() / b.r.sum()
    # mix centrado na margem média base (Σ Δw = 0 quando não há entradas/saídas): produto de margem ACIMA da média que ganha peso => efeito positivo
    out["efeito_mix"] = np.where(cont, (a.w - b.w) * (b.m - M0), 0.0)
    out["efeito_taxa"] = np.where(cont, a.w * (a.m - b.m), 0.0)
    out["efeito_entrada_saida"] = np.where(novo, a.w * a.m, 0.0) - np.where(sai, b.w * b.m, 0.0)
    res = dict(margem_base=float(M0), margem_atual=float(M1), delta=float(M1 - M0), mix=float(out.efeito_mix.sum()),
               taxa=float(out.efeito_taxa.sum()), entrada_saida=float(out.efeito_entrada_saida.sum()))
    res["residuo"] = res["delta"] - res["mix"] - res["taxa"] - res["entrada_saida"]
    return res, out


def executar(D: Dados) -> Investigacao:
    anos = [D.ultimo_mes.year - 2, D.ultimo_mes.year - 1, D.ultimo_mes.year]
    lim = D.ultimo_mes.month
    inv = Investigacao(
        "INV4", "Margem bruta e resultado operacional estimado: o que mudou entre 2024 e 2026?",
        "A margem bruta caiu por mudança de mix de produtos, por queda de margem dentro dos produtos ou por entrada/saída de itens? E o resultado operacional acompanhou?",
        f"Comparação sempre de jan a {fm(D.ultimo_mes)[:3]} em cada ano (mesmo nº de meses). Decomposição da variação da margem bruta em efeito MIX "
        "(Σ(Δ peso)·margem base) e efeito TAXA (Σ peso atual·Δ margem do produto) — fecha exatamente; custo e preço por unidade; "
        f"despesas por grupo sobre a receita ajustada. Rótulo: {ROTULO}.")
    # ---- tabela anual
    rows = []
    for a in anos:
        v = ytd(D, a)
        d = D.despesas[(D.despesas.mes.dt.year == a) & (D.despesas.mes.dt.month <= lim)]
        rec, cus = v.receita_liquida_entregue.sum(), v.custo_entregue.sum()
        rows.append(dict(ano=a, receita_ajustada=rec, custo_ajustado=cus, lucro_bruto=rec - cus, despesas=d.valor.sum(),
                         resultado_operacional_estimado=rec - cus - d.valor.sum(), margem_bruta=1 - cus / rec,
                         despesas_sobre_receita=d.valor.sum() / rec, margem_operacional=(rec - cus - d.valor.sum()) / rec))
    t = pd.DataFrame(rows)
    inv.tabelas["resumo_ytd"] = t
    inv.metricas["ytd"] = t.to_dict("records")
    r0, r1, r2 = t.iloc[0], t.iloc[1], t.iloc[2]
    inv.add(OBSERVACAO, f"Jan–{fm(D.ultimo_mes)[:3]}: receita ajustada {mil(r0.receita_ajustada)} → {mil(r1.receita_ajustada)} → {mil(r2.receita_ajustada)}; "
                        f"margem bruta {pct(r0.margem_bruta)} → {pct(r1.margem_bruta)} → {pct(r2.margem_bruta)}; "
                        f"despesas/receita {pct(r0.despesas_sobre_receita)} → {pct(r1.despesas_sobre_receita)} → {pct(r2.despesas_sobre_receita)}; "
                        f"margem operacional estimada {pct(r0.margem_operacional)} → {pct(r1.margem_operacional)} → {pct(r2.margem_operacional)}.")
    inv.add(OBSERVACAO, f"Resultado operacional estimado (jan–{fm(D.ultimo_mes)[:3]}): {mil(r0.resultado_operacional_estimado)} → {mil(r1.resultado_operacional_estimado)} → {mil(r2.resultado_operacional_estimado)}. "
                        f"É {ROTULO}.")

    # ---- decomposição da margem bruta
    dec = {}
    for a0, a1 in ((anos[0], anos[1]), (anos[1], anos[2]), (anos[0], anos[2])):
        res, por = decompor_margem(ytd(D, a1), ytd(D, a0))
        dec[(a0, a1)] = (res, por)
    inv.tabelas["decomposicao_margem_bruta"] = pd.DataFrame([{"de": k[0], "para": k[1], **v[0]} for k, v in dec.items()])
    inv.metricas["decomposicao"] = {f"{k[0]}-{k[1]}": v[0] for k, v in dec.items()}
    inv.metricas["chave_decomposicao_total"] = f"{anos[0]}-{anos[2]}"
    for (a0, a1), (res, por) in dec.items():
        inv.add(CONCLUSAO, f"Margem bruta {a0}→{a1}: {pp(res['delta'])} (de {pct(res['margem_base'])} para {pct(res['margem_atual'])}) = "
                           f"mix de produtos {pp(res['mix'])} + margem dentro de cada produto {pp(res['taxa'])}"
                           + (f" + entradas/saídas {pp(res['entrada_saida'])}" if abs(res['entrada_saida']) > 1e-12 else "") + f" (resíduo {num(res['residuo'] * 100, 4)} p.p.).")
    res, por = dec[(anos[0], anos[2])]
    nome = D.produtos.set_index("id_produto").produto
    por = por.join(nome)
    inv.tabelas["contribuicao_por_produto_24_26"] = por.sort_values("efeito_taxa").reset_index()
    piores = por.sort_values("efeito_taxa").head(3)
    inv.metricas["piores_taxa"] = [(r.produto, float(r.efeito_taxa)) for r in piores.itertuples()]
    inv.add(CONCLUSAO, f"Maiores contribuições negativas de margem DENTRO do produto ({anos[0]}→{anos[2]}): " + "; ".join(
        f"{r.produto} ({pp(r.efeito_taxa, 2)})" for r in piores.itertuples()) + ".")
    duas = piores.head(2)
    inv.metricas.update(duas_share_taxa=float(duas.efeito_taxa.sum() / res["taxa"]), duas_share_delta=float(duas.efeito_taxa.sum() / res["delta"]))
    inv.add(CONCLUSAO, f"{duas.produto.iloc[0]} e {duas.produto.iloc[1]} juntos respondem por {pct(inv.metricas['duas_share_taxa'], 0)} da perda de margem dentro dos produtos "
                       f"e por {pct(inv.metricas['duas_share_delta'], 0)} da queda total da margem bruta {anos[0]}→{anos[2]} ({pp(res['delta'])}).")
    pos = por.sort_values("efeito_mix").head(3)
    inv.add(CONCLUSAO, f"Maiores contribuições negativas de MIX ({anos[0]}→{anos[2]}): " + "; ".join(f"{r.produto} ({pp(r.efeito_mix, 2)})" for r in pos.itertuples())
                       + " (perda de peso de produtos de margem acima da média, ou ganho de peso de produtos de margem abaixo da média).")

    # ---- preço líquido × custo por unidade
    def unit(v):
        g = v.groupby("id_produto").agg(r=("receita_liquida_entregue", "sum"), c=("custo_entregue", "sum"),
                                        q=("quantidade", lambda s: s[v.loc[s.index, "eh_devolvida"] == False].sum()))  # noqa: E712
        g["p"], g["cu"] = g.r / g.q, g.c / g.q
        return g
    u0, u1 = unit(ytd(D, anos[1])), unit(ytd(D, anos[2]))
    j = u1.join(u0, lsuffix="_1", rsuffix="_0", how="inner")
    j["cresc_preco_liq"], j["cresc_custo"] = j.p_1 / j.p_0 - 1, j.cu_1 / j.cu_0 - 1
    j["custo_cresceu_mais"] = j.cresc_custo > j.cresc_preco_liq
    j = j.join(nome)
    peso = j.r_1 / j.r_1.sum()
    inv.tabelas["preco_liquido_vs_custo_unitario"] = j.reset_index()[["id_produto", "produto", "cresc_preco_liq", "cresc_custo", "custo_cresceu_mais"]]
    pm_p, pm_c = float((j.cresc_preco_liq * peso).sum()), float((j.cresc_custo * peso).sum())
    inv.metricas.update(prods_custo_maior=int(j.custo_cresceu_mais.sum()), prods_total=len(j), cresc_preco_ponderado=pm_p, cresc_custo_ponderado=pm_c)
    inv.add(OBSERVACAO, f"Por unidade vendida ({anos[1]}→{anos[2]}, mesmo período do ano): preço líquido cresceu em média {var(pm_p)} e custo {var(pm_c)} (média por produto ponderada pela receita). "
                        f"Em {int(j.custo_cresceu_mais.sum())} de {len(j)} produtos o custo por unidade subiu mais que o preço líquido.")
    inv.add(PROGRAMADO, "P06 e P07: o gerador reajusta preço (`ip`) e custo (`ic`) de cada produto todo mês; o padrão é ic=ip=0,15% a.m., com exceções "
                        "(Notebook Pro 14\": custo +0,45% e preço +0,20% a.m.; Smartphone X Max: custo +1,00% e preço 0%). "
                        "Logo, a compressão de margem destes dois produtos é programada; a dos demais depende do sorteio de custo/preço (±1,5%) em torno de reajustes iguais.")

    # ---- despesas por grupo
    gr = []
    for a in anos:
        d = D.despesas[(D.despesas.mes.dt.year == a) & (D.despesas.mes.dt.month <= lim)]
        rec = ytd(D, a).receita_liquida_entregue.sum()
        s = d.groupby("grupo_dre").valor.sum() / rec
        gr.append(s.rename(a))
    G = pd.concat(gr, axis=1)
    G["delta_24_26_pp"] = G[anos[2]] - G[anos[0]]
    inv.tabelas["despesas_sobre_receita_por_grupo"] = G.reset_index()
    tot = G[anos].sum()
    d_desp = float(tot[anos[2]] - tot[anos[0]])
    inv.metricas.update(delta_desp_ratio=d_desp, delta_mb=float(r2.margem_bruta - r0.margem_bruta), delta_mo=float(r2.margem_operacional - r0.margem_operacional))
    g_ord = G.sort_values("delta_24_26_pp")
    inv.add(CONCLUSAO, f"Margem operacional {anos[0]}→{anos[2]}: {pp(r2.margem_operacional - r0.margem_operacional)} = margem bruta {pp(r2.margem_bruta - r0.margem_bruta)} − variação de despesas/receita ({pp(d_desp)}). "
                       "Por grupo (variação de despesas/receita): " + "; ".join(f"{g} {pp(x, 2)}" for g, x in g_ord.delta_24_26_pp.items()))
    fin = G.loc["Despesas Financeiras", "delta_24_26_pp"] if "Despesas Financeiras" in G.index else 0.0
    if fin > 0:
        inv.add(PROGRAMADO, f"Despesas financeiras/receita {pp(fin, 2)} entre {anos[0]} e {anos[2]}: coerente com P16 (juros bancários sobem desde mar/2025 no gerador).")
    inv.add(OBSERVACAO, f"A queda da margem bruta foi em grande parte compensada por despesas que cresceram menos que a receita (despesas/receita {pp(d_desp)}); "
                        "sem essa alavancagem, a margem operacional teria caído o mesmo que a bruta.")

    # ---- série mensal
    m = D.vendas.groupby("mes").agg(rec=("receita_liquida_entregue", "sum"), cus=("custo_entregue", "sum")).reindex(D.meses)
    m["desp"] = D.despesas.groupby("mes").valor.sum().reindex(D.meses)
    m["resultado"] = m.rec - m.cus - m.desp
    m["margem_bruta"], m["margem_operacional"] = 1 - m.cus / m.rec, m.resultado / m.rec
    inv.tabelas["serie_mensal"] = m.reset_index().rename(columns={"index": "mes"})
    neg_m = m[m.resultado < 0]
    pior = m.margem_operacional.idxmin()
    inv.metricas.update(meses_resultado_negativo=len(neg_m), pior_mes=pior, pior_margem_op=float(m.margem_operacional.min()),
                        melhor_mes=m.margem_operacional.idxmax(), melhor_margem_op=float(m.margem_operacional.max()))
    inv.add(OBSERVACAO, f"Série mensal: margem operacional estimada entre {pct(m.margem_operacional.min())} ({fm(pior)}) e {pct(m.margem_operacional.max())} ({fm(m.margem_operacional.idxmax())}); "
                        f"{len(neg_m)} {'mês' if len(neg_m) == 1 else 'meses'} com resultado estimado negativo" + (f" ({', '.join(fm(x) for x in neg_m.index)})." if len(neg_m) else "."))
    inv.add(HIPOTESE, "O mix pode estar mudando por política comercial (mais volume de itens de menor margem) ou por crescimento diferente entre categorias; "
                      "os dados mostram a mudança de composição, não a intenção. Sobre despesas: parte do crescimento menor que a receita pode ser "
                      "custo fixo diluído (despesas de pessoal e administrativas) — compatível com os dados, não testado.")
    inv.limitacoes = [f"{ROTULO}.", "Despesas não são alocadas a produtos/canais: margem por produto é margem BRUTA.",
                      "Receita ajustada provisória (devoluções excluídas; custo devolvido considerado recuperado — PN-DEV-02, hipótese).",
                      "Três anos de dados sintéticos; tendências não são previsões."]
    inv.recomendacoes = [
        "Se a margem bruta seguir caindo com despesas crescendo menos que a receita, a alavancagem operacional não será suficiente a longo prazo: priorizar revisão de preço/custo dos produtos com maior contribuição negativa de taxa.",
        "Se o mix de produtos de menor margem estiver crescendo por incentivo comercial, rever metas e comissões para que reflitam margem, e não só receita.",
        "Acompanhar mensalmente a decomposição mix × taxa da margem bruta, em vez de apenas a margem total."]
    inv.proximas = ["As despesas de pessoal cresceram abaixo da receita por ganho de produtividade ou por falta de contratação?",
                    "Quais produtos tiveram aumento de custo repassado ao preço e quais não?",
                    "Qual o resultado por filial depois de alocar despesas corporativas da Matriz?"]
    return inv
