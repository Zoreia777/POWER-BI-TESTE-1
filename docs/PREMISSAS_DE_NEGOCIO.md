# Premissas de negócio

Registro das decisões que valem para o cenário **fictício** da Empresa X. Também estão no banco: `SELECT * FROM mart.ref_premissas_negocio`.
Tipos: **Decisão** (escolha do negócio), **Hipótese** (assumida, não comprovada pelos dados), **Limitação** (o dado não permite mais).
Aprovadas pelo usuário em 14/10/2026.

| ID | Tipo | Premissa | Onde se aplica |
|---|---|---|---|
| PN-DEV-01 | Decisão | Devolução integral cancela a receita da venda (por linha de pedido; não há devolução parcial de quantidade). Valores originais preservados. | `receita_reconhecida_provisoria = vendas_entregues` |
| PN-DEV-02 | **Hipótese (não comprovada)** | Produto devolvido volta ao estoque revendável; custo recuperável. | custo ajustado; sensibilidade `lucro_bruto_se_custo_nao_recuperado` |
| PN-DEV-03 | Limitação | Não existe data de devolução; nada é atribuído a período de estorno; o indicador ajustado não é receita contábil oficial. | séries por mês da venda original |
| PN-DEV-04 | Decisão | Registrada, entregues e devoluções são indicadores separados e reconciliáveis. | `kpi_devolucoes_reconciliacao` |
| PN-MRG-01 | Decisão | Margens negativas preservadas e sinalizadas; custos e preços intocados. | `flag_margem_negativa`, `kpi_margem_negativa_*` |
| PN-ORC-01 | Decisão | Orçado/meta × realizado só no período realizado. | `periodo_realizado`, `orcado_vs_realizado_*` |
| PN-PRC-01 | Decisão | Preço praticado preservado; variação de preço ≠ desconto; razão de somas. | `kpi_preco_*` |
| PN-SIN-01 | Limitação | Dados fictícios; padrões programados no gerador não são evidência de mercado. | `ref_comportamentos_sinteticos` |

Regra de uso: qualquer resultado que dependa de PN-DEV-01/02/03 deve citar a premissa ao ser apresentado (em tabela, gráfico ou entrevista).
