"""Investigação 1 — Por que Porto Alegre caiu 48,9% em fev/2026 (ano contra ano)?"""
from __future__ import annotations

import pandas as pd

from . import pvm
from .achados import CONCLUSAO, HIPOTESE, OBSERVACAO, PROGRAMADO, Investigacao
from .dados import Dados
from .fmt import brl, mes as fm, mil, num, pct, var

FILIAL = "Porto Alegre"
ATUAL, BASE = pd.Timestamp("2026-02-01"), pd.Timestamp("2025-02-01")


def executar(D: Dados) -> Investigacao:
    fid = int(D.filiais.loc[D.filiais.filial == FILIAL, "id_filial"].iloc[0])
    v = D.vendas
    pa = v[v.id_filial == fid]
    inv = Investigacao(
        "INV1", "Porto Alegre em fev/2026: o que explica a queda ano a ano?",
        f"A queda de {fm(ATUAL)} contra {fm(BASE)} em {FILIAL} indica perda de clientes/pedidos ou é um efeito de composição e de base de comparação?",
        "Série mensal da filial; comparação fev/25 × fev/26 em pedidos, linhas, unidades e receita por linha; decomposição "
        "volume/mix/preço (mesma metodologia da Etapa 3, aplicada só à filial); concentração por produto e por cliente na base; "
        "posição da variação entre todas as variações anuais de filiais; sensibilidade aritmética removendo as maiores linhas da base.")

    # ---- série e comparação
    s = pa.groupby("mes").agg(receita_ajustada=("receita_liquida_entregue", "sum"), pedidos=("id_pedido", "nunique"),
                              linhas=("id_venda", "count"), unidades=("quantidade", "sum")).reindex(D.meses, fill_value=0)
    s["receita_por_linha"] = s.receita_ajustada / s.linhas
    s["receita_por_pedido"] = s.receita_ajustada / s.pedidos
    s["yoy_pct"] = s.receita_ajustada / s.receita_ajustada.shift(12) - 1
    inv.tabelas["serie_mensal"] = s.reset_index().rename(columns={"index": "mes"})
    c = pd.DataFrame({"base": s.loc[BASE], "atual": s.loc[ATUAL]})
    c["variacao_pct"] = c.atual / c.base - 1
    inv.tabelas["comparacao_fev25_fev26"] = c.drop(index="yoy_pct").reset_index().rename(columns={"index": "metrica"})
    r0, r1 = s.loc[BASE], s.loc[ATUAL]
    inv.metricas.update(yoy=r1.receita_ajustada / r0.receita_ajustada - 1, queda_rs=r0.receita_ajustada - r1.receita_ajustada,
                        var_pedidos=r1.pedidos / r0.pedidos - 1, var_linhas=r1.linhas / r0.linhas - 1,
                        var_unidades=r1.unidades / r0.unidades - 1, var_rpl=r1.receita_por_linha / r0.receita_por_linha - 1)

    inv.add(OBSERVACAO, f"Receita ajustada de {FILIAL}: {brl(r0.receita_ajustada)} em {fm(BASE)} → {brl(r1.receita_ajustada)} em {fm(ATUAL)} "
                        f"({var(inv.metricas['yoy'])}; queda de {mil(inv.metricas['queda_rs'])}).")
    inv.add(OBSERVACAO, f"A atividade não encolheu na mesma proporção: pedidos {var(inv.metricas['var_pedidos'])}, linhas {var(inv.metricas['var_linhas'])}, "
                        f"unidades {var(inv.metricas['var_unidades'])}; a receita por linha caiu {pct(-inv.metricas['var_rpl'])} "
                        f"({brl(r0.receita_por_linha)} → {brl(r1.receita_por_linha)}).")

    # ---- decomposição
    res, por = pvm.decompor(pa, ATUAL, BASE)
    inv.tabelas["decomposicao_filial"] = pd.DataFrame([res]).T.reset_index().rename(columns={"index": "componente", 0: "valor"})
    pp = por.join(D.produtos.set_index("id_produto")[["produto"]]).sort_values("variacao")
    inv.tabelas["decomposicao_por_produto"] = pp.head(10).reset_index()
    inv.metricas["pvm"] = res
    inv.metricas["pvm_produto_top"] = pp.index[0]
    top = pp.iloc[0]
    inv.add(CONCLUSAO, f"Decomposição da variação registrada ({mil(res['variacao_registrada'])}): volume {mil(res['volume'])}, mix {mil(res['mix'])}, "
                       f"preço {mil(res['preco'])}, desconto {mil(res['desconto'])}, produtos que deixaram de vender {mil(res['produto_descontinuado'])}, "
                       f"produtos novos {mil(res['produto_novo'])}. Preço e desconto praticamente não contribuem; o resíduo é {num(res['residuo'], 2)}.")
    share_top = top.variacao / res["variacao_registrada"]
    inv.add(CONCLUSAO, f"Um único produto, {top.produto}, responde por {mil(top.variacao)} ({pct(share_top)} da variação registrada): "
                       f"{num(top.q0)} unidades em {fm(BASE)} contra {num(top.q1)} em {fm(ATUAL)}.")
    inv.metricas["top_produto_share"] = share_top

    # ---- o quanto a base era atípica para esse produto na filial
    pid = int(pp.index[0])
    ser = pa[pa.id_produto == pid].groupby("mes").quantidade.sum().reindex(D.meses, fill_value=0)
    inv.metricas.update(prod_unid_media=float(ser.mean()), prod_unid_mediana=float(ser.median()), prod_unid_max=float(ser.max()),
                        prod_unid_base=float(ser[BASE]), prod_base_eh_maximo=bool(ser[BASE] == ser.max()),
                        prod_meses_ge_base=int((ser >= ser[BASE]).sum()))
    inv.tabelas["produto_top_unidades_mensais"] = ser.rename("unidades").reset_index().rename(columns={"index": "mes"})
    inv.add(OBSERVACAO, f"Em {FILIAL}, {top.produto} vendeu em média {num(ser.mean(), 1)} unidades/mês (mediana {num(ser.median(), 1)}); "
                        f"{fm(BASE)} teve {num(ser[BASE])} unidades — {'o máximo da série de 33 meses' if ser[BASE] == ser.max() else 'acima da média'}; "
                        f"{fm(ATUAL)} teve {num(ser[ATUAL])}. Meses com volume igual ou maior que o da base: {int((ser >= ser[BASE]).sum())}.")

    # ---- concentração por cliente na base
    b = pa[pa.mes == BASE]
    cli = b.groupby("id_cliente").receita_liquida_entregue.sum().sort_values(ascending=False)
    cli.head(2)
    a_cli = pa[pa.mes == ATUAL].groupby("id_cliente").receita_liquida_entregue.sum()
    l5 = b.receita_liquida_entregue.sort_values(ascending=False).head(5).sum() / b.receita_liquida_entregue.sum()
    l5a = pa[pa.mes == ATUAL].receita_liquida_entregue.sort_values(ascending=False).head(5).sum() / pa[pa.mes == ATUAL].receita_liquida_entregue.sum()
    inv.metricas.update(cli_top_share_base=float(cli.iloc[0] / cli.sum()), top5_linhas_base=float(l5), top5_linhas_atual=float(l5a),
                        cli_top_id=int(cli.index[0]), cli_top_base=float(cli.iloc[0]), cli_top_atual=float(a_cli.get(cli.index[0], 0.0)))
    inv.tabelas["clientes_maiores_na_base"] = cli.head(5).rename("receita_ajustada_base").reset_index().assign(
        receita_ajustada_atual=lambda d: d.id_cliente.map(a_cli).fillna(0.0))
    inv.add(OBSERVACAO, f"Concentração na base: as 5 maiores linhas de {fm(BASE)} somam {pct(l5)} da receita do mês (em {fm(ATUAL)}: {pct(l5a)}). "
                        f"O maior cliente da base (id {int(cli.index[0])}) comprou {brl(cli.iloc[0])} ({pct(cli.iloc[0] / cli.sum())} da filial no mês); "
                        f"em {fm(ATUAL)} esse cliente comprou {brl(a_cli.get(cli.index[0], 0.0))}.")

    # ---- sensibilidade aritmética
    maiores = b.nlargest(3, "receita_liquida_entregue")
    base_aj = s.loc[BASE, "receita_ajustada"] - maiores.receita_liquida_entregue.sum()
    sens = s.loc[ATUAL, "receita_ajustada"] / base_aj - 1
    inv.metricas.update(sens_sem_3_maiores=float(sens), sens_valor_3_maiores=float(maiores.receita_liquida_entregue.sum()))
    inv.add(CONCLUSAO, f"Sensibilidade aritmética (não é cenário real): retirando da base as 3 maiores linhas ({brl(maiores.receita_liquida_entregue.sum())}), "
                       f"a variação anual seria {var(sens)} em vez de {var(inv.metricas['yoy'])}.")

    # ---- contexto: posição entre todas as variações anuais de filiais
    m = v.groupby(["id_filial", "mes"]).receita_liquida_entregue.sum().unstack(0).reindex(D.meses, fill_value=0.0)
    y = (m / m.shift(12) - 1).where(m.shift(12) > 0).iloc[12:].stack()
    inv.metricas.update(n_yoy_filiais=len(y), yoy_filiais_min=float(y.min()), pa_eh_minimo=bool(y[(ATUAL, fid)] == y.min()),
                        yoy_filiais_mediana=float(y.median()))
    inv.add(OBSERVACAO, f"Entre as {len(y)} variações anuais mês×filial calculáveis, a de {FILIAL} em {fm(ATUAL)} é "
                        f"{'a pior' if inv.metricas['pa_eh_minimo'] else 'uma das piores'} (mediana geral: {var(y.median())}).")
    fj = (m.loc[[pd.Timestamp(f"{a}-02-01") for a in (2024, 2025, 2026)]].values / m.loc[[pd.Timestamp(f"{a}-01-01") for a in (2024, 2025, 2026)]].values)
    inv.tabelas["razao_fev_jan_por_filial"] = pd.DataFrame(fj.T, index=m.columns, columns=["2024", "2025", "2026"]).join(
        D.filiais.set_index("id_filial").filial).reset_index()
    inv.add(OBSERVACAO, f"Relação fev/jan em {FILIAL}: {num(fj[0, fid - 1], 2)} (2024), {num(fj[1, fid - 1], 2)} (2025), {num(fj[2, fid - 1], 2)} (2026). "
                        f"Na empresa toda foi {num(m.loc['2024-02-01'].sum() / m.loc['2024-01-01'].sum(), 2)}, "
                        f"{num(m.loc['2025-02-01'].sum() / m.loc['2025-01-01'].sum(), 2)} e {num(m.loc['2026-02-01'].sum() / m.loc['2026-01-01'].sum(), 2)}.")

    # ---- programado?
    inv.add(PROGRAMADO, "O gerador programa para Porto Alegre apenas o efeito de concorrente em jun–ago/2025 (P10, −18%). "
                        "Nenhum padrão P01–P17 cobre fev/2025 nem fev/2026 em Porto Alegre; a sazonalidade de fevereiro (P01, 0,84×) é um fator geral do gerador, não específico de Porto Alegre.")
    inv.add(HIPOTESE, f"Base de comparação atípica: fev/2025 teria sido inflado por poucas compras grandes (concentradas em {top.produto} e em poucos clientes), "
                      "não recorrentes. É coerente com os números acima, mas NÃO está provado — os dados não distinguem compra pontual de demanda recorrente. "
                      "Em dados sintéticos, a variação aleatória das quantidades por linha é uma explicação natural; em uma empresa real seria preciso verificar contratos/pedidos.")
    inv.add(HIPOTESE, "Hipótese alternativa (não sustentada pelos pedidos): perda de clientes ou de demanda local. Os pedidos caíram pouco "
                      f"({var(inv.metricas['var_pedidos'])}) e as linhas subiram ({var(inv.metricas['var_linhas'])}), o que a torna menos provável, mas não a elimina.")
    inv.limitacoes = ["Uma comparação de um único mês por filial é estatisticamente frágil (≈100 linhas).",
                      "Não há dados de pipeline, contratos, estoque ou concorrência para testar as hipóteses.",
                      "Dados sintéticos: variações aleatórias do gerador não correspondem a fatos de mercado."]
    inv.recomendacoes = [
        f"Se a empresa confirmar que as compras grandes de {fm(BASE)} foram pontuais, tratar {fm(BASE)} como base atípica e comparar {FILIAL} com a média móvel de 3–6 meses, não com um único mês.",
        f"Se, ao contrário, os clientes grandes de {FILIAL} deixaram de comprar, abrir uma ação comercial dirigida a eles (a carteira é pequena e a perda seria material).",
        "Em ambos os casos, acompanhar indicadores de concentração (peso das 5 maiores linhas/clientes) junto com a receita."]
    inv.proximas = ["Os grandes pedidos de fev/2025 em Porto Alegre eram recorrentes (contrato) ou únicos?",
                    "Os clientes que mais compraram em fev/2025 compraram em outros meses e filiais?",
                    "Houve mudança de equipe, estoque ou preço local em fev/2026?"]
    return inv
