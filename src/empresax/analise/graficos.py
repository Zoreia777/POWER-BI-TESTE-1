"""Gráficos Plotly (estáticos em HTML) das investigações. Cada função recebe o dicionário {id: Investigacao}."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

AZUL, VERM, CINZA, VERDE, LARANJA = "#1f4e79", "#c0392b", "#9aa5b1", "#2e8b57", "#e08e0b"
LAYOUT = dict(template="plotly_white", font=dict(family="Arial, sans-serif", size=13), margin=dict(l=60, r=30, t=70, b=50), height=460)


def _fig(titulo: str, **kw) -> go.Figure:
    f = go.Figure()
    f.update_layout(**{**LAYOUT, "title": dict(text=titulo, x=0.01), **kw})
    return f


def g01_pa_serie(I) -> go.Figure:
    s = I["INV1"].tabelas["serie_mensal"]
    cores = [VERM if m == pd.Timestamp("2026-02-01") else (LARANJA if m == pd.Timestamp("2025-02-01") else AZUL) for m in s.mes]
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_bar(x=s.mes, y=s.receita_ajustada, marker_color=cores, name="Receita ajustada (R$)")
    f.add_scatter(x=s.mes, y=s.receita_por_linha, name="Receita por linha (R$)", line=dict(color=CINZA, width=3), secondary_y=True)
    f.update_layout(title=dict(text="Porto Alegre: receita mensal (fev/25 em laranja, fev/26 em vermelho) e receita por linha", x=0.01), **LAYOUT,
                    legend=dict(orientation="h", y=-0.15))
    f.update_yaxes(title_text="R$", secondary_y=False); f.update_yaxes(title_text="R$ por linha", secondary_y=True, showgrid=False)
    return f


def g02_pa_waterfall(I) -> go.Figure:
    r = I["INV1"].metricas["pvm"]
    nomes = ["Volume", "Mix", "Preço", "Desconto", "Produto novo", "Produto que parou"]
    vals = [r["volume"], r["mix"], r["preco"], r["desconto"], r["produto_novo"], r["produto_descontinuado"]]
    f = _fig("Porto Alegre fev/26 vs fev/25: decomposição da variação da receita (R$)")
    f.add_trace(go.Waterfall(x=["Fev/25"] + nomes + ["Fev/26"], y=[r["receita_base"]] + vals + [0],
                             measure=["absolute"] + ["relative"] * len(vals) + ["total"],
                             text=[f"{x / 1e3:,.0f} mil" for x in [r["receita_base"]] + vals + [r["receita_atual"]]], textposition="outside",
                             decreasing=dict(marker_color=VERM), increasing=dict(marker_color=VERDE), totals=dict(marker_color=AZUL)))
    return f


def g03_pa_notebook(I) -> go.Figure:
    s = I["INV1"].tabelas["produto_top_unidades_mensais"]
    cores = [LARANJA if m == pd.Timestamp("2025-02-01") else (VERM if m == pd.Timestamp("2026-02-01") else AZUL) for m in s.mes]
    f = _fig("Porto Alegre: unidades mensais do produto que mais explica a queda")
    f.add_bar(x=s.mes, y=s.unidades, marker_color=cores)
    f.update_yaxes(title_text="unidades")
    return f


def g04_heatmap_yoy(I) -> go.Figure:
    m = I["INV2"].tabelas["matriz_yoy_filial"].set_index("mes").dropna(how="all")
    f = _fig("Variação anual da receita ajustada por filial e mês (vazio = sem base de comparação)", height=420)
    f.add_trace(go.Heatmap(z=(m.T.values * 100), x=[x.strftime("%Y-%m") for x in m.index], y=list(m.columns), zmid=0, zmin=-50, zmax=50,
                           colorscale="RdBu", colorbar=dict(title="%"), hovertemplate="%{y} %{x}: %{z:.1f}%<extra></extra>"))
    return f


def g05_quedas_produto(I) -> go.Figure:
    t = I["INV2"].tabelas["quedas_produto_yoy"].head(15).iloc[::-1]
    cor = [VERM if p else (LARANJA if s else CINZA) for p, s in zip(t.programado != "", t.persistente)]
    f = _fig("15 maiores quedas anuais de produto (vermelho = evento programado; laranja = persistente; cinza = episódio curto)", height=520)
    f.add_bar(y=[f"{a} · {m:%b/%y}" for a, m in zip(t.produto, t.mes)], x=t.queda_rs, orientation="h", marker_color=cor)
    f.update_xaxes(title_text="receita perdida vs mesmo mês do ano anterior (R$)")
    return f


def g06_smartphone(I) -> go.Figure:
    s = I["INV3"].tabelas["serie_mensal"]
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_scatter(x=s.mes, y=s.preco_liquido_un, name="Preço líquido por unidade", line=dict(color=AZUL, width=3))
    f.add_scatter(x=s.mes, y=s.custo_un, name="Custo por unidade", line=dict(color=VERM, width=3))
    f.add_bar(x=s.mes, y=s.pct_linhas_neg * 100, name="% de linhas com margem negativa", marker_color=CINZA, opacity=0.35, secondary_y=True)
    f.update_layout(title=dict(text="Smartphone X Max: custo por unidade ultrapassa o preço líquido", x=0.01), **LAYOUT, legend=dict(orientation="h", y=-0.15))
    f.update_yaxes(title_text="R$ por unidade", secondary_y=False); f.update_yaxes(title_text="% linhas negativas", secondary_y=True, range=[0, 100], tickvals=[0, 25, 50, 75, 100], showgrid=False)
    return f


def g07_margens(I) -> go.Figure:
    s = I["INV4"].tabelas["serie_mensal"]
    f = _fig("Margem bruta e margem operacional ESTIMADA do dataset (receita ajustada)")
    f.add_scatter(x=s.mes, y=s.margem_bruta * 100, name="Margem bruta (%)", line=dict(color=AZUL, width=3))
    f.add_scatter(x=s.mes, y=s.margem_operacional * 100, name="Margem operacional estimada (%)", line=dict(color=VERDE, width=3))
    f.update_yaxes(title_text="%"); f.update_layout(legend=dict(orientation="h", y=-0.15))
    return f


def g08_margem_waterfall(I) -> go.Figure:
    d = I["INV4"].metricas["decomposicao"]
    chave = I["INV4"].metricas["chave_decomposicao_total"]
    res = d[chave]
    por = I["INV4"].tabelas["contribuicao_por_produto_24_26"]
    sm, nb = por[por.produto == "Smartphone X Max"].efeito_taxa.sum(), por[por.produto == 'Notebook Pro 14"'].efeito_taxa.sum()
    outros = res["taxa"] - sm - nb
    f = _fig(f"Variação da margem bruta {chave.replace('-', '→')} (jan–set, em pontos percentuais)")
    f.add_trace(go.Waterfall(x=[f"Margem {chave.split('-')[0]}", "Mix de produtos", "Taxa: Smartphone X Max", "Taxa: Notebook Pro 14\"", "Taxa: demais produtos", f"Margem {chave.split('-')[1]}"],
                             y=[res["margem_base"] * 100, res["mix"] * 100, sm * 100, nb * 100, outros * 100, 0],
                             measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                             text=[f"{x * 100:.2f}" for x in (res["margem_base"], res["mix"], sm, nb, outros, res["margem_atual"])], textposition="outside",
                             decreasing=dict(marker_color=VERM), increasing=dict(marker_color=VERDE), totals=dict(marker_color=AZUL)))
    f.update_yaxes(range=[36, 45], title_text="%")
    return f


def g09_orcamento_conceitos(I) -> go.Figure:
    t = I["INV5"].tabelas["tres_conceitos_por_ano"].iloc[-1]
    f = _fig(f"Orçamento {int(t.ano)}: anual × acumulado × realizado (R$)")
    f.add_bar(x=["Orçamento ANUAL", "Orçamento ACUMULADO", "Realizado ACUMULADO"], y=[t.orcamento_anual, t.orcamento_acumulado, t.realizado_acumulado],
              marker_color=[CINZA, AZUL, VERDE], text=[f"{v / 1e6:.2f} mi" for v in (t.orcamento_anual, t.orcamento_acumulado, t.realizado_acumulado)], textposition="outside")
    f.add_annotation(x=0.5, y=1.0, xref="paper", yref="paper", showarrow=False, yshift=18,
                     text=f"Leitura correta: {t.execucao_correta * 100:.1f}% · leitura ingênua (÷ anual): {t.leitura_ingenua * 100:.1f}%")
    return f


def g10_orcamento_categoria(I) -> go.Figure:
    t = I["INV5"].tabelas["por_categoria"].sort_values("execucao")
    cor = [VERM if s == "acima_do_orcado" else (AZUL if s == "abaixo_do_orcado" else CINZA) for s in t.situacao]
    f = _fig("Execução acumulada por categoria de despesa (% do orçado acumulado; faixa de ±5% sombreada)", height=560)
    f.add_vrect(x0=95, x1=105, fillcolor="lightgray", opacity=0.4, line_width=0)
    f.add_bar(y=t.categoria_despesa, x=t.execucao * 100, orientation="h", marker_color=cor)
    f.update_xaxes(range=[80, max(135, float(t.execucao.max() * 100) + 3)], title_text="%")
    return f


def g11_pvm_yoy(I) -> go.Figure:
    s = I["INV6"].tabelas["pvm_yoy_serie"]
    f = _fig("Variação anual da receita registrada decomposta (R$)")
    for k, nome, cor in (("volume", "Volume", AZUL), ("mix", "Mix", LARANJA), ("preco", "Preço", VERDE), ("desconto", "Desconto", VERM)):
        f.add_bar(x=s.periodo, y=s[k], name=nome, marker_color=cor)
    f.update_layout(barmode="relative", legend=dict(orientation="h", y=-0.15))
    return f


def g12_correlacoes(I) -> go.Figure:
    c = I["INV6"].tabelas["correlacao_spearman_variacao_mensal"].set_index("indicador")
    f = _fig("Correlação de Spearman entre variações mensais (associação, não causa)", height=480)
    f.add_trace(go.Heatmap(z=c.values, x=list(c.columns), y=list(c.index), zmin=-1, zmax=1, colorscale="RdBu", text=np.round(c.values, 2), texttemplate="%{text}"))
    return f


def g13_canais(I) -> go.Figure:
    s = I["INV6"].tabelas["serie_mensal"]
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_scatter(x=s.mes, y=s.share_marketplace * 100, name="Peso do marketplace (% da receita bruta)", line=dict(color=LARANJA, width=3))
    f.add_scatter(x=s.mes, y=s.margem_bruta * 100, name="Margem bruta (%)", line=dict(color=AZUL, width=3), secondary_y=True)
    f.update_layout(title=dict(text="Mix de canais (marketplace) e margem bruta", x=0.01), **LAYOUT, legend=dict(orientation="h", y=-0.15))
    return f


GRAFICOS = {"g01_pa_serie": g01_pa_serie, "g02_pa_waterfall": g02_pa_waterfall, "g03_pa_notebook": g03_pa_notebook,
            "g04_heatmap_yoy": g04_heatmap_yoy, "g05_quedas_produto": g05_quedas_produto, "g06_smartphone": g06_smartphone,
            "g07_margens": g07_margens, "g08_margem_waterfall": g08_margem_waterfall, "g09_orcamento_conceitos": g09_orcamento_conceitos,
            "g10_orcamento_categoria": g10_orcamento_categoria, "g11_pvm_yoy": g11_pvm_yoy, "g12_correlacoes": g12_correlacoes,
            "g13_canais": g13_canais}
