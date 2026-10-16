# Aplicativo analítico (Streamlit) — Etapa 5

Aplicativo de BI com 5 páginas sobre as views `bi` do warehouse DuckDB. Código em `app/` (interface) e `src/empresax/app/` (dados, filtros, gráficos, estudos de caso — sem Streamlit, para ser testável).

## Como executar (local)

```bash
pip install -r requirements.txt
python scripts/run_etl.py         # 1) cria o warehouse (CSVs → raw → stg → mart)
python scripts/run_powerbi.py     # 2) cria as views `bi` (o app lê SOMENTE elas)
python scripts/run_analises.py    # 3) gera os achados rotulados exibidos em "Investigações" (opcional, mas recomendado)
streamlit run app/streamlit_app.py
```

Abre em `http://localhost:8501`. Para usar outro banco: `EMPRESAX_BANCO=/caminho/empresa_x.duckdb streamlit run app/streamlit_app.py`.

**Atenção (DuckDB):** o ETL e o `run_powerbi.py` precisam de acesso de escrita ao arquivo; o DuckDB não permite escrita enquanto outro processo mantém o arquivo aberto, nem mesmo em leitura. **Feche o aplicativo antes de rodar o ETL de novo.** Se o banco for regravado com o app aberto, a próxima interação usa o novo arquivo (a chave de cache inclui o mtime e o tamanho do arquivo).

Se o banco ou as views não existirem, o app mostra uma mensagem com o comando a executar (não uma pilha de erro).

## Páginas

| Página | Pergunta | Destaques |
|---|---|---|
| Visão Geral | Como está a empresa no recorte? | 8 indicadores com unidade e contexto; reconciliação registrada = entregues + devoluções (diferença R$ 0,00); tendência com margem; anos lado a lado |
| Filiais | Quem vende mais, com que margem, como evoluiu? | ranking de receita e margem; variação anual só com base comparável; mapa de calor filial × mês; tabela |
| Produtos e Margem | Quem sustenta a receita e quem corrói a margem? | bolhas receita × margem; menores margens; categorias; piso de linhas configurável (padrão 200, como na Etapa 3) |
| Orçamento | O gasto está dentro do orçado dos mesmos meses? | execução (realizado ÷ orçado **acumulado**); anual × acumulado × realizado explicados; departamentos e categorias com faixa ±5% |
| Investigações | Estudos de caso | **Porto Alegre** (pedidos × linhas × receita por linha), **Smartphone X Max** (preço, custo, margem), **preço × volume × mix** reconciliado, todos os achados rotulados |

Filtros da barra lateral: período (somente meses realizados), filiais, produtos, canais. Campo vazio = todos.

## Regras de negócio aplicadas

- PN-DEV-01/02/03: receita ajustada sempre rotulada **provisória**, ao lado de registrada e devoluções; nenhuma data de devolução é inventada; premissas exibidas em cada página.
- Comparação anual **somente** contra o período equivalente do ano anterior (mesmos meses, mesmos filtros). Sem base ou base zero → “sem comparação” com o motivo, nunca 0% ou infinito.
- Nenhum mês futuro é tratado como realizado (o período é limitado ao último mês realizado e o orçamento anual é mostrado apenas como referência).
- Despesas e orçamento não têm produto/canal: com esses filtros ativos são omitidos (Visão Geral, Filiais) ou ignorados com aviso (Orçamento).
- Hipóteses sempre rotuladas e com aviso de que não são causa comprovada; padrões programados no simulador são sinalizados.
- Recorte sem vendas: aviso e **nenhum indicador** (evita que “0” seja lido como resultado).

## Decomposição preço × volume × mix (página Investigações)

Mesma identidade de `docs/METODOLOGIA_DECOMPOSICAO.md` aplicada a **períodos** (cada período é agregado por produto): volume, mix, preço, desconto, impostos, produtos novos, produtos que pararam e devoluções. A cascata vai da receita ajustada da base à do período atual e fecha com resíduo R$ 0,00 (exibido). Efeitos de preço e volume não provam causalidade. O eixo da cascata é ampliado quando os efeitos são pequenos diante da base, com aviso na própria figura.

## Segurança e desempenho

- **Conexão somente leitura** (`read_only=True`, única chamada `duckdb.connect` do app); testes tentam `CREATE/DELETE/DROP` e falham como esperado.
- **Sem injeção de SQL:** valores de filtros entram **sempre como parâmetros** (`?`); ids precisam ser inteiros existentes nas dimensões; datas precisam ser meses realizados; nomes de coluna/tabela vêm de dicionários fixos (lista branca).
- **Cache** (`st.cache_data`/`cache_resource`): a chave inclui o caminho, o mtime e o tamanho do banco — um novo ETL invalida tudo. Cada consulta usa um cursor próprio.

## Testes (Etapa 5)

`tests/test_app.py` (camada de dados: filtros, segurança, somente leitura, falhas do banco, valores × 290 referências independentes, 60 combinações aleatórias de filtros × pandas nos CSVs, vazios e denominadores zerados, decomposição × Python puro, estudos de caso) e `tests/test_app_ui.py` (execução real das páginas com `streamlit.testing`: sem exceções, premissas presentes, filtros alteram resultados, estados vazios, banco ausente, escape de `$`, gráficos).

## Evidências de execução

`reports/app_evidencias/*.png`: capturas do app rodando em servidor real (Chromium/Playwright): as 5 páginas, as abas de Investigações, filtro de filial, recorte vazio e visão em tela estreita. A conferência visual foi feita **nas capturas listadas**; não houve teste de todas as combinações possíveis de filtros em navegador (isso é coberto na camada de dados e no `AppTest`, que não renderiza pixels).

## Limitações conhecidas

- Dados 100% fictícios (PN-SIN-01). O app não faz previsões nem recomenda preços.
- Tabelas são formatadas como texto em pt-BR (ordenar pela coluna usa ordem alfabética).
- Os achados rotulados vêm de `reports/executivo/evidencias/` (gerados pelo `run_analises.py`): se os dados mudarem, rode-o de novo.
- Medidas DAX continuam **não executadas no Power BI** (ver `docs/POWERBI_ROTEIRO_DE_CONSTRUCAO.md`).

## Rodada de melhorias visuais (apenas apresentação)

Nenhum cálculo, consulta SQL, regra de negócio ou dado foi alterado; mudaram só CSS, layout e cores dos gráficos.

| Problema encontrado no navegador (antes) | Correção |
|---|---|
| Valores dos cartões ("R$ 41,29 mi", "R$ 14,06 mi", "R$ 179,4 mil") cortados com reticências (80 casos medidos em 40 combinações de tema × largura × página) | Valor e rótulo quebram de linha em vez de cortar; fonte do valor escala com a largura do cartão (`clamp` + container query); colunas passam para a linha de baixo em telas estreitas |
| Rótulo longo "Execução (realizado ÷ orçado acumulado)" | Título curto "Execução do orçamento"; a explicação completa fica no tooltip (?) |
| Rótulos nas pontas das barras ilegíveis no tema escuro (contraste 1,28:1; 296 textos) | Removidos o `template="plotly_white"` e a cor de fonte fixa: o tema do Streamlit define texto/grade; paleta com contraste ≥ 3:1 em fundo claro **e** escuro |
| Variação anual (Investigações): rótulos negativos sobre a barra/cortados | Eixo com folga para rótulos positivos e negativos, `automargin`, rótulos fora da barra |
| Faixa "±5%" sobreposta às barras (Orçamento) | Legenda movida para fora da área do gráfico; barras de execução ganharam rótulo de valor |

Verificação: `tests/test_visual_navegador.py` sobe o app de verdade (Chromium/Playwright) em tema claro e escuro, de 1440 px a 390 px (inclui 1024 px com escala de 125%, como em notebooks Windows) e exige: nenhum texto de cartão cortado, nenhuma rolagem horizontal, nenhuma exceção, contraste ≥ 3:1 nos textos dos gráficos. Capturas antes/depois e as medições: `reports/app_evidencias/melhorias_visuais/`.
