# Relatório final de auditoria — Empresa X · Inteligência Comercial 360°

Revisão técnica final e preparação para publicação (14/10/2026). **Nada foi publicado, nenhum release foi criado e o projeto NÃO foi dado como encerrado:** aguardo a revisão conjunta.

## 1. Status de cada etapa

| Etapa | Entrega | Status |
|---|---|---|
| 1 — Dados e diagnóstico | 13 CSVs sintéticos, diagnóstico, dicionário | ✅ Concluída; 13 CSVs intactos (SHA-256 em `data/CHECKSUMS.sha256`) |
| 2 — ETL (raw → stg → mart) | DuckDB, 146 verificações, idempotente | ✅ Concluída e reproduzida em ambiente limpo |
| 3 — SQL | 8 análises, 21 resultados determinísticos | ✅ Concluída e reproduzida |
| 4 — Investigações Python e relatório | 6 investigações, 69 achados rotulados, 13 gráficos, relatório executivo | ✅ Concluída e reproduzida (saídas idênticas byte a byte) |
| 4 — Camada Power BI | 12 views `bi`, 29 indicadores com DAX, 290 valores de referência | 🟡 Views **validadas** (SQL × cálculo independente); **DAX NÃO executado no Power BI** |
| 5 — Aplicativo Streamlit | 5 páginas, somente leitura, filtros parametrizados | ✅ Concluída; executada em navegador real; **não testada no Windows** |
| Revisão final | Auditoria, reprodução, testes, README, guia, Power BI guiado | ✅ Concluída (este relatório), pendências abaixo |

## 2. Testes

**410 testes aprovados** (0 falhas), em instalação limpa a partir do `requirements-lock.txt` (Python 3.13.16; 190,9 s). Os **344 testes originais** continuam todos presentes e inalterados (apenas um helper de `tests/test_powerbi.py` passou a receber as contagens das views). Acréscimos: 2 de mutação do aplicativo, 1 do roteiro guiado, 37 do conferidor do checklist, 26 de higiene de publicação.

| Arquivo | Testes |
|---|---|
| `test_etl.py` / `test_consultas.py` / `test_devolucoes.py` / `test_diagnostico.py` | 88 / 58 / 12 / 8 |
| `test_analise.py` | 41 |
| `test_powerbi.py` | 31 |
| `test_app.py` / `test_app_ui.py` | 52 / 55 |
| **novos:** `test_mutacao_app.py` / `test_powerbi_checklist.py` / `test_publicacao.py` | 2 / 37 / 26 |

## 3. Evidências de reprodução em ambiente limpo

Detalhes, versões e tempos em [`AMBIENTE_E_REPRODUCAO.md`](AMBIENTE_E_REPRODUCAO.md). Resumo: venv novo, cópia sem artefatos e em outra pasta, instalação pelo lock, ETL 6,3 s → consultas 1,1 s → análises 6,2 s → Power BI 4,1 s → app (5 páginas sem exceção) → 410 testes passados. Saídas **idênticas byte a byte** às do ambiente de desenvolvimento; 13/13 hashes dos CSVs conferem. Python 3.12 também passou (na época, 346 testes). Sem dependência de arquivos temporários nem de caminhos absolutos (verificado por teste automático). **Só Linux.**

## 4. Arquivos modificados e justificativas

| Arquivo | Mudança | Por quê |
|---|---|---|
| `README.md` | Reescrito (objetivo, aviso de dados fictícios, arquitetura, resultados, capturas, Windows, testes, limitações, links) | Era o README da fase 1 (upload ao GitHub, Power Query) e estava desatualizado |
| `docs/legado/FASE1_BANCO_E_POWERBI.md` | Novo: conteúdo antigo do README preservado, marcado como legado | Não perder o histórico e não confundir o recrutador |
| `requirements.txt` | Faixas das versões testadas + `scipy` | `scipy` estava implícito; faixas antigas nunca foram testadas |
| `requirements-lock.txt` | Novo, versões exatas | Instalação reproduzível |
| `data/CHECKSUMS.sha256`, `.gitattributes` | Novos | Proteger os 13 CSVs de conversão de fim de linha (Windows/Git) |
| `.gitignore` | `checklist_preenchido*`, relatório de conferência, `.ruff_cache/` | Arquivos locais |
| `tests/test_mutacao_app.py` | Novo: 8 mutantes de negócio permanentes | Transformar os testes manuais de defeito injetado em automáticos |
| `tests/test_publicacao.py` | Novo | Caminhos absolutos, segredos, arquivos grandes, dependências, README e links |
| `src/empresax/powerbi_checklist.py`, `scripts/conferir_powerbi.py`, `tests/test_powerbi_checklist.py` | Novos | Conferência automática dos 290 valores (não executa DAX) |
| `src/empresax/powerbi_doc.py`, `scripts/run_powerbi.py`, `docs/POWERBI_ROTEIRO_DE_CONSTRUCAO.md`, `tests/test_powerbi.py` | Roteiro guiado, critérios A1–A6, contagens de linhas | Pedido do item 5; assert antigos preservados |
| `app/paginas/visao_geral.py`, `filiais.py` | Rótulos "Ticket por pedido" e "Despesas % da Receita Ajustada" | Alinhar ao dicionário de indicadores (só texto) |
| `reports/app_evidencias/*.png` + `scripts/capturar_evidencias_app.py` | 10 capturas refeitas e script versionado | As antigas eram anteriores aos rótulos novos |
| `src/empresax/analise/*.py` | Removidos imports e variáveis sem uso (ruff) | Limpeza; **saídas idênticas** (verificado por diff) |
| `powerbi/gerador/gerar_pbip.py`, `validar.py` | Sem caminho pessoal/`/tmp` por padrão; exigem argumento | Caminho da máquina do desenvolvedor no código |
| `powerbi/gerador/diff_deploy.py` | **Removido do repositório** (arquivado fora dele) | Ferramenta de transferência do ambiente de desenvolvimento, caminhos específicos |
| `docs/ETL.md` | "108 testes" → suíte completa; caminho `/tmp` removido | Desatualizado |
| `docs/GUIA_DE_ESTUDO_E_ENTREVISTA.md` | Autoria humano × IA, 3 apresentações, 24 perguntas difíceis, correções (92%, p.p.) | Item 6 |
| `docs/AMBIENTE_E_REPRODUCAO.md`, `docs/DEPENDENCIAS_E_LICENCAS.md`, este relatório | Novos | Itens 2, 3, 4 e 7 |

Não alterados: `data/*.csv`, `sql/`, resultados de qualquer análise, regras de negócio.

## 5. Problemas encontrados e corrigidos

1. **`scipy` não declarado** — a reprodução limpa falhou em `run_analises.py`. Declarado; teste impede novas dependências implícitas.
2. **"93% volume" (guia) × "92%" (relatório)** — investigada na origem: são denominadores diferentes (app: 92,8% da variação da receita **ajustada**; relatório `INV6.11`: R$ 6,56 mi ÷ R$ 7,11 mi = 92,3% da **registrada**). Nenhum número estava errado; guia e README agora explicam os dois. (Na primeira versão deste relatório eu havia chamado o 93% de erro; ao conferir o app, corrigi essa conclusão.)
3. **Exemplo de p.p. no guia** (43,3% → 40,3% = "−3,0") contradizia o −3,1 p.p. do relatório: a diferença vem do arredondamento (43,33% → 40,25% = −3,08). Explicado no glossário.
4. **Nomes de indicador** divergentes entre app e dicionário ("Ticket médio", "Despesas % receita") — alinhados.
5. **"108 testes" desatualizado** no ETL.md; README da fase 1 desatualizado.
6. **Caminho pessoal do desenvolvedor** (pasta de usuário do Windows) como padrão de `gerar_pbip.py` e `/tmp` em scripts legados.
7. **Roteiro do Power BI** era um checklist, não um procedimento guiado; agora tem passos, critérios e conferidor.
8. **Capturas antigas** não refletiam os rótulos novos; refeitas. (A primeira tentativa de recaptura saiu truncada, 1000 px; corrigida.)
9. **Código morto** (imports/variáveis não usados) removido sem alterar saídas.

Investigados e **não** são divergência: "71,5%" (orçamento acumulado ÷ anual) × "71,8%" (realizado ÷ anual) — grandezas diferentes; "25 tabelas" no mart + 3 views; "143" validações + 3 observações = 146 registros em `ops.qualidade_checks`.

Duplicações: não há funções idênticas; `_fig` existe em dois módulos de gráficos com paletas e layouts propositalmente distintos (unificar mudaria os HTML do relatório) — mantido.

## 6. Pendências técnicas

| # | Pendência | Classe |
|---|---|---|
| T1 | Execução e testes em **Windows** (e macOS) não realizados; comandos do README para Windows são não verificados | **Importante** |
| T2 | Os artefatos da **fase 1** em `powerbi/` (medidas DAX manuais, consultas M, gerador PBIP) nunca foram abertos no Power BI e coexistem com a camada nova; decidir: manter como legado (rotulado) ou remover | **Importante** |
| T3 | Rótulos de mês em inglês ("Jan 2026", "Aug") em alguns gráficos Plotly do app | Melhoria futura |
| T4 | Sem integração contínua (GitHub Actions) e sem configuração de lint (`ruff`) versionada | Melhoria futura |
| T5 | Teste em Python 3.11/3.14 e novas versões das bibliotecas (faixas só cobrem o testado) | Melhoria futura |
| T6 | `scripts/gerar_dados.py` tem uma variável sem uso (`meses_real`); não alterei o gerador | Melhoria futura |
| T7 | Os 64 testes adicionados após a execução em Python 3.12 não foram repetidos nessa versão | Melhoria futura |

## 7. Pendências de validação manual

| # | Pendência | Classe |
|---|---|---|
| M1 | **Validar as 29 medidas DAX no Power BI Desktop** (290 valores) seguindo o roteiro; só com `APROVADO` pode-se dizer "validado" | **Crítica** (para qualquer afirmação sobre Power BI) |
| M2 | Revisão conjunta do README, das capturas e do guia (tom, nomes, o que você consegue sustentar) | **Importante** |
| M3 | Confirmar o texto "Como foi desenvolvido" (apoio de IA, decisões suas) | **Importante** |
| M4 | Ensaiar as 3 apresentações e fazer os 5 exercícios da seção 1 do guia | **Importante** |
| M5 | Conferência visual do app em outros navegadores/telas (feita só com Chromium, 1440 px e 390 px) | Melhoria futura |

## 8. Checklist de publicação no GitHub

- [x] Dados 100% fictícios avisados no README e nos relatórios
- [x] README completo (objetivo, arquitetura, resultados, capturas reais, Windows, testes, limitações, links)
- [x] `.gitignore`, `.gitattributes`, sem `warehouse/`, logs, caches nem `powerbi/dados/` versionáveis (verificado com `git init` descartável: 180 arquivos, ≈ 25 MB, maior arquivo 6,4 MB)
- [x] Nenhum segredo, token, caminho pessoal ou absoluto (teste automático)
- [x] Dependências travadas e licenças das dependências listadas a partir dos metadados
- [x] 13 CSVs originais intactos
- [ ] **Escolher e adicionar `LICENSE`** (decisão sua; opções em `DEPENDENCIAS_E_LICENCAS.md`) — **ausente**
- [ ] Confirmar nome do autor/links (marcador `TODO` no fim do README)
- [ ] Decidir o destino de `powerbi/` da fase 1 (T2) e de `database/empresa_x.db` (SQLite de 13 MB da fase 1; conferido: mesmas contagens dos CSVs)
- [ ] Revisar a conta/organização, nome e visibilidade do repositório; o repositório **ainda não é um repositório git**
- [ ] Sua autorização explícita para `git init`, primeiro commit, push e qualquer release

## 9. Avaliação da prontidão para portfólio

**Pronto com ressalvas.** Pontos fortes: reprodutibilidade comprovada, rigor de validação (oráculos independentes, mutação, determinismo), separação clara entre observação, conta, hipótese e padrão programado, premissas explícitas (devoluções) e honestidade sobre limites. Ressalvas: (1) dados sintéticos — demonstra método, não descoberta; (2) as medidas DAX **não validadas** exigem cautela em qualquer fala sobre Power BI; (3) o código foi escrito com apoio de IA — o valor para a entrevista depende de você **dominar e saber explicar** o que está aqui (guia, seção 1); (4) licença e autoria por definir; (5) sem teste em Windows. Para uma vaga de Analista Júnior, o projeto excede o usual em qualidade de método; o risco principal é a defesa oral, não o código.

## 10. Próximos passos recomendados

1. Revisão conjunta deste relatório, do README e das capturas (M2, M3).
2. **Executar o roteiro do Power BI** (≈ 2–3 h) e rodar `python scripts/conferir_powerbi.py`; me enviar o relatório para atualizar a documentação (M1).
3. Escolher a licença e confirmar autoria; decidir o destino de `powerbi/` da fase 1 (T2).
4. Rodar a instalação no seu Windows e me avisar de qualquer falha (T1).
5. Treinar as três apresentações e os exercícios do guia (M4).
6. Só então autorizar a publicação (init, commit, push) — e, se quiser, um release.
7. Depois: GitHub Actions rodando `pytest`, rótulos de mês em português nos gráficos (T3, T4).
