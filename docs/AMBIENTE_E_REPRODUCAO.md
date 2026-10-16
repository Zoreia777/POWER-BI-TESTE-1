# Ambiente, dependências e reprodução

## Versões testadas

| Item | Versão |
|---|---|
| Python | **3.13.16** e **3.12** (Linux x86-64) |
| numpy / pandas / scipy | 2.5.4 / 3.0.6 / 1.18.1 |
| duckdb | 1.5.6 |
| plotly / streamlit / pytest | 7.1.0 / 1.66.0 / 9.1.1 |
| Sistema | Linux. **Windows e macOS não foram testados** (os comandos do README para Windows seguem o padrão do Python, mas nunca foram executados lá). |

Durante o desenvolvimento rodou-se também com pandas 3.0.5 e streamlit 1.65.0: as saídas foram **idênticas byte a byte** às da instalação limpa (pandas 3.0.6 / streamlit 1.66.0). Versões fora das faixas de `requirements.txt` não foram testadas (pandas 2.x, por exemplo, **não** foi testado).

## Estratégia de instalação reproduzível

| Arquivo | Para quê |
|---|---|
| `requirements-lock.txt` | **Versões exatas** (`pip freeze` do venv limpo onde a suíte passou). Use este para reproduzir. |
| `requirements.txt` | **Faixas** compatíveis (`>=testada,<próxima major`) para quem quiser integrar o código num ambiente existente. Inclui `scipy`, exigido por `DataFrame.corr(method="spearman")` — dependência que estava **implícita** e só apareceu na reprodução limpa. |

Opcionais, fora dos arquivos acima: `playwright` (apenas `scripts/capturar_evidencias_app.py`) e `jsonschema`/`referencing` (apenas o gerador PBIP legado em `powerbi/gerador/`).

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.13 -m venv .venv  &&  .venv\Scripts\activate.bat
pip install -r requirements-lock.txt
python scripts/run_etl.py && python scripts/run_queries.py && python scripts/run_analises.py && python scripts/run_powerbi.py
streamlit run app/streamlit_app.py
python -m pytest tests -q
```

## Evidência de reprodução em ambiente limpo (14/10/2026)

**Método:** cópia do projeto **sem** artefatos gerados (sem `warehouse/`, `logs/`, `powerbi/dados/`, `reports/consultas/`, `reports/executivo/`, relatórios de qualidade e do ETL, `__pycache__`), numa pasta com **outro nome** e outro caminho; `venv` novo; instalação **pelo lock**; nenhum arquivo temporário nem caminho da máquina de desenvolvimento.

| Passo | Comando | Resultado | Tempo |
|---|---|---|---|
| 1. Ambiente + dependências | `python3.13 -m venv` + `pip install -r requirements-lock.txt` | OK | ≈ 27 s |
| 2. ETL | `python scripts/run_etl.py` | OK (raw 75.471 · stg 75.471 · mart 83.521 registros) | 6,3 s |
| 3. Consultas SQL | `python scripts/run_queries.py` | OK, 21 resultados | 1,1 s |
| 4. Análises + relatório | `python scripts/run_analises.py` | OK, 6 investigações, 69 achados, 55 arquivos | 6,2 s |
| 5. Camada Power BI | `python scripts/run_powerbi.py` | OK, 12 views `bi`, 290 valores (SQL = independente) | 4,1 s |
| 6. Aplicativo | `streamlit run app/streamlit_app.py` | `/_stcore/health` = `ok`; navegador real (Chromium): as 5 páginas abriram **sem exceção** do Streamlit | — |
| 7. Testes | `python -m pytest tests -q` | **410 passed** | 190,9 s |

Conferências adicionais:
- Todos os arquivos gerados (`reports/consultas/*`, `reports/executivo/*`, `powerbi/dados/*`, docs e checklist do Power BI, relatórios de qualidade) saíram **idênticos byte a byte** aos do ambiente de desenvolvimento.
- Os 13 CSVs de `data/` conferem com `data/CHECKSUMS.sha256` (13/13) e com `ops.arquivos_origem`.
- Python 3.12 com o lock: instalação OK e suíte completa **passou** (execução anterior, 346 testes na época; os 64 testes adicionados depois não foram reexecutados na 3.12).
- Um `git init` descartável na cópia mostrou 180 arquivos versionáveis, ≈ 25 MB, **nenhum** `.duckdb`, log, `__pycache__` ou `powerbi/dados`.

### Problemas encontrados na reprodução e soluções

| Problema | Causa | Solução |
|---|---|---|
| `run_analises.py` falhou: `ModuleNotFoundError: scipy` | Dependência implícita (`corr(method="spearman")`) instalada por acaso no ambiente de desenvolvimento | `scipy` declarado em `requirements.txt` e no lock; teste `test_todo_import_de_terceiros_esta_em_requirements` + checagem de `requirements` em `tests/test_publicacao.py` |
| (ambiente de desenvolvimento) `pip` não resolvia `pypi.org` | Rede da sandbox | Específico da sandbox; não é problema do projeto |
| DuckDB: erro de bloqueio ao rodar `run_powerbi.py` com o app aberto | Um escritor por vez; o leitor também segura o arquivo | Documentado: feche o app antes do ETL |

## Limites desta evidência
Foi feita em **Linux**. Não substitui um teste em Windows. A conferência visual do app foi feita com Chromium (Playwright), não com todos os navegadores.
