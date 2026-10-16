# Devoluções — investigação e decisão pendente

## O que foi investigado (fatos medidos em `data/fact_vendas.csv`)

| Pergunta | Evidência |
|---|---|
| Existe lançamento de estorno? | **Não.** Nenhum valor negativo; nenhuma linha referencia outra venda; `id_venda` é sequencial e único. |
| Existe data da devolução? | **Não.** Não há coluna de data/motivo/documento de devolução. A linha `Devolvido` tem a mesma data da venda. |
| Qual a granularidade do status? | **Por item de pedido.** 31.922 pedidos 100 % entregues, 915 parcialmente devolvidos, 372 totalmente devolvidos. |
| Valores nas linhas devolvidas | Receita bruta, desconto, impostos, líquida e **custo** permanecem integrais e positivos (R$ 2,99 mi de receita líquida, 2,19 % do total; ~R$ 2,06 mi de custo). |
| Convenção anterior do projeto | `sql/views.sql` e `powerbi/medidas_dax.md` excluem `Devolvido` da receita e do CMV, como "simplificação", sem justificativa contábil. |
| Origem do padrão | No gerador, o status é sorteado por linha com probabilidade por produto (`p['dev']`, linha 580): é um atributo simulado, não um processo (Cadeira Gamer ≈ 9,8 % da receita). |

## Conclusão da investigação

Os dados **não permitem determinar** o tratamento contábil: sem data não dá para saber *quando* a receita foi estornada; sem lançamento não
dá para saber se o custo foi recuperado; e não há como distinguir cancelamento antes da entrega de devolução posterior.
Por isso a decisão abaixo é uma **premissa do cenário fictício**, não um fato extraído dos dados.

## Decisão de negócio (aprovada em 14/10/2026)

| # | Decisão | Natureza | Implementação |
|---|---|---|---|
| 1 | Uma devolução integral cancela a receita da venda; valores originais preservados; indicadores separados (registrada, entregues, devoluções) | Decisão | `receita_reconhecida_provisoria = vendas_entregues`; `registrada = entregues + devoluções` (diferença 0, testado) |
| 2 | O produto devolvido volta ao estoque revendável e seu custo é recuperável | **Hipótese do cenário, não comprovada** | Custo ajustado exclui `custo_devolvido`; `lucro_bruto_se_custo_nao_recuperado` mostra a sensibilidade |
| 3 | Sem data de devolução: não inventar datas nem atribuir estornos a períodos; não chamar o indicador ajustado de receita contábil oficial | Limitação documentada | Séries mensais usam o **mês da venda original** (`base_temporal_devolucao`); rótulos "provisória/não oficial" + `COMMENT` nas colunas |

O que **não** foi feito: nenhuma linha excluída, nenhum valor invertido para negativo, nenhuma data criada, nenhum CSV alterado.

## Como ler os indicadores

- `devolucoes` de março/2025 = vendas **de março/2025** que constam como devolvidas, e não estornos ocorridos em março.
- `receita_reconhecida_provisoria` é a receita "líquida de devoluções" por mês da venda sob a premissa 1. Apresente-a sempre junto das três métricas e da premissa.
- Reabrir a decisão se o negócio fornecer data de devolução (então o estorno poderá ir ao período correto) ou comprovar que o custo não é recuperável.
