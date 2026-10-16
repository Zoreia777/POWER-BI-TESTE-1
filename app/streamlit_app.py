"""Empresa X — Inteligência Comercial 360° · aplicativo analítico (Etapa 5).

    streamlit run app/streamlit_app.py

Lê SOMENTE as views `bi` do warehouse DuckDB, em modo somente leitura. Se o banco não existir: python scripts/run_etl.py && python scripts/run_powerbi.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "app")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from componentes import Contexto, rodape  # noqa: E402
from empresax.analise import fmt  # noqa: E402
from empresax.app.base import BancoIndisponivel, abrir, assinatura, caminho_banco  # noqa: E402
from empresax.app.consultas import Repositorio  # noqa: E402
from empresax.app.filtros import Filtros  # noqa: E402
from paginas import filiais, investigacoes, orcamento, produtos, visao_geral  # noqa: E402

st.set_page_config(page_title="Empresa X · Inteligência Comercial 360°", page_icon="📊", layout="wide", initial_sidebar_state="auto")
st.markdown("""<style>
.block-container {padding-top: 2.2rem; max-width: 1400px;}
/* Cartões de métrica: nada de reticências. Rótulo quebra em até 2 linhas; valor reduz com a largura do cartão. */
[data-testid="stMetric"] {container-type: inline-size; width: 100%; min-width: 0; overflow: visible;}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] p {
    white-space: normal !important; overflow: visible !important; text-overflow: clip !important; overflow-wrap: anywhere; line-height: 1.25;}
[data-testid="stMetricLabel"] p {font-size: 0.82rem; opacity: 0.72;}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {
    white-space: normal !important; overflow: visible !important; text-overflow: clip !important; overflow-wrap: anywhere;
    font-size: clamp(1.05rem, 11cqw, 1.55rem); line-height: 1.2;}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] > div {white-space: normal !important; overflow: visible !important; text-overflow: clip !important; overflow-wrap: anywhere;}
/* Colunas: em telas estreitas quebram de linha em vez de espremer os cartões. */
[data-testid="stHorizontalBlock"] {flex-wrap: wrap; row-gap: 0.75rem;}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width: min(100%, 11.5rem);}
[data-testid="stHorizontalBlock"]:has(.js-plotly-plot) > [data-testid="stColumn"] {min-width: min(100%, 22rem);}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Abrindo o banco (somente leitura)…", max_entries=2)
def _repositorio(caminho: str, assin: tuple) -> Repositorio:
    """A assinatura (mtime+tamanho do arquivo) faz parte da chave: um novo ETL gera nova conexão e invalida os caches de dados."""
    return Repositorio(abrir(Path(caminho)))


def _barra_lateral(repo: Repositorio):
    st.sidebar.header("Filtros")
    meses = repo.meses
    atalho = st.sidebar.selectbox("Período", ["Ano corrente (até o último mês realizado)", "Últimos 12 meses", "Todo o histórico", "Personalizado"], key="atalho")
    ultimo = meses[-1]
    if atalho.startswith("Ano"):
        ini, fim = max(meses[0], ultimo.replace(month=1)), ultimo
    elif atalho.startswith("Últimos"):
        ini, fim = meses[max(0, len(meses) - 12)], ultimo
    elif atalho.startswith("Todo"):
        ini, fim = meses[0], ultimo
    else:
        ini, fim = st.sidebar.select_slider("Meses", options=meses, value=(max(meses[0], ultimo.replace(month=1)), ultimo), format_func=lambda d: fmt.mes(pd.Timestamp(d)), key="meses")
    st.sidebar.caption(f"Somente meses realizados (até {fmt.mes(pd.Timestamp(ultimo))}).")
    nf = st.sidebar.multiselect("Filiais", list(repo.filiais.filial), placeholder="Todas", key="f_filial")
    npd = st.sidebar.multiselect("Produtos", list(repo.produtos.produto), placeholder="Todos", key="f_prod")
    nc = st.sidebar.multiselect("Canais", list(repo.canais.canal), placeholder="Todos", key="f_canal")
    ids = lambda df, col_nome, col_id, sel: tuple(int(x) for x in df.loc[df[col_nome].isin(sel), col_id])  # noqa: E731
    f = Filtros(ini, fim, ids(repo.filiais, "filial", "id_filial", nf), ids(repo.produtos, "produto", "id_produto", npd), ids(repo.canais, "canal", "id_canal", nc))
    nomes = dict(filiais=", ".join(nf) or "todas", produtos=", ".join(npd) or "todos", canais=", ".join(nc) or "todos")
    st.sidebar.caption("Deixe os campos vazios para incluir todos.")
    return repo.validar(f), nomes


def main():
    caminho = caminho_banco()
    try:
        repo = _repositorio(str(caminho), assinatura(caminho))
    except BancoIndisponivel as e:
        st.title("Empresa X · Inteligência Comercial 360°")
        st.error(str(e), icon="🛑")
        st.stop()
    f, nomes = _barra_lateral(repo)
    ctx = Contexto(repo, assinatura(caminho), f, nomes)
    paginas = [st.Page(lambda: visao_geral.render(ctx), title="Visão Geral", icon=":material/dashboard:", url_path="visao-geral", default=True),
               st.Page(lambda: filiais.render(ctx), title="Filiais", icon=":material/store:", url_path="filiais"),
               st.Page(lambda: produtos.render(ctx), title="Produtos e Margem", icon=":material/inventory_2:", url_path="produtos"),
               st.Page(lambda: orcamento.render(ctx), title="Orçamento", icon=":material/account_balance_wallet:", url_path="orcamento"),
               st.Page(lambda: investigacoes.render(ctx), title="Investigações", icon=":material/search:", url_path="investigacoes")]
    st.navigation(paginas, position="top").run()
    rodape(ctx)


main()
