# 📊 Empresa X · Banco de dados + Power BI

Um banco de dados completo (e **100% fictício**) para controlar **vendas, lucros, gastos, orçamento,
metas e pessoas** de uma empresa — pronto para virar dashboards dinâmicos no Power BI.

- **~59 mil vendas, ~7 mil lançamentos de despesa**, 3 anos de história (jan/2024 → set/2026) e
  orçamento/metas projetados até dez/2026
- **Modelo estrela** (8 dimensões + 5 fatos), em **CSV** e em **SQLite**
- **Medidas DAX** prontas: DRE, YoY, YTD, orçado × realizado, Pareto, turnover, simulador de cenários
- **Protótipo interativo** do dashboard em HTML (`docs/prototipo_dashboard.html`) para você ver o resultado antes de montar
- **Temas** escuro e claro, **roteiro de 7 páginas** de dashboard e 15 "histórias escondidas" nos dados
- Gerador reproduzível em Python — troque pelos dados reais da sua empresa quando quiser

```
empresa-x-powerbi/
├── data/                     ← 13 CSVs prontos para o Power BI
├── database/empresa_x.db     ← o mesmo conteúdo em SQLite (com views)
├── sql/                      ← schema.sql, views.sql, consultas_exemplo.sql
├── powerbi/
│   ├── medidas_dax.md        ← todas as medidas, por tema
│   ├── GUIA_DASHBOARDS.md    ← as 7 páginas, visual por visual
│   ├── MODELO_E_CARGA.md     ← relacionamentos + como carregar (GitHub/local/SQLite)
│   ├── tema_empresa_x_escuro.json / tema_empresa_x_claro.json
│   └── consultas_m/          ← Power Query pronto (github/ e local/)
├── docs/dicionario_de_dados.md
├── docs/prototipo_dashboard.html   ← prévia interativa (abra no navegador)
└── scripts/gerar_dados.py    ← gera tudo de novo (semente fixa)
```

---

## 🚀 1. Subir para o seu GitHub

No terminal, dentro da pasta do projeto:

```bash
git init
git add .
git commit -m "Banco de dados da Empresa X para Power BI"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/empresa-x-powerbi.git
git push -u origin main
```

Antes, crie o repositório vazio em <https://github.com/new> (nome sugerido: `empresa-x-powerbi`).
Para o Power BI ler os CSVs direto da internet, deixe o repositório **público**.

> O maior arquivo tem ~7 MB (`fact_vendas.csv`) e o banco SQLite ~13 MB — bem abaixo do limite
> de 100 MB por arquivo do GitHub.

## 📥 2. Carregar no Power BI

O jeito mais rápido (atualiza sozinho quando você der `git push` em novos dados):

1. **Transformar dados → Gerenciar parâmetros → Novo parâmetro**: nome `BaseUrl`, tipo Texto, valor  
   `https://raw.githubusercontent.com/SEU_USUARIO/empresa-x-powerbi/main/data/`
2. Para cada arquivo de `powerbi/consultas_m/github/`: **Nova fonte → Consulta em branco →
   Editor Avançado**, cole o conteúdo e dê à consulta o nome do arquivo (`fact_vendas`, etc.).
3. **Fechar e aplicar** e siga [`powerbi/MODELO_E_CARGA.md`](powerbi/MODELO_E_CARGA.md) para
   relacionamentos, tabela de datas e ordenação de colunas (5 minutos).
4. Importe um tema: **Exibição → Temas → Procurar temas** → `tema_empresa_x_escuro.json`.
5. Crie as medidas de [`powerbi/medidas_dax.md`](powerbi/medidas_dax.md) e monte as páginas com o
   [`powerbi/GUIA_DASHBOARDS.md`](powerbi/GUIA_DASHBOARDS.md).

Prefere banco de dados de verdade? Veja as opções SQLite/ODBC, PostgreSQL e SQL Server em
`MODELO_E_CARGA.md`.

## 🗃️ 3. Usar o banco SQLite

```bash
sqlite3 database/empresa_x.db
sqlite> SELECT * FROM vw_dre_mensal LIMIT 5;
sqlite> .read sql/consultas_exemplo.sql
```

Views prontas: `vw_vendas_detalhada`, `vw_dre_mensal`, `vw_orcado_vs_realizado`,
`vw_meta_vs_realizado_filial` e `vw_curva_abc_clientes`.

## 🔁 4. Regenerar os dados (ou mudar o período)

```bash
pip install -r requirements.txt
python scripts/gerar_dados.py
```

O script recria CSVs, banco SQLite e consultas Power Query. As constantes no topo
(`DATA_INICIO`, `DATA_CORTE`, `DATA_FIM`, `PEDIDOS_BASE_DIA`, `SEED`…) controlam período, volume
e a "sorte" dos dados.

## 🏢 5. Trocar pelos dados reais da sua empresa

Mantenha **os mesmos nomes de tabelas e colunas** (veja
[`docs/dicionario_de_dados.md`](docs/dicionario_de_dados.md)) e substitua os CSVs. Ordem sugerida:
filiais/departamentos/categorias → despesas e orçamento → vendas → metas e RH. Seus dashboards
e medidas continuam funcionando.

## 🔎 6. Histórias escondidas nos dados

Black Friday que derruba a margem, produto vendido quase a custo zero, filial com concorrente
agressivo, verba de marketing estourada, custo de nuvem fugindo do controle… são 15 "easter eggs"
listados no final do [`GUIA_DASHBOARDS.md`](powerbi/GUIA_DASHBOARDS.md). Bom exercício para ver se
seus dashboards realmente contam a história.

---

### Aviso
Todos os nomes de pessoas, clientes e empresas são inventados; qualquer semelhança é coincidência.
Os números não representam nenhuma empresa real.
