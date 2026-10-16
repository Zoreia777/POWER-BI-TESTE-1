# Metodologia — decomposição da variação de receita (Análise 08)

Implementação: `sql/analise/08_fatores_variacao.sql` (TEMP VIEW `analise_pvm_produto`). Testes: `tests/test_consultas.py` (oráculo em Python puro + cenários calculados à mão + mutação).

## 1. Ideia

Para cada produto *i*, a receita registrada de um período é

> R = Bruta − Desconto − Impostos = **Q · P · (1 − d) · (1 − t)**

- Q unidades; P preço bruto médio = Bruta/Q; d desconto efetivo = Desconto/Bruta; t imposto efetivo = Impostos/(Bruta − Desconto).

Comparando o período atual (1) com a base (0), a variação ΔR é repartida em **volume, mix, preço, desconto e imposto**. Como R é um produto de fatores, a repartição é feita de forma *encadeada*: cada efeito troca um fator por vez e mantém os anteriores (fatores ainda não trocados na base, os já trocados no atual). A soma fecha **por identidade algébrica** (série telescópica), sem “resíduo” ajustado.

## 2. Fórmulas (produto continuante: Q₀>0 e Q₁>0)

Seja Q₀c e Q₁c o total de unidades dos produtos continuantes na base e no atual.

| Efeito | Fórmula | Leitura |
|---|---|---|
| Volume | (Q₁c − Q₀c) · R₀ᵢ / Q₀c | o conjunto de continuantes cresce/encolhe na proporção da base |
| Mix | (Q₁ᵢ − Q₁c · Q₀ᵢ/Q₀c) · R₀ᵢ/Q₀ᵢ | mudança de composição entre produtos, a receita média base de cada um |
| Preço | Q₁ᵢ · (P₁ − P₀) · (1 − d₀)(1 − t₀) | variação do preço bruto médio |
| Desconto | − Q₁ᵢ · P₁ · (d₁ − d₀) · (1 − t₀) | variação do desconto efetivo |
| Imposto | − Q₁ᵢ · P₁ · (1 − d₁) · (t₁ − t₀) | variação da carga efetiva |

Volume + mix de um produto = (Q₁ − Q₀) · R₀/Q₀ (telescopa com os demais). Preço + desconto + imposto = Q₁ · [P₁(1−d₁)(1−t₁) − P₀(1−d₀)(1−t₀)]. Somando tudo: R₁ − R₀.

## 3. Casos especiais (decisões)

| Situação | Tratamento |
|---|---|
| **Produto novo** (Q₀=0, Q₁>0) | efeito = +R₁ em coluna própria (`efeito_produto_novo`); não entra em volume/mix/preço |
| **Produto descontinuado** (Q₀>0, Q₁=0) | efeito = −R₀ (`efeito_produto_descontinuado`) |
| **Sem vendas nos dois períodos** | efeito 0; contado em `08d` como `sem_vendas` |
| **Base inexistente** (início da série / 12 meses atrás fora do calendário) | `status_base = sem_base`; efeitos e % ficam NULL |
| **Base realizada sem nenhuma venda** | `status_base = base_zerada`; percentual NULL; tudo cai em “novo” |
| **Denominador zero** (Q₀c, b₀, b₀−d₀) | só ocorre fora do conjunto de continuantes (Q₀>0 garante b₀>0); contribuição % com variação total ≈ 0 vira NULL |
| **Mudança de composição** | é exatamente o efeito *mix*; novos/descontinuados são separados para não contaminar o mix |
| **Arredondamento** | única parcela fora dos efeitos: (liq_reg − (bruta − desc − imp)); aparece em `efeito_arredondamento_nao_e_negocio` (0,00 neste dataset). Não é efeito de negócio |
| **Devoluções** | a decomposição é sobre a receita **registrada**; `efeito_devolucoes = −Δ(devoluções)` leva à **receita ajustada provisória** (PN-DEV-01). `residuo_ajustada` = 0 |

## 4. Exemplos feitos à mão (viram testes)

1. **Só preço**: A 10 un. a R$100 → R$110. Preço = 10 × 10 = **100**; demais 0.
2. **Só volume**: A 10@100 e B 10@50 (R$1.500) → dobro: volume = **+1.500**.
3. **Só mix**: A 10→15 (R$100) e B 10→5 (R$50): mix = 5×100 − 5×50 = **+250**, volume 0.
4. **Preço + mix**: como 3, com A a R$110 → preço **150** (só A), mix **250**, total **400**.
5. **Desconto** 10%→20% (imposto 10%): −1000 × 0,10 × 0,90 = **−90**. **Imposto** 10%→12%: −1000 × 1 × 0,02 = **−20**.
6. **Novo / descontinuado**: +300 / −500 em colunas próprias; classes `novo`, `descontinuado`, `sem_vendas` conferidas.

## 5. Interpretação e limites

- Os efeitos são **conclusão aritmética**; atribuir uma *causa* (campanha, concorrência, ruptura) é **hipótese**.
- O preço é o **preço médio do produto no período**: mudança de preço entre canais/filiais/segmentos aparece dentro do efeito preço ou desconto. O desconto efetivo embute o mix de canal e de cliente.
- Ordem do encadeamento (volume → mix → preço → desconto → imposto) influencia a divisão entre efeitos *cruzados* (ex.: variação de preço × variação de volume); a ordem é fixa e documentada, e o total nunca muda.
- Nos dados reais não há produtos novos nem descontinuados nem lacunas produto-mês: esses ramos só são exercitados pelos cenários injetados.
