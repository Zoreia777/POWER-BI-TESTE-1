# Relatório executivo — Investigação analítica da Empresa X (Etapa 4)

> **Dados 100% sintéticos.** Padrões, quedas e margens foram em parte *programados* no gerador (`mart.ref_comportamentos_sinteticos`, P01–P17). Nada aqui é evidência sobre empresas ou mercados reais; o objetivo é demonstrar método. Receita = *receita ajustada provisória* (PN-DEV-01). “Resultado operacional estimado” **não é lucro líquido contábil**.

## Como ler os achados

- **OBSERVAÇÃO** — o que os dados mostram, medido.
- **CONCLUSÃO ARITMÉTICA** — decorre diretamente das contas, sem interpretar causa.
- **HIPÓTESE** — explicação possível, NÃO comprovada.
- **PADRÃO PROGRAMADO** — criado de propósito no gerador sintético (registro P01–P17).

Nenhuma causa é atribuída sem evidência: onde só há hipótese, ela vem rotulada e acompanhada de uma pergunta a investigar.

## Resumo executivo

1. **Crescimento é sobretudo volume.** Receita ajustada jan–set: R$ 41,29 mi (+20,4% sobre o ano anterior). Na decomposição, volume responde por 92% da variação, preço 10% e mix -1%.
2. **Margem bruta em queda de 3,1 p.p. em dois anos, concentrada em dois produtos.** Smartphone X Max e Notebook Pro 14" respondem por 76% da queda da margem bruta. Despesas crescendo menos que a receita mantiveram a margem operacional estimada em 6,3% → 6,0%.
3. **Smartphone X Max vende com prejuízo bruto desde nov/25** (100% das linhas negativas); custo por unidade +37% com preço fixo. Para margem zero o preço teria de subir 14% sobre a lista (cálculo aritmético, sem elasticidade).
4. **Porto Alegre em fev/26 (-48,9%) é, em grande parte, efeito de uma base atípica**: pedidos -6,6% e linhas +2,9%, mas receita por linha -50,4%; um produto explica 62% da variação. Causa não comprovada (hipótese).
5. **Quedas anuais: poucas merecem atenção.** 18 quedas de filial (nenhuma persistente) e 104 de produto (3 persistentes). A maior (Notebook Pro, ago/25) é evento programado (ruptura).
6. **Orçamento: comparar com o acumulado.** Execução correta 100,5% contra 71,8% na leitura ingênua; Tecnologia da Informação é o único departamento acima da faixa (105,7%).
7. **Desconto e quantidade: a associação some ao controlar canal e segmento** (de 0.127 para -0.001 unidade por p.p.): exemplo de confusão que impede ler correlação como causa.

## Porto Alegre em fev/2026: o que explica a queda ano a ano?

**Pergunta de negócio.** A queda de fev/26 contra fev/25 em Porto Alegre indica perda de clientes/pedidos ou é um efeito de composição e de base de comparação?

**Método.** Série mensal da filial; comparação fev/25 × fev/26 em pedidos, linhas, unidades e receita por linha; decomposição volume/mix/preço (mesma metodologia da Etapa 3, aplicada só à filial); concentração por produto e por cliente na base; posição da variação entre todas as variações anuais de filiais; sensibilidade aritmética removendo as maiores linhas da base.

### Evidências

- **[OBSERVAÇÃO]** `INV1.1` Receita ajustada de Porto Alegre: R$ 351.281 em fev/25 → R$ 179.410 em fev/26 (-48,9%; queda de R$ 171,9 mil).
- **[OBSERVAÇÃO]** `INV1.2` A atividade não encolheu na mesma proporção: pedidos -6,6%, linhas +2,9%, unidades -22,2%; a receita por linha caiu 50,4% (R$ 3.378 → R$ 1.677).
- **[OBSERVAÇÃO]** `INV1.5` Em Porto Alegre, Notebook Pro 14" vendeu em média 4,5 unidades/mês (mediana 4,0); fev/25 teve 20 unidades — o máximo da série de 33 meses; fev/26 teve 2. Meses com volume igual ou maior que o da base: 1.
- **[OBSERVAÇÃO]** `INV1.6` Concentração na base: as 5 maiores linhas de fev/25 somam 38,1% da receita do mês (em fev/26: 22,7%). O maior cliente da base (id 421) comprou R$ 103.131 (29,4% da filial no mês); em fev/26 esse cliente comprou R$ 22.135.
- **[OBSERVAÇÃO]** `INV1.8` Entre as 168 variações anuais mês×filial calculáveis, a de Porto Alegre em fev/26 é a pior (mediana geral: +18,6%).
- **[OBSERVAÇÃO]** `INV1.9` Relação fev/jan em Porto Alegre: 1,12 (2024), 1,07 (2025), 0,58 (2026). Na empresa toda foi 0,84, 0,97 e 0,77.
- **[CONCLUSÃO ARITMÉTICA]** `INV1.3` Decomposição da variação registrada (-R$ 171,5 mil): volume -R$ 75,1 mil, mix -R$ 90,5 mil, preço R$ 3,1 mil, desconto -R$ 0,8 mil, produtos que deixaram de vender -R$ 12,9 mil, produtos novos R$ 4,7 mil. Preço e desconto praticamente não contribuem; o resíduo é 0,00.
- **[CONCLUSÃO ARITMÉTICA]** `INV1.4` Um único produto, Notebook Pro 14", responde por -R$ 106,6 mil (62,2% da variação registrada): 20 unidades em fev/25 contra 2 em fev/26.
- **[CONCLUSÃO ARITMÉTICA]** `INV1.7` Sensibilidade aritmética (não é cenário real): retirando da base as 3 maiores linhas (R$ 105.897), a variação anual seria -26,9% em vez de -48,9%.
- **[HIPÓTESE]** `INV1.11` Base de comparação atípica: fev/2025 teria sido inflado por poucas compras grandes (concentradas em Notebook Pro 14" e em poucos clientes), não recorrentes. É coerente com os números acima, mas NÃO está provado — os dados não distinguem compra pontual de demanda recorrente. Em dados sintéticos, a variação aleatória das quantidades por linha é uma explicação natural; em uma empresa real seria preciso verificar contratos/pedidos.
- **[HIPÓTESE]** `INV1.12` Hipótese alternativa (não sustentada pelos pedidos): perda de clientes ou de demanda local. Os pedidos caíram pouco (-6,6%) e as linhas subiram (+2,9%), o que a torna menos provável, mas não a elimina.
- **[PADRÃO PROGRAMADO]** `INV1.10` O gerador programa para Porto Alegre apenas o efeito de concorrente em jun–ago/2025 (P10, −18%). Nenhum padrão P01–P17 cobre fev/2025 nem fev/2026 em Porto Alegre; a sazonalidade de fevereiro (P01, 0,84×) é um fator geral do gerador, não específico de Porto Alegre.

- 📈 Gráfico interativo: [`graficos/g01_pa_serie.html`](graficos/g01_pa_serie.html)
- 📈 Gráfico interativo: [`graficos/g02_pa_waterfall.html`](graficos/g02_pa_waterfall.html)
- 📈 Gráfico interativo: [`graficos/g03_pa_notebook.html`](graficos/g03_pa_notebook.html)

**Tabela — comparacao_fev25_fev26** (CSV completo em `evidencias/INV1_comparacao_fev25_fev26.csv`)

| metrica | base | atual | variacao_pct |
|---|---|---|---|
| receita_ajustada | 351,281.39 | 179,410.16 | -0.4893 |
| pedidos | 61.0000 | 57.0000 | -0.0656 |
| linhas | 104.00 | 107.00 | 0.0288 |
| unidades | 297.00 | 231.00 | -0.2222 |
| receita_por_linha | 3,377.71 | 1,676.73 | -0.5036 |
| receita_por_pedido | 5,758.71 | 3,147.55 | -0.4534 |


**Tabela — clientes_maiores_na_base** (CSV completo em `evidencias/INV1_clientes_maiores_na_base.csv`)

| id_cliente | receita_ajustada_base | receita_ajustada_atual |
|---|---|---|
| 421 | 103,130.66 | 22,134.73 |
| 555 | 94,621.76 | 1,878.71 |
| 444 | 28,019.34 | 22,757.12 |
| 32 | 20,587.24 | 18,885.87 |
| 70 | 12,523.94 | 0.0000 |

### Limitações dos dados

- Uma comparação de um único mês por filial é estatisticamente frágil (≈100 linhas).
- Não há dados de pipeline, contratos, estoque ou concorrência para testar as hipóteses.
- Dados sintéticos: variações aleatórias do gerador não correspondem a fatos de mercado.

### Recomendações gerenciais (condicionais)

- Se a empresa confirmar que as compras grandes de fev/25 foram pontuais, tratar fev/25 como base atípica e comparar Porto Alegre com a média móvel de 3–6 meses, não com um único mês.
- Se, ao contrário, os clientes grandes de Porto Alegre deixaram de comprar, abrir uma ação comercial dirigida a eles (a carteira é pequena e a perda seria material).
- Em ambos os casos, acompanhar indicadores de concentração (peso das 5 maiores linhas/clientes) junto com a receita.

### Próximas perguntas para uma empresa real

- Os grandes pedidos de fev/2025 em Porto Alegre eram recorrentes (contrato) ou únicos?
- Os clientes que mais compraram em fev/2025 compraram em outros meses e filiais?
- Houve mudança de equipe, estoque ou preço local em fev/2026?

## Quedas ano a ano por filial e por produto

**Pergunta de negócio.** Entre as quedas anuais (≤ -10%) de filiais e produtos, quais são relevantes em reais, persistentes e não explicadas por eventos programados?

**Método.** Grade completa mês × unidade; queda = variação anual ≤ -10%; persistente = ≥ 3 meses seguidos; decomposição volume/mix/preço de cada queda de filial; produto líder da queda; rótulo de coincidência com eventos programados (P09–P11).

### Evidências

- **[OBSERVAÇÃO]** `INV2.1` 18 quedas anuais (≤ -10%) em mês×filial, somando R$ 1,67 mi de receita a menos que no mesmo mês do ano anterior. As três maiores: Porto Alegre fev/26 (-48,9%, -R$ 171,9 mil); São Paulo (Matriz) jul/26 (-10,0%, -R$ 157,0 mil); Belo Horizonte nov/25 (-19,7%, -R$ 151,6 mil).
- **[OBSERVAÇÃO]** `INV2.2` Persistência: 0 das 18 quedas fazem parte de sequências de 3+ meses seguidos. As demais (18) são episódios curtos.
- **[OBSERVAÇÃO]** `INV2.6` 104 quedas anuais (≤ -10%) em produto×mês, em 38 dos 39 produtos; as 10 maiores concentram 39% do valor perdido (R$ 2,75 mi no total).
- **[OBSERVAÇÃO]** `INV2.7` Persistência: 3 das 104 quedas pertencem a sequências de 3+ meses; 101 são episódios curtos.
- **[OBSERVAÇÃO]** `INV2.8` Maior queda: Notebook Pro 14" em ago/25 (-95,4%; -R$ 256,1 mil).
- **[OBSERVAÇÃO]** `INV2.10` Produtos com maior valor acumulado de quedas anuais: Notebook Pro 14" (4 meses, -R$ 503,3 mil); Notebook Essencial 15" (4 meses, -R$ 249,2 mil); Monitor 27" 4K (3 meses, -R$ 171,6 mil); Consultoria de Layout (6 meses, -R$ 137,3 mil); Mesa Regulável Elétrica (2 meses, -R$ 130,0 mil).
- **[CONCLUSÃO ARITMÉTICA]** `INV2.3` Em 100% das quedas de filial, o efeito volume+mix é maior (em módulo) que o efeito preço+desconto+imposto: as quedas anuais são, aritmeticamente, de quantidade/composição de produtos, não de preço.
- **[HIPÓTESE]** `INV2.5` As 15 quedas curtas e sem evento programado podem refletir variação natural de pedidos grandes (ver INV1 — Porto Alegre) e de calendário (dias úteis); isso não foi testado causa a causa.
- **[HIPÓTESE]** `INV2.11` Como 101 de 104 quedas de produto são episódios curtos, a explicação mais compatível é variação pontual de pedidos (e, no caso do P09, ruptura), e não perda estrutural de demanda. É hipótese: não foi testada produto a produto.
- **[PADRÃO PROGRAMADO]** `INV2.4` 3 quedas de filial coincidem com a janela de um evento programado: Porto Alegre jul/25 (P10: Concorrente em Porto Alegre (-18%)); Rio de Janeiro mar/25 (P10: Chuvas no Rio de Janeiro (-22%)); Porto Alegre jun/25 (P10: Concorrente em Porto Alegre (-18%)).
- **[PADRÃO PROGRAMADO]** `INV2.9` Notebook Pro 14" em ago/25 coincide com P09: Ruptura de estoque do Notebook Pro 14 (fator 0,10× no gerador) — causa conhecida; em dado real equivaleria a uma ruptura de estoque a confirmar.

- 📈 Gráfico interativo: [`graficos/g04_heatmap_yoy.html`](graficos/g04_heatmap_yoy.html)
- 📈 Gráfico interativo: [`graficos/g05_quedas_produto.html`](graficos/g05_quedas_produto.html)

**Tabela — quedas_filial_yoy** (CSV completo em `evidencias/INV2_quedas_filial_yoy.csv`)

| filial | mes | receita_ajustada | receita_ano_anterior | yoy_pct | queda_rs | linhas_base | linhas_atual | pedidos_base | pedidos_atual | efeito_volume_mix | efeito_preco_desconto | produto_lider | share_produto_lider | sequencia_meses | programado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Porto Alegre | 2026-02 | 179,410.16 | 351,281.39 | -0.4893 | 171,871.23 | 104 | 107 | 61 | 57 | -165,613.32 | 2,342.81 | Notebook Pro 14" | 0.6217 | 2 |  |
| São Paulo (Matriz) | 2026-07 | 1,410,315.59 | 1,567,311.37 | -0.1002 | 156,995.78 | 659 | 583 | 366 | 332 | -151,641.73 | 19,042.61 | Notebook Pro 14" | 0.6317 | 1 |  |
| Belo Horizonte | 2025-11 | 617,620.19 | 769,258.09 | -0.1971 | 151,637.90 | 261 | 254 | 145 | 146 | -169,237.17 | 4,410.77 | Notebook Pro 14" | 0.5396 | 1 |  |
| Belo Horizonte | 2026-09 | 530,270.04 | 660,219.40 | -0.1968 | 129,949.36 | 254 | 210 | 137 | 129 | -124,444.26 | 8,144.44 | Notebook Pro 14" | 0.4281 | 1 |  |
| Belo Horizonte | 2025-01 | 445,538.16 | 571,679.59 | -0.2207 | 126,141.43 | 192 | 152 | 109 | 85 | -135,367.62 | 6,011.83 | ERP Lite (mensalidade) | 0.4308 | 1 |  |
| Recife | 2026-07 | 331,267.68 | 440,757.01 | -0.2484 | 109,489.33 | 158 | 170 | 88 | 97 | -106,620.02 | 5,106.53 | Notebook Essencial 15" | 0.5400 | 1 |  |
| Belo Horizonte | 2026-07 | 619,719.80 | 711,875.33 | -0.1295 | 92,155.53 | 237 | 242 | 137 | 141 | -81,701.10 | 6,116.55 | Cadeira Ergonômica Presidente | 0.3637 | 1 |  |
| Curitiba | 2025-09 | 352,415.43 | 444,180.05 | -0.2066 | 91,764.62 | 182 | 196 | 103 | 106 | -60,412.94 | 9,368.42 | Notebook Essencial 15" | 0.5088 | 1 |  |


**Tabela — quedas_produto_resumo** (CSV completo em `evidencias/INV2_quedas_produto_resumo.csv`)

| produto | meses_em_queda | queda_total_rs | maior_sequencia |
|---|---|---|---|
| Notebook Pro 14" | 4 | 503,326.29 | 2 |
| Notebook Essencial 15" | 4 | 249,226.36 | 1 |
| Monitor 27" 4K | 3 | 171,566.55 | 1 |
| Consultoria de Layout | 6 | 137,291.11 | 2 |
| Mesa Regulável Elétrica | 2 | 130,017.54 | 1 |
| Plataforma de Videoconferência (anual) | 3 | 127,022.52 | 2 |
| Licença Office Suite (anual) | 2 | 118,601.99 | 1 |
| ERP Lite (mensalidade) | 1 | 116,652.11 | 1 |

### Limitações dos dados

- A grade usa receita ajustada (entregue); devoluções ficam no mês da venda (sem data de devolução).
- Limiares (-10% YoY, 3 meses) são parâmetros de gestão, não verdades estatísticas.
- Dados sintéticos: não há sazonalidade de mercado real, apenas a programada (P01–P05).

### Recomendações gerenciais (condicionais)

- Se a gestão priorizar poucas frentes, acompanhar primeiro as 3 quedas de produto persistentes e as 0 de filial persistentes; as curtas só merecem investigação se envolverem grandes valores.
- Se uma queda coincidir com ruptura de estoque confirmada, tratar como problema de abastecimento (não de demanda) antes de mexer em preço ou promoção.
- Usar média móvel de 3 meses ao lado da variação anual do mês para reduzir falsos alarmes de pedidos grandes.

### Próximas perguntas para uma empresa real

- Quais quedas persistentes têm causa operacional documentada (estoque, equipe, concorrente)?
- Os produtos em queda perderam clientes ou foram substituídos por outros da mesma categoria?
- Qual a margem dos produtos em queda: perder esse volume custa muito ou pouco lucro?

## Smartphone X Max: por que a margem é crítica e onde estão as linhas negativas?

**Pergunta de negócio.** O problema de margem do Smartphone X Max é pontual (descontos, canal, filial) ou estrutural (custo × preço)? Qual o tamanho do impacto na empresa?

**Método.** Evolução mensal de preço líquido por unidade × custo por unidade; participação do produto nas linhas e no prejuízo bruto negativos; taxa de linhas negativas por faixa de desconto, canal, filial e período; impacto na margem da empresa com e sem o produto; cálculo aritmético do preço necessário para margens-alvo (não é recomendação de preço).

### Evidências

- **[OBSERVAÇÃO]** `INV3.1` 607 das 612 linhas com margem negativa da empresa (99,2%) são do Smartphone X Max; prejuízo bruto dessas linhas: R$ 412.711 de R$ 413.544 (99,8%).
- **[OBSERVAÇÃO]** `INV3.2` Preço bruto médio por unidade: R$ 5.290 em jan/24 → R$ 5.290 em set/26 (0,0% de variação); custo por unidade: R$ 3.389 → R$ 4.647 (+37,1%, ≈ 0,99% ao mês). Margem bruta do produto: 17,6% → -13,7%.
- **[OBSERVAÇÃO]** `INV3.3` Marcos: primeira linha negativa em nov/24; margem mensal do produto fica negativa em set/25; metade das linhas do mês é negativa a partir de set/25; 100% das linhas do mês são negativas a partir de nov/25.
- **[OBSERVAÇÃO]** `INV3.5` Taxa de linhas negativas por faixa de desconto (todo o período): 0% 16%; 0–5% 39%; 5–10% 56%; 10–15% 66%; >15% 100%. A associação com o desconto é em parte mecânica (desconto reduz a receita) e em parte de calendário (as linhas mais recentes, quando o custo já é alto, pesam mais nas faixas).
- **[OBSERVAÇÃO]** `INV3.6` Antes de nov/25 (período em que ainda há linhas positivas), a taxa de linhas negativas por canal varia de 9% a 21% e por filial de 12% a 38%; essas diferenças misturam canal/filial com a data em que cada uma vendeu mais (efeito de calendário), por isso não indicam, sozinhas, que um canal ou filial seja o 'culpado'.
- **[CONCLUSÃO ARITMÉTICA]** `INV3.4` Desde nov/25 todas as 511 linhas do produto têm margem negativa, em qualquer canal, filial ou faixa de desconto — a causa é estrutural (custo por unidade acima do preço líquido), e não de desconto pontual.
- **[CONCLUSÃO ARITMÉTICA]** `INV3.7` Cálculo aritmético em set/26 (custo R$ 4.647/un., desconto efetivo 5,8%, imposto efetivo 18,0%): para margem bruta de 0% o preço bruto teria de ser R$ 6.017 (13,7% sobre o preço de lista de R$ 5.290); para margem bruta de 10% o preço bruto teria de ser R$ 6.686 (26,4% sobre o preço de lista de R$ 5.290); para margem bruta de 20% o preço bruto teria de ser R$ 7.521 (42,2% sobre o preço de lista de R$ 5.290). Não considera elasticidade da demanda nem preço dos concorrentes — não é recomendação de preço.
- **[CONCLUSÃO ARITMÉTICA]** `INV3.8` Em 2026 (jan–set), o Smartphone X Max representa 7,8% da receita ajustada, mas seu lucro bruto é negativo (-R$ 318.872, -1,9% do lucro bruto da empresa). A margem bruta da empresa seria 44,5% sem o produto, contra 40,3% com ele (-4,2 p.p.).
- **[HIPÓTESE]** `INV3.10` Em uma empresa real, o padrão seria compatível com repasse de custo (câmbio/fornecedor) sem reajuste de preço, ou com política comercial mantida por contrato/mercado. Os dados não permitem saber qual das duas — nem se o volume vendido depende do preço baixo.
- **[PADRÃO PROGRAMADO]** `INV3.9` P07: o gerador define para este produto aumento de custo de 1% ao mês com preço fixo (linha 304 de gerar_dados.py). O comportamento observado (custo ≈ +1% a.m., preço constante) é exatamente o programado — logo a 'causa' aqui é conhecida por construção, não descoberta.

- 📈 Gráfico interativo: [`graficos/g06_smartphone.html`](graficos/g06_smartphone.html)

**Tabela — preco_necessario** (CSV completo em `evidencias/INV3_preco_necessario.csv`)

| margem_alvo | preco_bruto_necessario | aumento_sobre_lista |
|---|---|---|
| 0.0000 | 6,017.18 | 0.1375 |
| 0.1000 | 6,685.75 | 0.2638 |
| 0.2000 | 7,521.47 | 0.4218 |


**Tabela — negativas_por_faixa_desconto** (CSV completo em `evidencias/INV3_negativas_por_faixa_desconto.csv`)

| faixa | linhas | pct_neg |
|---|---|---|
| 0% | 25 | 0.1600 |
| 0–5% | 626 | 0.3866 |
| 5–10% | 558 | 0.5591 |
| 10–15% | 59 | 0.6610 |
| >15% | 10 | 1.0000 |

### Limitações dos dados

- Custo unitário e preço são médias do mês; não há custo por lote/fornecedor.
- Sem dados de elasticidade: não é possível estimar o efeito de subir preço sobre o volume.
- A recuperação do custo nas devoluções é hipótese (PN-DEV-02); aqui a margem usa custo ajustado, e a sensibilidade está na Etapa 3 (03a).
- Dados sintéticos: custo e preço seguem regra do gerador.

### Recomendações gerenciais (condicionais)

- Se a margem do Smartphone X Max é de fato negativa na empresa real, reajustar o preço, renegociar custo ou limitar descontos antes de incentivar o volume: cada unidade adicional vendida hoje aumenta o prejuízo bruto.
- Se o produto é âncora estratégica (atrai clientes para outros itens), medir o ganho indireto (cesta de compra) antes de decidir reduzir sua oferta.
- Criar alerta mensal de margem por produto (custo unitário × preço líquido) para detectar o problema meses antes do ponto em que a margem fica negativa.

### Próximas perguntas para uma empresa real

- O Smartphone X Max é vendido em conjunto com produtos de maior margem (cesta)?
- O custo reajustado foi contratual ou pode ser renegociado?
- O preço é fixo por política ou por restrição de mercado? Qual a sensibilidade da demanda a reajustes?

## Margem bruta e resultado operacional estimado: o que mudou entre 2024 e 2026?

**Pergunta de negócio.** A margem bruta caiu por mudança de mix de produtos, por queda de margem dentro dos produtos ou por entrada/saída de itens? E o resultado operacional acompanhou?

**Método.** Comparação sempre de jan a set em cada ano (mesmo nº de meses). Decomposição da variação da margem bruta em efeito MIX (Σ(Δ peso)·margem base) e efeito TAXA (Σ peso atual·Δ margem do produto) — fecha exatamente; custo e preço por unidade; despesas por grupo sobre a receita ajustada. Rótulo: resultado operacional ESTIMADO do dataset (receita ajustada − custo ajustado − despesas); não é lucro líquido contábil.

### Evidências

- **[OBSERVAÇÃO]** `INV4.1` Jan–set: receita ajustada R$ 27,07 mi → R$ 34,28 mi → R$ 41,29 mi; margem bruta 43,3% → 41,8% → 40,3%; despesas/receita 37,1% → 35,6% → 34,2%; margem operacional estimada 6,3% → 6,2% → 6,0%.
- **[OBSERVAÇÃO]** `INV4.2` Resultado operacional estimado (jan–set): R$ 1,69 mi → R$ 2,11 mi → R$ 2,50 mi. É resultado operacional ESTIMADO do dataset (receita ajustada − custo ajustado − despesas); não é lucro líquido contábil.
- **[OBSERVAÇÃO]** `INV4.9` Por unidade vendida (2025→2026, mesmo período do ano): preço líquido cresceu em média +1,6% e custo +3,0% (média por produto ponderada pela receita). Em 25 de 39 produtos o custo por unidade subiu mais que o preço líquido.
- **[OBSERVAÇÃO]** `INV4.13` A queda da margem bruta foi em grande parte compensada por despesas que cresceram menos que a receita (despesas/receita -2,9 p.p.); sem essa alavancagem, a margem operacional teria caído o mesmo que a bruta.
- **[OBSERVAÇÃO]** `INV4.14` Série mensal: margem operacional estimada entre -2,4% (fev/26) e 13,3% (dez/24); 1 mês com resultado estimado negativo (fev/26).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.3` Margem bruta 2024→2025: -1,5 p.p. (de 43,3% para 41,8%) = mix de produtos -0,5 p.p. + margem dentro de cada produto -1,0 p.p. (resíduo 0,0000 p.p.).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.4` Margem bruta 2025→2026: -1,5 p.p. (de 41,8% para 40,3%) = mix de produtos -0,2 p.p. + margem dentro de cada produto -1,3 p.p. (resíduo 0,0000 p.p.).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.5` Margem bruta 2024→2026: -3,1 p.p. (de 43,3% para 40,3%) = mix de produtos -0,6 p.p. + margem dentro de cada produto -2,4 p.p. (resíduo 0,0000 p.p.).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.6` Maiores contribuições negativas de margem DENTRO do produto (2024→2026): Smartphone X Max (-1,85 p.p.); Notebook Pro 14" (-0,50 p.p.); Mesa de Reunião 8 Lugares (-0,01 p.p.).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.7` Smartphone X Max e Notebook Pro 14" juntos respondem por 97% da perda de margem dentro dos produtos e por 76% da queda total da margem bruta 2024→2026 (-3,1 p.p.).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.8` Maiores contribuições negativas de MIX (2024→2026): Licença Office Suite (anual) (-0,38 p.p.); Notebook Pro 14" (-0,15 p.p.); Smartphone X Max (-0,14 p.p.) (perda de peso de produtos de margem acima da média, ou ganho de peso de produtos de margem abaixo da média).
- **[CONCLUSÃO ARITMÉTICA]** `INV4.11` Margem operacional 2024→2026: -0,2 p.p. = margem bruta -3,1 p.p. − variação de despesas/receita (-2,9 p.p.). Por grupo (variação de despesas/receita): Despesas com Pessoal -1,82 p.p.; Despesas Administrativas -1,63 p.p.; Despesas Operacionais -0,04 p.p.; Despesas Comerciais -0,01 p.p.; Despesas Financeiras +0,64 p.p.
- **[HIPÓTESE]** `INV4.15` O mix pode estar mudando por política comercial (mais volume de itens de menor margem) ou por crescimento diferente entre categorias; os dados mostram a mudança de composição, não a intenção. Sobre despesas: parte do crescimento menor que a receita pode ser custo fixo diluído (despesas de pessoal e administrativas) — compatível com os dados, não testado.
- **[PADRÃO PROGRAMADO]** `INV4.10` P06 e P07: o gerador reajusta preço (`ip`) e custo (`ic`) de cada produto todo mês; o padrão é ic=ip=0,15% a.m., com exceções (Notebook Pro 14": custo +0,45% e preço +0,20% a.m.; Smartphone X Max: custo +1,00% e preço 0%). Logo, a compressão de margem destes dois produtos é programada; a dos demais depende do sorteio de custo/preço (±1,5%) em torno de reajustes iguais.
- **[PADRÃO PROGRAMADO]** `INV4.12` Despesas financeiras/receita +0,64 p.p. entre 2024 e 2026: coerente com P16 (juros bancários sobem desde mar/2025 no gerador).

- 📈 Gráfico interativo: [`graficos/g07_margens.html`](graficos/g07_margens.html)
- 📈 Gráfico interativo: [`graficos/g08_margem_waterfall.html`](graficos/g08_margem_waterfall.html)

**Tabela — resumo_ytd** (CSV completo em `evidencias/INV4_resumo_ytd.csv`)

| ano | receita_ajustada | custo_ajustado | lucro_bruto | despesas | resultado_operacional_estimado | margem_bruta | despesas_sobre_receita | margem_operacional |
|---|---|---|---|---|---|---|---|---|
| 2024 | 27,074,260.25 | 15,343,503.61 | 11,730,756.64 | 10,036,313.88 | 1,694,442.76 | 0.4333 | 0.3707 | 0.0626 |
| 2025 | 34,284,601.04 | 19,960,589.16 | 14,324,011.88 | 12,215,184.63 | 2,108,827.25 | 0.4178 | 0.3563 | 0.0615 |
| 2026 | 41,292,337.64 | 24,671,234.32 | 16,621,103.32 | 14,124,260.50 | 2,496,842.82 | 0.4025 | 0.3421 | 0.0605 |


**Tabela — decomposicao_margem_bruta** (CSV completo em `evidencias/INV4_decomposicao_margem_bruta.csv`)

| de | para | margem_base | margem_atual | delta | mix | taxa | entrada_saida | residuo |
|---|---|---|---|---|---|---|---|---|
| 2024 | 2025 | 0.4333 | 0.4178 | -0.0155 | -0.0050 | -0.0105 | 0.0000 | 0.0000 |
| 2025 | 2026 | 0.4178 | 0.4025 | -0.0153 | -0.0020 | -0.0132 | 0.0000 | -0.0000 |
| 2024 | 2026 | 0.4333 | 0.4025 | -0.0308 | -0.0065 | -0.0243 | 0.0000 | 0.0000 |

### Limitações dos dados

- resultado operacional ESTIMADO do dataset (receita ajustada − custo ajustado − despesas); não é lucro líquido contábil.
- Despesas não são alocadas a produtos/canais: margem por produto é margem BRUTA.
- Receita ajustada provisória (devoluções excluídas; custo devolvido considerado recuperado — PN-DEV-02, hipótese).
- Três anos de dados sintéticos; tendências não são previsões.

### Recomendações gerenciais (condicionais)

- Se a margem bruta seguir caindo com despesas crescendo menos que a receita, a alavancagem operacional não será suficiente a longo prazo: priorizar revisão de preço/custo dos produtos com maior contribuição negativa de taxa.
- Se o mix de produtos de menor margem estiver crescendo por incentivo comercial, rever metas e comissões para que reflitam margem, e não só receita.
- Acompanhar mensalmente a decomposição mix × taxa da margem bruta, em vez de apenas a margem total.

### Próximas perguntas para uma empresa real

- As despesas de pessoal cresceram abaixo da receita por ganho de produtividade ou por falta de contratação?
- Quais produtos tiveram aumento de custo repassado ao preço e quais não?
- Qual o resultado por filial depois de alocar despesas corporativas da Matriz?

## Orçado × realizado: anual, acumulado e a leitura correta

**Pergunta de negócio.** Quanto a empresa realmente gastou em relação ao orçado, qual o erro de comparar com o orçamento anual, e onde estão os desvios?

**Método.** Três conceitos separados: orçamento ANUAL (12 meses), orçamento ACUMULADO (jan→set) e realizado ACUMULADO; comparação correta = realizado ÷ orçado acumulado. Faixa 'dentro do orçado' = ±5%. Projeção de fim de ano = orçamento anual × taxa de execução acumulada (cálculo aritmético, não previsão).

### Evidências

- **[OBSERVAÇÃO]** `INV5.1` 2026 até set/26: orçamento anual R$ 19,67 mi; orçamento acumulado R$ 14,06 mi (71,5% do anual em 9 de 12 meses); realizado acumulado R$ 14,12 mi.
- **[OBSERVAÇÃO]** `INV5.3` Por departamento, apenas 1 está acima da faixa de ±5%: Tecnologia da Informação 105,7% (R$ 88,1 mil). Por categoria, 5 de 18 estão acima.
- **[OBSERVAÇÃO]** `INV5.4` Maiores desvios em reais (acima do orçado): Software & Licenças R$ 66,9 mil (117,6%); Energia, Água & Internet R$ 43,3 mil (107,8%); Juros & Tarifas Bancárias R$ 35,6 mil (130,4%). Esses três concentram 76% da soma dos desvios positivos por categoria. O desvio líquido total é R$ 63,7 mil (+0,5%).
- **[OBSERVAÇÃO]** `INV5.5` A maior execução PERCENTUAL é de 'Juros & Tarifas Bancárias' (130,4%), mas sobre valor orçado pequeno (R$ 117,0 mil); percentual alto e valor pequeno exigem menos atenção que desvio moderado em categoria grande.
- **[CONCLUSÃO ARITMÉTICA]** `INV5.2` Execução correta (realizado ÷ orçado acumulado): 100,5%. Leitura ingênua (÷ orçamento anual): 71,8% — daria a falsa impressão de que a empresa gastou 28% a menos que o planejado. Prorrateio linear (9/12): 95,7% — também erra, porque o orçamento não é distribuído igualmente pelos meses.
- **[CONCLUSÃO ARITMÉTICA]** `INV5.6` Se a taxa de execução acumulada (100,5%) se mantivesse, o gasto de 2026 fecharia em ≈ R$ 19,76 mi contra orçamento anual de R$ 19,67 mi (diferença R$ 89,1 mil). A projeção parte do orçamento anual completo. É extrapolação aritmética, sem considerar sazonalidade de despesas nem decisões futuras.
- **[HIPÓTESE]** `INV5.8` Desvios acima do orçado em categorias com crescimento contínuo (software, juros) podem refletir orçamento subdimensionado e não má gestão de gasto; os dados não permitem separar uma coisa da outra.
- **[PADRÃO PROGRAMADO]** `INV5.7` P14: Marketing executou 116,5% do orçado no 4T/2025 (jan–set/2025: 100,0%). P15: Software & Licenças executou 117,6% em 2026 (2025: 100,0%). P16: Juros & Tarifas Bancárias executaram 111,5% de mar a dez/2025 (2024: 99,5%). Os três desvios foram criados no gerador; aqui só confirmamos que os números os reproduzem.

- 📈 Gráfico interativo: [`graficos/g09_orcamento_conceitos.html`](graficos/g09_orcamento_conceitos.html)
- 📈 Gráfico interativo: [`graficos/g10_orcamento_categoria.html`](graficos/g10_orcamento_categoria.html)

**Tabela — tres_conceitos_por_ano** (CSV completo em `evidencias/INV5_tres_conceitos_por_ano.csv`)

| ano | mes_referencia | orcamento_anual | orcamento_acumulado | realizado_acumulado | execucao_correta | leitura_ingenua | proporcao_orcamento_ja_acumulada | meses_no_acumulado | leitura_proporcional_linear |
|---|---|---|---|---|---|---|---|---|---|
| 2024 | 2024-12 | 14,060,254.72 | 14,060,254.72 | 14,114,037.22 | 1.0038 | 1.0038 | 1.0000 | 12 | 1.0038 |
| 2025 | 2025-12 | 17,387,829.35 | 17,387,829.35 | 17,474,510.34 | 1.0050 | 1.0050 | 1.0000 | 12 | 1.0050 |
| 2026 | 2026-09 | 19,669,544.93 | 14,060,560.39 | 14,124,260.50 | 1.0045 | 0.7181 | 0.7148 | 9 | 0.9574 |


**Tabela — por_categoria** (CSV completo em `evidencias/INV5_por_categoria.csv`)

| categoria_despesa | orcado | realizado | desvio_rs | execucao | situacao |
|---|---|---|---|---|---|
| Software & Licenças | 380,304.00 | 447,176.38 | 66,872.38 | 1.1758 | acima_do_orcado |
| Energia, Água & Internet | 555,660.00 | 598,969.72 | 43,309.72 | 1.0779 | acima_do_orcado |
| Juros & Tarifas Bancárias | 117,000.00 | 152,610.82 | 35,610.82 | 1.3044 | acima_do_orcado |
| Consultoria & Terceiros | 333,000.00 | 355,190.25 | 22,190.25 | 1.0666 | acima_do_orcado |
| Marketing Digital | 1,381,214.22 | 1,390,812.49 | 9,598.27 | 1.0069 | dentro_da_faixa |
| Eventos & Patrocínios | 129,380.69 | 136,935.13 | 7,554.44 | 1.0584 | acima_do_orcado |
| Frete & Logística | 1,045,456.14 | 1,048,637.19 | 3,181.05 | 1.0030 | dentro_da_faixa |
| Tarifas de Pagamento & Marketplace | 1,093,323.05 | 1,095,276.61 | 1,953.56 | 1.0018 | dentro_da_faixa |

### Limitações dos dados

- Orçado × realizado compara apenas meses realizados; meses futuros do orçamento não entram (PN-ORC-01).
- Não há justificativas dos desvios nem versão revisada do orçamento.
- A projeção de fim de ano é extrapolação simples.

### Recomendações gerenciais (condicionais)

- Se a gestão acompanha o orçamento pelo painel, usar sempre realizado ÷ orçado ACUMULADO (e mostrar o anual apenas como referência de saldo).
- Se os desvios concentrados em poucas categorias forem recorrentes, revisar o orçamento dessas categorias (reforço ou travas), em vez de ações gerais de corte.
- Definir alçada por valor e por percentual (ex.: desvio > R$ X ou > Y% com valor relevante), para não gastar atenção com percentuais altos em valores pequenos.

### Próximas perguntas para uma empresa real

- Os desvios de software e juros foram aprovados fora do orçamento?
- O orçamento é revisado durante o ano (forecast) ou fica fixo?
- Há sazonalidade nas despesas que justifique a distribuição mensal do orçamento?

## Volume, preço, desconto, mix e rentabilidade: o que se relaciona com quê?

**Pergunta de negócio.** Os meses de maior desconto ou maior peso de marketplace têm margem menor? Descontos maiores vêm com quantidades maiores? Quanto do crescimento é volume, preço ou mix?

**Método.** Correlação de Spearman entre indicadores mensais (em nível e em variação mês a mês, para reduzir o efeito de tendência comum); regressão por linha com efeito fixo de produto (quantidade × desconto); decomposição mix × taxa da margem por canal; soma das decomposições preço/volume/mix dos meses comparáveis. Correlação NÃO é causalidade.

### Evidências

- **[OBSERVAÇÃO]** `INV6.1` Correlação de Spearman com a margem bruta mensal (33 meses; entre parênteses, em variação mês a mês): desconto efetivo -0,42 (0,06); peso do marketplace -0,62 (-0,20); preço praticado vs lista -0,62 (-0,42); peso de Eletrônicos -0,60 (-0,76).
- **[OBSERVAÇÃO]** `INV6.2` Em nível, quase tudo se correlaciona com tudo porque os indicadores têm tendência comum (tempo); por isso a leitura principal é a de variação mês a mês, mais exigente. Com 32–33 pontos, correlações pequenas (|ρ| < 0,35) não distinguem de acaso.
- **[OBSERVAÇÃO]** `INV6.3` Por linha de venda (59.365 linhas), dentro do mesmo produto: +1 p.p. de desconto está associado a 0,127 unidades a mais por linha (R² intra-produto 0,032; Spearman geral 0,18). Controlando também canal, segmento do cliente, novembro e ano, a associação passa a -0,001 unidades por p.p.
- **[OBSERVAÇÃO]** `INV6.4` A associação positiva entre desconto e quantidade cai 99% quando se comparam linhas do mesmo canal e segmento do cliente. É compatível com efeito de COMPOSIÇÃO (certos canais/segmentos têm desconto e quantidade maiores); a associação bruta não deve ser lida como 'o desconto vende mais'.
- **[OBSERVAÇÃO]** `INV6.7` Marketplace: 6,4% da receita ajustada (jan–set/2024) → 13,4% (2026); margem bruta 35,6% → 35,1%; desconto efetivo 7,8% → 7,8%.
- **[CONCLUSÃO ARITMÉTICA]** `INV6.8` Variação da margem bruta 2024→2026 por canal: -3,1 p.p. = mix de canais -0,6 p.p. + margem dentro de cada canal -2,4 p.p.. Como a margem de cada canal é uma média de produtos, o 'efeito taxa' por canal inclui o problema do Smartphone X Max (INV3) e o mix de produtos de cada canal.
- **[CONCLUSÃO ARITMÉTICA]** `INV6.10` Crescimento anual da receita registrada em 2025 (12 meses comparáveis, soma de R$ 10,81 mi): volume R$ 10,27 mi (95%), mix -R$ 295,9 mil (-3%), preço R$ 892,4 mil (8%), desconto -R$ 57,2 mil (-1%), impostos R$ 0,0 mil.
- **[CONCLUSÃO ARITMÉTICA]** `INV6.11` Crescimento anual da receita registrada em 2026 (9 meses comparáveis, soma de R$ 7,11 mi): volume R$ 6,56 mi (92%), mix -R$ 86,1 mil (-1%), preço R$ 716,9 mil (10%), desconto -R$ 84,4 mil (-1%), impostos R$ 0,0 mil.
- **[HIPÓTESE]** `INV6.6` Numa empresa real, descontos podem aumentar pedidos ou recorrência sem aumentar a quantidade por linha; esse teste não enxerga isso. Também pode haver desconto por volume (causa inversa) — aqui não há, por construção do gerador.
- **[HIPÓTESE]** `INV6.13` Associações entre desconto, marketplace e margem podem ser confundidas por tempo (tudo muda junto) e por produto (o Smartphone X Max pesa na margem e tem desconto como os demais). Sem experimento ou controles adicionais, os dados mostram associação, não efeito causal.
- **[PADRÃO PROGRAMADO]** `INV6.5` No gerador, o desconto vem do canal (3–7%), do segmento do cliente (0–3%), de novembro (+5 p.p.) e da Black Friday (+8 p.p. — P04), mais ruído; ele NÃO depende da quantidade. Qualquer associação restante é efeito de confusão, não de causa.
- **[PADRÃO PROGRAMADO]** `INV6.9` P12: o gerador migra o mix de canais para marketplace (comissão de 11% lançada em despesas, não em custo). A comissão NÃO aparece na margem bruta por canal; a rentabilidade real do marketplace é, portanto, menor que a mostrada aqui.
- **[PADRÃO PROGRAMADO]** `INV6.12` P05 (crescimento tendencial de 1,1% ao mês de pedidos) e P06 (reajuste mensal de preço) explicam, por construção, por que volume é o principal componente e preço o segundo.

- 📈 Gráfico interativo: [`graficos/g11_pvm_yoy.html`](graficos/g11_pvm_yoy.html)
- 📈 Gráfico interativo: [`graficos/g12_correlacoes.html`](graficos/g12_correlacoes.html)
- 📈 Gráfico interativo: [`graficos/g13_canais.html`](graficos/g13_canais.html)

**Tabela — desconto_vs_quantidade** (CSV completo em `evidencias/INV6_desconto_vs_quantidade.csv`)

| modelo | unidades_por_linha_a_cada_1pp_de_desconto |
|---|---|
| dentro do produto | 0.1269 |
| dentro do produto + canal + segmento do cliente + novembro + ano | -0.0013 |


**Tabela — canais_ytd** (CSV completo em `evidencias/INV6_canais_ytd.csv`)

| canal | share_receita | margem_bruta | desconto_efetivo | ano |
|---|---|---|---|---|
| Loja Física | 0.3126 | 0.4311 | 0.0424 | 2024 |
| E-commerce | 0.2441 | 0.4052 | 0.0621 | 2024 |
| Televendas B2B | 0.3789 | 0.4664 | 0.0600 | 2024 |
| Marketplace | 0.0644 | 0.3558 | 0.0784 | 2024 |
| Loja Física | 0.2549 | 0.4186 | 0.0424 | 2026 |
| E-commerce | 0.2557 | 0.3651 | 0.0614 | 2026 |
| Televendas B2B | 0.3554 | 0.4376 | 0.0600 | 2026 |
| Marketplace | 0.1340 | 0.3505 | 0.0782 | 2026 |

### Limitações dos dados

- Correlações com ~33 pontos mensais e variáveis em tendência são frágeis.
- Desconto efetivo é média ponderada; mistura canal, cliente e produto.
- A comissão do marketplace está em despesas e não entra na margem bruta por canal.
- Dados sintéticos: relações entre variáveis foram definidas pelo gerador, não por comportamento de clientes reais.

### Recomendações gerenciais (condicionais)

- Se a empresa real encontrar o mesmo padrão (desconto sem aumento de quantidade), testar redução controlada de descontos em um grupo de produtos/filiais antes de generalizar.
- Se o marketplace continuar a ganhar peso, incluir a comissão no cálculo de margem por canal antes de comparar canais.
- Reportar crescimento sempre decomposto em volume, mix e preço: 'crescer' por volume e por preço têm implicações bem diferentes para margem e caixa.

### Próximas perguntas para uma empresa real

- Descontos aumentam o número de pedidos ou a recorrência de clientes (não apenas a quantidade por linha)?
- Qual a margem líquida por canal depois de comissões, frete e devoluções?
- Qual a elasticidade preço-demanda por categoria (teste A/B ou histórico com variações isoladas)?

## Reprodutibilidade

`python scripts/run_etl.py && python scripts/run_analises.py` regenera tudo. Hashes SHA-256 (CSV de evidências e gráficos) em `manifesto.json`.

| Arquivo | SHA-256 (prefixo) |
|---|---|
| `evidencias/INV1_achados.json` | `57fa3a3f6dc38615…` |
| `evidencias/INV1_clientes_maiores_na_base.csv` | `99678e7c2a98c3a1…` |
| `evidencias/INV1_comparacao_fev25_fev26.csv` | `f21ce18be5ac28cd…` |
| `evidencias/INV1_decomposicao_filial.csv` | `224ce445264c2018…` |
| `evidencias/INV1_decomposicao_por_produto.csv` | `b9c454a40c5a8b03…` |
| `evidencias/INV1_produto_top_unidades_mensais.csv` | `34d1a3921d53e874…` |

(lista completa no manifesto)
