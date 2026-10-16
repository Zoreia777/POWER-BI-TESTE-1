"""Página 3 — Produtos e Margem."""
import streamlit as st

from componentes import esc, brl0, cabecalho, consultar, int0, pct1, premissas, sem_resultado, tabela, var1
from empresax.app import graficos as G
from empresax.config import Config


def render(ctx):
    cabecalho("Produtos e Margem", "Quais produtos sustentam a receita e quais corroem a margem.", ctx)
    d = consultar(ctx, "por_dimensao", None, "produto")
    if d.empty:
        sem_resultado()
        return
    piso_padrao = Config().piso_linhas_margem
    piso = st.slider("Piso de linhas de venda por produto no ranking de margem", 0, 1000, piso_padrao, step=50,
                     help="Evita ranquear produtos com poucas vendas. O padrão (200) é o mesmo usado nas análises SQL da Etapa 3. 0 = todos.")
    visiveis = d[d.linhas >= piso]
    ocultos = len(d) - len(visiveis)
    if ocultos:
        st.caption(esc(f"{ocultos} produto(s) com menos de {piso} linhas no recorte ficaram fora dos gráficos e do ranking (continuam no total da empresa)."))
    if visiveis.empty:
        st.warning("Nenhum produto atinge o piso de linhas neste recorte. Reduza o piso ou amplie o período.")
        return

    st.plotly_chart(G.bolhas_produtos(visiveis), width="stretch")
    st.caption("Produtos abaixo da linha tracejada vendem com prejuízo bruto. Bolhas vermelhas = margem negativa no recorte. A escala do eixo horizontal é logarítmica.")

    c1, c2 = st.columns(2)
    with c1:
        pior = visiveis.nsmallest(10, "margem_bruta")
        st.plotly_chart(G.ranking(pior, "margem_bruta", "10 menores margens brutas", "pct"), width="stretch")
    with c2:
        cat = consultar(ctx, "por_dimensao", None, "categoria")
        st.plotly_chart(G.ranking(cat, "margem_bruta", "Margem bruta por categoria", "pct"), width="stretch")

    st.subheader("Ranking de margem")
    t = visiveis.sort_values("margem_bruta").reset_index(drop=True)
    t.insert(0, "pos", range(1, len(t) + 1))
    tabela(t, {"pos": str, "nome": str, "ajustada": brl0, "margem_bruta": pct1, "pct_linhas_negativas": pct1, "desconto_efetivo": pct1, "taxa_devolucao": pct1, "yoy": var1, "linhas": int0},
           {"pos": "#", "nome": "Produto", "ajustada": "Receita ajustada", "margem_bruta": "Margem bruta", "pct_linhas_negativas": "% linhas negativas",
            "desconto_efetivo": "Desconto efetivo", "taxa_devolucao": "Taxa de devolução", "yoy": "Var. anual", "linhas": "Linhas"}, altura=420)
    neg = visiveis[visiveis.margem_bruta < 0]
    if len(neg):
        st.error(esc(f"{len(neg)} produto(s) com margem bruta NEGATIVA no recorte: {', '.join(neg.nome)}. Veja o estudo do Smartphone X Max em Investigações."), icon="🔴")
    premissas("PN-DEV-01", "PN-DEV-02", "PN-MRG-01", "PN-SIN-01")
