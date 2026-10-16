"""Gráficos Plotly do aplicativo (pt-BR: separators=',.' → 1.234,5; rótulos e tooltips com unidade)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Cores com contraste >= 3:1 contra fundo branco E contra o fundo escuro do Streamlit (#0e1117): servem nos dois temas.
AZUL, VERDE, VERMELHO, CINZA, LARANJA, ROXO = "#3F7FBF", "#2E9E62", "#D9473A", "#8A94A0", "#CC7A1E", "#8A78C8"
SEQ = [AZUL, LARANJA, VERDE, ROXO, "#23999F", CINZA, "#C0782B", "#7A9E3B"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
# Sem template nem cor de fonte fixos: o tema (claro/escuro) do Streamlit define texto, grade e fundo.
LAYOUT = dict(separators=",.", font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13),
              margin=dict(l=10, r=10, t=50, b=10), hoverlabel=dict(font_size=13), legend=dict(orientation="h", y=-0.18, x=0))
R = "R$ "


def rotulo_mes(ts) -> str:
    ts = pd.Timestamp(ts)
    return f"{MESES[ts.month - 1]}/{str(ts.year)[2:]}"


def _fig(titulo: str, altura: int = 380, **kw) -> go.Figure:
    f = go.Figure()
    f.update_layout(**{**LAYOUT, "title": dict(text=titulo, x=0, font=dict(size=15)), "height": altura, **kw})
    return f


def vazio(titulo: str, motivo: str) -> go.Figure:
    f = _fig(titulo, 220)
    f.add_annotation(text=motivo, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False)
    return f


def tendencia(serie: pd.DataFrame, titulo="Receita ajustada (provisória) e margem bruta por mês") -> go.Figure:
    if serie.empty:
        return vazio(titulo, "Sem vendas no período e recorte escolhidos.")
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_bar(x=serie.mes, y=serie.ajustada, name="Receita ajustada", marker_color=AZUL, customdata=np.c_[serie.registrada, serie.devolucoes],
              hovertemplate="<b>%{x|%b/%Y}</b><br>Receita ajustada: R$ %{y:,.0f}<br>Registrada: R$ %{customdata[0]:,.0f}<br>Devoluções: R$ %{customdata[1]:,.0f}<extra></extra>")
    f.add_scatter(x=serie.mes, y=serie.margem_bruta, name="Margem bruta %", mode="lines+markers", line=dict(color=LARANJA, width=2), secondary_y=True,
                  hovertemplate="<b>%{x|%b/%Y}</b><br>Margem bruta: %{y:.1%}<extra></extra>")
    f.update_layout(**{**LAYOUT, "title": dict(text=titulo, x=0, font=dict(size=15)), "height": 380})
    f.update_yaxes(title_text="Receita (R$)", tickprefix=R, tickformat=",.0f", secondary_y=False)
    f.update_yaxes(title_text="Margem bruta", tickformat=".0%", secondary_y=True, showgrid=False)
    return f


def sobreposicao_anual(serie: pd.DataFrame, titulo="Receita ajustada por mês — anos lado a lado") -> go.Figure:
    """Cada ano em uma linha, eixo = mês do ano. Só mostra meses existentes (nenhum mês futuro é preenchido)."""
    if serie.empty:
        return vazio(titulo, "Sem vendas no período e recorte escolhidos.")
    f = _fig(titulo)
    for i, (ano, g) in enumerate(serie.assign(ano=serie.mes.dt.year, m=serie.mes.dt.month).groupby("ano")):
        f.add_scatter(x=[MESES[m - 1] for m in g.m], y=g.ajustada, name=str(ano), mode="lines+markers", line=dict(color=SEQ[i % len(SEQ)], width=2),
                      hovertemplate=f"<b>%{{x}}/{ano}</b><br>Receita ajustada: R$ %{{y:,.0f}}<extra></extra>")
    f.update_xaxes(categoryorder="array", categoryarray=MESES)
    f.update_yaxes(tickprefix=R, tickformat=",.0f")
    return f


def ranking(df: pd.DataFrame, col: str, titulo: str, formato: str = "money", destaque: str | None = None, altura: int | None = None) -> go.Figure:
    """Barras horizontais ordenadas. formato: 'money' | 'pct'."""
    d = df.dropna(subset=[col]).sort_values(col)
    if d.empty:
        return vazio(titulo, "Sem dados para exibir.")
    cores = [VERMELHO if (v < 0 and formato == "pct") else (LARANJA if n == destaque else AZUL) for n, v in zip(d.nome, d[col])]
    hov = "R$ %{x:,.0f}" if formato == "money" else "%{x:.1%}"
    f = _fig(titulo, altura or max(300, 28 * len(d) + 110))
    f.add_bar(y=d.nome, x=d[col], orientation="h", marker_color=cores, hovertemplate="<b>%{y}</b><br>" + hov + "<extra></extra>",
              text=[(f"{v:,.0f}" if formato == "money" else f"{v * 100:.1f}%").replace(",", "X").replace(".", ",").replace("X", ".") for v in d[col]], textposition="outside", cliponaxis=False, textfont=dict(size=13))
    f.update_xaxes(tickprefix=R if formato == "money" else "", tickformat=",.0f" if formato == "money" else ".0%")
    topo = float(d[col].max())
    base = float(min(d[col].min(), 0))
    f.update_xaxes(range=[base * 1.7 if base < 0 else 0, topo * 1.3 if topo > 0 else 1], automargin=True)
    f.update_yaxes(automargin=True)      # espaço para o rótulo da barra maior
    return f


def mapa_yoy(m: pd.DataFrame, titulo="Variação anual da receita ajustada — filial × mês") -> go.Figure:
    if m.empty or m.notna().sum().sum() == 0:
        return vazio(titulo, "Não há mês com base comparável do ano anterior neste período.")
    z = m.values
    lim = float(np.nanmax(np.abs(np.clip(z, -1, 1.5))))
    f = _fig(titulo, max(300, 38 * len(m) + 120))
    f.add_heatmap(z=z, x=[rotulo_mes(c) for c in m.columns], y=list(m.index), colorscale="RdBu", zmid=0, zmin=-lim, zmax=lim, colorbar=dict(title="YoY", tickformat=".0%"),
                  hovertemplate="<b>%{y}</b> · %{x}<br>Variação anual: %{z:.1%}<extra></extra>", hoverongaps=False)
    return f


def bolhas_produtos(df: pd.DataFrame, titulo="Receita × margem bruta por produto (tamanho = nº de linhas)") -> go.Figure:
    d = df.dropna(subset=["margem_bruta"])
    if d.empty:
        return vazio(titulo, "Sem dados para exibir.")
    f = _fig(titulo, 460)
    f.add_scatter(x=d.ajustada, y=d.margem_bruta, mode="markers", text=d.nome, customdata=np.c_[d.linhas, d.pct_linhas_negativas.fillna(0)],
                  marker=dict(size=np.clip(np.sqrt(d.linhas) * 1.6, 7, 42), color=[VERMELHO if m < 0 else AZUL for m in d.margem_bruta], opacity=0.75, line=dict(width=0.5, color="white")),
                  hovertemplate="<b>%{text}</b><br>Receita ajustada: R$ %{x:,.0f}<br>Margem bruta: %{y:.1%}<br>Linhas: %{customdata[0]:,.0f}<br>Linhas com margem negativa: %{customdata[1]:.1%}<extra></extra>")
    f.add_hline(y=0, line_dash="dash", line_color=CINZA)
    f.update_xaxes(title="Receita ajustada (R$, escala logarítmica)", type="log", tickvals=[1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7],
                   ticktext=["R$ 100 mil", "R$ 200 mil", "R$ 500 mil", "R$ 1 mi", "R$ 2 mi", "R$ 5 mi", "R$ 10 mi"])
    f.update_yaxes(title="Margem bruta ajustada", tickformat=".0%")
    return f


def execucao_orcamento(df: pd.DataFrame, titulo: str, tolerancia: float = 0.05) -> go.Figure:
    d = df.dropna(subset=["execucao"]).sort_values("execucao")
    if d.empty:
        return vazio(titulo, "Sem orçamento no período e filial escolhidos.")
    f = _fig(titulo, max(300, 28 * len(d) + 120))
    cor = [VERMELHO if e > 1 + tolerancia else (VERDE if e < 1 - tolerancia else AZUL) for e in d.execucao]
    f.add_bar(y=d.nome, x=d.execucao, orientation="h", marker_color=cor, text=[f"{e * 100:.1f}%".replace(".", ",") for e in d.execucao], textposition="outside", cliponaxis=False, customdata=np.c_[d.orcado, d.realizado, d.desvio],
              hovertemplate="<b>%{y}</b><br>Execução: %{x:.1%}<br>Orçado: R$ %{customdata[0]:,.0f}<br>Realizado: R$ %{customdata[1]:,.0f}<br>Desvio: R$ %{customdata[2]:,.0f}<extra></extra>")
    f.add_vrect(x0=1 - tolerancia, x1=1 + tolerancia, fillcolor=CINZA, opacity=0.15, line_width=0)
    f.add_annotation(text=f"faixa cinza = ±{tolerancia:.0%} em torno de 100%", xref="paper", yref="paper", x=0, y=-0.2 if len(d) > 3 else -0.45, showarrow=False, font=dict(size=11))
    f.update_xaxes(tickformat=".0%", title="Realizado ÷ orçado ACUMULADO", range=[0, float(d.execucao.max()) * 1.18], automargin=True)
    f.update_yaxes(automargin=True)
    return f


def curva_orcamento(df: pd.DataFrame, titulo="Orçado × realizado por mês") -> go.Figure:
    if df.empty:
        return vazio(titulo, "Sem orçamento no período e filial escolhidos.")
    f = _fig(titulo)
    f.add_bar(x=df.mes, y=df.orcado, name="Orçado", marker_color=CINZA, hovertemplate="<b>%{x|%b/%Y}</b><br>Orçado: R$ %{y:,.0f}<extra></extra>")
    f.add_scatter(x=df.mes, y=df.realizado, name="Realizado", mode="lines+markers", line=dict(color=AZUL, width=2.5), hovertemplate="<b>%{x|%b/%Y}</b><br>Realizado: R$ %{y:,.0f}<extra></extra>")
    f.update_yaxes(tickprefix=R, tickformat=",.0f")
    return f


NOMES_EFEITOS = [("volume", "Volume"), ("mix", "Mix"), ("preco", "Preço"), ("desconto", "Desconto"), ("impostos", "Impostos"),
                 ("produto_novo", "Produtos novos"), ("produto_descontinuado", "Produtos que pararam"), ("efeito_devolucoes", "Devoluções")]


def cascata_pvm(res: dict, titulo: str, rot_base: str, rot_atual: str) -> go.Figure:
    """Receita ajustada da base → efeitos → receita ajustada do período atual. Fecha exatamente (o resíduo, se existir, vira uma barra)."""
    efeitos = [(n, float(res[k])) for k, n in NOMES_EFEITOS]
    resid = float(res["variacao_ajustada"]) - sum(v for _, v in efeitos)
    if abs(resid) >= 0.5:
        efeitos.append(("Resíduo", resid))
    base, atual = float(res["ajustada_base"]), float(res["ajustada_atual"])
    x = [rot_base] + [n for n, _ in efeitos] + [rot_atual]
    y = [base] + [v for _, v in efeitos] + [atual]
    txt = [_s(base)] + [_s(v, True) for _, v in efeitos] + [_s(atual)]
    f = _fig(titulo, 440)
    f.add_trace(go.Waterfall(x=x, y=y, measure=["absolute"] + ["relative"] * len(efeitos) + ["total"], text=txt, textposition="outside", cliponaxis=False,
                             connector=dict(line=dict(color=CINZA, width=1)), increasing=dict(marker=dict(color=VERDE)), decreasing=dict(marker=dict(color=VERMELHO)),
                             totals=dict(marker=dict(color=AZUL)), hovertemplate="<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>"))
    f.update_yaxes(tickprefix=R, tickformat=",.0f")
    menor, maior = min(base, atual), max(base, atual)
    if menor > 0 and max(abs(v) for _, v in efeitos) < 0.3 * menor:       # efeitos pequenos diante da base: ampliar o eixo, avisando
        f.update_yaxes(range=[menor * 0.85, maior * 1.04])
        f.add_annotation(text="Atenção: o eixo vertical não começa em zero (ampliado para mostrar os efeitos)", xref="paper", yref="paper", x=0, y=-0.32, showarrow=False, font=dict(size=11))
    return f


def _s(v: float, sinal: bool = False) -> str:
    s = f"{abs(v) / 1e3:,.1f} mil".replace(",", "X").replace(".", ",").replace("X", ".")
    return (("+" if v >= 0 else "−") if sinal else ("−" if v < 0 else "")) + s


def contribuicao_produtos(por: pd.DataFrame, titulo="Variação por produto (receita registrada)", n: int = 10) -> go.Figure:
    d = por.assign(abs_=por.variacao.abs()).nlargest(n, "abs_").sort_values("variacao")
    if d.empty:
        return vazio(titulo, "Sem dados.")
    f = _fig(titulo, max(300, 30 * len(d) + 110))
    f.add_bar(y=d.produto, x=d.variacao, orientation="h", marker_color=[VERDE if v >= 0 else VERMELHO for v in d.variacao],
              text=[_s(v, True) for v in d.variacao], textposition="outside", cliponaxis=False,
              hovertemplate="<b>%{y}</b><br>Variação: R$ %{x:,.0f}<extra></extra>")
    lo, hi = float(min(d.variacao.min(), 0)), float(max(d.variacao.max(), 0))
    pad = (hi - lo) * 0.28 or 1
    f.update_xaxes(tickprefix=R, tickformat=",.0f", range=[lo - (pad if lo < 0 else 0), hi + (pad if hi > 0 else 0)], automargin=True)
    f.update_yaxes(automargin=True)
    return f


def pa_serie(s: pd.DataFrame, destaque: pd.Timestamp, titulo="Porto Alegre — receita ajustada mensal e variação anual") -> go.Figure:
    f = make_subplots(specs=[[{"secondary_y": True}]])
    cores = [LARANJA if m == destaque else AZUL for m in s.mes]
    f.add_bar(x=s.mes, y=s.ajustada, name="Receita ajustada", marker_color=cores, hovertemplate="<b>%{x|%b/%Y}</b><br>Receita ajustada: R$ %{y:,.0f}<extra></extra>")
    f.add_scatter(x=s.mes, y=s.yoy, name="Variação anual", mode="lines+markers", line=dict(color=VERMELHO, width=1.8), marker=dict(size=5), secondary_y=True,
                  hovertemplate="<b>%{x|%b/%Y}</b><br>Variação anual: %{y:.1%}<extra></extra>")
    f.update_layout(**{**LAYOUT, "title": dict(text=titulo, x=0, font=dict(size=15)), "height": 400})
    f.update_yaxes(tickprefix=R, tickformat=",.0f", secondary_y=False)
    f.update_yaxes(tickformat=".0%", secondary_y=True, showgrid=False)
    return f


def pa_atividade(comp: pd.DataFrame, rot_base: str, rot_atual: str, titulo: str) -> go.Figure:
    """Variação % de cada medida: se pedidos/linhas mal mudam e a receita por linha despenca, a queda não é de 'movimento'."""
    d = comp.dropna(subset=["variacao"])
    f = _fig(titulo, 340)
    f.add_bar(x=d.metrica, y=d.variacao, marker_color=[VERDE if v >= 0 else VERMELHO for v in d.variacao], customdata=np.c_[d.base, d.atual],
              text=[f"{v * 100:+.1f}%".replace(".", ",") for v in d.variacao], textposition="outside", cliponaxis=False, textfont=dict(size=14),
              hovertemplate=f"<b>%{{x}}</b><br>{rot_base}: %{{customdata[0]:,.0f}}<br>{rot_atual}: %{{customdata[1]:,.0f}}<br>Variação: %{{y:.1%}}<extra></extra>")
    lo, hi = float(min(d.variacao.min(), 0)), float(max(d.variacao.max(), 0))
    pad = (hi - lo) * 0.18 or 0.1
    f.update_yaxes(tickformat=".0%", range=[lo - (pad if lo < 0 else 0), hi + (pad if hi > 0 else 0)], automargin=True)
    f.update_xaxes(automargin=True)
    return f


def sp_preco_custo(s: pd.DataFrame, programados: list | None = None, titulo="Smartphone X Max — preço, custo por unidade e margem bruta") -> go.Figure:
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_scatter(x=s.mes, y=s.preco_liquido_un, name="Preço líquido/un.", line=dict(color=AZUL, width=2.5), hovertemplate="<b>%{x|%b/%Y}</b><br>Preço líquido: R$ %{y:,.0f}/un.<extra></extra>")
    f.add_scatter(x=s.mes, y=s.custo_un, name="Custo/un.", line=dict(color=VERMELHO, width=2.5), hovertemplate="<b>%{x|%b/%Y}</b><br>Custo: R$ %{y:,.0f}/un.<extra></extra>")
    f.add_scatter(x=s.mes, y=s.margem_bruta, name="Margem bruta", line=dict(color=LARANJA, width=2, dash="dot"), secondary_y=True, hovertemplate="<b>%{x|%b/%Y}</b><br>Margem bruta: %{y:.1%}<extra></extra>")
    f.update_layout(**{**LAYOUT, "title": dict(text=titulo, x=0, font=dict(size=15)), "height": 420})
    f.update_yaxes(tickprefix=R, tickformat=",.0f", secondary_y=False)
    f.update_yaxes(tickformat=".0%", secondary_y=True, showgrid=False, zeroline=True)
    return f


def sp_linhas_negativas(s: pd.DataFrame, titulo="Smartphone X Max — % de linhas com margem negativa por mês") -> go.Figure:
    f = _fig(titulo, 300)
    f.add_bar(x=s.mes, y=s.pct_linhas_negativas, marker_color=VERMELHO, customdata=np.c_[s.linhas_negativas, s.linhas],
              hovertemplate="<b>%{x|%b/%Y}</b><br>%{y:.1%} das linhas (%{customdata[0]:.0f} de %{customdata[1]:.0f})<extra></extra>")
    f.update_yaxes(tickformat=".0%", range=[0, 1.05])
    return f
