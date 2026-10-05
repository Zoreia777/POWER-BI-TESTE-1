# Dicionário de dados · Empresa X

Modelo estrela com **8 dimensões** e **5 fatos**. Datas em `AAAA-MM-DD`, valores em R$,
separador decimal ponto, codificação UTF-8.

## Dimensões

### `dim_calendario` (1.096 linhas · 01/01/2024 a 31/12/2026)
| Coluna | Descrição |
|---|---|
| `data` | Chave. Um dia por linha |
| `ano`, `semestre` (S1/S2), `trimestre` (T1–T4) | Agrupadores de tempo |
| `mes_num`, `mes_nome`, `mes_abrev` | Mês numérico, por extenso e abreviado |
| `ano_mes` | `2025-03` — bom para ordenar e para eixos |
| `mes_ano` | `mar/25` — rótulo amigável |
| `ordem_ano_mes` | `202503` — use para ordenar `mes_ano` |
| `dia`, `dia_semana_num` (1=segunda), `dia_semana`, `dia_semana_abrev`, `semana_do_ano` | Detalhe de dia |
| `fim_de_semana`, `dia_util` | Flags 0/1 (feriados nacionais descontados) |
| `feriado` | Nome do feriado nacional, quando houver |
| `realizado` | 1 = data até o corte (30/09/2026); 0 = projetado |
| `status_periodo` | "Realizado" ou "Projetado" |
| `primeiro_dia_mes` | Primeiro dia do mês da linha |

### `dim_filial` (8)
`id_filial` (chave), `filial`, `cidade`, `uf`, `regiao`, `tipo` (Matriz/Filial),
`data_abertura`, `latitude`, `longitude`.

### `dim_produto` (39)
`id_produto` (chave), `sku`, `produto`, `categoria` (Eletrônicos, Escritório, Casa & Conforto,
Software & Assinaturas, Serviços), `subcategoria`, `preco_lista`, `custo_unitario_base`,
`margem_lista_pct`, `aliquota_imposto`.

### `dim_cliente` (650)
`id_cliente` (chave), `nome_cliente`, `segmento` (Consumidor Final, Pequena Empresa, Média Empresa,
Corporativo), `cidade`, `uf`, `regiao`, `data_cadastro`, `data_primeira_compra`
(vazia para clientes que nunca compraram).

### `dim_vendedor` (24)
`id_vendedor` (chave), `nome_vendedor`, `equipe`, `cargo` (Júnior/Pleno/Sênior), `data_admissao`.
O vendedor "Atendimento Digital" recebe as vendas de e-commerce e marketplace.

### `dim_canal` (4)
`id_canal` (chave), `canal` (Loja Física, E-commerce, Televendas B2B, Marketplace),
`tipo_canal` (Físico, Digital, Remoto).

### `dim_departamento` (8)
`id_departamento` (chave), `departamento`, `centro_custo`, `responsavel`,
`tipo_area` (Área-fim / Suporte).

### `dim_categoria_despesa` (18)
`id_categoria_despesa` (chave), `categoria_despesa`, `grupo_dre` (Despesas com Pessoal, Comerciais,
Operacionais, Administrativas, Financeiras), `tipo_custo` (Fixa/Variável), `ordem_dre`.

## Fatos

### `fact_vendas` — uma linha por **item de pedido** (~59 mil linhas)
| Coluna | Descrição |
|---|---|
| `id_venda` | Chave da linha |
| `id_pedido` | Pedido (`PED-000123`); um pedido tem 1 a 4 itens |
| `data` | → `dim_calendario` |
| `id_cliente`, `id_produto`, `id_filial`, `id_vendedor`, `id_canal` | Chaves das dimensões |
| `quantidade`, `preco_unitario` | Unidades e preço praticado (reajusta ao longo do tempo) |
| `desconto_pct` | Fração (0,05 = 5%) |
| `receita_bruta` | `quantidade × preco_unitario` |
| `desconto_valor` | `receita_bruta × desconto_pct` |
| `impostos_valor` | Alíquota da categoria sobre (bruta − desconto) |
| `receita_liquida` | `receita_bruta − desconto_valor − impostos_valor` |
| `custo_total` | **CMV** do item (`quantidade × custo unitário do dia`) |
| `forma_pagamento` | PIX, Cartão de Crédito, Cartão de Débito, Boleto, Transferência |
| `status` | `Entregue` ou `Devolvido` (devolvidos não entram na receita) |

### `fact_despesas` — um lançamento de gasto (~7 mil linhas)
`id_despesa` (chave), `data`, `id_departamento`, `id_categoria_despesa`, `id_filial`,
`fornecedor`, `valor`. Existe só para o período realizado (até 30/09/2026).

### `fact_orcamento` — orçamento mensal
`mes` (primeiro dia do mês), `id_departamento`, `id_categoria_despesa`, `id_filial`,
`valor_orcado`. Vai até dez/2026. Grão: mês × departamento × categoria × filial.

### `fact_metas_vendas` — meta mensal por filial
`mes` (primeiro dia do mês), `id_filial`, `meta_receita_liquida`, `meta_margem_bruta_pct`,
`meta_lucro_bruto`. Vai até dez/2026.

### `fact_rh_mensal` — foto do quadro no fim do mês
`data_referencia` (último dia do mês), `id_departamento`, `id_filial`, `headcount`,
`headcount_planejado`, `admissoes`, `desligamentos`.

## Regras de negócio embutidas

- **DRE:** Receita Bruta − Descontos − Impostos = Receita Líquida; − CMV = Lucro Bruto;
  − Despesas = Resultado Operacional.
- **Folha:** `Salários` = headcount × salário médio do departamento (reajuste em março);
  `Encargos` = 36% dos salários; `Benefícios` = valor fixo por funcionário.
- **Variáveis:** comissões (~1,8% da receita), frete e tarifas dependem do canal; marketplace
  cobra 11% de comissão.
- **Filiais novas:** Recife (jun/2024) e Salvador (fev/2025) começam com vendas em rampa de 9 meses
  e já têm despesas no mês anterior à abertura.
- **Orçamento e metas** são calculados sobre a receita *esperada*; por isso o realizado oscila
  em torno deles (e as histórias do README fazem o realizado desviar).
