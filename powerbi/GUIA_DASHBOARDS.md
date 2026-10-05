# Guia dos dashboards · Empresa X

Sete páginas, uma narrativa: **"Como a empresa está? → De onde vem o dinheiro? → Para onde
ele vai? → O que sobra? → Quem são nossos clientes? → Quem faz tudo isso acontecer? → E se
mudarmos algo?"**

Formato de página: **16:9 (1280 × 720)** · Tema: `tema_empresa_x_escuro.json`
(*Exibição → Temas → Procurar temas*) ou `tema_empresa_x_claro.json`.
Todas as medidas estão em [`medidas_dax.md`](medidas_dax.md).

## Padrões que valem para todas as páginas

| Elemento | Como fazer |
|---|---|
| **Faixa de filtros** (topo, 60 px) | Segmentações horizontais: `ano`, `trimestre`, `filial`, `status_periodo`. Sincronize (*Exibição → Sincronizar segmentações*) para valer em todas as páginas. |
| **Navegação** | Botões *Navegador de páginas* (Inserir → Botões → Navegador → Navegador de páginas) em uma coluna à esquerda. |
| **Cartões KPI** | Cartão novo + valor + variação (`[Var. YoY %]`) com seta ▲▼ e cor condicional (verde ≥ 0, vermelho < 0). |
| **Tooltips** | Página oculta "Tooltip · Mês" (tamanho *Dica de ferramenta*) com mini-gráfico de linha diário. Ative nos visuais de coluna/linha. |
| **Drill-through** | Página oculta "Detalhe da Filial" (campo `dim_filial[filial]`). Clique direito em qualquer filial → *Drill-through*. |
| **Marcadores** | Um marcador por visão alternativa (ex.: "Ver por Receita/Lucro/Margem"). |
| **Cor com significado** | Teal = receita/positivo · Âmbar = atenção · Vermelho = estouro/queda · Azul = comparativo (ano anterior/orçado). |
| **Dados "projetados"** | Segmentação `status_periodo` = *Realizado* por padrão; troque para *Projetado* para ver orçamento e metas futuros. |

---

## 01 · Visão Geral — "o painel do dono"

**Pergunta:** a empresa está bem hoje?

| Zona | Visual | Campos |
|---|---|---|
| Topo (5 cartões) | Cartões KPI | `Receita Líquida`, `Lucro Bruto`, `Despesas Totais`, `Resultado Operacional`, `Margem Operacional %` — cada um com `Var. YoY %` |
| Esquerda-centro | **Linha + colunas** | Eixo `mes_ano`; colunas = `Receita Líquida`; linha = `Receita Líquida LY (comparável)`; linha tracejada = `Meta Receita` |
| Direita-centro | **Mapa de bolhas** | Local = `cidade`/`uf` (ou lat/long); tamanho = `Receita Líquida`; cor = `Atingimento da Meta %` (verde/âmbar/vermelho) |
| Inferior esquerdo | **Medidor (gauge)** | Valor = `Receita Líquida`; destino = `Meta Receita (realizado)` |
| Inferior centro | **Texto inteligente** | Cartão com `[Texto Destaque]` |
| Inferior direito | **Barras** por filial | `Receita Líquida`, ordenado desc., rótulo + `Margem Bruta %` na dica |

**Interação:** clicar em uma filial no mapa filtra a página inteira. Botão de marcador
alterna o gráfico principal entre *Receita / Lucro / Resultado* (usa `sel_metrica`).

---

## 02 · Vendas — "de onde vem o dinheiro"

**Perguntas:** quais produtos, canais e vendedores puxam o resultado?

- **Treemap** categoria → subcategoria → produto (`Receita Líquida`, cor = `Margem Bruta %`).
- **Barras empilhadas 100%** por `mes_ano` e `canal` — mostra o **Marketplace crescendo**.
- **Dispersão (bolhas)**: eixo X = `Receita Líquida`, Y = `Margem Bruta %`, tamanho = `Itens Vendidos`,
  detalhe = `produto`. Quadrante inferior direito = "vende muito, ganha pouco".
- **Ranking de vendedores**: barras horizontais, top 10, rótulo com `Ranking Vendedor`.
- **Matriz** produto × mês com formatação condicional (escala de cor) em `Receita Líquida`.
- **Árvore de decomposição** (*Decomposition tree*): `Receita Líquida` ← `canal`, `categoria`,
  `filial`, `segmento` — deixe o usuário explorar a causa de uma queda.
- **Cartões:** `Pedidos`, `Ticket Médio`, `Desconto Médio %`, `Taxa de Devolução %`.

---

## 03 · Gastos & Orçamento — "para onde vai o dinheiro"

**Perguntas:** estamos dentro do orçado? Quem estourou?

- **Cartões:** `Despesas Totais`, `Despesa Orçada (realizado)`, `Variação vs Orçado (R$)`,
  `Execução do Orçamento %` (cor = `[Cor do Orçamento]`).
- **Colunas agrupadas** realizado × orçado por `mes_ano`.
- **Matriz de calor** departamento × mês com `Variação vs Orçado %`
  (formatação condicional divergente: verde → branco → vermelho).
- **Barras** por `categoria_despesa` com `Execução do Orçamento %` e ícone `[Ícone do Orçamento]`.
- **Rosca** por `grupo_dre` (Pessoal, Comerciais, Operacionais, Administrativas, Financeiras).
- **Top 10 fornecedores**: barras horizontais (`fornecedor` × `Despesas Totais`) com filtro *N principais*.
- **Segmentação** `tipo_custo` (Fixa/Variável) para separar o que dá para cortar.

**Interação:** botão "Mostrar só estouros" (marcador) aplica filtro `Execução do Orçamento % > 1`.

---

## 04 · Lucratividade (DRE) — "o que sobra"

**Perguntas:** a margem está sendo comida por desconto, custo ou despesa?

- **Cascata (waterfall)** do DRE: `tbl_dre[Linha]` × `[Valor DRE]` (veja `medidas_dax.md`, bloco 3).
- **Linhas** `Margem Bruta %` e `Margem Operacional %` por mês (eixo secundário para a segunda).
- **Matriz DRE** (linhas = grupos, colunas = meses/anos) com subtotais.
- **Barras** de margem bruta por `categoria` (compare Eletrônicos × Software).
- **Painel de alertas**: tabela com produtos de **margem < 5%** (filtro visual em `Margem Bruta %`).

---

## 05 · Clientes & Pareto — "quem paga as contas"

- **Pareto (curva ABC):** colunas = `Receita Líquida` por `nome_cliente` (top 50); linha =
  `% Acumulado Clientes` no eixo secundário; linha de referência em 80%.
- **Cartões:** `Clientes Ativos`, `Novos Clientes`, `Receita por Cliente`.
- **Rosca** de receita por `segmento`.
- **Tabela** com `nome_cliente`, `segmento`, `cidade`, `Receita Líquida`, `Classe ABC`
  (cor condicional: A = teal, B = âmbar, C = cinza).
- **Colunas** de novos clientes por mês (`Novos Clientes` × `mes_ano`).
- **Mapa** (preenchido por UF) com `Receita Líquida` por `uf`.

---

## 06 · Pessoas — "quem faz acontecer"

- **Cartões:** `Headcount (fim do período)`, `Turnover %`, `Custo de Pessoal por Funcionário`,
  `Receita por Funcionário`, `Vagas em Aberto`.
- **Colunas empilhadas** de `Headcount` por departamento ao longo dos meses.
- **Barras** de `Turnover %` por departamento (TI e Operações & Logística costumam liderar).
- **Linhas** `Admissões` × `Desligamentos`.
- **Dispersão:** `Custo de Pessoal por Funcionário` × `Receita por Funcionário` por filial.

---

## 07 · Simulador de Cenários — "e se…?"

Segmentações de barra deslizante: `par_preco`, `par_volume`, `par_custo`, `par_despesa`.

- **Cartões:** `Receita Líquida (Cenário)`, `Resultado (Cenário)`, `Δ Resultado vs Base`,
  `Margem Operacional (Cenário)`.
- **Colunas lado a lado:** `Resultado Operacional` (base) × `Resultado (Cenário)` por trimestre.
- **Cascata:** impacto de cada alavanca (preço, volume, custo, despesas) no resultado.
- **Linha com previsão** (*Análise → Previsão*) sobre `Receita Líquida` por mês (12 meses, 95%).
- **Cartão:** `Projeção de Receita do Ano` × `Meta Receita` do ano.

Dica: crie **marcadores** com cenários prontos — "Pessimista" (volume −10%, custo +8%),
"Realista" (tudo zero), "Otimista" (preço +3%, despesas −5%).

---

## Histórias escondidas nos dados 🔎

Os dados fictícios têm "easter eggs" para você praticar análise. Descubra-os pelos dashboards:

1. **Black Friday:** novembro explode em receita, mas a margem cai (desconto + frete caro).
2. **Marketplace** cresce de ~7% (2024) para ~14% (3T26) do faturamento — e leva 11% de comissão.
3. **Smartphone X Max:** o custo sobe todo mês e o preço não — margem quase zero.
4. **Cadeira Gamer:** taxa de devolução ~9%, muito acima do resto.
5. **Notebook Pro 14":** ruptura de estoque em **ago/2025** (vendas despencam).
6. **Porto Alegre:** queda em jun–ago/2025 (concorrente agressivo).
7. **Rio de Janeiro:** mês de março/2025 fraco (chuvas).
8. **Brasília:** bate a meta com folga em 2026 (pico entre mar e jun, contrato com órgão público).
9. **Recife (jun/2024) e Salvador (fev/2025):** filiais novas, vendas crescendo em rampa.
10. **Marketing** estourou o orçamento no **4º trimestre de 2025**.
11. **Software & Licenças (TI)** foge do orçado mês a mês em **2026** (custo de nuvem).
12. **Juros bancários** sobem desde mar/2025.
13. **TI e Operações & Logística** lideram o turnover (~2,4% ao mês).
14. **Um vendedor de São Paulo** vende ~3× mais que a média.
15. Cerca de 25% dos clientes geram 80% da receita (**Pareto**) — e os corporativos pesam muito mais que o número deles.
