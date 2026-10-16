# Análises SQL da Etapa 3 — guia (pergunta → consulta → técnicas → regras → limites)

Execução: `python scripts/run_etl.py && python scripts/run_queries.py` → `reports/consultas/*.csv` (21 resultados) + `reports/resultados_etapa3.md` (hash de cada um).
Parâmetros em `src/empresax/config.py`: `limiar_queda_mom=-0.15`, `limiar_queda_yoy=-0.10`, `piso_linhas_margem=200` (0 = todos), `tolerancia_orcamento_pct=0.05`.

## Convenções que valem para todas

- **Indicador principal**: *receita ajustada provisória* (= vendas entregues, PN-DEV-01), **sempre ao lado** da receita registrada, das vendas entregues e das devoluções (`registrada = entregues + devoluções`, diferença 0,00). Não é reconhecimento contábil definitivo.
- Só meses **realizados** (até 2026-09). 2026 é comparado com jan–set dos anos anteriores (YTD equivalente).
- Percentuais sempre como **razão de somas**; nunca média de percentuais.
- `sem_base` / `sem_atividade` / `base_zerada` ≠ crescimento nem 0 %: o percentual fica vazio.
- Rótulos nos textos: **OBSERVAÇÃO** (medido pela consulta) · **CONCLUSÃO ARITMÉTICA** (decorre das contas) · **HIPÓTESE** (explicação não comprovada) · **PADRÃO PROGRAMADO** (o gerador sintético o criou — P-id em `mart.ref_comportamentos_sinteticos`; não é evidência de mercado).
- “Resultado operacional **estimado do dataset**” = receita ajustada − custo ajustado − despesas; **não é lucro líquido contábil**.

## 01 · Faturamento (`01_faturamento.sql`)
**Pergunta:** quanto a empresa faturou? **Técnicas:** CTE, LEFT JOIN com calendário, LAG(1)/LAG(12), CASE de status, FILTER.
- 01a mensal; 01b anual e YTD. Última linha (set/26): registrada R$ 5.410.973,76 = entregues R$ 5.301.783,74 + devoluções R$ 109.190,02.
- **OBSERVAÇÃO:** YTD jan–set: 2024 R$ 27,07 mi → 2025 R$ 34,28 mi (+26,6 %) → 2026 R$ 41,29 mi (+20,4 %).
- **Limite:** devoluções ficam no mês da venda (sem data de devolução).

## 02 · Produtos por receita (`02_produtos_receita.sql`)
**Técnicas:** window SUM() OVER (participação e acumulado), RANK, curva ABC. Regra ABC: classe pela participação acumulada *antes* do próprio produto (A < 80 %, B < 95 %).
- **OBSERVAÇÃO:** Notebook Pro 14" lidera (R$ 11,45 mi; 8,6 %); 18 produtos A, 12 B, 9 C.

## 03 · Menor margem (`03_margem_produtos.sql`)
**Técnicas:** LEFT JOIN, FILTER, NULLIF, RANK NULLS LAST. **Filtro explícito** (`filtro_aplicado` em cada linha; `03b` conta incluídos/excluídos): piso de 200 linhas entregues (config; 0 inclui todos — produto sem vendas aparece com margem NULA, por último). Com piso 200 nenhum dos 39 produtos é excluído (menor volume = 676).
- **OBSERVAÇÃO:** Smartphone X Max margem bruta ajustada 0,44 %, 47,5 % das linhas com margem negativa; −1,8 % se o custo devolvido não fosse recuperado. **PADRÃO PROGRAMADO P07** (custo +1 %/mês, preço fixo).
- **Hipótese de custo (PN-DEV-02, não comprovada):** custo da devolução recuperado; a coluna de sensibilidade mostra o outro extremo.

## 04 · Despesas por filial (`04_despesas_filial.sql`)
**Técnicas:** JOIN, GROUP BY, participação por window, razão despesa/receita. Absoluto, % do total, por grupo DRE e % da receita ajustada.
- **OBSERVAÇÃO:** Matriz = R$ 22,42 mi (49,0 % das despesas; 51,8 % da sua receita); 54,3 % da Matriz é pessoal. A Matriz concentra **despesas corporativas** (nota na coluna `nota_leitura`): **não** compará-la a filial comercial nem classificar “eficiência” só por esta razão. Demais filiais 22–31 % da receita.

## 05 · Resultado operacional estimado (`05_lucratividade.sql`)
**Técnicas:** CTE, window com `ROWS BETWEEN 2 PRECEDING`, acumulado por ano, NULLIF. Média móvel 3m = Σresultado ÷ Σreceita (razão de somas).
- **OBSERVAÇÃO:** margem operacional estimada YTD: 6,26 % (2024), 6,15 % (2025), 6,05 % (2026); margem bruta 43,3 % → 41,8 % → 40,3 %. **CONCLUSÃO ARITMÉTICA:** a margem bruta cai ~3 p.p. em 2 anos; o resultado operacional cai bem menos porque as despesas crescem menos que a receita.

## 06 · Orçado × realizado (`06_orcado_vs_realizado.sql`)
Três conceitos separados (PN-ORC-01): orçamento **anual**, **acumulado** (jan→mês de referência), realizado acumulado. Execução = realizado acum. ÷ orçado **acum.**; faixa ±5 % configurável.
- **OBSERVAÇÃO (06c):** em 2026 a leitura *ingênua* (÷ anual) dá 71,8 % — “economia” falsa; a correta dá 100,5 %.
- TI 105,7 % (única acima da faixa por departamento; **PADRÃO PROGRAMADO P15**); por categoria 5 de 18 acima da faixa (Juros e tarifas 130,4 %, Software 117,6 %, Energia/água/internet 107,8 %).

## 07 · Quedas (`07_quedas.sql`)
Limiares: MoM ≤ −15 %, YoY ≤ −10 %. Grade completa (mês × unidade). **Técnicas:** CROSS JOIN, LAG(1/12), CASE, UNION ALL, FILTER.
- **OBSERVAÇÃO:** empresa: 4 quedas MoM (fev/24, jan/25, jan/26, fev/26 — **P01/P05**), **0 quedas YoY**. Filial: 47 MoM / 18 YoY; produto: 330 MoM / 104 YoY.
- Maior queda YoY em reais por filial: **Porto Alegre fev/26 −48,9 % (−R$ 171,9 mil)**: **não** corresponde a nenhum padrão programado (P10 cobre jun–ago/2025). **HIPÓTESE não verificada** (ex.: base de fev/25 atípica); investigar na Etapa 4.
- Por produto: **Notebook Pro 14" ago/25 −95,4 % YoY** — **PADRÃO PROGRAMADO P09** (ruptura).

## 08 · Fatores de variação (`08_fatores_variacao.sql`)
Metodologia e exemplos: `docs/METODOLOGIA_DECOMPOSICAO.md`. 08a total (volume, mix, preço, desconto, imposto, novo, descontinuado, arredondamento, devoluções); 08b contribuição por filial/canal/produto; 08c por produto no último mês; 08d auditoria.
- **CONCLUSÃO ARITMÉTICA (set/26 vs ago/26, registrada −R$ 105,4 mil):** volume −R$ 182,0 mil, mix +R$ 85,7 mil, preço +R$ 7,9 mil, desconto −R$ 17,0 mil, imposto ≈ 0; devoluções levam a ajustada −R$ 121,8 mil. Resíduo 0,00 em 53 comparações válidas (32 MoM + 21 YoY).
- YoY set/26 (+R$ 654,5 mil ajustada): volume +512,3 mil, mix +48,0 mil, preço +94,2 mil.
- Contribuição YoY por filial (set/26): Matriz +R$ 382 mil (58 % da variação), Curitiba +229 mil, Brasília +174 mil; Belo Horizonte −130 mil. Participação pode passar de ±100 % quando unidades se compensam, e é NULA se a variação total ≈ 0.
- **Limite:** “por que o volume caiu?” é **HIPÓTESE** — o SQL só mostra *onde* e *quanto*.

## Qualidade de teste
`tests/test_consultas.py` (58 testes): oráculos independentes (pandas / Python puro), 13 cenários injetados em mini-mart, 9 mutações, determinismo (2 execuções → mesmos bytes), CSVs de origem intactos (hash), cabeçalhos e rótulos. Um defeito real de determinismo (zero negativo e ordem de soma em ponto flutuante) foi detectado por esses testes e corrigido em `consultas.py`.
