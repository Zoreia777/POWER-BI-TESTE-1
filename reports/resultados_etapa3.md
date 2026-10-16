# Resultados das análises SQL (Etapa 3)

Gerado por `scripts/run_queries.py`. Conteúdo determinístico: o hash prova que duas execuções geram o mesmo resultado.

| Resultado | Arquivo SQL | Linhas | SHA-256 (CSV) |
|---|---|---:|---|
| `01a_faturamento_mensal` | 01_faturamento.sql | 33 | `5ea439d63de3c880…` |
| `01b_faturamento_anual_ytd` | 01_faturamento.sql | 3 | `bd08a2d90e58f61b…` |
| `02a_ranking_produtos_receita` | 02_produtos_receita.sql | 39 | `c70a095a6816886c…` |
| `02b_receita_por_categoria` | 02_produtos_receita.sql | 5 | `e17ba7c15c84c4c4…` |
| `03a_margem_por_produto` | 03_margem_produtos.sql | 39 | `8724edb0e214cfcd…` |
| `03b_filtro_piso_resumo` | 03_margem_produtos.sql | 1 | `038e7005849a37d9…` |
| `04a_despesas_por_filial` | 04_despesas_filial.sql | 8 | `cd1c27a10b231bc9…` |
| `04b_despesas_filial_por_grupo` | 04_despesas_filial.sql | 40 | `2a1178ac69ac896e…` |
| `05a_resultado_operacional_mensal` | 05_lucratividade.sql | 33 | `9919e98d12cc414c…` |
| `05b_resultado_anual_ytd` | 05_lucratividade.sql | 3 | `ca8e250441011a0d…` |
| `06a_orcado_realizado_departamento_ytd` | 06_orcado_vs_realizado.sql | 8 | `ef0f59b13f306e18…` |
| `06b_orcado_realizado_categoria_ytd` | 06_orcado_vs_realizado.sql | 18 | `88b992108a7ec91d…` |
| `06c_leitura_ingenua_vs_correta` | 06_orcado_vs_realizado.sql | 3 | `245c77c0368667ce…` |
| `07a_quedas_empresa` | 07_quedas.sql | 33 | `0f9d01b0b2011bbe…` |
| `07b_quedas_filial` | 07_quedas.sql | 57 | `fc1a119543f48c9a…` |
| `07c_quedas_produto_yoy` | 07_quedas.sql | 104 | `735b5f35321faaa8…` |
| `07d_resumo_quedas_por_nivel` | 07_quedas.sql | 6 | `08926a2b3c57a62e…` |
| `08a_decomposicao_total` | 08_fatores_variacao.sql | 66 | `de09c327c86c6047…` |
| `08b_contribuicao_por_dimensao` | 08_fatores_variacao.sql | 2703 | `92b49ca0bccbc38f…` |
| `08c_decomposicao_produto_ultimo_mes` | 08_fatores_variacao.sql | 78 | `364a21529603b2f3…` |
| `08d_decomposicao_verificacao` | 08_fatores_variacao.sql | 2 | `fbf78436d3db48df…` |
