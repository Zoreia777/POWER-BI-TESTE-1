"""Investigação 6 — Relações entre volume, preço, desconto, mix e rentabilidade (associações, não causas)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import pvm
from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, Investigacao
from .dados import Dados
from .fmt import mes as fm, mil, num, pct, pp
from .inv_margem import decompor_margem, ytd


def _mensal(D: Dados) -> pd.DataFrame:
    v = D.vendas.merge(D.canais[["id_canal", "canal"]], on="id_canal").merge(D.produtos[["id_produto", "categoria"]], on="id_produto")
    g = v.groupby("mes")
    m = pd.DataFrame({
        "pedidos": g.id_pedido.nunique(),
        "unidades": g.quantidade.sum(),
        "preco_vs_lista": g.efeito_preco_valor.sum() / g.valor_a_preco_lista.sum(),
        "desconto_efetivo": g.desconto_valor.sum() / g.receita_bruta.sum(),
        "margem_bruta": 1 - g.custo_entregue.sum() / g.receita_liquida_entregue.sum(),
        "receita_ajustada": g.receita_liquida_entregue.sum()}).reindex(D.meses)
    m["share_marketplace"] = (v[v.canal == "Marketplace"].groupby("mes").receita_bruta.sum() / g.receita_bruta.sum()).reindex(D.meses)
    m["share_eletronicos"] = (v[v.categoria == "Eletrônicos"].groupby("mes").receita_liquida_entregue.sum() / g.receita_liquida_entregue.sum()).reindex(D.meses)
    m["ticket_por_pedido"] = m.receita_ajustada / m.pedidos
    m["black_friday_mes"] = (m.index.month == 11).astype(float)
    return m


def _fe_ols(y: np.ndarray, x: np.ndarray, grupos: np.ndarray) -> tuple[float, float]:
    """OLS de y em x com efeito fixo por grupo; devolve (coeficiente de x, R² intra-grupo)."""
    df = pd.DataFrame({"y": y, "x": x, "g": grupos})
    yd = df.y - df.groupby("g").y.transform("mean")
    xd = df.x - df.groupby("g").x.transform("mean")
    b = float((xd * yd).sum() / (xd ** 2).sum())
    r2 = float(1 - ((yd - b * xd) ** 2).sum() / (yd ** 2).sum())
    return b, r2


def _ols_controlado(y: np.ndarray, x: np.ndarray, dummies: pd.DataFrame) -> float:
    """Coeficiente de x em y ~ x + dummies (mínimos quadrados)."""
    X = np.column_stack([x, np.ones(len(y)), dummies.to_numpy(float)])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(coef[0])


def executar(D: Dados) -> Investigacao:
    v = D.vendas
    inv = Investigacao(
        "INV6", "Volume, preço, desconto, mix e rentabilidade: o que se relaciona com quê?",
        "Os meses de maior desconto ou maior peso de marketplace têm margem menor? Descontos maiores vêm com quantidades maiores? Quanto do crescimento é volume, preço ou mix?",
        "Correlação de Spearman entre indicadores mensais (em nível e em variação mês a mês, para reduzir o efeito de tendência comum); "
        "regressão por linha com efeito fixo de produto (quantidade × desconto); decomposição mix × taxa da margem por canal; "
        "soma das decomposições preço/volume/mix dos meses comparáveis. Correlação NÃO é causalidade.")

    # ---- correlações mensais
    m = _mensal(D)
    cols = ["unidades", "preco_vs_lista", "desconto_efetivo", "share_marketplace", "share_eletronicos", "margem_bruta"]
    c_n = m[cols].corr(method="spearman")
    c_d = m[cols].diff().iloc[1:].corr(method="spearman")
    inv.tabelas["serie_mensal"] = m.reset_index().rename(columns={"index": "mes"})
    inv.tabelas["correlacao_spearman_nivel"] = c_n.reset_index().rename(columns={"index": "indicador"})
    inv.tabelas["correlacao_spearman_variacao_mensal"] = c_d.reset_index().rename(columns={"index": "indicador"})
    inv.metricas.update(corr_desc_margem=float(c_n.loc["desconto_efetivo", "margem_bruta"]), corr_desc_margem_diff=float(c_d.loc["desconto_efetivo", "margem_bruta"]),
                        corr_mkt_margem=float(c_n.loc["share_marketplace", "margem_bruta"]), corr_mkt_margem_diff=float(c_d.loc["share_marketplace", "margem_bruta"]),
                        corr_preco_margem=float(c_n.loc["preco_vs_lista", "margem_bruta"]), corr_preco_margem_diff=float(c_d.loc["preco_vs_lista", "margem_bruta"]),
                        n_meses=len(m))
    inv.add(OBSERVACAO, f"Correlação de Spearman com a margem bruta mensal ({len(m)} meses; entre parênteses, em variação mês a mês): "
                        f"desconto efetivo {num(c_n.loc['desconto_efetivo', 'margem_bruta'], 2)} ({num(c_d.loc['desconto_efetivo', 'margem_bruta'], 2)}); "
                        f"peso do marketplace {num(c_n.loc['share_marketplace', 'margem_bruta'], 2)} ({num(c_d.loc['share_marketplace', 'margem_bruta'], 2)}); "
                        f"preço praticado vs lista {num(c_n.loc['preco_vs_lista', 'margem_bruta'], 2)} ({num(c_d.loc['preco_vs_lista', 'margem_bruta'], 2)}); "
                        f"peso de Eletrônicos {num(c_n.loc['share_eletronicos', 'margem_bruta'], 2)} ({num(c_d.loc['share_eletronicos', 'margem_bruta'], 2)}).")
    inv.add(OBSERVACAO, "Em nível, quase tudo se correlaciona com tudo porque os indicadores têm tendência comum (tempo); por isso a leitura principal é a de variação mês a mês, "
                        "mais exigente. Com 32–33 pontos, correlações pequenas (|ρ| < 0,35) não distinguem de acaso.")

    # ---- desconto × quantidade (linha, efeito fixo de produto) e o papel de variáveis de confusão
    b, r2 = _fe_ols(v.quantidade.to_numpy(float), v.desconto_pct.to_numpy(float), v.id_produto.to_numpy())
    corr_lin = float(pd.Series(v.quantidade.to_numpy(float)).corr(pd.Series(v.desconto_pct.to_numpy(float)), method="spearman"))
    vc = v.merge(D.clientes, on="id_cliente", how="left")
    dum = pd.get_dummies(vc[["id_produto", "id_canal", "segmento"]].astype(str), drop_first=True)
    dum["mes_novembro"] = (vc.mes.dt.month == 11).astype(float)
    dum["ano_2025"], dum["ano_2026"] = (vc.mes.dt.year == 2025).astype(float), (vc.mes.dt.year == 2026).astype(float)
    b_ctrl = _ols_controlado(vc.quantidade.to_numpy(float), vc.desconto_pct.to_numpy(float), dum)
    inv.metricas.update(coef_desc_qtd=b, r2_desc_qtd=r2, corr_lin_desc_qtd=corr_lin, coef_desc_qtd_controlado=b_ctrl)
    inv.tabelas["desconto_vs_quantidade"] = pd.DataFrame([
        {"modelo": "dentro do produto", "unidades_por_linha_a_cada_1pp_de_desconto": b / 100},
        {"modelo": "dentro do produto + canal + segmento do cliente + novembro + ano", "unidades_por_linha_a_cada_1pp_de_desconto": b_ctrl / 100}])
    inv.add(OBSERVACAO, f"Por linha de venda ({num(len(v))} linhas), dentro do mesmo produto: +1 p.p. de desconto está associado a {num(b / 100, 3)} unidades a mais por linha "
                        f"(R² intra-produto {num(r2, 3)}; Spearman geral {num(corr_lin, 2)}). Controlando também canal, segmento do cliente, novembro e ano, a associação passa a {num(b_ctrl / 100, 3)} unidades por p.p.")
    reduz = 1 - abs(b_ctrl) / abs(b) if b else 0.0
    inv.metricas["reducao_associacao"] = float(reduz)
    inv.add(OBSERVACAO, f"A associação positiva entre desconto e quantidade cai {pct(reduz, 0)} quando se comparam linhas do mesmo canal e segmento do cliente. "
                        "É compatível com efeito de COMPOSIÇÃO (certos canais/segmentos têm desconto e quantidade maiores); a associação bruta não deve ser lida como 'o desconto vende mais'.")
    inv.add(PROGRAMADO, "No gerador, o desconto vem do canal (3–7%), do segmento do cliente (0–3%), de novembro (+5 p.p.) e da Black Friday (+8 p.p. — P04), mais ruído; ele NÃO depende da quantidade. "
                        "Qualquer associação restante é efeito de confusão, não de causa.")
    inv.add(HIPOTESE, "Numa empresa real, descontos podem aumentar pedidos ou recorrência sem aumentar a quantidade por linha; esse teste não enxerga isso. "
                      "Também pode haver desconto por volume (causa inversa) — aqui não há, por construção do gerador.")

    # ---- canal
    a0, a1 = D.ultimo_mes.year - 2, D.ultimo_mes.year
    v0, v1 = ytd(D, a0), ytd(D, a1)
    can = D.canais.set_index("id_canal").canal
    rows = []
    for nome, ano, vv in ((a0, a0, v0), (a1, a1, v1)):
        g = vv.groupby("id_canal")
        t = pd.DataFrame({"share_receita": g.receita_liquida_entregue.sum() / vv.receita_liquida_entregue.sum(),
                          "margem_bruta": 1 - g.custo_entregue.sum() / g.receita_liquida_entregue.sum(),
                          "desconto_efetivo": g.desconto_valor.sum() / g.receita_bruta.sum()})
        t["ano"] = ano
        rows.append(t.rename(index=can).reset_index().rename(columns={"id_canal": "canal"}))
    ct = pd.concat(rows)
    inv.tabelas["canais_ytd"] = ct
    res_c, por_c = decompor_margem(v1, v0, "id_canal")
    por_c = por_c.rename(index=can)
    inv.tabelas["decomposicao_margem_por_canal"] = por_c.reset_index().rename(columns={"id_canal": "canal"})
    inv.metricas["decomp_canal"] = res_c
    mk = ct[ct.canal == "Marketplace"].set_index("ano")
    inv.add(OBSERVACAO, f"Marketplace: {pct(mk.loc[a0, 'share_receita'])} da receita ajustada (jan–{fm(D.ultimo_mes)[:3]}/{a0}) → {pct(mk.loc[a1, 'share_receita'])} ({a1}); "
                        f"margem bruta {pct(mk.loc[a0, 'margem_bruta'])} → {pct(mk.loc[a1, 'margem_bruta'])}; desconto efetivo {pct(mk.loc[a0, 'desconto_efetivo'])} → {pct(mk.loc[a1, 'desconto_efetivo'])}.")
    inv.add(CONCLUSAO, f"Variação da margem bruta {a0}→{a1} por canal: {pp(res_c['delta'])} = mix de canais {pp(res_c['mix'])} + margem dentro de cada canal {pp(res_c['taxa'])}. "
                       "Como a margem de cada canal é uma média de produtos, o 'efeito taxa' por canal inclui o problema do Smartphone X Max (INV3) e o mix de produtos de cada canal.")
    inv.add(PROGRAMADO, "P12: o gerador migra o mix de canais para marketplace (comissão de 11% lançada em despesas, não em custo). A comissão NÃO aparece na margem bruta por canal; "
                        "a rentabilidade real do marketplace é, portanto, menor que a mostrada aqui.")

    # ---- decomposição preço/volume/mix acumulada
    inv.metricas["pvm_anos"] = {}
    for ano in (D.ultimo_mes.year - 1, D.ultimo_mes.year):
        s = pvm.serie(v, D.meses, "YoY")
        s = s[s.periodo.dt.year == ano]
        tot = {k: float(s[k].sum()) for k in ["volume", "mix", "preco", "desconto", "impostos", "variacao_registrada"]}
        inv.metricas["pvm_anos"][ano] = {**tot, "meses": len(s)}
    inv.tabelas["pvm_yoy_serie"] = pvm.serie(v, D.meses, "YoY")
    for ano, t in inv.metricas["pvm_anos"].items():
        den = t["variacao_registrada"]
        inv.add(CONCLUSAO, f"Crescimento anual da receita registrada em {ano} ({t['meses']} meses comparáveis, soma de {mil(den)}): volume {mil(t['volume'])} ({pct(t['volume'] / den, 0)}), "
                           f"mix {mil(t['mix'])} ({pct(t['mix'] / den, 0)}), preço {mil(t['preco'])} ({pct(t['preco'] / den, 0)}), desconto {mil(t['desconto'])} ({pct(t['desconto'] / den, 0)}), "
                           f"impostos {mil(t['impostos'])}.")
    inv.add(PROGRAMADO, "P05 (crescimento tendencial de 1,1% ao mês de pedidos) e P06 (reajuste mensal de preço) explicam, por construção, por que volume é o principal componente e preço o segundo.")
    inv.add(HIPOTESE, "Associações entre desconto, marketplace e margem podem ser confundidas por tempo (tudo muda junto) e por produto (o Smartphone X Max pesa na margem e tem desconto como os demais). "
                      "Sem experimento ou controles adicionais, os dados mostram associação, não efeito causal.")
    inv.limitacoes = ["Correlações com ~33 pontos mensais e variáveis em tendência são frágeis.",
                      "Desconto efetivo é média ponderada; mistura canal, cliente e produto.",
                      "A comissão do marketplace está em despesas e não entra na margem bruta por canal.",
                      "Dados sintéticos: relações entre variáveis foram definidas pelo gerador, não por comportamento de clientes reais."]
    inv.recomendacoes = [
        "Se a empresa real encontrar o mesmo padrão (desconto sem aumento de quantidade), testar redução controlada de descontos em um grupo de produtos/filiais antes de generalizar.",
        "Se o marketplace continuar a ganhar peso, incluir a comissão no cálculo de margem por canal antes de comparar canais.",
        "Reportar crescimento sempre decomposto em volume, mix e preço: 'crescer' por volume e por preço têm implicações bem diferentes para margem e caixa."]
    inv.proximas = ["Descontos aumentam o número de pedidos ou a recorrência de clientes (não apenas a quantidade por linha)?",
                    "Qual a margem líquida por canal depois de comissões, frete e devoluções?",
                    "Qual a elasticidade preço-demanda por categoria (teste A/B ou histórico com variações isoladas)?"]
    return inv
