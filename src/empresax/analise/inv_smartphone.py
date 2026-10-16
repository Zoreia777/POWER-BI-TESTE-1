"""Investigação 3 — Smartphone X Max: margem crítica e concentração de linhas negativas."""
from __future__ import annotations

import pandas as pd

from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, Investigacao
from .dados import Dados
from .fmt import brl, mes as fm, pct, pp

PRODUTO = "Smartphone X Max"


def _margem(df: pd.DataFrame, col_rec="receita_liquida_entregue", col_cus="custo_entregue") -> float:
    r = df[col_rec].sum()
    return float((r - df[col_cus].sum()) / r) if r else float("nan")


def executar(D: Dados) -> Investigacao:
    v = D.vendas
    pid = int(D.produtos.loc[D.produtos.produto == PRODUTO, "id_produto"].iloc[0])
    sp = v[v.id_produto == pid]
    inv = Investigacao(
        "INV3", "Smartphone X Max: por que a margem é crítica e onde estão as linhas negativas?",
        "O problema de margem do Smartphone X Max é pontual (descontos, canal, filial) ou estrutural (custo × preço)? Qual o tamanho do impacto na empresa?",
        "Evolução mensal de preço líquido por unidade × custo por unidade; participação do produto nas linhas e no prejuízo bruto negativos; "
        "taxa de linhas negativas por faixa de desconto, canal, filial e período; impacto na margem da empresa com e sem o produto; "
        "cálculo aritmético do preço necessário para margens-alvo (não é recomendação de preço).")

    # ---- série mensal
    g = sp.groupby("mes").agg(linhas=("id_venda", "count"), linhas_neg=("flag_margem_negativa", "sum"), unidades=("quantidade", "sum"),
                              bruta=("receita_bruta", "sum"), desc=("desconto_valor", "sum"), imp=("impostos_valor", "sum"),
                              liq=("receita_liquida", "sum"), custo=("custo_total", "sum")).reindex(D.meses)
    g["preco_bruto_un"] = g.bruta / g.unidades
    g["preco_liquido_un"] = g.liq / g.unidades
    g["custo_un"] = g.custo / g.unidades
    g["desconto_efetivo"] = g.desc / g.bruta
    g["margem_bruta"] = 1 - g.custo / g.liq
    g["pct_linhas_neg"] = g.linhas_neg / g.linhas
    inv.tabelas["serie_mensal"] = g.reset_index().rename(columns={"index": "mes"})

    # ---- participação na empresa
    neg = v[v.flag_margem_negativa]
    prej = (neg.custo_total - neg.receita_liquida)
    neg.groupby("id_produto").size()
    prej_sp = float(prej[neg.id_produto == pid].sum())
    inv.metricas.update(linhas_neg_total=len(neg), linhas_neg_sp=int((neg.id_produto == pid).sum()),
                        share_linhas_neg=float((neg.id_produto == pid).mean()), prejuizo_total=float(prej.sum()), prejuizo_sp=prej_sp)
    inv.add(OBSERVACAO, f"{inv.metricas['linhas_neg_sp']} das {len(neg)} linhas com margem negativa da empresa ({pct(inv.metricas['share_linhas_neg'])}) são do {PRODUTO}; "
                        f"prejuízo bruto dessas linhas: {brl(prej_sp)} de {brl(prej.sum())} ({pct(prej_sp / prej.sum())}).")

    # ---- evolução: preço líquido × custo
    primeira_neg = g.index[g.margem_bruta < 0][0]
    metade = g.index[g.pct_linhas_neg >= 0.5][0]
    cem = g.index[g.pct_linhas_neg >= 0.999][0]
    primeira_linha_neg = g.index[g.linhas_neg > 0][0]
    cresc_custo = g.custo_un.iloc[-1] / g.custo_un.iloc[0] - 1
    cresc_preco = g.preco_bruto_un.iloc[-1] / g.preco_bruto_un.iloc[0] - 1
    n = len(g) - 1
    inv.metricas.update(primeira_mes_margem_neg=primeira_neg, mes_metade_linhas_neg=metade, mes_todas_linhas_neg=cem,
                        primeira_linha_neg=primeira_linha_neg, cresc_custo=cresc_custo, cresc_preco=cresc_preco,
                        margem_inicio=float(g.margem_bruta.iloc[0]), margem_fim=float(g.margem_bruta.iloc[-1]),
                        custo_un_fim=float(g.custo_un.iloc[-1]), preco_liq_fim=float(g.preco_liquido_un.iloc[-1]),
                        cresc_custo_mensal=float((1 + cresc_custo) ** (1 / n) - 1))
    inv.add(OBSERVACAO, f"Preço bruto médio por unidade: {brl(g.preco_bruto_un.iloc[0])} em {fm(g.index[0])} → {brl(g.preco_bruto_un.iloc[-1])} em {fm(g.index[-1])} ({pct(cresc_preco)} de variação); "
                        f"custo por unidade: {brl(g.custo_un.iloc[0])} → {brl(g.custo_un.iloc[-1])} (+{pct(cresc_custo)}, ≈ {pct(inv.metricas['cresc_custo_mensal'], 2)} ao mês). "
                        f"Margem bruta do produto: {pct(g.margem_bruta.iloc[0])} → {pct(g.margem_bruta.iloc[-1])}.")
    inv.add(OBSERVACAO, f"Marcos: primeira linha negativa em {fm(primeira_linha_neg)}; margem mensal do produto fica negativa em {fm(primeira_neg)}; "
                        f"metade das linhas do mês é negativa a partir de {fm(metade)}; 100% das linhas do mês são negativas a partir de {fm(cem)}.")
    apos = sp[sp.mes >= cem]
    inv.metricas["apos_cem_n"] = len(apos)
    inv.metricas["apos_cem_neg"] = int(apos.flag_margem_negativa.sum())
    inv.add(CONCLUSAO, f"Desde {fm(cem)} todas as {len(apos)} linhas do produto têm margem negativa, em qualquer canal, filial ou faixa de desconto — "
                       "a causa é estrutural (custo por unidade acima do preço líquido), e não de desconto pontual.")

    # ---- desconto / canal / filial
    sp = sp.assign(faixa=pd.cut(sp.desconto_pct, [-0.001, 0.0, 0.05, 0.10, 0.15, 1.0], labels=["0%", "0–5%", "5–10%", "10–15%", ">15%"]))
    f_desc = sp.groupby("faixa", observed=True).agg(linhas=("id_venda", "count"), pct_neg=("flag_margem_negativa", "mean"))
    inv.tabelas["negativas_por_faixa_desconto"] = f_desc.reset_index()
    sp[sp.mes >= cem]
    pre = sp[sp.mes < cem]
    canais = D.canais.set_index("id_canal").canal
    fil = D.filiais.set_index("id_filial").filial
    pc = pre.groupby("id_canal").flag_margem_negativa.agg(["mean", "size"]).rename(index=canais)
    inv.tabelas["negativas_por_canal_antes_100pct"] = pc.reset_index()
    pf = pre.groupby("id_filial").flag_margem_negativa.agg(["mean", "size"]).rename(index=fil)
    inv.tabelas["negativas_por_filial_antes_100pct"] = pf.reset_index()
    fd = f_desc.pct_neg
    inv.add(OBSERVACAO, "Taxa de linhas negativas por faixa de desconto (todo o período): " + "; ".join(f"{k} {pct(x, 0)}" for k, x in fd.items())
                        + ". A associação com o desconto é em parte mecânica (desconto reduz a receita) e em parte de calendário (as linhas mais recentes, quando o custo já é alto, pesam mais nas faixas).")
    inv.add(OBSERVACAO, f"Antes de {fm(cem)} (período em que ainda há linhas positivas), a taxa de linhas negativas por canal varia de {pct(pc['mean'].min(), 0)} a {pct(pc['mean'].max(), 0)} "
                        f"e por filial de {pct(pf['mean'].min(), 0)} a {pct(pf['mean'].max(), 0)}; essas diferenças misturam canal/filial com a data em que cada uma vendeu mais (efeito de calendário), "
                        "por isso não indicam, sozinhas, que um canal ou filial seja o 'culpado'.")

    # ---- sensibilidade: preço necessário
    ult = sp[sp.mes == D.ultimo_mes]
    d_ef = ult.desconto_valor.sum() / ult.receita_bruta.sum()
    t_ef = ult.impostos_valor.sum() / (ult.receita_bruta.sum() - ult.desconto_valor.sum())
    custo_un = ult.custo_total.sum() / ult.quantidade.sum()
    lista = float(D.produtos.loc[D.produtos.id_produto == pid, "preco_lista"].iloc[0])
    tab = []
    for m in (0.0, 0.10, 0.20):
        pn = custo_un / ((1 - d_ef) * (1 - t_ef) * (1 - m))
        tab.append(dict(margem_alvo=m, preco_bruto_necessario=pn, aumento_sobre_lista=pn / lista - 1))
    inv.tabelas["preco_necessario"] = pd.DataFrame(tab)
    inv.metricas.update(preco_lista=lista, desc_ef_ult=float(d_ef), imp_ef_ult=float(t_ef), tab_preco=tab)
    inv.add(CONCLUSAO, f"Cálculo aritmético em {fm(D.ultimo_mes)} (custo {brl(custo_un)}/un., desconto efetivo {pct(d_ef)}, imposto efetivo {pct(t_ef)}): "
                       + "; ".join(f"para margem bruta de {pct(r['margem_alvo'], 0)} o preço bruto teria de ser {brl(r['preco_bruto_necessario'])} ({pct(r['aumento_sobre_lista'])} sobre o preço de lista de {brl(lista)})" for r in tab)
                       + ". Não considera elasticidade da demanda nem preço dos concorrentes — não é recomendação de preço.")

    # ---- impacto na empresa (YTD do último ano)
    ano = D.ultimo_mes.year
    y = v[(v.mes.dt.year == ano)]
    m_com = _margem(y)
    m_sem = _margem(y[y.id_produto != pid])
    rec_sp = y.loc[y.id_produto == pid, "receita_liquida_entregue"].sum()
    lucro_sp = rec_sp - y.loc[y.id_produto == pid, "custo_entregue"].sum()
    lucro_tot = y.receita_liquida_entregue.sum() - y.custo_entregue.sum()
    inv.metricas.update(margem_com=m_com, margem_sem=m_sem, rec_share=float(rec_sp / y.receita_liquida_entregue.sum()),
                        lucro_share=float(lucro_sp / lucro_tot), lucro_sp=float(lucro_sp), rec_sp=float(rec_sp))
    inv.add(CONCLUSAO, f"Em {ano} (jan–{fm(D.ultimo_mes)[:3]}), o {PRODUTO} representa {pct(rec_sp / y.receita_liquida_entregue.sum())} da receita ajustada, mas "
                       + (f"seu lucro bruto é negativo ({brl(lucro_sp)}, {pct(lucro_sp / lucro_tot)} do lucro bruto da empresa)" if lucro_sp < 0 else f"só {pct(lucro_sp / lucro_tot)} do lucro bruto ({brl(lucro_sp)})") + f". A margem bruta da empresa seria {pct(m_sem)} sem o produto, contra {pct(m_com)} com ele ({pp(m_com - m_sem)}).")
    inv.add(PROGRAMADO, "P07: o gerador define para este produto aumento de custo de 1% ao mês com preço fixo (linha 304 de gerar_dados.py). "
                        "O comportamento observado (custo ≈ +1% a.m., preço constante) é exatamente o programado — logo a 'causa' aqui é conhecida por construção, não descoberta.")
    inv.add(HIPOTESE, "Em uma empresa real, o padrão seria compatível com repasse de custo (câmbio/fornecedor) sem reajuste de preço, ou com política comercial "
                      "mantida por contrato/mercado. Os dados não permitem saber qual das duas — nem se o volume vendido depende do preço baixo.")
    inv.limitacoes = ["Custo unitário e preço são médias do mês; não há custo por lote/fornecedor.",
                      "Sem dados de elasticidade: não é possível estimar o efeito de subir preço sobre o volume.",
                      "A recuperação do custo nas devoluções é hipótese (PN-DEV-02); aqui a margem usa custo ajustado, e a sensibilidade está na Etapa 3 (03a).",
                      "Dados sintéticos: custo e preço seguem regra do gerador."]
    inv.recomendacoes = [
        f"Se a margem do {PRODUTO} é de fato negativa na empresa real, reajustar o preço, renegociar custo ou limitar descontos antes de incentivar o volume: cada unidade adicional vendida hoje aumenta o prejuízo bruto.",
        "Se o produto é âncora estratégica (atrai clientes para outros itens), medir o ganho indireto (cesta de compra) antes de decidir reduzir sua oferta.",
        "Criar alerta mensal de margem por produto (custo unitário × preço líquido) para detectar o problema meses antes do ponto em que a margem fica negativa."]
    inv.proximas = [f"O {PRODUTO} é vendido em conjunto com produtos de maior margem (cesta)?",
                    "O custo reajustado foi contratual ou pode ser renegociado?",
                    "O preço é fixo por política ou por restrição de mercado? Qual a sensibilidade da demanda a reajustes?"]
    return inv
