# Checklist de validação manual das 5 páginas do aplicativo

**Como usar:** abra o app (`docs\GUIA_WINDOWS_PASSO_A_PASSO.md`, seção 6), deixe os filtros **padrão** (Período = *Ano corrente (até o último mês realizado)*, Filiais/Produtos/Canais vazios = todos) e marque cada item. Os valores esperados saem do app executado no ambiente de desenvolvimento (dados fictícios, **jan–set/2026**). Diferença de arredondamento na última casa não é erro; **valor muito diferente é**.

Dados da validação: Data ____/____/______ · Windows ______ · Navegador ______ · Resolução ______ · Python ______

## 0. Geral (vale para todas as páginas)

- [ ] Abre sem tela de erro vermelha (`Traceback`/"exception") nas 5 páginas
- [ ] Menu superior com 5 itens: Visão Geral · Filiais · Produtos e Margem · Orçamento · Investigações
- [ ] Barra lateral "Filtros" com Período, Filiais, Produtos e Canais
- [ ] Linha "Recorte:" no topo mostra `período jan/26 a set/26 · filiais: todas · produtos: todos · canais: todos`
- [ ] Rodapé informa "somente leitura", "Dados fictícios" e a data da última carga do ETL
- [ ] Números em formato brasileiro (ponto nos milhares, vírgula decimal; `R$ 41,29 mi`)
- [ ] Textos com "R$ … R$" aparecem normais (nada vira fórmula/itálico estranho)
- [ ] Gráficos mudam de cor/dica ao passar o mouse (tooltip)

## 1. Visão Geral

- [ ] Receita ajustada (provisória): **R$ 41,29 mi**, **↑ +20,4%** vs. jan/25 a set/25
- [ ] Margem bruta ajustada: **40,3%**, **↓ −1,5 p.p.**
- [ ] Devoluções: **R$ 869,2 mil** (2,1% da receita registrada)
- [ ] Pedidos: **10.188**; "Ticket por pedido: R$ 4.053"
- [ ] Despesas (dataset): **R$ 14,12 mi** (34,2% da receita ajustada)
- [ ] Resultado operacional estimado: **R$ 2,50 mi**; "Margem: 6,0% · não é lucro líquido contábil"
- [ ] Unidades entregues: **48.390**; "Preço bruto médio: R$ 1.069/un."
- [ ] Linhas com margem negativa: **376** (2,1% das 18.227 linhas)
- [ ] Painel de reconciliação: registrada **R$ 42.161.509** − devoluções **R$ 869.171** = entregues **R$ 41.292.338**; mensagem verde "Diferença … R$ 0,00 ✓"
- [ ] Premissas PN-DEV-01 e PN-DEV-03 visíveis
- [ ] Gráfico "Receita ajustada (provisória) e margem bruta por mês" (barras + linha) e gráfico de anos lado a lado aparecem
- [ ] **Filtro:** Filiais = *Porto Alegre* → Receita **R$ 2,97 mi (+4,8%)**, margem **39,1% (−0,8 p.p.)**, pedidos **786**, devoluções **R$ 64,6 mil**, resultado **R$ 285,1 mil** (margem 9,6%), **32** linhas negativas. Depois **limpe** o filtro (clique no "x") e confira que voltou a R$ 41,29 mi.

## 2. Filiais

- [ ] Gráfico de receita por filial: São Paulo (Matriz) **12.279.853** no topo; Porto Alegre **2.970.981** na base
- [ ] Margem bruta por filial: maior Belo Horizonte **42,5%**; menor Brasília **38,9%**
- [ ] Variação anual: Salvador **+115,2%** (maior), Porto Alegre **+4,8%** (menor); nenhuma filial negativa
- [ ] Mapa de calor filial × mês: Salvador sem cor em jan/26 (sem base) e azul escuro de fev a abr/26
- [ ] Tabela com 8 filiais; Matriz: receita R$ 12.279.853, var. +10,4%, margem 41,3%, despesas % **56,2%**, pedidos **2.991**, ticket **R$ 4.106**
- [ ] Colunas "Despesas % da Receita Ajustada" e "Ticket por pedido" presentes; nota sobre a Matriz não comparável
- [ ] **Filtro:** Canais = *(um canal)* → a página recalcula e nenhuma exceção aparece

## 3. Produtos e Margem

- [ ] Controle "Piso de linhas de venda por produto" = **200** (pode mover; a tabela muda)
- [ ] Gráfico de bolhas (receita × margem, eixo horizontal logarítmico): **uma bolha vermelha** abaixo da linha de 0%
- [ ] "10 menores margens brutas": Smartphone X Max **−9,9%** (vermelho), Notebook Pro 14" **13,8%**
- [ ] Margem por categoria: Software & Assinaturas **79,1%** (maior), Eletrônicos **13,4%** (menor)
- [ ] Ranking de margem (11 produtos com piso 200): #1 Smartphone X Max, receita **R$ 3.215.394**, margem **−9,9%**, linhas negativas **99,5%**, **378** linhas
- [ ] Faixa vermelha: "1 produto(s) com margem bruta NEGATIVA no recorte: Smartphone X Max"
- [ ] **Piso = 500** → a tabela diminui (menos produtos); **piso = 0/mínimo** → aumenta. Sem erro.

## 4. Orçamento

- [ ] Orçado acumulado **R$ 14,06 mi** · Realizado **R$ 14,12 mi** · Execução **100,5%** ("Dentro da faixa") · Desvio **R$ 63,7 mil**
- [ ] Bloco "Três conceitos…": Anual **R$ 19,67 mi**, Acumulado **R$ 14,06 mi**, Realizado **R$ 14,12 mi**; texto cita **71,8%** como leitura **errada**
- [ ] PN-ORC-01 visível
- [ ] Gráfico orçado × realizado: **9 meses** (jan–set/26), nenhum mês futuro
- [ ] Execução por departamento: só **Tecnologia da Informação** em vermelho (**105,7%**, segundo o relatório)
- [ ] Execução por categoria: 5 em vermelho (Juros & Tarifas Bancárias, Software & Licenças, Energia/Água/Internet, Consultoria & Terceiros, Eventos & Patrocínios)
- [ ] Tabela "Maiores desvios": Software & Licenças R$ 66.872 (**117,6%**), Energia, Água & Internet R$ 43.310 (**107,8%**), Juros & Tarifas Bancárias R$ 35.611 (**130,4%**)
- [ ] **Filtro:** Produtos ou Canais = *(qualquer um)* → a página avisa que despesas/orçamento não têm vínculo com produto (não mostra número enganoso)

## 5. Investigações

Aviso azul: Porto Alegre e Smartphone ignoram os filtros laterais; "Preço, volume e mix" usa os filtros.

**Aba Porto Alegre**
- [ ] Receita ajustada **R$ 179,4 mil (−48,9%)** · Pedidos **57 (−6,6%)** · Linhas **107 (+2,9%)** · Unidades **231 (−22,2%)** · Receita por linha **R$ 1.677 (−50,4%)**
- [ ] Barra de fev/26 destacada em laranja; seletor "Mês analisado" mexe sem erro
- [ ] Cascata "Decomposição da variação" de **351,3 mil → 179,4 mil**
- [ ] Mensagem: nenhum padrão programado cobre este mês; achados INV1.x rotulados (OBSERVAÇÃO etc.)

**Aba Smartphone X Max**
- [ ] Preço bruto médio **R$ 5.290 (+0,0%)** · Custo por unidade **R$ 4.647 (+37,1%)** · Margem **−13,7% (−31,4 p.p.)** · Linhas negativas **607 (99,2% do total)**
- [ ] Gráficos de preço/custo/margem e % de linhas negativas por mês (100% desde nov/25)
- [ ] Controle "Margem bruta-alvo": em 0% → preço **R$ 6.017 (+13,7%)**
- [ ] Caixa "Padrão programado (P06/P07)" e legenda dos 4 rótulos

**Aba Preço, volume e mix** (período padrão, "Mesmo período do ano anterior")
- [ ] Cascata de **34.284,6 mil (jan/25 a set/25) → 41.292,3 mil (jan/26 a set/26)**
- [ ] Tabela: Volume **R$ 6.502.009 (92,8%)** · Mix **−R$ 40.643** · Preço **R$ 713.507 (10,2%)** · Desconto **−R$ 65.433** · Devoluções **−R$ 101.703**
- [ ] Mensagem verde: variação **R$ 7.007.737 = soma dos efeitos · resíduo R$ 0,00**
- [ ] Trocar para "Período imediatamente anterior" → recalcula e o resíduo continua **R$ 0,00**

**Aba Todos os achados**
- [ ] Lista de achados com selos OBSERVAÇÃO / CONCLUSÃO ARITMÉTICA / HIPÓTESE / PADRÃO PROGRAMADO; seletor de investigação (INV1…INV6) funciona

## 6. Casos de borda e responsividade

- [ ] **Recorte vazio:** Período = *Personalizado*, meses **jan/24 a dez/24**, Filiais = *Salvador* → aviso de "sem vendas/sem base"; **sem** cartões com números falsos e **sem** erro
- [ ] **Sem base anual:** Período = *Todo o histórico* (Visão Geral) → comparação anual indisponível com motivo explicado (não mostra 0%)
- [ ] **Estreitar a janela** do navegador (≈ 400 px) → o conteúdo se reorganiza, **sem barra de rolagem horizontal**
- [ ] Recarregar (F5) mantém o app funcionando

## 7. Encerramento

- [ ] Ctrl + C no PowerShell encerra o servidor; <http://localhost:8501> deixa de responder
- [ ] Rodar de novo `python scripts\run_powerbi.py` funciona (prova que o app liberou o banco)

## Resultado

| Página | OK | Observações / divergências (valor visto × esperado) |
|---|---|---|
| Geral | ☐ | |
| Visão Geral | ☐ | |
| Filiais | ☐ | |
| Produtos e Margem | ☐ | |
| Orçamento | ☐ | |
| Investigações | ☐ | |
| Casos de borda | ☐ | |

**Critério:** a validação da interface no Windows é considerada concluída quando **todas as caixas estiverem marcadas** ou cada divergência estiver explicada e registrada acima. Envie-me este quadro preenchido (e prints de qualquer problema) para eu atualizar o relatório de auditoria.
