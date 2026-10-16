"""Gera docs/POWERBI_CAMADA_DE_CONSUMO.md a partir do contrato, do dicionário e dos valores de referência (nada digitado à mão)."""
from __future__ import annotations

import pandas as pd

from .powerbi import CONTEXTOS, CONTRATO, INDICADORES, RELACIONAMENTOS


def _fmt(v, fmt: str) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "(vazio)"
    if "%" in fmt:
        return f"{v * 100:.2f}%".replace(".", ",")
    if "0.00" in fmt:
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{v:,.0f}".replace(",", ".")


def gerar_documento(ref: pd.DataFrame, linhas: dict[str, int]) -> str:
    L = ["# Camada de consumo do Power BI — views, indicadores, DAX e validação", "",
         "> ⚠️ **Estado de validação:** as medidas DAX abaixo **NÃO foram executadas no Power BI** (o ambiente de desenvolvimento não tem Power BI). "
         "O que foi validado: (1) as views SQL, contra cálculos independentes em pandas; (2) as definições DAX, por *lint* estático "
         "(colunas e medidas referenciadas existem; parênteses balanceados). O que falta: abrir o modelo no Power BI e conferir os "
         "**valores de referência** da seção 5. Este documento é gerado por `scripts/run_powerbi.py`.", "",
         "## 1. Visão geral", "",
         "`python scripts/run_etl.py && python scripts/run_powerbi.py` cria o schema `bi` no DuckDB (views estáveis) e exporta cada view para `powerbi/dados/*.csv` "
         "(o Power BI Desktop importa CSV sem driver adicional). A receita principal é a **receita ajustada provisória** (PN-DEV-01), sempre ao lado de registrada, entregues e devoluções.",
         "O arquivo `powerbi/medidas_dax.md` (anterior) segue válido como material de apoio; as medidas desta camada seguem a política de devoluções e o contrato de views testado.", "",
         "## 2. Modelo e relacionamentos (muitos-para-um; filtro vai da dimensão para o fato)", "",
         "| Fato (coluna) | → | Dimensão (coluna) |", "|---|---|---|"]
    L += [f"| `{a}[{b}]` | → | `{c}[{d}]` |" for a, b, c, d in RELACIONAMENTOS]
    L += ["", "Dimensão de datas: marcar `dim_calendario` como tabela de datas (coluna `data`). Fatos mensais (`fato_orcamento`, `fato_orcado_realizado_mes`) usam o 1º dia do mês em `mes`.", "",
          "## 3. Contrato das views (nomes e ordem das colunas — testados)", "",
          "| View / tabela | Linhas | Colunas |", "|---|---:|---|"]
    L += [f"| `{v}` | {linhas[v]:,} | {', '.join(f'`{c}`' for c in cs)} |".replace(f"{linhas[v]:,}", f"{linhas[v]:,}".replace(",", ".")) for v, cs in CONTRATO.items()]
    L += ["", "## 4. Regras de filtro e granularidade", "",
          "| Regra | Por quê |", "|---|---|",
          "| `fato_vendas` tem 1 linha por **item de pedido**; **Pedidos** é contagem distinta e **não soma** entre cortes. | Um pedido pode ter até 4 itens/produtos. |",
          "| Despesas e orçamento **não têm** produto, canal nem cliente: as medidas retornam **vazio** se esses cortes estiverem ativos. | Evita exibir o total da empresa dentro de um produto (leitura enganosa). |",
          "| Por filial, a **Matriz** concentra despesas corporativas: não compare `Despesas % da Receita Ajustada` da Matriz com as demais. | PN-SIN-01/Etapa 3 (análise 04). |",
          "| Percentuais são **razão de somas** (`DIVIDE(SUM, SUM)`), nunca média de percentuais. | Média de percentuais pondera errado. |",
          "| Variação MoM/YoY é **vazia** (BLANK) sem base ou com base zero. | Não é crescimento nem 0%. |",
          "| Em 2026, compare apenas meses realizados (`dim_calendario[realizado] = 1`); o orçamento **anual** inclui meses futuros. | PN-ORC-01. |",
          "| `Resultado Operacional Estimado` deve exibir o rótulo “estimado do dataset; não é lucro líquido contábil”. | Não há impostos sobre lucro, juros de capital etc. |",
          "| `Receita Ajustada` é **provisória**: exibir a nota quando for o KPI principal. | PN-DEV-01..04. |", "",
          "## 5. Dicionário de indicadores e definições DAX (não executadas no Power BI)", ""]
    for i in INDICADORES:
        L += [f"### {i['id']} · {i['nome']}", "", f"- **Definição:** {i['definicao']}", f"- **Tipo:** {i['tipo']} · **Grão:** {i['grao']} · **Filtros válidos:** {i['filtros']} · **Formato:** `{i['formato']}`"]
        if i["premissa"]:
            L.append(f"- **Premissa/observação:** {i['premissa']}")
        L += ["", "```dax", f"{i['nome']} =", f"    {i['dax']}", "```", ""]
    L += ["## 6. Checklist de validação no Power BI (valores de referência)", "",
          "Calculados **de forma independente** direto dos 13 CSVs (pandas) e iguais ao SQL sobre as views `bi` (`scripts/run_powerbi.py` interrompe se divergirem). "
          "Para cada contexto, aplique os filtros indicados e confira a medida; tolerância R$ 0,01 (valores) / 0,01 p.p. (percentuais). "
          "Arquivo completo: `powerbi/referencia/valores_referencia.csv`.", ""]
    fmt = {i["id"]: i["formato"] for i in INDICADORES}
    chaves = ["IND-01", "IND-03", "IND-04", "IND-09", "IND-17", "IND-19", "IND-24", "IND-26", "IND-28"]
    nome = {i["id"]: i["nome"] for i in INDICADORES}
    L += ["| Contexto | " + " | ".join(nome[k] for k in chaves) + " |", "|---|" + "|".join("---:" for _ in chaves) + "|"]
    for c in CONTEXTOS:
        r = ref[ref.contexto_id == c["id"]].set_index("indicador_id").valor_esperado
        L.append(f"| **{c['id']}** {c['nome']} | " + " | ".join(_fmt(r.get(k), fmt[k]) for k in chaves) + " |")
    L += ["", "**Como registrar o resultado:** marque cada linha conferida; qualquer divergência deve ser reportada com o contexto e a medida. "
          "Só depois disso o texto “validado no Power BI” pode ser usado.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------------------- roteiro de construção
PAGINAS_PBI = [
    ("1. Visão Geral", "Como está a empresa no período? A receita ajustada reconcilia com a registrada?",
     "Cartões: Receita Ajustada, Margem Bruta Ajustada %, Devoluções, Pedidos, Despesas, Resultado Operacional Estimado; matriz/cartões de reconciliação (IND-01, 02, 03, 05); colunas + linha: Receita Ajustada e Margem por mês.",
     "Segmentações: dim_calendario[ano], filial, canal. Filtre `dim_calendario[realizado] = 1`.",
     "Rotular a receita como PROVISÓRIA. Despesas/Resultado ficam vazios com produto/canal filtrados (por desenho)."),
    ("2. Filiais", "Quem vende mais, com que margem e como evoluiu contra o mesmo período do ano anterior?",
     "Barras: Receita Ajustada por filial; barras: Margem Bruta %; matriz filial × mês com Variação YoY % (formatação condicional); tabela com Despesas % e Pedidos.",
     "Segmentação de período e canal.", "Matriz não é comparável em Despesas %. YoY é vazio sem base: não troque por zero."),
    ("3. Produtos e Margem", "Quais produtos sustentam a receita e quais corroem a margem?",
     "Dispersão: eixo X Receita Ajustada, eixo Y Margem Bruta %, tamanho = número de linhas (`COUNTROWS`, medida auxiliar nova); barras: % Linhas com Margem Negativa; tabela com Preço Bruto Médio e Desconto Efetivo.",
     "Segmentações: categoria, produto, período.", "Preço Bruto Médio só faz sentido por produto. Aplique um filtro de visual 'linhas ≥ 200' para o ranking de margem (mesmo piso da Etapa 3)."),
    ("4. Orçamento", "O gasto realizado está dentro do orçado dos mesmos meses?",
     "Cartões: Orçamento Acumulado, Realizado Acumulado, Execução do Orçamento %; barras por departamento e por categoria com Execução %; colunas: orçado × realizado por mês. Um cartão separado 'Consumo do Orçamento Anual %' com a nota 'NÃO é execução'.",
     "Segmentações: período e filial (produto/canal não se aplicam).", "Nunca divida o realizado pelo orçamento anual para avaliar execução (IND-29 existe só para mostrar o erro)."),
    ("5. Investigações", "Estudos de caso: Porto Alegre e Smartphone X Max.",
     "Porto Alegre: linhas Receita Ajustada, Pedidos, Linhas (`COUNTROWS ( fato_vendas )`) e Receita por Linha (`DIVIDE ( [Receita Ajustada], COUNTROWS ( fato_vendas ) )`) por mês — as duas últimas são medidas auxiliares novas, sem valor de referência, filtradas em filial = Porto Alegre. Smartphone X Max: Preço Bruto Médio, Custo por Unidade (medida auxiliar nova: `DIVIDE ( SUM ( fato_vendas[custo_registrado] ), SUM ( fato_vendas[quantidade] ) )`, fora dos 29 indicadores e sem valor de referência) e Margem por mês, filtrados no produto.",
     "Filtros de página fixos (filial ou produto). Decomposição preço × volume × mix NÃO tem medida DAX nesta camada: use o aplicativo (Etapa 5) ou a tabela exportada de `reports/consultas/`.",
     "Sem causalidade: rotule hipóteses. O Smartphone X Max tem custo programado no simulador (P06/P07)."),
]


def descrever_contexto(c: dict) -> str:
    partes = []
    if c.get("ano") is not None:
        partes.append(f"`dim_calendario[ano]` = {c['ano']}")
    if c.get("mes") is not None:
        partes.append(f"`dim_calendario[primeiro_dia_mes]` = {c['mes'].strftime('%Y-%m-%d')}")
    if c.get("ano") is None and c.get("mes") is None:
        partes.append("sem filtro de data")
    partes.append("`dim_calendario[realizado]` = 1")
    if c.get("filial"):
        partes.append(f"`dim_filial[filial]` = {c['filial']}")
    if c.get("produto"):
        partes.append(f"`dim_produto[produto]` = {c['produto']}")
    return " e ".join(partes)


def tabela_checklist(ref: pd.DataFrame) -> pd.DataFrame:
    """Planilha de conferência: uma linha por (contexto × indicador) com colunas em branco para preencher no Power BI."""
    ctx = {c["id"]: descrever_contexto(c).replace("`", "") for c in CONTEXTOS}
    fmt = {i["id"]: i["formato"] for i in INDICADORES}
    out = ref.copy()
    out["filtros_a_aplicar"] = out.contexto_id.map(ctx)
    out["formato"] = out.indicador_id.map(fmt)
    out["tolerancia"] = out.formato.map(lambda f: "0,0001 (0,01 p.p.)" if "%" in f else "0,01")
    out["valor_powerbi"] = ""
    out["confere"] = ""
    return out[["contexto_id", "contexto", "filtros_a_aplicar", "indicador_id", "indicador", "formato", "valor_esperado", "tolerancia", "valor_powerbi", "confere"]]


def gerar_roteiro(ref: pd.DataFrame, contagens: dict | None = None) -> str:
    """`contagens` = linhas de cada view `bi` (para a coluna 'Linhas esperadas'); opcional para manter o gerador usável isoladamente."""
    L = ["# Roteiro guiado: construir e conferir o relatório no Power BI Desktop", "",
         "> ⚠️ **Estado de validação:** este roteiro foi escrito, mas **nenhuma medida DAX foi executada no Power BI** (o ambiente de desenvolvimento não o possui). "
         "Só depois de executar as medidas e conferir os valores da seção 6 é que se pode dizer que estão validadas. Documento gerado por `scripts/run_powerbi.py`; "
         "dicionário completo e definições em `docs/POWERBI_CAMADA_DE_CONSUMO.md`.", "",
         "## 0. Antes de começar", "",
         "- **Para quem:** quem já abriu o Power BI Desktop, importou arquivos e criou uma medida simples (nível intermediário). Nada aqui exige Power Query avançado.",
         "- **Você precisa de:** Windows com **Power BI Desktop** (gratuito, da Microsoft Store ou do site da Microsoft) e o projeto já instalado (veja o README, seção *Instalação no Windows*). Tempo estimado: 2 a 3 horas na primeira vez.",
         "- **Regra de ouro:** se um valor não conferir, **corrija a medida ou a importação — nunca o valor de referência** (a ferramenta de conferência detecta esperado alterado).",
         "- **Este roteiro ainda não foi executado no Power BI Desktop por ninguém.** Se um menu tiver nome diferente na sua versão do Power BI Desktop, siga o sentido do passo e registre a diferença na seção 8.", "",
         "### Critérios de aprovação (todos obrigatórios)", "",
         "| # | Critério | Como verificar |", "|---|---|---|",
         "| A1 | As 12 tabelas foram importadas com o número de linhas esperado | seção 1, passo 6 |",
         "| A2 | Os relacionamentos da seção 2 existem (muitos-para-um, filtro único) e a `dim_calendario` está marcada como tabela de datas | seção 2 |",
         "| A3 | As 29 medidas foram criadas sem nenhum erro de DAX e na ordem indicada | seção 3 |",
         "| A4 | Os **290 valores** da planilha conferem dentro da tolerância (R$ 0,01; 0,01 p.p.), incluindo as células que devem ficar **(vazio)** | seção 6 |",
         "| A5 | `python scripts/conferir_powerbi.py` termina com **APROVADO** (290/290; 0 pendentes; 0 inválidos; 0 problemas na planilha) | seção 6 |",
         "| A6 | Você guardou as evidências (prints da página de conferência por contexto, relatório da conferência, versão do Power BI Desktop e data) | seção 8 |",
         "", "Se qualquer critério falhar, as medidas continuam **NÃO VALIDADAS**. Se você não puder abrir o Power BI Desktop agora, nada se perde: o item permanece como pendência registrada.", "",
         "## 1. Preparar e importar os dados", "",
         "1. Abra o *Prompt de Comando* ou o *PowerShell* na pasta do projeto e rode (nesta ordem; feche o aplicativo Streamlit antes, se estiver aberto):",
         "   ```bat", "   .venv\\Scripts\\activate", "   python scripts\\run_etl.py", "   python scripts\\run_powerbi.py", "   ```",
         "   Isso cria a pasta `powerbi\\dados\\` com os 12 arquivos CSV listados abaixo.",
         "2. Abra o **Power BI Desktop** → *Arquivo → Opções e configurações → Opções → **ARQUIVO ATUAL** → Configurações regionais* e escolha **Localidade para importação: Inglês (Estados Unidos)**. "
         "Faça isso **antes** de importar: os CSVs usam ponto decimal e datas `AAAA-MM-DD`.",
         "3. *Página Inicial → Obter dados → Texto/CSV*. Escolha um arquivo de `powerbi\\dados\\`, clique em **Transformar Dados** (não em Carregar direto) e confira se datas aparecem como *Data* e valores monetários como *Número decimal*. Repita para os 12 arquivos (pode selecionar um por vez).",
         "4. Em *Opções → ARQUIVO ATUAL → Carregamento de dados*, **desmarque** *Detectar automaticamente novos relacionamentos* (você vai criá-los na seção 2).",
         "5. Clique em **Fechar e Aplicar**.",
         "6. Confira as linhas: *Exibição de Tabela* → clique no nome da tabela; a barra inferior mostra `TABELA: nome (N linhas)`. Compare com a coluna **Linhas esperadas**.", "",
         "| Arquivo | View de origem | Papel | Linhas esperadas |", "|---|---|---|---|"]
    papel = {"dim_": "dimensão", "fato_": "fato", "kpi_": "tabela de apoio (conferência)"}
    for v in CONTRATO:
        pp = next(x for k, x in papel.items() if v.startswith(k))
        n = f"{contagens[v]:,}".replace(",", ".") if contagens and v in contagens else "—"
        L.append(f"| `{v}.csv` | `bi.{v}` | {pp} | {n} |")
    L += ["", "Colunas de cada arquivo (nomes e ordem testados): seção 3 de `POWERBI_CAMADA_DE_CONSUMO.md`. Se uma contagem não bater, refaça o passo 1 (e confira se o ETL terminou sem erro).", "",
          "## 2. Modelo de dados", "",
          "Crie os relacionamentos **muitos-para-um**, direção de filtro **única** (da dimensão para o fato):", "",
          "| Fato (coluna) | → | Dimensão (coluna) |", "|---|---|---|"]
    L += [f"| `{a}[{b}]` | → | `{c}[{d}]` |" for a, b, c, d in RELACIONAMENTOS]
    L += ["", "**Como fazer:** *Exibição de Modelo* → arraste a coluna do fato até a coluna da dimensão (ou *Gerenciar relacionamentos → Novo*). Cardinalidade **Muitos para um (*:1)**, direção do filtro cruzado **Única**, relacionamento **ativo**. "
          "`fato_orcamento` e `fato_orcado_realizado_mes` usam o 1º dia do mês em `mes`, ligado a `dim_calendario[data]`.",
          "", "**Depois:** na *Exibição de Tabela*, selecione `dim_calendario` → *Ferramentas de tabela → Marcar como tabela de datas* → coluna `data`. Oculte as colunas de chave dos fatos (opcional). "
          "Se algum relacionamento aparecer tracejado (inativo) ou com direção *Ambas*, corrija: o resultado de várias medidas depende disso.", "",
          "## 3. Medidas DAX (criar numa tabela vazia `_Medidas`, nesta ordem)", "",
          "A ordem abaixo respeita as dependências (cada medida só usa medidas anteriores). Formatos nos comentários. **Estas definições não foram executadas no Power BI.**", "",
          "**Como criar uma medida:** (1) *Página Inicial → Inserir dados*, crie uma tabela com uma coluna e nenhum valor, nomeie `_Medidas` e carregue. (2) Selecione `_Medidas` no painel *Dados* → *Ferramentas de tabela → Nova medida*. "
          "(3) Cole **o bloco inteiro** (o nome da medida, o sinal `=` e a expressão) e pressione Enter. (4) Em *Ferramentas de medida*, ajuste o *Formato* conforme o comentário `formato`. (5) Passe para a medida seguinte, **na ordem**. "
          "Uma medida sublinhada em vermelho ou que mostre erro é uma falha: leia a mensagem, corrija e só então continue.", "",
          "> **Possível diferença de separador (não testado):** dependendo da configuração regional do Windows, o editor DAX pode exigir `;` entre argumentos de funções em vez de `,`. "
          "Se *todas* as medidas com mais de um argumento acusarem erro de sintaxe, troque as vírgulas que separam argumentos por `;` (as vírgulas decimais não existem nestas fórmulas) e registre isso na seção 8.", ""]
    for i in INDICADORES:
        L += [f"```dax\n// {i['id']} — formato: {i['formato']}\n{i['nome']} =\n    {i['dax']}\n```", ""]
    L += ["## 4. Regras de filtro e granularidade (não negociar)", "",
          "- `fato_vendas` = 1 linha por **item de pedido**; **Pedidos** é `DISTINCTCOUNT` e não soma entre cortes.",
          "- Despesas e orçamento não têm produto, canal ou cliente: as medidas devolvem vazio quando esses cortes estão ativos.",
          "- Percentuais são sempre `DIVIDE(soma, soma)`; nunca média de percentuais.",
          "- Compare 2026 **somente com meses realizados** (`dim_calendario[realizado] = 1`); o orçamento **anual** inclui meses futuros.",
          "- MoM/YoY vazios sem base ou com base zero: não é crescimento nem 0%.",
          "- Receita ajustada = **provisória** (PN-DEV-01); custo ajustado depende da hipótese PN-DEV-02; devoluções ficam no mês da venda (PN-DEV-03: não há data de devolução).",
          "- Resultado operacional estimado **não é lucro líquido contábil**.", "",
          "## 5. Estrutura recomendada das páginas", ""]
    for nome, pergunta, visuais, filtros, cuidados in PAGINAS_PBI:
        L += [f"### {nome}", "", f"- **Pergunta:** {pergunta}", f"- **Visuais:** {visuais}", f"- **Filtros:** {filtros}", f"- **Cuidados:** {cuidados}", ""]
    L += ["Tema visual: `powerbi/tema_empresa_x_claro.json` / `tema_empresa_x_escuro.json` (da fase anterior; opcionais). Evite elementos decorativos que escondam o dado.", "",
          "## 6. Conferir o relatório com os 290 valores de referência", "",
          f"São {len(ref)} valores ({len(CONTEXTOS)} contextos × {len(INDICADORES)} indicadores), calculados de forma **independente** direto dos 13 CSVs (pandas) e iguais ao SQL sobre as views `bi`. "
          "Arquivos: `powerbi/referencia/valores_referencia.csv` (valores esperados) e **`powerbi/referencia/checklist_validacao.csv`** (planilha pronta para preencher).", "",
          "### 6.1 Montar a página de conferência", "",
          "1. Nova página chamada `Conferência`. Insira um visual **Cartão de várias linhas** (*Multi-row card*) e arraste **as 29 medidas** para ele (ou use dois visuais). ",
          "2. Para que dê para ler o valor exato: no painel *Formatar visual → Valores de legenda* (Callout values) defina **Unidades de exibição = Nenhum** e **Casas decimais = 2**. "
          "Nas medidas em %, use o formato `0,00%`. (O padrão do Power BI mostra `R$ 136,51 mi`, que impede a conferência.)",
          "3. Adicione segmentações (*slicers*) para `dim_calendario[ano]`, `dim_calendario[primeiro_dia_mes]`, `dim_calendario[realizado]`, `dim_filial[filial]` e `dim_produto[produto]`, ou use o painel de *Filtros* da página.", "",
          "### 6.2 Conferir contexto por contexto", "",
          "Para cada linha da tabela abaixo (C01 a C10): limpe os filtros, aplique os filtros indicados (**inclusive `realizado` = 1**) e leia as 29 medidas.", "",
          "| Contexto | Filtros a aplicar |", "|---|---|"]
    L += [f"| **{c['id']}** {c['nome']} | {descrever_contexto(c)} |" for c in CONTEXTOS]
    L += ["",
          "### 6.3 Preencher a planilha", "",
          "1. **Copie** `powerbi\\referencia\\checklist_validacao.csv` para `powerbi\\referencia\\checklist_preenchido.csv` (o original continua em branco como modelo; a cópia está no `.gitignore`).",
          "2. Abra a cópia no Excel (ou no Bloco de Notas/VS Code). **No Excel, formate a coluna `valor_powerbi` como *Texto* antes de digitar**, para ele não converter `41,25%` ou `(vazio)`. Salve como **CSV UTF-8**.",
          "3. Em `valor_powerbi`, digite o valor **como o cartão mostra**: `R$ 136.505.354,39`, `41,25%`, `33.209`. Medida que mostra vazio: digite `(vazio)`. **Célula em branco = ainda não conferido** (conta como pendente).",
          "4. Percentuais precisam do símbolo `%`; indicadores que não são % não podem tê-lo. Se o seu Power BI usa o padrão americano (`1,234.56`), rode a ferramenta com `--localidade en`.",
          "5. Não altere `valor_esperado`. A ferramenta compara a planilha com `valores_referencia.csv` e acusa qualquer alteração.", "",
          "### 6.4 Rodar a conferência automática", "",
          "```bat", "python scripts\\conferir_powerbi.py powerbi\\referencia\\checklist_preenchido.csv --localidade pt --relatorio reports\\powerbi_conferencia.md", "```", "",
          "A saída mostra `OK / DIVERGE / PENDENTE / INVÁLIDO`. O código de saída é 0 só quando **todos os 290** estão OK. Tolerâncias: **R$ 0,01** em valores e contagens; **0,01 ponto percentual** em %. "
          "Células **(vazio)** na referência significam que a medida deve exibir vazio (BLANK) naquele contexto — não zero. "
          "A ferramenta apenas compara números: ela **não executa DAX** e não substitui a sua conferência visual dos cartões.", "",
          "### 6.5 Se algo não conferir", "",
          "| Sintoma | Causa provável | O que fazer |", "|---|---|---|",
          "| Todos os valores de receita divergem por centavos ou por fator de 10/100 | Localidade/tipo errado na importação | Refaça a seção 1 passos 2–3; confira o tipo *Número decimal* |",
          "| `INVÁLIDO`: número fora do padrão | Cartão em `mi`/`mil` ou localidade trocada | Unidades de exibição = Nenhum; use `--localidade` correto |",
          "| Despesas/orçamento aparecem em C09/C10 em vez de vazio | Falta o teste de filtro de produto na medida | Revise o DAX da medida (`ISFILTERED`) |",
          "| MoM/YoY divergem só em C05–C07 | Tabela de datas não marcada ou relacionamento inativo | Seção 2 |",
          "| Pedidos divergem por filial/produto | Medida soma em vez de `DISTINCTCOUNT` | Medida *Pedidos* da seção 3 |",
          "| Só 1 ou 2 contextos divergem | Filtro esquecido (`realizado` = 1) | Reaplique os filtros do contexto |",
          "| Tudo certo, mas a ferramenta diz `PENDENTE` | Células em branco | Preencha ou digite `(vazio)` quando for o caso |", "",
          "Para cada divergência real, registre contexto, medida, valor esperado e obtido; corrija a medida (**não** o valor de referência) e repita o contexto. "
          "Só quando os 290 valores conferirem as medidas podem ser descritas como validadas no Power BI.", "",
          "## 7. Armadilhas comuns ao conferir", "",
          "- **`ISFILTERED`:** as medidas de despesas/orçamento devolvem vazio quando há filtro de produto, canal ou cliente. Em C09 e C10 (produto filtrado) o esperado é (vazio).",
          "- **Datas:** `SAMEPERIODLASTYEAR`/`DATEADD` exigem a tabela de datas marcada e contígua. Para o ano de 2026, a base do ano anterior deve cobrir apenas os meses realizados selecionados.",
          "- **Pedidos:** a soma de pedidos por filial coincide com o total (cada pedido pertence a uma única filial), mas por produto, canal ou mês a soma NÃO coincide (um pedido tem vários itens/produtos). Isso não é erro da medida.",
          "- **Importação:** se as receitas divergirem por centavos, revise o tipo decimal e a localidade na importação.", "",
          "## 8. Registrar o resultado (somente depois da conferência real)", "",
          "Copie o quadro abaixo para `docs/POWERBI_VALIDACAO_REGISTRO.md` (ou envie ao Claude para atualizar a documentação) **depois** de rodar a conferência. Não atualize nenhum documento para 'validado' sem preencher este quadro com dados reais.", "",
          "| Item | Preencher |", "|---|---|",
          "| Data da conferência | |", "| Versão do Power BI Desktop (*Ajuda → Sobre*) | |", "| Idioma/região do Windows e localidade usada (`pt`/`en`) | |",
          "| Linhas importadas conferem (A1) | sim / não |", "| Relacionamentos e tabela de datas (A2) | sim / não |", "| Medidas criadas sem erro (A3) | sim / não — separador `;` foi necessário? |",
          "| Resultado da ferramenta (A4/A5) | OK=__ DIVERGE=__ PENDENTE=__ INVÁLIDO=__ |", "| Evidências guardadas (A6) | onde |",
          "| Medidas corrigidas durante a conferência | quais e por quê |", "| Diferenças de menu/nome neste roteiro | quais |", ""]
    return "\n".join(L)
