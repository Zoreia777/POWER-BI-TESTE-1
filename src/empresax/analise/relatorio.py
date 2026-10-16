"""Monta o relatório executivo (Markdown + HTML) e grava evidências (CSV) e gráficos (HTML) de forma determinística."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import pandas as pd

from ..config import Config
from ..consultas import para_csv
from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, TIPOS, Investigacao
from .dados import Dados, carregar
from .fmt import mes as fm, mil, pct, pp, var
from .graficos import GRAFICOS
from . import inv_margem, inv_orcamento, inv_porto_alegre, inv_quedas, inv_relacoes, inv_smartphone

ORDEM = ["INV1", "INV2", "INV3", "INV4", "INV5", "INV6"]
GRAFICOS_POR_INV = {"INV1": ["g01_pa_serie", "g02_pa_waterfall", "g03_pa_notebook"], "INV2": ["g04_heatmap_yoy", "g05_quedas_produto"],
                    "INV3": ["g06_smartphone"], "INV4": ["g07_margens", "g08_margem_waterfall"], "INV5": ["g09_orcamento_conceitos", "g10_orcamento_categoria"],
                    "INV6": ["g11_pvm_yoy", "g12_correlacoes", "g13_canais"]}
LEGENDA = {OBSERVACAO: "o que os dados mostram, medido", CONCLUSAO: "decorre diretamente das contas, sem interpretar causa",
           HIPOTESE: "explicação possível, NÃO comprovada", PROGRAMADO: "criado de propósito no gerador sintético (registro P01–P17)"}
COR = {OBSERVACAO: "#1f4e79", CONCLUSAO: "#2e8b57", HIPOTESE: "#e08e0b", PROGRAMADO: "#7d3c98"}


def executar_todas(cfg: Config | None = None, D: Dados | None = None) -> dict[str, Investigacao]:
    cfg = cfg or Config()
    D = D or carregar(cfg)
    invs = [inv_porto_alegre.executar(D), inv_quedas.executar(D, cfg), inv_smartphone.executar(D), inv_margem.executar(D),
            inv_orcamento.executar(D, cfg), inv_relacoes.executar(D)]
    return {i.id: i for i in invs}


# ------------------------------------------------------------------ Markdown / HTML
def tabela_md(df: pd.DataFrame, n: int = 8, fmt: dict | None = None) -> str:
    d = df.head(n).copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m")
        elif pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else (f"{x:,.2f}" if abs(x) >= 100 else f"{x:.4f}"))
    cab = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "|".join("---" for _ in d.columns) + "|\n"
    return cab + "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in d.itertuples(index=False)) + "\n"


def tabela_html(df: pd.DataFrame, n: int = 8) -> str:
    d = df.head(n).copy()
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m")
        elif pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else (f"{x:,.2f}" if abs(x) >= 100 else f"{x:.4f}"))
    return d.to_html(index=False, border=0, classes="t", escape=True)


TABELA_CHAVE = {"INV1": ["comparacao_fev25_fev26", "clientes_maiores_na_base"], "INV2": ["quedas_filial_yoy", "quedas_produto_resumo"],
                "INV3": ["preco_necessario", "negativas_por_faixa_desconto"], "INV4": ["resumo_ytd", "decomposicao_margem_bruta"],
                "INV5": ["tres_conceitos_por_ano", "por_categoria"], "INV6": ["desconto_vs_quantidade", "canais_ytd"]}


def resumo_executivo(I: dict[str, Investigacao], D: Dados) -> list[str]:
    a, b, c, d, e, f = (I[k] for k in ORDEM)
    ytd = d.metricas["ytd"]
    cresc = ytd[2]["receita_ajustada"] / ytd[1]["receita_ajustada"] - 1
    pv = f.metricas["pvm_anos"][D.ultimo_mes.year]
    return [
        f"**Crescimento é sobretudo volume.** Receita ajustada jan–{fm(D.ultimo_mes)[:3]}: {mil(ytd[2]['receita_ajustada'])} ({var(cresc)} sobre o ano anterior). "
        f"Na decomposição, volume responde por {pct(pv['volume'] / pv['variacao_registrada'], 0)} da variação, preço {pct(pv['preco'] / pv['variacao_registrada'], 0)} e mix {pct(pv['mix'] / pv['variacao_registrada'], 0)}.",
        f"**Margem bruta em queda de {pp(d.metricas['delta_mb']).lstrip('+-')} em dois anos, concentrada em dois produtos.** {d.tabelas['contribuicao_por_produto_24_26'].sort_values('efeito_taxa').produto.iloc[0]} e "
        f"{d.tabelas['contribuicao_por_produto_24_26'].sort_values('efeito_taxa').produto.iloc[1]} respondem por {pct(d.metricas['duas_share_delta'], 0)} da queda da margem bruta. "
        f"Despesas crescendo menos que a receita mantiveram a margem operacional estimada em {pct(ytd[0]['margem_operacional'])} → {pct(ytd[2]['margem_operacional'])}.",
        f"**Smartphone X Max vende com prejuízo bruto desde {fm(c.metricas['mes_todas_linhas_neg'])}** (100% das linhas negativas); custo por unidade +{pct(c.metricas['cresc_custo'], 0)} com preço fixo. "
        f"Para margem zero o preço teria de subir {pct(c.metricas['tab_preco'][0]['aumento_sobre_lista'], 0)} sobre a lista (cálculo aritmético, sem elasticidade).",
        f"**Porto Alegre em fev/26 ({var(a.metricas['yoy'])}) é, em grande parte, efeito de uma base atípica**: pedidos {var(a.metricas['var_pedidos'])} e linhas {var(a.metricas['var_linhas'])}, "
        f"mas receita por linha {var(a.metricas['var_rpl'])}; um produto explica {pct(a.metricas['top_produto_share'], 0)} da variação. Causa não comprovada (hipótese).",
        f"**Quedas anuais: poucas merecem atenção.** {b.metricas['n_quedas_filial']} quedas de filial (nenhuma persistente) e {b.metricas['n_quedas_produto']} de produto "
        f"({b.metricas['n_prod_persistentes']} persistentes). A maior (Notebook Pro, ago/25) é evento programado (ruptura).",
        f"**Orçamento: comparar com o acumulado.** Execução correta {pct(e.metricas['exec_correta'])} contra {pct(e.metricas['exec_ingenua'])} na leitura ingênua; "
        f"{e.metricas['dep_top']} é o único departamento acima da faixa ({pct(e.metricas['dep_top_exec'])}).",
        f"**Desconto e quantidade: a associação some ao controlar canal e segmento** (de {f.metricas['coef_desc_qtd'] / 100:.3f} para {f.metricas['coef_desc_qtd_controlado'] / 100:.3f} unidade por p.p.): "
        "exemplo de confusão que impede ler correlação como causa.",
    ]


def _bloco_achados(inv: Investigacao, html_mode: bool) -> str:
    out = []
    for t in TIPOS:
        for a in [x for x in inv.achados if x.tipo == t]:
            if html_mode:
                out.append(f'<p class="a"><span class="b" style="background:{COR[t]}">{t}</span> <small>{a.id}</small> {html.escape(a.texto)}</p>')
            else:
                out.append(f"- **[{t}]** `{a.id}` {a.texto}")
    return "\n".join(out)


def gerar_markdown(I: dict[str, Investigacao], D: Dados, h: dict[str, str]) -> str:
    L = ["# Relatório executivo — Investigação analítica da Empresa X (Etapa 4)", "",
         "> **Dados 100% sintéticos.** Padrões, quedas e margens foram em parte *programados* no gerador (`mart.ref_comportamentos_sinteticos`, P01–P17). "
         "Nada aqui é evidência sobre empresas ou mercados reais; o objetivo é demonstrar método. Receita = *receita ajustada provisória* (PN-DEV-01). "
         "“Resultado operacional estimado” **não é lucro líquido contábil**.", "",
         "## Como ler os achados", ""]
    L += [f"- **{t}** — {LEGENDA[t]}." for t in TIPOS]
    L += ["", "Nenhuma causa é atribuída sem evidência: onde só há hipótese, ela vem rotulada e acompanhada de uma pergunta a investigar.", "",
          "## Resumo executivo", ""] + [f"{i}. {x}" for i, x in enumerate(resumo_executivo(I, D), 1)] + [""]
    for k in ORDEM:
        inv = I[k]
        L += [f"## {inv.titulo}", "", f"**Pergunta de negócio.** {inv.pergunta}", "", f"**Método.** {inv.metodo}", "", "### Evidências", "", _bloco_achados(inv, False), ""]
        for g in GRAFICOS_POR_INV[k]:
            L += [f"- 📈 Gráfico interativo: [`graficos/{g}.html`](graficos/{g}.html)"]
        for nome in TABELA_CHAVE[k]:
            L += ["", f"**Tabela — {nome}** (CSV completo em `evidencias/{k}_{nome}.csv`)", "", tabela_md(inv.tabelas[nome])]
        L += ["### Limitações dos dados", ""] + [f"- {x}" for x in inv.limitacoes]
        L += ["", "### Recomendações gerenciais (condicionais)", ""] + [f"- {x}" for x in inv.recomendacoes]
        L += ["", "### Próximas perguntas para uma empresa real", ""] + [f"- {x}" for x in inv.proximas] + [""]
    L += ["## Reprodutibilidade", "", "`python scripts/run_etl.py && python scripts/run_analises.py` regenera tudo. Hashes SHA-256 (CSV de evidências e gráficos) em `manifesto.json`.", ""]
    L += ["| Arquivo | SHA-256 (prefixo) |", "|---|---|"] + [f"| `{k}` | `{v[:16]}…` |" for k, v in sorted(h.items()) if k.startswith("evidencias/")][:6] + ["", "(lista completa no manifesto)", ""]
    return "\n".join(L)


CSS = """body{font-family:Arial,sans-serif;max-width:1050px;margin:24px auto;padding:0 16px;color:#222;line-height:1.5}
h1{color:#1f4e79}h2{border-bottom:2px solid #1f4e79;padding-bottom:4px;margin-top:40px}.b{color:#fff;border-radius:4px;padding:1px 6px;font-size:11px;white-space:nowrap}
.a{margin:6px 0}table.t{border-collapse:collapse;font-size:12px}table.t td,table.t th{border:1px solid #ddd;padding:3px 7px;text-align:right}
.aviso{background:#fff7e6;border-left:4px solid #e08e0b;padding:8px 12px}small{color:#888}"""


def gerar_html(I: dict[str, Investigacao], D: Dados, figs: dict) -> str:
    P = ['<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Relatório executivo — Empresa X</title>',
         '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>', f"<style>{CSS}</style></head><body>",
         "<h1>Relatório executivo — Investigação analítica da Empresa X (Etapa 4)</h1>",
         '<p class="aviso"><b>Dados 100% sintéticos.</b> Padrões, quedas e margens foram em parte <i>programados</i> no gerador (P01–P17). Nada aqui é evidência sobre empresas reais; '
         "o objetivo é demonstrar método. “Resultado operacional estimado” não é lucro líquido contábil.</p>", "<h2>Como ler os achados</h2><ul>"]
    P += [f'<li><span class="b" style="background:{COR[t]}">{t}</span> {LEGENDA[t]}</li>' for t in TIPOS] + ["</ul><h2>Resumo executivo</h2><ol>"]
    P += [f"<li>{html.escape(x).replace('**', '')}</li>" for x in resumo_executivo(I, D)] + ["</ol>"]
    for k in ORDEM:
        inv = I[k]
        P += [f"<h2>{html.escape(inv.titulo)}</h2>", f"<p><b>Pergunta de negócio.</b> {html.escape(inv.pergunta)}</p>", f"<p><b>Método.</b> {html.escape(inv.metodo)}</p>", "<h3>Evidências</h3>", _bloco_achados(inv, True)]
        for g in GRAFICOS_POR_INV[k]:
            P.append(figs[g])
        for nome in TABELA_CHAVE[k]:
            P += [f"<p><b>Tabela — {nome}</b></p>", tabela_html(inv.tabelas[nome])]
        P += ["<h3>Limitações dos dados</h3><ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in inv.limitacoes) + "</ul>",
              "<h3>Recomendações gerenciais (condicionais)</h3><ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in inv.recomendacoes) + "</ul>",
              "<h3>Próximas perguntas para uma empresa real</h3><ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in inv.proximas) + "</ul>"]
    P.append("</body></html>")
    return "\n".join(P)


# ------------------------------------------------------------------ gravação determinística
def gravar(I: dict[str, Investigacao], D: Dados, cfg: Config | None = None, destino: Path | None = None) -> dict[str, str]:
    cfg = cfg or Config()
    dest = Path(destino or cfg.pasta_executivo)
    for sub in ("evidencias", "graficos"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
        for f in (dest / sub).glob("*"):
            f.unlink()
    h: dict[str, str] = {}

    def escrever(rel: str, texto: str):
        (dest / rel).write_text(texto, encoding="utf-8", newline="")
        h[rel] = hashlib.sha256(texto.encode("utf-8")).hexdigest()

    for k, inv in I.items():
        for nome, df in inv.tabelas.items():
            escrever(f"evidencias/{k}_{nome}.csv", para_csv(df))
        escrever(f"evidencias/{k}_achados.json", json.dumps([a.__dict__ for a in inv.achados], ensure_ascii=False, indent=1))
    figs_div = {}
    for nome, fn in GRAFICOS.items():
        fig = fn(I)
        escrever(f"graficos/{nome}.html", fig.to_html(full_html=True, include_plotlyjs="cdn", div_id=nome))
        figs_div[nome] = fig.to_html(full_html=False, include_plotlyjs=False, div_id=nome)
    escrever("RELATORIO_EXECUTIVO.md", gerar_markdown(I, D, h))
    escrever("RELATORIO_EXECUTIVO.html", gerar_html(I, D, figs_div))
    escrever("manifesto.json", json.dumps({k: v for k, v in sorted(h.items())}, indent=1))
    return h
