"""Página 1 — Visão Geral."""
import pandas as pd
import streamlit as st

from componentes import esc, brl0, brl_mil, cabecalho, consultar, int0, metrica, pct1, premissas, rodape, sem_resultado, tabela, var1  # noqa: F401
from empresax.analise import fmt
from empresax.app import graficos as G
from empresax.app import textos
from empresax.app.filtros import Filtros


def render(ctx):
    cabecalho("Visão Geral", "Indicadores principais da empresa no recorte escolhido na barra lateral.", ctx)
    f = ctx.filtros
    k = consultar(ctx, "kpis")
    if k["vazio"]:
        sem_resultado()
        premissas("PN-DEV-01", "PN-DEV-03")
        return
    anual = consultar(ctx, "comparacao_anual")
    desp = consultar(ctx, "despesas", None, k)

    ref = ""
    if anual["disponivel"]:
        ref = f"vs. {fmt.mes(pd.Timestamp(anual['periodo_base'][0]))} a {fmt.mes(pd.Timestamp(anual['periodo_base'][1]))}"
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(border=True):
        metrica("Receita ajustada (provisória)", brl_mil(k["ajustada"]), var1(anual["variacao"]) + " " + ref if anual["disponivel"] else None,
                f"{brl0(k['ajustada'])}. Vendas entregues (PN-DEV-01). A variação compara com o período equivalente do ano anterior.")
        if not anual["disponivel"]:
            st.caption("Sem comparação anual: " + anual["motivo"])
    with c2, st.container(border=True):
        d_pp = None
        if anual["disponivel"] and anual["margem_base"] is not None and k["margem_bruta"] is not None:
            d_pp = fmt.pp(k["margem_bruta"] - anual["margem_base"])
        metrica("Margem bruta ajustada", pct1(k["margem_bruta"]), d_pp, "Lucro bruto ÷ receita ajustada (razão de somas). Custo ajustado: PN-DEV-02 (hipótese).")
    with c3, st.container(border=True):
        metrica("Devoluções", brl_mil(k["devolucoes"]), None, f"{brl0(k['devolucoes'])}, no mês da venda (PN-DEV-03).")
        st.caption(esc(f"{pct1(k['taxa_devolucao'])} da receita registrada"))
    with c4, st.container(border=True):
        metrica("Pedidos", int0(k["pedidos"]), None, "Pedidos distintos no recorte (não é aditivo entre filiais ou meses).")
        st.caption(esc(f"Ticket por pedido: {brl0(k['ticket_pedido'])}"))

    d1, d2, d3, d4 = st.columns(4)
    if desp is None:
        with d1:
            st.info(textos.DESPESAS_INDISPONIVEIS)
    else:
        with d1, st.container(border=True):
            metrica("Despesas (dataset)", brl_mil(desp["total"]), None, brl0(desp["total"]))
            st.caption(esc(f"{pct1(desp['pct_receita'])} da receita ajustada"))
        with d2, st.container(border=True):
            metrica("Resultado operacional estimado", brl_mil(desp["resultado"]), None, textos.RESULTADO_OPERACIONAL)
            st.caption(esc(f"Margem: {pct1(desp['margem_operacional'])} · não é lucro líquido contábil"))
    with d3, st.container(border=True):
        metrica("Unidades entregues", int0(k["unidades_entregues"]))
        st.caption(esc(f"Preço bruto médio: {brl0(k['preco_bruto_medio'])}/un. (só comparável dentro de um produto)"))
    with d4, st.container(border=True):
        metrica("Linhas com margem negativa", int0(k["linhas_negativas"]), None, "Custo maior que a receita líquida da linha (PN-MRG-01).")
        st.caption(esc(f"{pct1(k['pct_linhas_negativas'])} das {int0(k['linhas'])} linhas"))

    with st.expander("Reconciliação da receita (registrada = entregues + devoluções)", expanded=True):
        a, b, c, d = st.columns(4)
        a.metric("Receita registrada", brl0(k["registrada"]))
        b.metric("− Devoluções", brl0(k["devolucoes"]))
        c.metric("= Vendas entregues", brl0(k["entregues"]))
        d.metric("Receita ajustada (provisória)", brl0(k["ajustada"]))
        ok = abs(k["diferenca_reconciliacao"]) < 0.01
        (st.success if ok else st.error)(esc(f"Diferença de reconciliação (registrada − entregues − devoluções): {fmt.brl(k['diferenca_reconciliacao'], 2)}" + (" ✔" if ok else " — INVESTIGAR")))
        st.markdown(textos.PREMISSAS["PN-DEV-01"])
        st.markdown(textos.PREMISSAS["PN-DEV-03"])

    serie = consultar(ctx, "serie_mensal")
    st.plotly_chart(G.tendencia(serie), width="stretch")

    tudo = Filtros(ctx.repo.primeiro_mes, ctx.repo.ultimo_mes, f.filiais, f.produtos, f.canais)
    st.plotly_chart(G.sobreposicao_anual(consultar(ctx, "serie_mensal", tudo)), width="stretch")
    st.caption("Cada linha é um ano. O ano em curso termina no último mês realizado: meses futuros não são preenchidos nem projetados. Compare sempre meses equivalentes.")
    premissas("PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-MRG-01", "PN-SIN-01")
