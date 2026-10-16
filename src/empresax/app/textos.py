"""Textos fixos do aplicativo: premissas de negócio e avisos. Os testes conferem que aparecem onde são necessários."""

PREMISSAS = {
    "PN-DEV-01": "**PN-DEV-01** — A *receita ajustada* é PROVISÓRIA: considera apenas vendas com status Entregue. Devolução é tratada como integral e cancela a receita da linha. Não é reconhecimento contábil definitivo.",
    "PN-DEV-02": "**PN-DEV-02** — HIPÓTESE (não comprovada): o produto devolvido volta ao estoque e o custo é recuperado; por isso o custo ajustado exclui o custo das devoluções.",
    "PN-DEV-03": "**PN-DEV-03** — Não existe data de devolução nos dados. As devoluções ficam no mês da venda original; nenhuma data de estorno é inventada.",
    "PN-MRG-01": "**PN-MRG-01** — Margens negativas são preservadas e sinalizadas; custos e preços não foram corrigidos.",
    "PN-ORC-01": "**PN-ORC-01** — Orçado × realizado só é comparado nos meses já realizados; o orçamento ANUAL inclui meses futuros e não deve ser dividido pelo realizado parcial.",
    "PN-SIN-01": "**PN-SIN-01** — Dados 100% FICTÍCIOS, gerados por um simulador: alguns padrões foram programados e não são evidência de mercado.",
}

RESULTADO_OPERACIONAL = "Resultado operacional estimado = lucro bruto ajustado − despesas do dataset. **Não é lucro líquido contábil.**"
SEM_RESULTADO = "Não há vendas para a combinação de filtros escolhida. Nenhum indicador é exibido para não induzir a uma leitura errada (0 não é o mesmo que 'sem dados')."
DESPESAS_INDISPONIVEIS = "Despesas não têm vínculo com produto nem canal: com esses filtros ativos, despesas e resultado operacional não são exibidos."
ORCAMENTO_FILTROS = "Orçamento e despesas não têm vínculo com produto nem canal. Esses filtros são ignorados nesta página; valem período e filial."
