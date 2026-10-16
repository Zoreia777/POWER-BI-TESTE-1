"""Página 2 — Filiais."""
import streamlit as st

from componentes import brl0, cabecalho, consultar, int0, pct1, premissas, sem_resultado, tabela, var1
from empresax.app import graficos as G
from empresax.app import textos


def render(ctx):
    cabecalho("Filiais", "Quanto cada filial vende, com que margem e como evoluiu contra o mesmo período do ano anterior.", ctx)
    d = consultar(ctx, "por_dimensao", None, "filial")
    if d.empty:
        sem_resultado()
        return
    desp = consultar(ctx, "despesas_por_filial")
    d = d.copy()
    if desp is not None:
        d = d.merge(desp.rename(columns={"nome": "nome"}), on="nome", how="left")
        d["desp_pct"] = d.despesas / d.ajustada.where(d.ajustada != 0)
    else:
        d["despesas"] = float("nan")
        d["desp_pct"] = float("nan")
        st.info(textos.DESPESAS_INDISPONIVEIS)
    d["ticket"] = d.ajustada / d.pedidos.where(d.pedidos != 0)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(G.ranking(d, "ajustada", "Receita ajustada por filial (R$)"), width="stretch")
    with c2:
        st.plotly_chart(G.ranking(d, "margem_bruta", "Margem bruta ajustada por filial", "pct"), width="stretch")
    st.caption("Margem bruta: razão de somas (lucro bruto ÷ receita ajustada) dentro de cada filial, nunca média de percentuais.")

    st.subheader("Variação anual por filial (período equivalente)")
    ok = d.dropna(subset=["yoy"])
    if ok.empty:
        st.info("Nenhuma filial tem base comparável no ano anterior neste recorte (período inicia em 2024 ou a filial ainda não existia).")
    else:
        st.plotly_chart(G.ranking(ok, "yoy", "Variação anual da receita ajustada", "pct"), width="stretch")
        sem = d[d.yoy.isna()].nome.tolist()
        if sem:
            st.caption("Sem base comparável (filial não vendia no período equivalente do ano anterior — não é crescimento nem queda): " + ", ".join(sem) + ".")
    st.plotly_chart(G.mapa_yoy(consultar(ctx, "matriz_yoy_filial")), width="stretch")
    st.caption("Mapa de calor: cada célula compara o mês com o MESMO mês do ano anterior; células vazias não têm base. A Etapa 4 mostrou que quedas de um mês isolado costumam ser base atípica — veja o estudo de Porto Alegre em Investigações.")

    st.subheader("Tabela")
    d["sede"] = d.nome.map(lambda n: "Matriz" if "Matriz" in n else "")
    tabela(d, {"nome": str, "ajustada": brl0, "yoy": var1, "margem_bruta": pct1, "taxa_devolucao": pct1, "despesas": brl0, "desp_pct": pct1, "pedidos": int0, "ticket": brl0},
           {"nome": "Filial", "ajustada": "Receita ajustada", "yoy": "Var. anual", "margem_bruta": "Margem bruta", "taxa_devolucao": "Taxa de devolução",
            "despesas": "Despesas", "desp_pct": "Despesas % da Receita Ajustada", "pedidos": "Pedidos", "ticket": "Ticket por pedido"})
    st.caption("A Matriz concentra despesas corporativas: 'Despesas % da Receita Ajustada' da Matriz não é comparável às demais filiais. Pedidos não são aditivos entre filiais.")
    premissas("PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-SIN-01")
