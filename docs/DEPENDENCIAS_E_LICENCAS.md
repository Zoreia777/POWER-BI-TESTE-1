# Dependências e licenças

> Levantamento **mecânico** dos metadados que cada pacote declara (`importlib.metadata`) nas versões do `requirements-lock.txt` (venv limpo, Python 3.13). **Não é parecer jurídico** e não substitui a leitura dos textos oficiais de licença de cada projeto. Nada aqui foi preenchido de memória: o que o pacote não declara aparece como "não declarada".

## Licença do projeto (decisão pendente — do autor)

O repositório **não tem arquivo `LICENSE`** e eu não escolhi uma por você: a escolha (e o nome do titular dos direitos autorais) é sua. Sem licença, o código fica "todos os direitos reservados" por padrão — recrutadores conseguem ler, mas ninguém tem permissão formal de reutilizar. Opções comuns para portfólio:

| Opção | Efeito | Quando faz sentido |
|---|---|---|
| **MIT** | Permissiva: permite uso, cópia e modificação, exige manter o aviso de copyright | Portfólio aberto, simples e muito usada |
| **Apache-2.0** | Permissiva com concessão explícita de patentes e texto mais longo | Se quiser cláusula de patentes |
| **Sem licença** | Ninguém pode reutilizar sem pedir | Se preferir só exibir o trabalho |

Os **dados** são fictícios e gerados pelo próprio código; a licença escolhida cobriria também o gerador. Se publicar, acrescente `LICENSE` na raiz e ajuste o README (hoje há um aviso de licença pendente).

## Dependências diretas (declaradas em `requirements.txt`)

| Pacote | Versão (lock) | Licença declarada nos metadados |
|---|---|---|
| duckdb | 1.5.6 | MIT License |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| pandas | 3.0.6 | BSD License |
| plotly | 7.1.0 | MIT |
| pytest | 9.1.1 | MIT |
| scipy | 1.18.1 | BSD License |
| streamlit | 1.66.0 | Apache-2.0 |

## Dependências transitivas instaladas

| Pacote | Versão | Licença declarada nos metadados |
|---|---|---|
| altair | 6.3.0 | BSD License |
| anyio | 4.15.1 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0) |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| h11 | 0.16.0 | MIT License |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| itsdangerous | 2.2.0 | BSD License |
| Jinja2 | 3.1.6 | BSD License |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| narwhals | 2.27.1 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pillow | 12.3.0 | MIT-CMU |
| pluggy | 1.6.0 | MIT License |
| protobuf | 7.36.2 | 3-Clause BSD License |
| pyarrow | 26.0.0 | Apache-2.0 |
| pydeck | 0.9.3 | Apache License 2.0 |
| Pygments | 2.21.0 | BSD-2-Clause |
| python-dateutil | 2.9.0.post0 | BSD License |
| python-multipart | 0.0.32 | Apache-2.0 |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache Software License |
| rpds-py | 2026.9.1 | MIT |
| six | 1.17.0 | MIT License |
| starlette | 1.8.0 | BSD-3-Clause |
| typing_extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.8.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| watchdog | 6.0.0 | Apache Software License |
| websockets | 17.2 | BSD-3-Clause |

Observações: (1) `pillow` e `certifi`, por exemplo, têm licenças próprias (MIT-CMU, MPL-2.0) — conferir se for **redistribuir** binários; instalar via `pip` a partir do PyPI não redistribui nada. (2) **Playwright** (só para `scripts/capturar_evidencias_app.py`) e `jsonschema`/`referencing` (só para o gerador PBIP legado) **não** fazem parte de `requirements.txt`; no ambiente de desenvolvimento, Playwright 1.56.0 declara Apache-2.0. (3) Fontes/ícones e o Chromium usados nas capturas não são distribuídos pelo repositório.
