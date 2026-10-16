# Pipeline ETL — documentação técnica (Etapa 2)

CSV (`data/`) → **raw** → **stg** → **mart** em um banco DuckDB local (`warehouse/empresa_x.duckdb`).

## Como executar

```bash
pip install -r requirements.txt
python scripts/run_etl.py                         # ou: PYTHONPATH=src python -m empresax
python scripts/run_etl.py --dados outra_pasta --banco teste.duckdb
python -m pytest tests -q                         # suíte completa (416 testes)
```

Saídas: `warehouse/empresa_x.duckdb` (ignorado no git), `logs/etl_*.log`, `reports/relatorio_qualidade.md`.
Código de saída `0` = sucesso, `1` = falha controlada (mensagem em stderr).

## Camadas

| Camada | O que contém | Regras |
|---|---|---|
| `raw` | Cópia fiel dos 13 CSVs, tudo como texto + `_linha_origem` (linha do CSV; cabeçalho = 1) | Nada convertido, nada filtrado. Cabeçalho validado contra `schema.py`. Registros conferidos com o módulo `csv` (parser independente). |
| `stg` | Mesmas linhas, tipadas (`DATE`, `DECIMAL(14,2)`, `DECIMAL(7,4)`, `BIGINT`, `VARCHAR`) | `TRIM`, vazio → `NULL`, conversão **estrita** (regex + `TRY_CAST`; o `CAST` do DuckDB aceitaria `'1.0'` como inteiro). Valores não são corrigidos nem descartados. |
| `mart` | Modelo estrela + KPIs (25 tabelas) | SQL versionado em `sql/etl/mart/*.sql`, executado em ordem. |
| `ops` | `execucoes` (histórico), `qualidade_checks` (última rodada), `arquivos_origem` (SHA-256 dos CSVs) | Auditoria. |

**Reprodutibilidade e idempotência.** Toda tabela é recriada (`CREATE OR REPLACE`) a partir dos CSVs, dentro de **uma única
transação**: se qualquer validação obrigatória falhar, há `ROLLBACK` e o banco continua no último estado válido. Rodar duas
vezes gera exatamente o mesmo conteúdo (testado por hash de cada tabela). Só `ops.execucoes` cresce, por design.
Caminhos são relativos à raiz do repositório (`src/empresax/config.py`).

## Validações (143 na execução padrão; falha obrigatória aborta o pipeline)

raw = linhas do CSV · stg = raw · PK única · valores convertidos (datas reconvertidas para texto e comparadas ao original) ·
somas monetárias raw = stg · domínio de `status` · 19 relacionamentos sem órfãos · percentuais entre 0 e 1 · valores > 0 ·
`bruta = qtd × preço`, `desconto = bruta × %`, `líquida = bruta − desconto − impostos` (±R$ 0,02) · mart = stg ·
entregue + devolvido = total · devoluções e margens negativas preservadas · preço/custo inalterados ·
nenhuma linha em meses sem realizado · Σ orçado/realizado = CSV · reconciliação das devoluções · rastreabilidade (`linha_csv_origem`). Três **observações** (não erros) são registradas no relatório:

| Observação | Exige ação? |
|---|---|
| OBS-1 Devoluções preservadas com valores positivos; receita ajustada aplica PN-DEV-01/02/03 | **Não no ETL.** Decisão registrada. Manter o rótulo "provisória/não oficial"; reabrir se surgir data ou lançamento de estorno. |
| OBS-2 Margens negativas preservadas e sinalizadas | **Não no ETL.** Dado preservado; investigar por produto/período na análise (Etapas 3 e 4). |
| OBS-3 Orçamento futuro (após o último mês realizado) fora das comparações | **Não.** Orçamento é prospectivo; o corte avança sozinho com novos meses realizados. |

## Regras de negócio implementadas

### Devoluções (decisão aprovada em 14/10/2026 — ver `docs/DEVOLUCOES.md` e `docs/PREMISSAS_DE_NEGOCIO.md`)
As 1.310 linhas `Devolvido` ficam no `mart.fact_vendas` **com os valores originais (positivos)**. Quatro indicadores separados e reconciliáveis:

| Indicador | Definição |
|---|---|
| `receita_liquida_registrada` | todas as linhas (Entregue + Devolvido) |
| `vendas_entregues` | `receita_liquida` das linhas `Entregue` |
| `devolucoes` | `receita_liquida` das linhas `Devolvido`, **pelo mês da venda original** |
| `receita_reconhecida_provisoria` | = `vendas_entregues`. Indicador **ajustado e não oficial** (PN-DEV-01): "devolução integral cancela a receita" |

Reconciliação exata: `registrada = vendas_entregues + devolucoes` (view `mart.kpi_devolucoes_reconciliacao`, por ano e total, diferença = 0).
Custo: pela hipótese PN-DEV-02 (**não comprovada**), o custo devolvido é recuperável e sai do custo ajustado; `lucro_bruto_se_custo_nao_recuperado`
mostra a sensibilidade. Não existe data de devolução (PN-DEV-03): nada é atribuído a período de estorno e o indicador ajustado nunca é chamado de receita contábil oficial.
Rastreabilidade: `fact_vendas.linha_csv_origem` aponta a linha do CSV; `kpi_devolucoes_pedido` classifica os pedidos (31.922 sem devolução, 915 parciais, 372 totais).

### Margens negativas
`flag_margem_negativa = custo_total > receita_liquida` (612 linhas, 611 pedidos). Custos e preços não são tocados.
Tabelas: `kpi_margem_negativa_produto | _filial | _mes | _pedido`.

### Orçamento × realizado
O **último mês realizado** é derivado dos fatos (`mart.periodo_realizado`) e conferido com `dim_calendario.realizado`.
Tabelas `orcado_vs_realizado_mensal | _acumulado` e `meta_vs_realizado_mensal` só têm meses ≤ esse corte.

| Conceito | Definição | 2026 (jan–set) |
|---|---|---:|
| Orçamento **anual** | 12 meses do ano (inclui out–dez) | R$ 19,67 mi |
| Orçamento **acumulado** | jan → mês de referência | R$ 14,06 mi |
| Realizado **acumulado** | despesas jan → mês de referência | R$ 14,12 mi |

Realizado ÷ acumulado = **100,5 %** (comparação correta). Realizado ÷ anual = 71,8 %, que pareceria "economia" e é falso.
Linhas orçadas sem lançamento (10) aparecem com `realizado = 0` e `sem_lancamento_no_mes = true`.

### Preços
`mart.fact_vendas` mantém `preco_unitario` (praticado) e traz `preco_lista` de `dim_produto`.
`variacao_preco_pct = Σ(receita_bruta) / Σ(qtd × preço de lista) − 1`; `desconto_pct_efetivo = Σ desconto / Σ receita_bruta`.
São medidas **distintas**: `receita_bruta` já está a preço praticado, e o desconto é aplicado depois.
Limitação: `dim_produto.preco_lista` não tem vigência por data, então a comparação é contra a lista cadastrada (base jan/2024).
Tabelas: `kpi_preco_produto_mes`, `kpi_preco_mes`.

## Tabelas do mart

Dimensões: `dim_calendario, dim_canal, dim_categoria_despesa, dim_cliente, dim_departamento, dim_filial, dim_produto, dim_vendedor` ·
Fatos: `fact_vendas` (+ colunas derivadas), `fact_despesas, fact_orcamento, fact_metas_vendas, fact_rh_mensal` ·
KPIs: `kpi_vendas_mes, kpi_margem_negativa_*, kpi_preco_*, orcado_vs_realizado_*, meta_vs_realizado_mensal` ·
Referência: `periodo_realizado, ref_comportamentos_sinteticos` · Views: `kpi_devolucoes_reconciliacao, kpi_devolucoes_pedido, ref_premissas_negocio`.

## Exemplos de consultas

```sql
-- Receita registrada, entregue e devolvida por ano (componentes separados)
SELECT year(mes) ano, sum(receita_liquida_registrada) registrada, sum(vendas_entregues) entregues,
       sum(devolucoes) devolucoes, sum(devolucoes)/sum(receita_liquida_registrada) taxa
FROM mart.kpi_vendas_mes GROUP BY 1 ORDER BY 1;

-- Produtos com mais linhas de margem negativa
SELECT produto, linhas_margem_negativa, pct_linhas_margem_negativa, prejuizo_bruto
FROM mart.kpi_margem_negativa_produto ORDER BY linhas_margem_negativa DESC LIMIT 5;

-- Execução do orçamento por departamento no último mês realizado (acumulado x acumulado)
SELECT departamento, orcamento_acumulado, realizado_acumulado, execucao_acumulada_pct
FROM mart.orcado_vs_realizado_acumulado
WHERE mes_referencia = (SELECT ultimo_mes_realizado FROM mart.periodo_realizado)
ORDER BY execucao_acumulada_pct DESC;

-- Reajuste de preço (razão de somas) e desconto no mesmo mês, lado a lado
SELECT strftime(mes,'%Y-%m') mes, variacao_preco_pct, desconto_pct_efetivo FROM mart.kpi_preco_mes ORDER BY mes DESC LIMIT 3;
```

## Estrutura do código

`src/empresax/`: `config.py` (caminhos/política) · `schema.py` (contrato de dados) · `raw.py` · `staging.py` · `quality.py` ·
`mart.py` (executa `sql/etl/mart/*.sql`) · `pipeline.py` (transação, auditoria) · `errors.py` · `logger.py` · `comportamentos.py`.

## Análises (Etapa 3)

`src/empresax/consultas.py` executa `sql/analise/*.sql` sobre o mart (somente leitura) — ver `docs/CONSULTAS_SQL.md`.

> Etapa 4: o schema `bi` (views de consumo do Power BI) é criado por `scripts/run_powerbi.py` sobre o mart e não altera nenhuma tabela do ETL; ver `docs/POWERBI_CAMADA_DE_CONSUMO.md`.
