# Diagnóstico dos dados brutos — Empresa X

> Gerado por `scripts/diagnostico.py`. Todos os números abaixo foram medidos nos CSVs de `data/`; os dados são **fictícios** (gerados com semente fixa por `scripts/gerar_dados.py`).

## 1. Tabelas, chaves e qualidade

| Tabela | Linhas | Colunas | Linhas duplicadas | Chave duplicada | Nulos |
|---|---:|---:|---:|---:|---|
| dim_calendario | 1,096 | 21 | 0 | 0 | {'feriado': 1057} |
| dim_canal | 4 | 3 | 0 | 0 | — |
| dim_categoria_despesa | 18 | 5 | 0 | 0 | — |
| dim_cliente | 650 | 8 | 0 | 0 | {'data_primeira_compra': 5} |
| dim_departamento | 8 | 5 | 0 | 0 | — |
| dim_filial | 8 | 9 | 0 | 0 | — |
| dim_produto | 39 | 9 | 0 | 0 | — |
| dim_vendedor | 24 | 5 | 0 | 0 | — |
| fact_despesas | 7,075 | 7 | 0 | 0 | — |
| fact_metas_vendas | 270 | 5 | 0 | 0 | — |
| fact_orcamento | 6,005 | 5 | 0 | 0 | — |
| fact_rh_mensal | 909 | 7 | 0 | 0 | — |
| fact_vendas | 59,365 | 18 | 0 | 0 | — |

## 2. Relacionamentos validados (registros órfãos)

| Relacionamento | Órfãos |
|---|---:|
| fact_vendas.id_cliente -> dim_cliente.id_cliente | 0 |
| fact_vendas.id_produto -> dim_produto.id_produto | 0 |
| fact_vendas.id_filial -> dim_filial.id_filial | 0 |
| fact_vendas.id_vendedor -> dim_vendedor.id_vendedor | 0 |
| fact_vendas.id_canal -> dim_canal.id_canal | 0 |
| fact_vendas.data -> dim_calendario.data | 0 |
| fact_despesas.id_departamento -> dim_departamento.id_departamento | 0 |
| fact_despesas.id_categoria_despesa -> dim_categoria_despesa.id_categoria_despesa | 0 |
| fact_despesas.id_filial -> dim_filial.id_filial | 0 |
| fact_despesas.data -> dim_calendario.data | 0 |
| fact_orcamento.id_departamento -> dim_departamento.id_departamento | 0 |
| fact_orcamento.id_categoria_despesa -> dim_categoria_despesa.id_categoria_despesa | 0 |
| fact_orcamento.id_filial -> dim_filial.id_filial | 0 |
| fact_metas_vendas.id_filial -> dim_filial.id_filial | 0 |
| fact_rh_mensal.id_departamento -> dim_departamento.id_departamento | 0 |
| fact_rh_mensal.id_filial -> dim_filial.id_filial | 0 |

## 3. Consistência financeira (`fact_vendas`, tolerância R$ 0,02)

- receita_bruta ≠ quantidade × preço: **0**
- desconto_valor ≠ bruta × desconto_pct: **0**
- receita_líquida ≠ bruta − desconto − impostos: **0**
- valores ≤ 0 (qtd, preço, receita, custo): **0**
- linhas com margem negativa (custo > receita líquida): **612**
- linhas com preço ≠ preço de lista: **56,927**
- linhas `Devolvido`: **1,310** — receita líquida associada R$ 2,990,526.94 (2.19% do total), **registrada com sinal positivo**

## 4. Granularidade

- `fact_vendas`: 1 linha por **item de pedido** (33,209 pedidos, até 4 itens cada); pedido+produto duplicado: 0; pedidos com cliente/filial/data divergentes: 0
- `fact_despesas`: 1 linha por lançamento (data × departamento × categoria × filial × fornecedor)
- `fact_orcamento`: mensal × departamento × categoria × filial · `fact_metas_vendas`: mensal × filial · `fact_rh_mensal`: fim de mês × departamento × filial

## 5. Cobertura temporal

| Fato | Início | Fim |
|---|---|---|
| vendas | 2024-01-01 | 2026-09-30 |
| despesas | 2024-01-01 | 2026-09-30 |
| orcamento | 2024-01-01 | 2026-12-01 |
| metas | 2024-01-01 | 2026-12-01 |
| rh | 2024-01-31 | 2026-09-30 |

- Último mês realizado: **2026-09**. Linhas de orçamento posteriores a ele: **527** (comparar orçado × realizado exige limitar ao período realizado).
- Linhas de orçamento até o último mês realizado sem despesa correspondente: **10**.
- Vendas antes da abertura da filial: 0 · antes do cadastro do cliente: 0 · clientes sem nenhuma venda: 5

## 6. Pontos de atenção para análise (observações, ainda não explicações)

- Quedas mensais de receita > 15 %: {'2024-02': -0.167, '2025-01': -0.381, '2026-01': -0.288, '2026-02': -0.238}
- Menores margens por produto (apenas `Entregue`): {'Smartphone X Max': 0.004, 'Notebook Pro 14"': 0.158, 'Smartphone X Lite': 0.17}
