# Comportamentos programados × resultados medidos

Os dados são **fictícios**. Vários padrões foram colocados de propósito em `scripts/gerar_dados.py`.
Nenhum deles é evidência sobre o mercado real. A tabela `mart.ref_comportamentos_sinteticos` lista os 17 comportamentos
programados (parâmetro, linha do gerador, tabela afetada). A regra de leitura:

- **Programado** = causa conhecida, definida no gerador (coluna "Parâmetro").
- **Medido** = efeito observado por consulta SQL sobre o mart (coluna "Resultado da consulta"). Medir um padrão programado
  confirma que o pipeline o preserva; não o transforma em descoberta.

| ID | Programado no gerador | Resultado da consulta (mart) |
|---|---|---|
| P01 | Sazonalidade mensal: nov 1,38×, dez 1,30×, jan 0,88×, fev 0,84× (`SAZONALIDADE`, l. 50) | Receita de 2025 ÷ média mensal: nov 1,40, dez 1,39, jan 0,74, fev 0,72 (inclui tendência e Black Friday) |
| P04 | Black Friday: pedidos 2,2×, desconto +8 p.p. (l. 143) | Meses de pico de margem negativa: nov/25 (65 linhas) e dez/25 (64) |
| P06 | Reajuste mensal de preço por produto (`ip`, l. 571) | Variação de preço vs lista: 0,0 % (jan/24) → 1,75 % (jan/25) → 3,52 % (jan/26) → 4,77 % (set/26), razão de somas |
| P07 | Smartphone X Max: custo +1 %/mês, preço fixo (l. 304) | 607 das 612 linhas de margem negativa (99,2 %) são desse produto; prejuízo bruto R$ 412,7 mil |
| P08 | Devolução por produto (`dev`, l. 580), Cadeira Gamer 9 % | Cadeira Gamer: 9,8 % da receita devolvida; média geral 2,19 % |
| P14, P15 | Marketing +28 % no 4T25; TI/nuvem cresce em 2026 (l. 782, 842) | TI com 105,7 % do orçamento acumulado em 2026 (maior desvio entre departamentos) |
| Quedas jan/fev | Efeito de P01 + P05 | Quedas > 15 % mês a mês: fev/24, jan/25, jan/26, fev/26 |

Itens P02, P03, P05, P09–P13, P16 e P17 constam do registro com sua origem programada; a verificação por consulta de cada um
é escopo das Etapas 3 e 4 (análise), não do ETL.
