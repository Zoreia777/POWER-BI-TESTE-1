"""Página 4 — Orçamento."""
import streamlit as st

from componentes import esc, brl0, brl_mil, cabecalho, consultar, metrica, pct1, premissas, tabela
from empresax.app import graficos as G
from empresax.app import textos
from empresax.config import Config


def render(ctx):
    cabecalho("Orçamento", "Despesas realizadas contra o orçamento dos MESMOS meses (acumulado).", ctx)
    if ctx.filtros.tem_produto_ou_canal:
        st.info(textos.ORCAMENTO_FILTROS)
    o = consultar(ctx, "orcamento")
    if o["vazio"]:
        st.warning("Não há orçamento nem despesas para o período e a filial escolhidos.", icon="⚠️")
        premissas("PN-ORC-01")
        return
    tol = Config().tolerancia_orcamento_pct
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(border=True):
        metrica("Orçado acumulado", brl_mil(o["orcado_acumulado"]), None, f"{brl0(o['orcado_acumulado'])}. Orçamento dos meses do período (todos realizados).")
    with c2, st.container(border=True):
        metrica("Realizado", brl_mil(o["realizado"]), None, brl0(o["realizado"]))
    with c3, st.container(border=True):
        metrica("Execução do orçamento", pct1(o["execucao"]), None, f"Realizado ÷ orçado acumulado. Dentro da faixa quando entre {pct1(1 - tol)} e {pct1(1 + tol)}.")
        dentro = o["execucao"] is not None and abs(o["execucao"] - 1) <= tol
        st.caption("Dentro da faixa" if dentro else ("Acima do orçado" if (o["execucao"] or 0) > 1 else "Abaixo do orçado"))
    with c4, st.container(border=True):
        metrica("Desvio", brl_mil(o["desvio"]), None, "Realizado − orçado acumulado. Positivo = gastou acima do orçado.", delta_color="off")

    with st.expander("Três conceitos que NÃO se misturam: anual × acumulado × realizado", expanded=True):
        a, b, c = st.columns(3)
        a.metric("Orçamento ANUAL (12 meses)", brl_mil(o["orcado_anual"]), help="Inclui meses futuros. Referência de saldo, não de execução.")
        b.metric("Orçamento ACUMULADO (meses do período)", brl_mil(o["orcado_acumulado"]))
        c.metric("Realizado", brl_mil(o["realizado"]))
        st.markdown(esc(f"Dividir o realizado pelo orçamento **anual** daria **{pct1(o['consumo_anual'])}** ('consumo do orçamento anual'), o que sugere uma economia que **não existe** quando o ano ainda não terminou. "
                    f"A leitura correta é contra o orçado dos mesmos meses: **{pct1(o['execucao'])}**."))
        st.markdown(textos.PREMISSAS["PN-ORC-01"])

    st.plotly_chart(G.curva_orcamento(consultar(ctx, "orcamento_mensal")), width="stretch")
    e1, e2 = st.columns(2)
    with e1:
        st.plotly_chart(G.execucao_orcamento(consultar(ctx, "orcamento_por", None, "departamento"), "Execução por departamento", tol), width="stretch")
    with e2:
        st.plotly_chart(G.execucao_orcamento(consultar(ctx, "orcamento_por", None, "categoria"), "Execução por categoria de despesa", tol), width="stretch")
    st.subheader("Maiores desvios em reais (acima do orçado)")
    cat = consultar(ctx, "orcamento_por", None, "categoria")
    tabela(cat.head(8), {"nome": str, "orcado": brl0, "realizado": brl0, "desvio": brl0, "execucao": pct1},
           {"nome": "Categoria", "orcado": "Orçado acumulado", "realizado": "Realizado", "desvio": "Desvio (R$)", "execucao": "Execução"})
    st.caption("Percentuais altos em valores pequenos merecem menos atenção que desvios grandes em reais: avalie os dois.")
    premissas("PN-ORC-01", "PN-SIN-01")
