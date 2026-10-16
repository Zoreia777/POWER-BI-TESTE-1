# Guia de estudo e entrevista — Projeto 01 · Inteligência Comercial 360°

> Para quem vai **explicar e defender** este projeto numa entrevista de Analista de Dados Júnior. Linguagem simples de propósito.
> Todos os números abaixo foram medidos no projeto (`reports/`, `docs/`). Os dados são **fictícios**: a Empresa X não existe e nada aqui é evidência sobre empresas reais.

---

## 1. Quem decidiu o quê (leia antes de qualquer entrevista)

Seja transparente: o código, os testes e os documentos foram **escritos com apoio de IA (Claude)**. Você **dirigiu** o projeto. Numa entrevista, a regra é simples: **só afirme o que consegue explicar e demonstrar.** Esta tabela separa as coisas; o registro das aprovações está nas premissas ([`PREMISSAS_DE_NEGOCIO.md`](PREMISSAS_DE_NEGOCIO.md): "aprovadas pelo usuário").

| Área | Você (responsável pelo projeto) | Implementação com apoio de IA | Como tornar defensável |
|---|---|---|---|
| **Problema e escopo** | Definiu o objetivo (inteligência comercial de ponta a ponta), a sequência de etapas e o que ficava fora (ex.: Streamlit só na etapa 5) | Organizou as etapas em tarefas | Explique o problema em 30 s sem olhar |
| **Premissas de negócio** | Aprovou PN-DEV-01…04, PN-MRG-01, PN-ORC-01, PN-PRC-01, PN-SIN-01 (devolução cancela a linha; custo recuperado é hipótese; sem data de devolução) | Levantou as evidências (`DEVOLUCOES.md`) e redigiu as opções | Saiba dizer **por que** a devolução vem positiva no CSV e o que muda se a premissa mudar |
| **Regras de qualidade** | Exigiu: não alterar os CSVs, não tratar hipótese como causa, não declarar validação sem executar, comparar períodos equivalentes, não usar meses futuros como realizados | Transformou as regras em validações e testes | Cite as regras e mostre onde o teste as protege |
| **Critérios de aceite** | Aprovou etapa a etapa com base em resultados (testes, reconciliações, 13 CSVs intactos) | Produziu os resultados e os relatórios | Rode `pytest` e `run_etl.py` ao vivo, se pedirem |
| **Código** (ETL, SQL, Python, app, DAX) | Revisou entregas e decidiu prioridades | **Escreveu** o ETL, as 8 consultas SQL, as investigações, o app e o DAX | **Estude** o código (exercícios abaixo) antes de dizer "eu fiz" |
| **Testes e mutação** | Exigiu testes independentes e injeção de defeitos | **Escreveu** oráculos, cenários e mutantes | Saiba explicar o que é um oráculo e um mutante, com um exemplo |
| **Resultados e conclusões** | Pediu rótulos (observação / conta / hipótese / padrão programado) e condicionais nas recomendações | Calculou e redigiu | Reproduza 2–3 números à mão ou no DuckDB |
| **Power BI** | Reconheceu que o DAX **não foi validado** e exigiu que isso ficasse registrado | Escreveu medidas, roteiro e conferidor | Só diga "validado" depois de rodar o roteiro (seção 9) |

**Frases para NÃO dizer** (a menos que se tornem verdade): "eu escrevi o ETL/as consultas/o app sozinho"; "as medidas DAX estão validadas"; "o app foi testado no Windows"; "isso mostra a causa real das vendas" (os dados são sintéticos).
**Frases honestas que funcionam:** "Dirigi o projeto e aprovei cada etapa; a implementação foi feita com apoio de IA e eu revisei e testei os resultados." / "Consigo explicar a lógica e reproduzir os números; o código eu estudei para defender."

### Exercícios para transformar "revisei" em "domino" (faça antes de entrevistas)
1. Abra `sql/analise/07_quedas.sql` e explique cada CTE em voz alta; reescreva a variação YoY de **um** produto numa query sua, com `LAG` ou `JOIN`.
2. No DuckDB (`duckdb warehouse/empresa_x.duckdb`), reproduza: receita registrada = entregues + devoluções (R$ 136,51 mi = 133,51 + 2,99).
3. Quebre de propósito uma fórmula (ex.: troque `aj` por `reg` em `margem_bruta`) e veja qual teste falha (`pytest tests/test_app.py -x`). Desfaça.
4. Rode o conferidor com a planilha em branco e entenda por que o resultado é "NÃO APROVADO".
5. Explique em 1 minuto por que `Pedidos` não soma entre filiais/produtos.

---

## 1b. Três apresentações (decore a estrutura, não o texto)

> Use os números como estão: todos saem de `reports/` e do app. Sempre diga que os dados são **fictícios**.

### Pitch de 30 segundos
> "Dirigi um projeto de portfólio de ponta a ponta com dados **fictícios** de uma varejista de tecnologia: 13 CSVs, 59 mil vendas, jan/24 a set/26. Montei um pipeline reproduzível — ETL em camadas no DuckDB, SQL, investigações em Python e um aplicativo Streamlit — com apoio de IA para a implementação e testes automáticos para cada número. Dois achados: o Smartphone X Max vende com prejuízo bruto desde nov/25, e a queda de 49% em Porto Alegre é em boa parte efeito de base, sem causa comprovada. Deixei a camada de Power BI preparada, mas as medidas DAX **ainda não foram validadas** lá."

Três frases-âncora para qualquer versão: (1) **"receita ajustada provisória"** com a reconciliação sempre à vista; (2) **"resultado operacional estimado" não é lucro contábil**; (3) **"não atribuí causalidade sem evidência"** — onde só havia hipótese, escrevi "hipótese".

### Apresentação de 2 minutos
1. **Problema (15 s):** "A diretoria quer saber onde a margem some, se uma queda é real e se o gasto está no orçamento."
2. **Dados e cuidados (25 s):** "13 CSVs. A devolução vem com sinal positivo, então a receita registrada superestima: criei a **receita ajustada provisória** e mostro a reconciliação (registrada = entregues + devoluções). Margens negativas não foram apagadas; foram sinalizadas."
3. **Arquitetura (25 s):** "CSV → raw → stg → mart no DuckDB, numa transação; views `bi` para o app e para o Power BI; o app só lê, em modo somente leitura."
4. **Um achado completo (35 s):** "Smartphone X Max: preço fixo de R$ 5.290, custo +37%, margem de 17,6% para −13,7%. Observação, conta e recomendação **condicional** — não sei se o custo é repasse real. E o padrão foi programado no simulador; eu sinalizo isso."
5. **Confiança (15 s):** "Mais de 400 testes: recalculo tudo por caminho independente e injeto defeitos para provar que os testes pegam erro."
6. **Limites (5 s):** "Dados sintéticos; DAX ainda não validado no Power BI."

### Demonstração técnica de 5 minutos
Está na **seção 10** (roteiro com o app aberto). Dica: ensaie cronometrado; se o app cair, use as capturas de `reports/app_evidencias/`.

---

## 2. Arquitetura e fluxo dos dados

```
data/*.csv  (13 arquivos, NUNCA alterados)
   │  scripts/run_etl.py
   ▼
warehouse/empresa_x.duckdb
   ├─ raw   → cópia fiel dos CSVs (tudo como texto) + número da linha de origem
   ├─ stg   → tipos corretos (datas, dinheiro), chaves e domínios validados
   ├─ mart  → modelo dimensional (fatos + dimensões) e KPIs prontos
   ├─ ops   → controle: arquivos lidos (SHA-256), execuções, checagens de qualidade
   └─ bi    → views estáveis para o Power BI (contrato de colunas)
   │
   ├─ sql/analise/01–08  → scripts/run_queries.py   → reports/consultas/*.csv (21 resultados)
   ├─ src/empresax/analise/ → scripts/run_analises.py → reports/executivo/ (relatório, 13 gráficos, evidências)
   └─ sql/powerbi + powerbi.py → scripts/run_powerbi.py → powerbi/referencia/*.csv + docs/POWERBI_CAMADA_DE_CONSUMO.md
```

**Por que camadas?** Cada camada faz uma coisa só. Se algo der errado, sei *onde* olhar: o dado chegou certo (raw)? Foi tipado certo (stg)? A regra de negócio está certa (mart)?

**Por que DuckDB?** Banco analítico em um único arquivo, roda sem servidor, lê SQL padrão e é rápido para agregações. Para um portfólio, qualquer pessoa reproduz com `pip install`.

**Reprodutibilidade:** rodar o ETL duas vezes dá o mesmo banco (testado por "impressão digital" de cada tabela). As saídas de análise são determinísticas (arredondamento fixo, ordem fixa, `SET threads = 1`); o `manifesto.json` guarda o SHA-256 de cada arquivo gerado.

---

## 3. ETL, raw, staging e mart — conceitos

| Conceito | O que é | Neste projeto |
|---|---|---|
| **ETL** | Extrair → Transformar → Carregar | CSV → raw → stg → mart |
| **raw** | Cópia fiel, sem interpretar | tudo texto; guarda a linha de origem (`_linha_origem`); o SHA-256 de cada CSV fica em `ops.arquivos_origem` |
| **staging (stg)** | Dado tipado e validado | datas viram `DATE`, valores `DECIMAL(14,2)`; chave primária, órfãos e domínio (`status` ∈ Entregue/Devolvido) checados |
| **mart** | Modelo pronto para análise | `fact_vendas`, `fact_despesas`, `fact_orcamento`, dimensões, KPIs |
| **Idempotente** | Rodar de novo não muda o resultado | testado |
| **Grão** | O que 1 linha representa | `fact_vendas`: 1 item de pedido (59.365 linhas); `fact_despesas`: 1 lançamento |
| **Fato × dimensão** | Fato = números/eventos; dimensão = descrições para filtrar | `fact_vendas` × `dim_produto`, `dim_filial`, `dim_canal`… |

**Decisões de negócio que o ETL carrega (e eu sei explicar):**
- **Devoluções (PN-DEV-01):** 3.0 mi de R$ 136,5 mi registrados são de linhas `Devolvido`, e no CSV elas vêm com **sinal positivo**. Decisão: devolução integral cancela a receita *da linha*. Então: registrada (R$ 136,51 mi) = ajustada (R$ 133,51 mi) + devoluções (R$ 2,99 mi). É **provisória**, porque não há data de devolução nem confirmação contábil.
- **Custo recuperado (PN-DEV-02):** *hipótese* de que o produto devolvido volta ao estoque; por isso existe uma sensibilidade "se o custo não for recuperado".
- **Margem negativa (PN-MRG-01):** linhas com custo > receita líquida **não são apagadas**; são sinalizadas (`flag_margem_negativa`).
- **Orçamento (PN-ORC-01):** comparar orçado × realizado só nos meses realizados.

---

## 4. Principais técnicas de SQL (e onde estão)

| Técnica | Para quê | Onde |
|---|---|---|
| `JOIN` / `LEFT JOIN` | juntar fato com dimensões; manter produto sem venda | `03_margem_produtos.sql` |
| `GROUP BY` + `FILTER (WHERE …)` | contar/somar só um subconjunto sem subconsulta | 03, 07 |
| **CTE** (`WITH`) | quebrar uma conta grande em passos legíveis | quase todas |
| **Window functions** (`LAG`, `RANK`, `SUM() OVER`) | variação mês a mês e ano a ano; ranking | `07_quedas.sql`, `01`, `03` |
| `CROSS JOIN` de grade | garantir que mês sem venda apareça como zero, não "sumisse" | `07_quedas.sql` |
| `NULLIF` / `DIVIDE`-style | evitar divisão por zero | `03_margem_produtos.sql` |
| `CASE WHEN` | classificar (queda relevante, base zerada…) | 07 |
| `UNION ALL` | empilhar níveis (empresa, filial, produto) | 07 |
| Razão de somas | margem do grupo = Σlucro ÷ Σreceita (**não** média das margens) | todas |

**Detalhe que mostra maturidade:** em `07_quedas.sql` eu separo `sem_base`, `sem_atividade`, `base_zerada` e `comparavel`. Uma filial que abre no mês X tem base zero — isso **não é crescimento infinito**, é "não comparável".

---

## 5. Como interpretar os indicadores

- **Receita registrada / entregue / devoluções / ajustada** — sempre juntas. Ajustada = entregues.
- **Margem bruta ajustada** = (receita ajustada − custo ajustado) ÷ receita ajustada. *Jan–set:* 43,3% (2024) → 41,8% (2025) → 40,3% (2026).
- **Resultado operacional estimado** = receita ajustada − custo ajustado − despesas. É **estimado e do dataset**; não considera impostos sobre lucro, depreciação, etc. Margem: 6,3% → 6,2% → 6,0%.
- **MoM × YoY:** mês a mês sofre sazonalidade; ano a ano compara o mesmo mês e elimina boa parte dela. Limiares: queda relevante MoM ≤ −15%, YoY ≤ −10% (configuráveis).
- **Queda persistente:** YoY negativo relevante por ≥ 3 meses seguidos. Queda de um mês só pode ser ruído ou base atípica.
- **Orçamento: anual × acumulado × realizado.** Anual = 12 meses (R$ 19,67 mi). Acumulado = só meses realizados (R$ 14,06 mi). Realizado = R$ 14,12 mi. Execução correta = realizado ÷ **acumulado** = **100,5%**. A leitura ingênua (÷ anual) dá 71,8% e sugere "economia" que não existe. O prorrateio linear 9/12 (95,7%) também erra.
- **Decomposição preço/volume/mix** — responde "cresci por vender *mais*, vender *mais caro* ou vender *outra coisa*?". Fecha com resíduo zero (identidade). Jan–set 2026 vs 2025: crescimento majoritariamente **volume**.
- **Decomposição da margem:** ΔMargem = efeito **mix** (vender mais do produto de margem baixa) + efeito **taxa** (a margem de cada produto mudou). 2024→2025: −1,5 p.p. = mix −0,5 + taxa −1,0.
- **Correlação ≠ causa.** Desconto × quantidade parecia associado (+0,127 unidade por p.p.), mas **some (−0,001)** ao controlar canal, segmento e sazonalidade. Era confusão, não efeito.

### Os quatro rótulos dos achados
| Rótulo | Significa |
|---|---|
| OBSERVAÇÃO | o dado mostra, medido |
| CONCLUSÃO ARITMÉTICA | decorre da conta, sem interpretar causa |
| HIPÓTESE | explicação possível, **não comprovada** |
| PADRÃO PROGRAMADO | criado de propósito no gerador sintético (P01–P17) |

---

## 6. Resultados concretos para citar

1. **Porto Alegre, fev/26: −48,9%** (R$ 351 mil → R$ 179 mil). Pedidos só −6,6% e linhas +2,9%; a receita *por linha* caiu 50,4%. Um produto (Notebook Pro 14") explica 62% da variação: 20 unidades na base contra 2. Retirando as 3 maiores linhas da base, a queda seria −26,9% (sensibilidade aritmética, **não** cenário real). Conclusão: **base atípica é a hipótese mais coerente, mas não está provada**.
2. **Smartphone X Max:** preço fixo (R$ 5.290) e custo unitário +37,1% → margem 17,6% → −13,7%. 607 das 612 linhas negativas da empresa são dele; **100% das linhas são negativas desde nov/25**, em qualquer canal, filial ou desconto → causa **estrutural** (custo > preço), não desconto pontual. Para margem zero, preço +14% sobre a lista (conta aritmética, sem elasticidade).
3. **Margem bruta −3,1 p.p. em 2 anos**, 76% da queda vinda de Smartphone X Max e Notebook Pro. A margem operacional ficou quase estável porque despesas/receita caíram 2,9 p.p. (alavancagem operacional).
4. **Crescimento de +20,4% (jan–set)** sobretudo volume.
5. **Quedas:** 18 de filial (nenhuma persistente) e 104 de produto (3 persistentes).
6. **Orçamento:** só TI está fora da faixa de ±5% (105,7%); três categorias concentram 76% dos desvios positivos.

---

## 7. Como defender as decisões de negócio

| Decisão | Justificativa em uma frase |
|---|---|
| Receita **ajustada** como principal | A devolução vem positiva no CSV; somar tudo superestimaria. Mas é **provisória**, então mostro a reconciliação. |
| Não corrigir custos/preços "estranhos" | Margem negativa pode ser real; apagar esconderia o problema (PN-MRG-01). |
| Razão de somas, não média de percentuais | Média de margens dá peso igual a produto grande e pequeno — erra. |
| Comparar 2026 só com meses equivalentes | jan–set/26 contra ano cheio de 25 seria injusto. |
| Piso de 200 linhas no ranking de margem | Evita ranquear produto com pouquíssimas vendas; o filtro aparece em cada linha do resultado. |
| Dizer "hipótese" | Dados não distinguem compra pontual de demanda recorrente; afirmar seria inventar. |
| Recomendações **condicionais** | "Se X for confirmado, então Y" — porque eu não tenho contexto da empresa. |

**Se perguntarem "você mudaria a política de devolução?"** → "Não decido sozinho: é uma decisão contábil. Deixei os três indicadores separados e a política em uma configuração, então trocar não exige refazer o projeto."

---

## 8. Como explicar os testes e a reconciliação

**416 testes passando** (conte com `python -m pytest tests -q --collect-only | tail -1`): etapas 1–3 (166), análises Python (41), camada Power BI e roteiro (31), conferidor do checklist (37), dados do aplicativo (52), interface com `streamlit.testing` (55), **mutação do aplicativo** (2, com 8 defeitos de negócio injetados) e higiene de publicação (26).

Camadas de teste, em linguagem simples:
1. **Reconciliação:** registrada = ajustada + devoluções, **linha a linha** e no total.
2. **Cálculo independente (oráculo):** recalculo os números direto dos CSVs em pandas / Python puro e comparo com o SQL e com o mart.
3. **Cenários feitos à mão:** monto 2–4 linhas, faço a conta no papel (ex.: preço sobe R$ 10 em 10 unidades com 10% de desconto → efeito preço = 90) e exijo exatamente esse resultado.
4. **Teste de mutação:** quebro a fórmula de propósito (ex.: peso do desconto errado) e verifico que algum teste **falha**. Se nenhum falhasse, o teste seria decorativo. Isso revelou um cenário que não cobria desconto + preço juntos, e foi corrigido. Na revisão final, os defeitos injetados à mão no app (margem sobre a receita registrada, filtro de canal ignorado, orçamento anual só do último ano, YoY com 11 meses, conexão com escrita…) viraram o teste permanente `tests/test_mutacao_app.py`.
5. **Determinismo:** rodar duas vezes gera arquivos idênticos (hash).
6. **Integridade:** os 13 CSVs originais não mudam (SHA-256 conferido contra `ops.arquivos_origem` e contra `data/CHECKSUMS.sha256`).
7. **Reprodução em ambiente limpo:** venv novo (Python 3.12 e 3.13), instalação pelo lock, ETL → consultas → análises → Power BI → app → testes; as saídas saíram idênticas byte a byte (ver `docs/AMBIENTE_E_REPRODUCAO.md`). A revisão encontrou uma dependência não declarada (`scipy`).

**Erros que encontrei e corrigi (ótimo para contar):**
- Orçamento anual vinha truncado e dava 100% — passei a usar a tabela completa (R$ 19,67 mi).
- Associação desconto × quantidade parecia real; era confusão por canal/segmento.
- Efeito mix sem centrar tornava as contribuições individuais ininterpretáveis → centralizei na margem total da base.
- Exportação não determinística (`-0.0`, ordem de soma) → arredondamento fixo e 1 thread.

---

## 9. Power BI — o que foi e o que NÃO foi feito

- **Feito:** 12 views `bi` com contrato de colunas testado; dicionário de 29 indicadores com definição e DAX; regras de filtro/granularidade; valores de referência para 10 contextos.
- **Validado:** as views (SQL × cálculo independente em pandas, 290 valores) e o DAX por *lint* estático (colunas e medidas existem, parênteses balanceados).
- **NÃO feito:** **as medidas DAX não foram executadas no Power BI.** O passo é seguir `docs/POWERBI_ROTEIRO_DE_CONSTRUCAO.md` (importar, relacionar, criar as 29 medidas, preencher a planilha) e rodar `python scripts/conferir_powerbi.py`; só o resultado **APROVADO (290/290)** autoriza dizer "validado". O conferidor só compara números; não executa DAX.

Resposta pronta: *"Escrevi e documentei as medidas, mas não tinha o Power BI no ambiente. Por isso não digo que estão validadas: deixei um checklist com valores esperados calculados por outro caminho."*

---

## 10. Roteiro de demonstração (≈ 5 minutos) — com o aplicativo aberto

Antes: `streamlit run app/streamlit_app.py`, página **Visão Geral**, período padrão (jan–set/26). Tenha à mão `docs/APLICATIVO_STREAMLIT.md`.

| Tempo | O que mostrar | O que dizer |
|---|---|---|
| 0:00–0:30 **Contexto** | Visão Geral (cartões) | "Empresa fictícia com 8 filiais, 59 mil linhas de venda e 7 mil lançamentos de despesa (jan/24–set/26). Construí um pipeline, um aplicativo e a camada para Power BI. Os dados são sintéticos." |
| 0:30–1:00 **Problema de negócio** | Barra lateral de filtros | "A direção precisa saber: onde crescemos, onde a margem some, se gastamos dentro do orçado e se uma queda é real ou efeito de comparação." |
| 1:00–1:45 **Arquitetura** | Rodapé (fonte) + diagrama da seção 2 | "CSV → raw → stg → mart no DuckDB; views `bi` estáveis; o app lê só essas views, em modo somente leitura, com SQL parametrizado. 13 CSVs nunca alterados; tudo testado." |
| 1:45–2:30 **Principais indicadores** | Cartões + painel de reconciliação | "Receita ajustada **provisória** R$ 41,29 mi (+20,4% contra jan–set/25), margem bruta 40,3% (−1,5 p.p.), resultado operacional **estimado** R$ 2,50 mi — não é lucro contábil. Mostro a reconciliação: registrada = entregues + devoluções, diferença R$ 0,00." |
| 2:30–3:20 **Estudo 1: Porto Alegre** | Investigações → Porto Alegre | "Fev/26 caiu 48,9%. Mas pedidos −6,6% e linhas +2,9%: o movimento quase não mudou; a receita por linha caiu 50,4%. Um produto responde por 62% da variação (20 unidades na base contra 2). Minha hipótese é base atípica — **não está provada**, e o simulador não programa nenhum evento para esse mês." |
| 3:20–4:10 **Estudo 2: Smartphone X Max** | Aba Smartphone X Max | "Preço parado em R$ 5.290; custo +37%; margem de 17,6% para −13,7%; desde nov/25, 100% das linhas dão prejuízo. A conta de preço (+13,7% para margem zero) é aritmética, sem elasticidade. Aqui o padrão foi programado no simulador — sinalizo isso." |
| 4:10–4:40 **Recomendações (condicionais)** | Aba Preço, volume e mix + Orçamento | "Se o custo for repasse real de fornecedor, reajustar preço ou limitar descontos antes de incentivar volume. O crescimento é cerca de 93% volume (92,8% da variação da receita ajustada no app; 92% da variação da receita registrada no relatório — denominadores diferentes): acompanhar mix e margem, não só receita. No orçamento, medir sempre contra o **acumulado** (100,5%), não o anual (71,8%)." |
| 4:40–5:00 **Limitações** | Bloco de premissas | "Dados sintéticos; devolução sem data; receita ajustada provisória; DAX escrito mas **não executado no Power BI** — deixei roteiro e 290 valores de referência para conferir." |

**Se sobrar tempo:** filtre uma filial e mostre que o recorte vazio (ex.: Salvador em 2024) não exibe números; abra a metodologia da decomposição.
**Se cair a demonstração ao vivo:** use as capturas de `reports/app_evidencias/`.

### Roteiro curto para conversar sem o app (apresentação verbal)
1. Problema → 2. Dados e cuidados (devoluções positivas, margem negativa, orçamento com meses futuros) → 3. Arquitetura → 4. Um achado completo (observação / conta / hipótese / recomendação condicional) → 5. Confiança (testes, reconciliação, mutação) → 6. Limites.
Dicas: use "observei / calculei / suponho / o simulador programou"; admita limites sem rodeio; prefira um achado bem explicado a dez superficiais.

---

## 11. Perguntas prováveis e respostas ancoradas no projeto (gerais)

**1. Qual foi sua maior descoberta?**
Que o Smartphone X Max vende com prejuízo bruto desde nov/25: preço parado em R$ 5.290 e custo +37%. É estrutural, porque 100% das linhas são negativas em qualquer canal/filial/desconto.

**2. A queda de 48,9% em Porto Alegre é preocupante?**
Não dá para afirmar. Pedidos caíram só 6,6% e as linhas subiram; a base de fev/25 tinha 20 unidades de um notebook (o máximo da série). A hipótese é base atípica, mas **não está provada**; numa empresa real eu checaria contratos/pedidos grandes e a carteira de clientes.

**3. Por que não usou a receita registrada?**
Porque ela inclui R$ 2,99 mi de linhas devolvidas com sinal positivo. Mostro as duas e a reconciliação; a ajustada é principal, mas provisória.

**4. O que é "resultado operacional estimado"?**
Receita ajustada − custo ajustado − despesas do dataset. Não é lucro líquido contábil.

**5. Como sabe que seus números estão certos?**
Recalculo por caminhos independentes (pandas/Python puro/CSV) e comparo; reconcilio linha a linha; faço testes de mutação para provar que os testes pegam erro.

**6. O que é teste de mutação?**
Alterar de propósito uma fórmula e verificar que algum teste falha.

**7. Diferença entre ETL e ELT?**
ETL transforma antes de carregar; ELT carrega bruto e transforma no banco. O meu é híbrido: carrego bruto no `raw` e transformo dentro do DuckDB com SQL — na prática, ELT em camadas.

**8. Por que média de margens está errada?**
Dá o mesmo peso a produtos de tamanhos diferentes. Uso razão de somas: Σlucro ÷ Σreceita.

**9. O que é granularidade?**
O que uma linha representa. Em `fact_vendas`, um item de pedido. Errar o grão duplica ou perde valores em joins.

**10. MoM ou YoY?**
YoY para decidir (elimina sazonalidade); MoM para acompanhar. Mostro os dois.

**11. O desconto aumenta as vendas?**
Na amostra bruta parece (+0,127 unidade por p.p.), mas ao controlar canal, segmento e sazonalidade vira −0,001. Não dá para afirmar efeito causal; seria preciso um teste controlado.

**12. A margem operacional ficou estável. Está tudo bem?**
Não: a margem bruta caiu 3,1 p.p.; a operacional ficou estável porque as despesas cresceram menos que a receita. Isso tem limite — se a bruta continuar caindo, a alavancagem não compensa para sempre.

**13. Execução do orçamento de 71,8%: a empresa economizou?**
Não. Esse número divide o realizado de 9 meses pelo orçamento de 12. O correto é contra o acumulado: 100,5%.

**14. Os padrões que você achou são reais?**
Os dados são sintéticos; vários padrões foram programados no gerador (P01–P17) e eu os registro como "padrão programado". O que demonstro é o método.

**15. O que faria com mais tempo / numa empresa real?**
Validar o DAX no Power BI, obter data de devolução e política contábil, incluir estoque e comissão de canal, e testar hipóteses com dados de contrato e câmbio.

**16. O que você faria diferente?**
Teria criado os cenários de teste "à mão" antes das fórmulas — o teste de mutação mostrou uma lacuna num cenário (desconto e preço juntos).

**17. Você usou IA?**
Sim — e é melhor dizer logo: "Dirigi o projeto, defini as premissas e aprovei cada etapa; o código, os testes e a documentação foram feitos com apoio de IA, e eu revisei os resultados, reproduzi os números e estudei a lógica para poder explicá-la." Só diga "consigo explicar cada fórmula" se tiver feito os exercícios da seção 1.

---

## 11b. Perguntas difíceis (com respostas ancoradas no projeto)

### SQL
**S1. Por que `LAG` e não um self-join para o YoY?** `LAG` com janela por entidade e ordenada por mês é mais curto e evita o erro de join que duplica linhas; mas ele só funciona se **não faltarem meses** — por isso uso um `CROSS JOIN` de grade (entidade × mês) para meses sem venda virarem zero e não "sumirem" (se sumissem, `LAG` pegaria o mês errado).
**S2. O que acontece com o YoY quando a base é zero?** Não calculo: a linha fica `base_zerada`/`sem_base` ("não comparável"). Dividir por zero ou chamar de "crescimento infinito" seria inventar.
**S3. Como evitou contar duas vezes ao juntar fato e dimensão?** Conferindo o **grão** (1 linha = 1 item de pedido), juntando dimensões por chave única (testado: PK única e 19 relacionamentos sem órfãos) e comparando o total depois do join com o total antes.
**S4. Como o app evita SQL injection?** Colunas e tabelas são fixas no texto; valores vão como parâmetros (`list_contains(?, coluna)`); ids são validados como inteiros e períodos como meses realizados; há teste com entradas maliciosas.
**S5. Por que `FILTER (WHERE …)` em vez de `CASE`?** Mesmo resultado, mais legível para somar/contar um subconjunto na mesma agregação; no DuckDB é padrão SQL.

### Python
**P1. Como a decomposição preço × volume × mix fecha com resíduo zero?** É uma identidade algébrica: cada efeito é definido para que a soma dos efeitos seja exatamente a variação da receita (inclusive produtos novos/descontinuados). Conferi por **três caminhos**: pandas, SQL (08a) e um oráculo em Python puro.
**P2. Por que um oráculo em Python puro se já tinha pandas?** Para não validar o código com ele mesmo: um cálculo feito por outra técnica (laços simples) só concorda por acaso se a lógica estiver certa.
**P3. O que é determinismo e por que se importou?** Duas execuções gerarem exatamente os mesmos bytes. Descobri que zero negativo e ordem de soma em ponto flutuante mudavam o arquivo; corrigi com arredondamento fixo e `threads = 1`.
**P4. Como o app evita mostrar dado velho?** O cache é chaveado pelo caminho, data de modificação e tamanho do arquivo do banco; se o ETL regrava o banco, a chave muda.
**P5. Por que `scipy` está nas dependências?** Porque `DataFrame.corr(method="spearman")` do pandas depende dele; foi encontrado na reprodução em ambiente limpo, que é exatamente o objetivo dela.

### ETL
**E1. E se o CSV chegar com uma coluna nova ou faltando?** O cabeçalho é validado contra `schema.py`; falha controlada (código de saída 1) em vez de carga silenciosa errada.
**E2. Por que uma única transação?** Para o banco nunca ficar meio atualizado: se qualquer validação obrigatória falha, há ROLLBACK e o último estado válido permanece.
**E3. Como sabe que nenhuma linha se perdeu?** Conto linhas: CSV = raw = stg; soma monetária raw = stg; mart = stg; os 13 hashes SHA-256 dos arquivos ficam em `ops.arquivos_origem`.
**E4. O que é idempotência e como provou?** Rodar de novo gera o mesmo conteúdo; provei com uma "impressão digital" (contagem + hash) de cada tabela entre duas execuções.

### Testes
**T1. Como sabe que um teste não é decorativo?** Teste de mutação: injeto um defeito de negócio e exijo que a suíte falhe. São 8 mutantes permanentes no app, e na etapa 4 mutantes já mostraram cenários que faltavam.
**T2. O que seus testes NÃO provam?** Que os dados representem uma empresa real; que as medidas DAX funcionem no Power BI; que a interface esteja visualmente ótima (o `streamlit.testing` não vê pixels — a conferência visual foi feita à parte, com navegador real, uma vez por mudança relevante); que funcione no Windows (não testei).
**T3. Teste de mutação cobre tudo?** Não. Cobre só os defeitos que eu lembrei de injetar; é uma amostra, não uma prova.

### Indicadores
**I1. Por que "Pedidos" não soma entre produtos?** Um pedido tem vários itens; somar por produto contaria o mesmo pedido várias vezes. Por filial soma, porque cada pedido tem uma filial só.
**I2. Por que "ticket por pedido" e não "ticket médio"?** O nome vem do dicionário de indicadores (Receita Ajustada ÷ Pedidos); usar o mesmo nome em todo lugar evita ambiguidade.
**I3. Margem de um grupo é a média das margens?** Não: Σlucro ÷ Σreceita. Média simples dá o mesmo peso a produto pequeno e grande.
**I4. Por que a "execução" do orçamento não é 71,8%?** Porque 71,8% divide 9 meses de gasto por 12 meses de orçamento. Compare com o acumulado dos mesmos meses: 100,5%.

### Devoluções
**D1. Por que a receita ajustada é "provisória"?** Porque não há data de devolução nem lançamento de estorno. Assumi (PN-DEV-01) que a devolução integral cancela a receita **da linha**, no mês da venda; isso é uma premissa de cenário, não um fato do dado.
**D2. E o custo do produto devolvido?** PN-DEV-02 é **hipótese**: assumo que o produto volta ao estoque. Por isso existe `lucro_bruto_se_custo_nao_recuperado` para ver a sensibilidade.
**D3. Qual o erro mais perigoso aqui?** Somar tudo: a devolução vem **positiva** no CSV, então a receita registrada superestima em R$ 2,99 mi (2,2%).
**D4. O que mudaria se houvesse data de devolução?** O estorno iria para o mês correto, e eu reabriria a premissa e as séries mensais.

### Limitações dos dados
**L1. O que este projeto prova?** O **método**: reconciliação, separação entre observação e hipótese, testes independentes. Não prova nada sobre mercados reais.
**L2. Alguns padrões foram programados. Isso não invalida?** Invalida como "descoberta", não como demonstração. Por isso há o rótulo PADRÃO PROGRAMADO (P01–P17) e eu digo quando uma causa é conhecida só porque o simulador a criou.
**L3. Qual é a pendência mais importante?** Validar as 29 medidas DAX no Power BI Desktop; está registrada, com roteiro e critérios de aprovação.
**L4. Você chamaria o resultado operacional de lucro?** Não: é estimado, do dataset, sem impostos sobre o lucro, depreciação etc.


## 12. Glossário rápido

- **p.p.** — ponto percentual (de 50% para 40% = −10 p.p., não −10%). Atenção ao arredondar: a margem foi de 43,33% para 40,25% = −3,08 p.p., e o relatório mostra **−3,1 p.p.** (subtraia primeiro, arredonde depois; 43,3% − 40,3% daria −3,0).
- **Mix** — composição das vendas entre produtos.
- **Efeito base** — variação grande porque o período de comparação foi atípico.
- **Oráculo** — cálculo independente usado só para conferir.
- **Idempotente** — repetir não altera o resultado.
- **Lint** — verificação estática sem executar.

## 13. Onde ler mais no repositório
`README.md` · `docs/AMBIENTE_E_REPRODUCAO.md` · `docs/RELATORIO_DE_AUDITORIA.md` · `docs/ETL.md` · `docs/PREMISSAS_DE_NEGOCIO.md` · `docs/DEVOLUCOES.md` · `docs/CONSULTAS_SQL.md` · `docs/METODOLOGIA_DECOMPOSICAO.md` · `docs/MODELO_DIMENSIONAL.md` · `docs/POWERBI_CAMADA_DE_CONSUMO.md` · `reports/executivo/RELATORIO_EXECUTIVO.md`
