"""Página 5 — Investigações: estudos de caso (Porto Alegre, Smartphone X Max), decomposição preço × volume × mix e achados rotulados."""
from datetime import date

import pandas as pd
import streamlit as st

from componentes import esc, brl0, brl_mil, cabecalho, int0, metrica, mostrar_achados, pct1, periodo_txt, pvm_cache, premissas, selo, tabela, var1
from empresax.analise import eventos, fmt
from empresax.app import casos
from empresax.app import graficos as G

TITULOS = {"INV1": "Porto Alegre em fev/2026", "INV2": "Quedas anuais por filial e produto", "INV3": "Smartphone X Max e a margem crítica",
           "INV4": "Margem bruta e resultado operacional estimado", "INV5": "Orçamento anual × acumulado × realizado", "INV6": "Preço, volume, mix, desconto e rentabilidade"}


@st.cache_data(show_spinner=False)
def _c(_repo, ass, nome, *args):
    return getattr(casos, nome)(_repo, *args)


def legenda_rotulos():
    st.markdown(" ".join(f"{selo(t)}" for t in ("OBSERVAÇÃO", "CONCLUSÃO ARITMÉTICA", "HIPÓTESE", "PADRÃO PROGRAMADO")))
    st.caption("Observação = o dado mostra · Conclusão aritmética = decorre da conta · Hipótese = explicação possível, NÃO comprovada · Padrão programado = criado de propósito pelo simulador dos dados.")


def porto_alegre(ctx):
    r, a = ctx.repo, ctx.assinatura
    st.subheader("Porto Alegre: a queda de faturamento é perda de movimento ou efeito de base?")
    st.markdown("A pergunta separa três coisas: **quantos pedidos**, **quantas linhas de pedido** e **quanto vale, em média, cada linha**. Se pedidos e linhas mal mudam e a receita por linha despenca, a queda não é falta de movimento.")
    opcoes = [m for m in r.meses if m >= date(2025, 1, 1)]
    mes = st.select_slider("Mês analisado (contra o mesmo mês do ano anterior)", options=opcoes, value=date(2026, 2, 1), format_func=lambda d: fmt.mes(pd.Timestamp(d)), key="pa_mes")
    comp = _c(r, a, "porto_alegre_comparacao", mes)
    serie = _c(r, a, "porto_alegre_serie")
    st.plotly_chart(G.pa_serie(serie, pd.Timestamp(mes)), width="stretch")
    if comp is None:
        st.warning("Sem base no ano anterior para este mês: a comparação não é calculada.")
        return
    cols = st.columns(len(comp))
    for c, (_, x) in zip(cols, comp.iterrows()):
        with c, st.container(border=True):
            v = brl_mil(x.atual) if "Receita" in x.metrica and "linha" not in x.metrica else (brl0(x.atual) if "linha" in x.metrica else int0(x.atual))
            metrica(x.metrica, v, var1(x.variacao), f"{fmt.mes(pd.Timestamp(mes) - pd.DateOffset(years=1))}: " + (brl0(x.base) if "Receita" in x.metrica else int0(x.base)), "normal")
    rb, ra = fmt.mes(pd.Timestamp(mes) - pd.DateOffset(years=1)), fmt.mes(pd.Timestamp(mes))
    st.plotly_chart(G.pa_atividade(comp, rb, ra, f"Variação anual por medida: {ra} vs. {rb}"), width="stretch")
    conc = _c(r, a, "porto_alegre_concentracao", pd.Timestamp(mes) - pd.DateOffset(years=1))
    if conc["disponivel"]:
        st.markdown(esc(f"**Concentração na base ({rb}):** as {conc['topn']} maiores linhas somam {pct1(conc['share_top_linhas'])} da receita do mês; o maior cliente, {pct1(conc['share_maior_cliente'])}. "
                    "Quando poucas linhas pesam muito, a base de comparação fica 'pontual' e a variação anual exagera."))
    res, por = _c(r, a, "porto_alegre_pvm", mes)
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(G.cascata_pvm(res, "Decomposição da variação (Porto Alegre)", rb, ra), width="stretch")
    with g2:
        st.plotly_chart(G.contribuicao_produtos(por), width="stretch")
    ev = eventos.rotular(pd.Timestamp(mes), id_filial=5) or eventos.rotular(pd.Timestamp(mes) - pd.DateOffset(years=1), id_filial=5)
    if ev:
        st.warning(esc(f"Padrão programado no simulador coincide com o período: {ev}."))
    else:
        st.info("Nenhum padrão programado do simulador (P01–P17) cobre este mês em Porto Alegre, nem o mês-base: o resultado não vem de um evento criado de propósito.")
    st.markdown("##### Achados rotulados desta investigação (INV1)")
    mostrar_achados(casos.achados_gerados("INV1"))


def smartphone(ctx):
    r, a = ctx.repo, ctx.assinatura
    st.subheader("Smartphone X Max: preço parado, custo subindo")
    s = _c(r, a, "smartphone_serie")
    rs = _c(r, a, "smartphone_resumo")
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(border=True):
        metrica("Preço bruto médio/un.", brl0(rs["preco_fim"]), var1(rs["variacao_preco"]), f"jan/24: {brl0(rs['preco_ini'])}", "off")
    with c2, st.container(border=True):
        metrica("Custo por unidade", brl0(rs["custo_fim"]), var1(rs["variacao_custo"]), f"jan/24: {brl0(rs['custo_ini'])}", "inverse")
    with c3, st.container(border=True):
        metrica("Margem bruta (set/26)", pct1(rs["margem_fim"]), fmt.pp(rs["margem_fim"] - rs["margem_ini"]), f"jan/24: {pct1(rs['margem_ini'])}")
    with c4, st.container(border=True):
        metrica("Linhas negativas do produto", int0(rs["linhas_neg"]), None, f"De {int0(rs['linhas_neg_empresa'])} linhas negativas da empresa inteira.")
        st.caption(esc(f"{pct1(rs['linhas_neg'] / rs['linhas_neg_empresa'])} do total da empresa"))
    st.plotly_chart(G.sp_preco_custo(s), width="stretch")
    st.plotly_chart(G.sp_linhas_negativas(s), width="stretch")
    if rs["primeira_negativa"] is not None:
        st.markdown(f"**Marcos:** primeira linha com margem negativa em {fmt.mes(rs['primeira_negativa'])}" + (f"; 100% das linhas do mês são negativas desde {fmt.mes(rs['cem_por_cento_desde'])}." if rs["cem_por_cento_desde"] is not None else "."))
    st.markdown("##### Conta aritmética: que preço zeraria (ou atingiria) uma margem-alvo?")
    alvo = st.select_slider("Margem bruta-alvo", options=[0.0, 0.05, 0.10, 0.15, 0.20], value=0.0, format_func=lambda x: f"{x * 100:.0f}%".replace(".", ","), key="sp_alvo")
    p = _c(r, a, "smartphone_preco_para_margem", alvo)
    if p:
        st.success(esc(f"Mantidos o custo de {fmt.mes(pd.Timestamp(p['mes']))} e os descontos e impostos efetivos observados, o preço bruto precisaria ir de {brl0(p['preco_atual'])} para {brl0(p['preco_necessario'])} "
                   f"({fmt.var(p['aumento'])}) para atingir {pct1(alvo)} de margem."))
        st.caption("Conta aritmética, NÃO é recomendação de preço: ignora a elasticidade (quanto a venda cai se o preço sobe), a concorrência e contratos.")
    st.info("**Padrão programado (P06/P07):** o simulador reajusta o custo deste produto em ~1% ao mês e mantém o preço fixo. A deterioração da margem é, portanto, uma característica criada nos dados, e não evidência sobre um mercado real.")
    legenda_rotulos()
    mostrar_achados(casos.achados_gerados("INV3"))


def pvm(ctx):
    f = ctx.filtros
    st.subheader("Preço × volume × mix: de onde veio a variação da receita?")
    st.markdown("A decomposição divide a variação da receita ajustada entre **volume**, **mix** (composição entre produtos), **preço**, **desconto**, **impostos**, **produtos novos / que pararam** e **devoluções**. A soma fecha exatamente com a variação total. Usa o período e os filtros da barra lateral.")
    modo = st.radio("Comparar com", ["Mesmo período do ano anterior", "Período imediatamente anterior (mesmo tamanho)"], horizontal=True, key="pvm_modo")
    base = f.deslocado(-12) if modo.startswith("Mesmo") else f.deslocado(-f.n_meses)
    if base.inicio < ctx.repo.primeiro_mes:
        st.warning(esc(f"O período de comparação ({periodo_txt(base)}) começa antes dos dados (jan/2024). Escolha um período mais recente ou outra base."))
        return
    res, por = pvm_cache(ctx, f, base)
    if res["ajustada_base"] == 0 or res["ajustada_atual"] == 0:
        st.warning("Há período sem vendas neste recorte (base ou período atual zerados): a decomposição não se aplica.")
        return
    rb, ra = periodo_txt(base), periodo_txt(f)
    st.plotly_chart(G.cascata_pvm(res, f"Receita ajustada: {rb} → {ra}", rb, ra), width="stretch")
    efeitos = [(n, float(res[k])) for k, n in G.NOMES_EFEITOS]
    var_aj = float(res["variacao_ajustada"])
    df = pd.DataFrame(efeitos, columns=["efeito", "valor"])
    df["pct"] = df.valor / var_aj if var_aj else float("nan")
    soma = df.valor.sum()
    tabela(df, {"efeito": str, "valor": brl0, "pct": pct1}, {"efeito": "Efeito", "valor": "Valor (R$)", "pct": "% da variação"})
    resid = var_aj - soma
    (st.success if abs(resid) < 0.5 else st.error)(esc(f"Variação da receita ajustada: {brl0(var_aj)} = soma dos efeitos {brl0(soma)} · resíduo {fmt.brl(resid, 2)}"))
    if abs(var_aj) > 0:
        st.caption("Percentuais são relativos à variação total; efeitos de sinais opostos podem passar de 100% (um compensa o outro).")
    st.plotly_chart(G.contribuicao_produtos(por), width="stretch")
    with st.expander("Metodologia (resumo) e limites", expanded=False):
        st.markdown("""
- **Identidade, não estimativa:** para cada produto presente nos dois períodos, a receita líquida é `quantidade × preço bruto × (1 − desconto%) × (1 − imposto%)`. Cada efeito muda um fator de cada vez.
- **Volume:** variação da quantidade total dos produtos comuns, na composição e no preço da base. **Mix:** quanto a composição entre produtos mudou, mantendo o volume total.
- **Preço:** variação do preço bruto médio de cada produto (com desconto e imposto da base). **Desconto** e **impostos:** variação das taxas efetivas. Nada vai para um 'efeito residual': o resíduo é verificado e mostrado.
- **Produtos novos / que pararam:** produtos sem venda em um dos períodos entram integralmente nestes dois efeitos.
- **Devoluções:** a decomposição é calculada sobre a receita registrada; a mudança das devoluções entre os períodos fecha a ponte até a receita ajustada (PN-DEV-01).
- **Limites:** com mais de um mês, os períodos são agregados por produto (preço médio do período). Não há elasticidade nem causalidade: um 'efeito preço' positivo não prova que o reajuste funcionou.
- Documento completo: `docs/METODOLOGIA_DECOMPOSICAO.md`; cálculo validado contra o SQL (análise 08) e contra um cálculo independente em Python puro.
""")


def achados(ctx):
    st.subheader("Achados rotulados das seis investigações")
    legenda_rotulos()
    inv = st.selectbox("Investigação", list(TITULOS), format_func=lambda k: f"{k} — {TITULOS[k]}", key="inv_sel")
    mostrar_achados(casos.achados_gerados(inv))
    st.caption("Gerados por scripts/run_analises.py (reports/executivo/). Cada hipótese vem acompanhada de aviso: nenhuma causa é atribuída sem evidência.")
    with st.expander("Padrões programados no simulador com janela e escopo (usados apenas para rotular coincidências)"):
        st.dataframe(pd.DataFrame([dict(Padrão=e[0], Descrição=e[1], Início=fmt.mes(e[4]), Fim=fmt.mes(e[5])) for e in eventos.EVENTOS]), hide_index=True, width="stretch")


def render(ctx):
    cabecalho("Investigações", "Estudos de caso com método explícito: observação, conta, hipótese e padrão programado nunca se misturam.", ctx)
    st.info("Os estudos de **Porto Alegre** e do **Smartphone X Max** têm escopo fixo e ignoram os filtros da barra lateral. A aba **Preço, volume e mix** usa período, filial, produto e canal da barra lateral.", icon="ℹ️")
    t1, t2, t3, t4 = st.tabs(["Porto Alegre", "Smartphone X Max", "Preço, volume e mix", "Todos os achados"])
    with t1:
        porto_alegre(ctx)
    with t2:
        smartphone(ctx)
    with t3:
        pvm(ctx)
    with t4:
        achados(ctx)
    premissas("PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-MRG-01", "PN-SIN-01")
