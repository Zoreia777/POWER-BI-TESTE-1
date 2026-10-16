"""Componentes compartilhados das páginas (formatação, cartões, estados vazios, premissas, cache)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from empresax.analise import fmt
from empresax.app import textos
from empresax.app.consultas import Repositorio
from empresax.app.filtros import Filtros
from empresax.app.graficos import rotulo_mes


@dataclass
class Contexto:
    repo: Repositorio
    assinatura: tuple
    filtros: Filtros
    nomes: dict          # descrição dos filtros para exibição


def chave(f: Filtros) -> tuple:
    return (f.inicio, f.fim, f.filiais, f.produtos, f.canais)


@st.cache_data(show_spinner=False, max_entries=512)
def _consulta(_repo: Repositorio, assinatura: tuple, metodo: str, f: tuple | None, extra: tuple):
    """Cache com invalidação controlada: a chave inclui a assinatura (mtime+tamanho) do arquivo do banco, então um novo ETL invalida tudo."""
    args = [Filtros(*f)] if f is not None else []
    return getattr(_repo, metodo)(*args, *extra)


def consultar(ctx: Contexto, metodo: str, f: Filtros | None = None, *extra):
    """Chama um método do repositório com cache. `f=None` usa os filtros da barra lateral; passe outro Filtros para consultas próprias."""
    f = ctx.filtros if f is None else f
    return _consulta(ctx.repo, ctx.assinatura, metodo, chave(f), tuple(extra))


def pvm_cache(ctx: Contexto, atual: Filtros, base: Filtros):
    return _pvm(ctx.repo, ctx.assinatura, chave(atual), chave(base))


@st.cache_data(show_spinner=False, max_entries=64)
def _pvm(_repo, assinatura, a, b):
    return _repo.pvm_periodo(Filtros(*a), Filtros(*b))


def periodo_txt(f: Filtros) -> str:
    return f"{rotulo_mes(f.inicio)} a {rotulo_mes(f.fim)}" if f.inicio != f.fim else rotulo_mes(f.inicio)


def cabecalho(titulo: str, subtitulo: str, ctx: Contexto):
    st.title(titulo)
    st.caption(subtitulo)
    n = ctx.nomes
    st.markdown(f"**Recorte:** período {periodo_txt(ctx.filtros)} · filiais: {n['filiais']} · produtos: {n['produtos']} · canais: {n['canais']}")


def brl_mil(x) -> str:
    return "—" if x is None or pd.isna(x) else fmt.mil(float(x))


def brl0(x) -> str:
    return "—" if x is None or pd.isna(x) else fmt.brl(float(x))


def pct1(x) -> str:
    return "—" if x is None or pd.isna(x) else fmt.pct(float(x))


def var1(x) -> str:
    return "—" if x is None or pd.isna(x) else fmt.var(float(x))


def int0(x) -> str:
    return "—" if x is None or pd.isna(x) else fmt.num(float(x))


def metrica(rotulo: str, valor: str, delta: str | None = None, ajuda: str | None = None, delta_color: str = "normal"):
    st.metric(rotulo, valor, delta=delta, help=ajuda, delta_color=delta_color)


def sem_resultado():
    st.warning(textos.SEM_RESULTADO, icon="⚠️")


def premissas(*ids: str, titulo: str = "Premissas e limitações que valem para esta página", aberto: bool = False):
    with st.expander(titulo, expanded=aberto):
        for i in ids:
            st.markdown("- " + textos.PREMISSAS[i])


def tabela(df: pd.DataFrame, formatos: dict, nomes: dict | None = None, altura: int | None = None):
    """Formata colunas como texto pt-BR (o formatador do navegador usaria separadores en-US)."""
    d = df.copy()
    for col, fn in formatos.items():
        d[col] = d[col].map(fn)
    d = d[list(formatos)].rename(columns=nomes or {})
    st.dataframe(d, hide_index=True, width="stretch", height=altura or "content")


def esc(texto: str) -> str:
    """Escapa o cifrão: no Markdown do Streamlit, dois 'R$' no mesmo texto viram fórmula (LaTeX) e quebram a leitura."""
    return texto.replace("$", "\\$")


def selo(tipo: str) -> str:
    cor = {"OBSERVAÇÃO": "blue", "CONCLUSÃO ARITMÉTICA": "green", "HIPÓTESE": "orange", "PADRÃO PROGRAMADO": "violet"}.get(tipo, "gray")
    return f":{cor}-badge[{tipo}]"


def mostrar_achados(achados: list[dict], ids: tuple | None = None):
    """Achados rotulados; hipóteses ganham um aviso explícito de que NÃO são causas comprovadas."""
    if not achados:
        st.info("Os achados rotulados ainda não foram gerados. Rode no terminal: python scripts/run_analises.py")
        return
    ordem = {"OBSERVAÇÃO": 0, "CONCLUSÃO ARITMÉTICA": 1, "HIPÓTESE": 2, "PADRÃO PROGRAMADO": 3}
    for a in sorted(achados, key=lambda x: (ordem.get(x["tipo"], 9), x["id"])):
        if ids and a["id"] not in ids:
            continue
        st.markdown(f"{selo(a['tipo'])} `{a['id']}` {esc(a['texto'])}")
        if a["tipo"] == "HIPÓTESE":
            st.caption("↳ Explicação possível, NÃO comprovada pelos dados.")


def rodape(ctx: Contexto):
    s = ctx.repo.fonte()
    carga = s["ultima_carga"].strftime("%d/%m/%Y %H:%M") if s["ultima_carga"] is not None else "não registrada"
    st.divider()
    st.caption(f"Fonte: warehouse DuckDB, views `bi` (somente leitura) · Dados de {rotulo_mes(s['primeiro_mes'])} a {rotulo_mes(s['ultimo_mes'])} (último mês realizado; meses futuros nunca são tratados como realizados) · "
               f"Última carga do ETL: {carga} · Dados fictícios (PN-SIN-01): números de uma empresa inexistente.")
