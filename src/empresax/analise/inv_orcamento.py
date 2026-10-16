"""Investigação 5 — Orçamento anual × orçamento acumulado × realizado."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, Investigacao
from .dados import Dados
from .fmt import mes as fm, mil, pct, var
from ..config import Config


def executar(D: Dados, cfg: Config | None = None) -> Investigacao:
    cfg = cfg or Config()
    tol = cfg.tolerancia_orcamento_pct
    o, ult = D.orcamento, D.ultimo_mes
    inv = Investigacao(
        "INV5", "Orçado × realizado: anual, acumulado e a leitura correta",
        "Quanto a empresa realmente gastou em relação ao orçado, qual o erro de comparar com o orçamento anual, e onde estão os desvios?",
        f"Três conceitos separados: orçamento ANUAL (12 meses), orçamento ACUMULADO (jan→{fm(ult)[:3]}) e realizado ACUMULADO; comparação correta = realizado ÷ orçado acumulado. "
        f"Faixa 'dentro do orçado' = ±{pct(tol, 0)}. Projeção de fim de ano = orçamento anual × taxa de execução acumulada (cálculo aritmético, não previsão).")

    # ---- três conceitos por ano
    rows = []
    for ano in sorted(o.mes.dt.year.unique()):
        oa = o[o.mes.dt.year == ano]
        ref = min(ult, pd.Timestamp(f"{ano}-12-01"))
        ac = oa[oa.mes <= ref]
        anual = D.orc_plano[D.orc_plano.mes.dt.year == ano].valor_orcado.sum()      # 12 meses, inclusive os futuros
        rows.append(dict(ano=int(ano), mes_referencia=ref, orcamento_anual=anual, orcamento_acumulado=ac.orcado.sum(),
                         realizado_acumulado=ac.realizado.sum()))
    t = pd.DataFrame(rows)
    t["execucao_correta"] = t.realizado_acumulado / t.orcamento_acumulado
    t["leitura_ingenua"] = t.realizado_acumulado / t.orcamento_anual
    t["proporcao_orcamento_ja_acumulada"] = t.orcamento_acumulado / t.orcamento_anual
    t["meses_no_acumulado"] = t.mes_referencia.dt.month
    t["leitura_proporcional_linear"] = t.realizado_acumulado / (t.orcamento_anual * t.meses_no_acumulado / 12)
    inv.tabelas["tres_conceitos_por_ano"] = t
    c = t.iloc[-1]
    inv.metricas.update(ano=int(c.ano), orc_anual=float(c.orcamento_anual), orc_acum=float(c.orcamento_acumulado), real_acum=float(c.realizado_acumulado),
                        exec_correta=float(c.execucao_correta), exec_ingenua=float(c.leitura_ingenua), exec_linear=float(c.leitura_proporcional_linear),
                        prop_acum=float(c.proporcao_orcamento_ja_acumulada), meses=int(c.meses_no_acumulado))
    inv.add(OBSERVACAO, f"{int(c.ano)} até {fm(c.mes_referencia)}: orçamento anual {mil(c.orcamento_anual)}; orçamento acumulado {mil(c.orcamento_acumulado)} "
                        f"({pct(c.proporcao_orcamento_ja_acumulada)} do anual em {int(c.meses_no_acumulado)} de 12 meses); realizado acumulado {mil(c.realizado_acumulado)}.")
    inv.add(CONCLUSAO, f"Execução correta (realizado ÷ orçado acumulado): {pct(c.execucao_correta)}. "
                       f"Leitura ingênua (÷ orçamento anual): {pct(c.leitura_ingenua)} — daria a falsa impressão de que a empresa gastou {pct(1 - c.leitura_ingenua, 0)} a menos que o planejado. "
                       f"Prorrateio linear ({int(c.meses_no_acumulado)}/12): {pct(c.leitura_proporcional_linear)} — também erra, porque o orçamento não é distribuído igualmente pelos meses.")

    # ---- departamento e categoria
    oy = o[(o.mes.dt.year == ult.year) & (o.mes <= ult)]
    def quadro(col):
        g = oy.groupby(col).agg(orcado=("orcado", "sum"), realizado=("realizado", "sum"))
        g["desvio_rs"] = g.realizado - g.orcado
        g["execucao"] = g.realizado / g.orcado
        g["situacao"] = np.where(g.execucao > 1 + tol, "acima_do_orcado", np.where(g.execucao < 1 - tol, "abaixo_do_orcado", "dentro_da_faixa"))
        return g.sort_values("desvio_rs", ascending=False)
    dep, cat = quadro("departamento"), quadro("categoria_despesa")
    inv.tabelas["por_departamento"], inv.tabelas["por_categoria"] = dep.reset_index(), cat.reset_index()
    acima = cat[cat.situacao == "acima_do_orcado"]
    inv.metricas.update(n_cat=len(cat), n_cat_acima=len(acima), dep_top=dep.index[0], dep_top_exec=float(dep.execucao.iloc[0]))
    inv.add(OBSERVACAO, f"Por departamento, apenas {(dep.situacao == 'acima_do_orcado').sum()} está acima da faixa de ±{pct(tol, 0)}: "
                        + "; ".join(f"{i} {pct(r.execucao)} ({mil(r.desvio_rs)})" for i, r in dep[dep.situacao == 'acima_do_orcado'].iterrows()) + ". "
                        f"Por categoria, {len(acima)} de {len(cat)} estão acima.")
    # concentração do desvio positivo
    pos = cat[cat.desvio_rs > 0]
    top3 = pos.desvio_rs.head(3)
    inv.metricas["share_top3_estouro"] = float(top3.sum() / pos.desvio_rs.sum())
    inv.add(OBSERVACAO, "Maiores desvios em reais (acima do orçado): " + "; ".join(f"{i} {mil(r.desvio_rs)} ({pct(r.execucao)})" for i, r in cat.head(3).iterrows())
                        + f". Esses três concentram {pct(inv.metricas['share_top3_estouro'], 0)} da soma dos desvios positivos por categoria. "
                        f"O desvio líquido total é {mil(c.realizado_acumulado - c.orcamento_acumulado)} ({var(c.execucao_correta - 1)}).")
    pct_maior = cat.execucao.idxmax()
    inv.add(OBSERVACAO, f"A maior execução PERCENTUAL é de '{pct_maior}' ({pct(cat.execucao.max())}), mas sobre valor orçado pequeno ({mil(cat.loc[pct_maior, 'orcado'])}); "
                        "percentual alto e valor pequeno exigem menos atenção que desvio moderado em categoria grande.")

    # ---- projeção aritmética
    proj = c.orcamento_anual * c.execucao_correta
    inv.metricas["projecao"] = float(proj)
    inv.add(CONCLUSAO, f"Se a taxa de execução acumulada ({pct(c.execucao_correta)}) se mantivesse, o gasto de {int(c.ano)} fecharia em ≈ {mil(proj)} contra orçamento anual de {mil(c.orcamento_anual)} "
                       f"(diferença {mil(proj - c.orcamento_anual)}). A projeção parte do orçamento anual completo. É extrapolação aritmética, sem considerar sazonalidade de despesas nem decisões futuras.")

    # ---- padrões programados presentes
    def exec_periodo(filtro, ini, fim):
        x = o[(o.mes >= ini) & (o.mes <= fim) & filtro]
        return x.realizado.sum() / x.orcado.sum()
    o.categoria_despesa.str.contains("Marketing", case=False) | (o.departamento == "Marketing")
    e_mk_4t = exec_periodo(o.departamento == "Marketing", pd.Timestamp("2025-10-01"), pd.Timestamp("2025-12-01"))
    e_mk_ref = exec_periodo(o.departamento == "Marketing", pd.Timestamp("2025-01-01"), pd.Timestamp("2025-09-01"))
    sw = o.categoria_despesa.str.startswith("Software")
    e_sw_26 = exec_periodo(sw, pd.Timestamp(f"{ult.year}-01-01"), ult)
    e_sw_25 = exec_periodo(sw, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-01"))
    ju = o.categoria_despesa.str.startswith("Juros")
    e_ju_25a = exec_periodo(ju, pd.Timestamp("2025-03-01"), pd.Timestamp("2025-12-01"))
    e_ju_24 = exec_periodo(ju, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-01"))
    inv.metricas.update(mk_4t=float(e_mk_4t), mk_ref=float(e_mk_ref), sw_26=float(e_sw_26), sw_25=float(e_sw_25), ju_25=float(e_ju_25a), ju_24=float(e_ju_24))
    inv.add(PROGRAMADO, f"P14: Marketing executou {pct(e_mk_4t)} do orçado no 4T/2025 (jan–set/2025: {pct(e_mk_ref)}). "
                        f"P15: Software & Licenças executou {pct(e_sw_26)} em {int(ult.year)} (2025: {pct(e_sw_25)}). "
                        f"P16: Juros & Tarifas Bancárias executaram {pct(e_ju_25a)} de mar a dez/2025 (2024: {pct(e_ju_24)}). "
                        "Os três desvios foram criados no gerador; aqui só confirmamos que os números os reproduzem.")
    # ---- série mensal de desvio
    ms = o.groupby("mes").agg(orcado=("orcado", "sum"), realizado=("realizado", "sum"))
    ms["execucao"] = ms.realizado / ms.orcado
    inv.tabelas["execucao_mensal"] = ms.reset_index()
    inv.add(HIPOTESE, "Desvios acima do orçado em categorias com crescimento contínuo (software, juros) podem refletir orçamento subdimensionado "
                      "e não má gestão de gasto; os dados não permitem separar uma coisa da outra.")
    inv.limitacoes = ["Orçado × realizado compara apenas meses realizados; meses futuros do orçamento não entram (PN-ORC-01).",
                      "Não há justificativas dos desvios nem versão revisada do orçamento.",
                      "A projeção de fim de ano é extrapolação simples."]
    inv.recomendacoes = [
        "Se a gestão acompanha o orçamento pelo painel, usar sempre realizado ÷ orçado ACUMULADO (e mostrar o anual apenas como referência de saldo).",
        "Se os desvios concentrados em poucas categorias forem recorrentes, revisar o orçamento dessas categorias (reforço ou travas), em vez de ações gerais de corte.",
        "Definir alçada por valor e por percentual (ex.: desvio > R$ X ou > Y% com valor relevante), para não gastar atenção com percentuais altos em valores pequenos."]
    inv.proximas = ["Os desvios de software e juros foram aprovados fora do orçamento?",
                    "O orçamento é revisado durante o ano (forecast) ou fica fixo?",
                    "Há sazonalidade nas despesas que justifique a distribuição mensal do orçamento?"]
    return inv
