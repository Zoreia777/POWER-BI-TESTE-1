# Guia passo a passo: rodar o projeto no Windows (PowerShell)

Feito para quem **não** quer depender de conhecimento avançado de terminal. Basta **copiar cada bloco, colar no PowerShell e apertar Enter**, na ordem. Tempo total: ≈ 30 a 40 minutos na primeira vez (a maior parte é espera).

> ⚠️ Este guia **ainda não foi executado em um Windows** — você é a primeira pessoa a fazê-lo. Se algo falhar, vá à seção 9 e, se não resolver, me envie o texto do erro (copie e cole) e o número do passo.
> Nada neste guia altera os dados (`data\`) nem publica nada na internet. O aplicativo só **lê** o banco.

**Como colar no PowerShell:** clique com o **botão direito** dentro da janela (cola o texto copiado) e aperte **Enter**. Rode **um bloco de cada vez** e espere o cursor voltar (`PS C:\...>`) antes do próximo.

---

## 1. Pré-requisitos

| O que | Como conferir / obter |
|---|---|
| Windows 10 ou 11 | — |
| **Python 3.13 (ou 3.12)** | Veja abaixo |
| ≈ 1 GB livres em disco e internet (só para instalar as bibliotecas) | — |
| Navegador (Chrome, Edge ou Firefox) | — |
| Permissão para instalar o Python **só para o seu usuário** (não precisa ser administrador) | Ao instalar, **não** marque "Instalar para todos os usuários" |

> 💼 **Computador do trabalho?** Redes corporativas podem bloquear o download das bibliotecas (erro de conexão/SSL no passo 4). Se acontecer, rode em casa ou numa rede pessoal — **não** desative a verificação de segurança.

**Verificar se já tem Python.** Abra o PowerShell (tecla Windows → digite `PowerShell` → Enter) e rode:

```powershell
py --list
```

- Se aparecer `-V:3.13` ou `-V:3.12` → ótimo, pule para a seção 2.
- Se aparecer só `3.14` ou `3.11` (ou nada): instale o 3.13. Duas formas:

**Forma A (site):** entre em <https://www.python.org/downloads/windows/>, baixe o instalador **Python 3.13 (64-bit)**, abra e **marque a caixa "Add python.exe to PATH"** antes de clicar em *Install Now*.

**Forma B (PowerShell):**
```powershell
winget install --id Python.Python.3.13 --scope user
```

Depois **feche o PowerShell e abra outro** e confirme:

```powershell
py -3.13 --version
```
Esperado: `Python 3.13.x`. (Se você instalou o 3.12, use `py -3.12` no lugar de `py -3.13` em todo o guia.)

---

## 2. Localizar e abrir a pasta do projeto

1. Receba o arquivo **`empresa-x-powerbi.zip`** (enviado por mim no chat) e salve em `Downloads`.
2. Crie uma pasta curta e sem acento e extraia lá. No PowerShell:
   ```powershell
   New-Item -ItemType Directory -Force C:\Projetos | Out-Null
   Expand-Archive -Path "$env:USERPROFILE\Downloads\empresa-x-powerbi.zip" -DestinationPath C:\Projetos -Force
   ```
   (Se o arquivo foi salvo em outro lugar, troque o caminho. Alternativa sem comando: botão direito no zip → *Extrair tudo…* → `C:\Projetos`.)
3. Entre na pasta:
   ```powershell
   cd C:\Projetos\empresa-x-powerbi
   dir
   ```
   **Esperado:** você vê `app`, `data`, `docs`, `scripts`, `src`, `tests`, `README.md`, `requirements-lock.txt` etc. Se aparecer "não encontrado", rode `dir C:\Projetos` para ver o nome real da pasta (às vezes o zip cria uma pasta dentro da outra).

> **Por que `C:\Projetos`?** Evita pastas sincronizadas (OneDrive/Área de Trabalho), nomes longos ou com acento e espaços — causas comuns de erro com o banco DuckDB.

**Atalho para abrir o PowerShell já na pasta:** no Explorador de Arquivos, abra `C:\Projetos\empresa-x-powerbi`, clique na **barra de endereço**, digite `powershell` e aperte Enter.

---

## 3. Criar e ativar o ambiente virtual

O ambiente virtual é uma "caixa" só deste projeto, para não mexer no resto do computador.

```powershell
py -3.13 -m venv .venv
```
(Demora ≈ 10 s e não imprime nada.)

```powershell
.\.venv\Scripts\Activate.ps1
```

**Esperado:** o início da linha passa a mostrar **`(.venv)`**.

**Se aparecer erro vermelho "a execução de scripts foi desabilitada neste sistema":** rode isto (vale só para o seu usuário) e repita o comando de ativar:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
(Responda `S` se perguntar.) Se a política for bloqueada por TI, use a alternativa: `.\.venv\Scripts\activate.bat` dentro do **Prompt de Comando** (`cmd`) — ou rode tudo sem ativar, trocando `python` por `.\.venv\Scripts\python.exe` nos comandos seguintes.

Confirme que está usando o Python certo:

```powershell
python --version
```
Esperado: `Python 3.13.x` (ou 3.12.x).

> **Toda vez que abrir um PowerShell novo**, repita: `cd C:\Projetos\empresa-x-powerbi` e `.\.venv\Scripts\Activate.ps1`.

---

## 4. Instalar as dependências (versões fixadas)

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
```

**O que faz:** instala **exatamente** as versões testadas (pandas, DuckDB, Streamlit, Plotly, pytest etc.). Demora 1 a 3 minutos.
**Esperado:** termina com `Successfully installed ...` (uma lista longa). Avisos amarelos sobre "scripts não estão no PATH" podem ser ignorados.

Confirme:

```powershell
python -c "import pandas, duckdb, streamlit, scipy, plotly; print('pandas', pandas.__version__, '| duckdb', duckdb.__version__, '| streamlit', streamlit.__version__)"
```
Esperado: `pandas 3.0.6 | duckdb 1.5.6 | streamlit 1.66.0`.

> Se o `requirements-lock.txt` falhar por alguma versão indisponível no Windows, tente `python -m pip install -r requirements.txt` (faixas de versões) e me avise qual foi o erro.

---

## 5. Executar ETL, consultas, análises e preparação do Power BI (nesta ordem)

> ⚠️ **Ordem obrigatória.** Se o aplicativo (Streamlit) estiver aberto, **feche-o antes**: o banco só aceita um programa escrevendo por vez.

**5.1 ETL** — lê os 13 CSVs e cria o banco `warehouse\empresa_x.duckdb`:
```powershell
python scripts\run_etl.py
```
Esperado (≈ 10 s): linhas como `raw: 75,471 registros em 13 tabelas`, `stg: 75,471 ...`, `mart: 83,521 registros em 25 tabelas` e o aviso final de sucesso. Cria também `reports\relatorio_qualidade.md`.

**5.2 Consultas SQL:**
```powershell
python scripts\run_queries.py
```
Esperado (≈ 2 s): `21 resultados exportados para ...\reports\consultas`.

**5.3 Análises e relatório executivo:**
```powershell
python scripts\run_analises.py
```
Esperado (≈ 10 s): `6 investigações, 69 achados, 55 arquivos em ...\reports\executivo`.

**5.4 Preparação do Power BI** (views `bi` + valores de referência):
```powershell
python scripts\run_powerbi.py
```
Esperado (≈ 10 s): `12 views bi, 79779 linhas exportadas, 290 valores de referência (SQL = independente)`.

Se qualquer passo mostrar `Traceback` ou "erro", **pare** e vá à seção 9. Para conferir os dados originais (opcional, não altera nada):
```powershell
cd data; Get-FileHash *.csv -Algorithm SHA256 | Select-Object Hash,@{n='Arquivo';e={Split-Path $_.Path -Leaf}} | Format-Table -AutoSize; cd ..
```
(Compare com `data\CHECKSUMS.sha256`: os 13 códigos devem ser iguais, em maiúsculas ou minúsculas.)

---

## 6. Iniciar e acessar o Streamlit

```powershell
python -m streamlit run app\streamlit_app.py --browser.gatherUsageStats false
```

**O que acontece:**
- Se perguntar `Email:`, apenas aperte **Enter** (não precisa informar).
- O navegador abre sozinho em **<http://localhost:8501>**. Se não abrir, copie esse endereço e cole no navegador.
- Se o Firewall do Windows perguntar sobre acesso à rede, pode clicar **Cancelar** — o app funciona só no seu computador.

**Esperado:** a página "Visão Geral" com 8 cartões e o menu no topo: *Visão Geral · Filiais · Produtos e Margem · Orçamento · Investigações*.

**Deixe esta janela do PowerShell aberta** enquanto usa o app (ela mostra o servidor rodando). Agora faça o **checklist de validação** (`docs\CHECKLIST_VALIDACAO_APP.md`).

---

## 7. Encerrar o aplicativo corretamente

1. Feche a aba do navegador (opcional).
2. Na janela do PowerShell onde o app está rodando, aperte **Ctrl + C** (uma vez; espere ≈ 3 s). O cursor `PS C:\...>` volta.
3. Só então rode ETL/Power BI de novo, se precisar.

**Se o Ctrl + C não funcionar ou você já fechou a janela e o app continua respondendo:**
```powershell
Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
```
Esse comando mostra um número (PID). Encerre com (troque `1234` pelo número):
```powershell
Stop-Process -Id 1234
```
Se não mostrar nada, o app já está encerrado.

---

## 8. Executar os testes e interpretar o resultado

Com o ambiente ativado (`(.venv)`) e o app **fechado**:

```powershell
python -m pytest tests -q
```

Demora **3 a 10 minutos** (uma barra de pontos vai crescendo; não é travamento). **Não feche a janela.**

| O que você vê | Significado |
|---|---|
| `.` | teste passou |
| `F` | teste **falhou** |
| `s` | teste pulado (esperado só dentro dos testes de mutação) |
| `416 passed in ...s` (ou `412 passed, 4 skipped` sem Playwright) | ✅ **tudo certo** (pode haver avisos "warnings"; não são falhas) |
| `1 failed, 409 passed` | ⚠️ ao final, a lista `FAILED tests/arquivo.py::nome` diz qual falhou |

**Se algum falhar:** copie as últimas ~40 linhas (a partir de `FAILED`/`Error`) e me envie. Para rodar **só** o que falhou: `python -m pytest tests\arquivo.py -q -x`.

Atalhos úteis:
```powershell
python -m pytest tests\test_publicacao.py -q          # rápido (≈ 1 s): higiene do repositório
python -m pytest tests\test_app.py -q                 # dados do app (≈ 40 s)
```

> Na primeira vez no Windows, é possível que algum teste ligado a **caminhos de arquivo ou permissões** falhe por diferença do sistema (os testes foram escritos e executados em Linux). Isso é exatamente o que esta validação procura — **não é motivo para desanimar**; me envie o erro.

---

## 9. Erros comuns e soluções

| Mensagem / sintoma | Causa | O que fazer |
|---|---|---|
| `'py' não é reconhecido…` | Python não instalado ou instalado sem o "py launcher" | Reinstale (seção 1, Forma A) e feche/abra o PowerShell |
| `python` abre a **Microsoft Store** | Atalho da Loja intercepta o comando | Use `py -3.13 …` ou desative: *Configurações → Aplicativos → Configurações avançadas → Aliases de execução de aplicativo* → desligue `python.exe` e `python3.exe` |
| `python --version` mostra versão errada **depois de ativar** o venv | venv não ativado | Rode `.\.venv\Scripts\Activate.ps1` e confira o `(.venv)` |
| **PATH:** `'python' não é reconhecido` | Python sem "Add to PATH" | Reinstale marcando a caixa; ou use sempre `py -3.13` fora do venv e `python` dentro dele |
| `a execução de scripts foi desabilitada` | Política do PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (seção 3) |
| `No matching distribution found` / `Could not find a version` / erro de SSL ou proxy no `pip install` | Rede corporativa bloqueando PyPI, ou Python 3.14/3.11 | Use outra rede; confirme `python --version` = 3.12/3.13; **não** use opções que desliguem a verificação SSL |
| `Microsoft Visual C++ 14.0 is required` | Python muito novo para as versões fixadas | Use Python 3.13 ou 3.12 |
| `ERROR: Could not install packages due to an OSError` / `[WinError 206]` (caminho longo) | Pasta muito profunda | Use `C:\Projetos\empresa-x-powerbi` (seção 2) |
| `PermissionError` ao instalar | Instalação do Python "para todos" | Instale para o seu usuário; ou use o venv (já é por usuário) |
| **DuckDB:** `IO Error: Cannot open file … being used by another process` ou `Could not set lock on file` | O Streamlit (ou outro Python) está com o banco aberto | Feche o app (seção 7) e rode de novo |
| **DuckDB:** `Banco não encontrado` / app diz "execute run_etl.py" | ETL ainda não rodou (ou pasta errada) | `cd C:\Projetos\empresa-x-powerbi` e rode 5.1 |
| App mostra aviso de **views `bi` ausentes** | `run_powerbi.py` ainda não rodou | Rode 5.4 (com o app fechado) |
| `Ambiguous reference to catalog or schema "bi"` | Arquivo de banco chamado `bi.duckdb` | Não renomeie o banco; use o padrão `warehouse\empresa_x.duckdb` |
| `ModuleNotFoundError: No module named 'xxx'` | venv não ativado ou instalação incompleta | Ative `(.venv)` e rode de novo o passo 4 |
| `Address already in use` / porta 8501 ocupada | Outro Streamlit aberto | Seção 7 (encerrar pelo PID) ou use `--server.port 8502` |
| Navegador não abre | — | Acesse manualmente <http://localhost:8501> |
| Página do app em branco/lenta no 1º acesso | Cache iniciando | Aguarde ≈ 10 s e recarregue (F5) |
| Caracteres estranhos (`Ã§`) no terminal | Codificação do console | Só visual; para forçar: `$env:PYTHONUTF8=1` antes do comando |
| Antivírus bloqueia/remove arquivo | Falso positivo em `.pyc`/`.exe` | Adicione `C:\Projetos` às exceções (se a política permitir) |

**Para me pedir ajuda, envie:** (1) o número do passo; (2) a saída de `python --version` e `py --list`; (3) o erro completo copiado do PowerShell.

---

## Resumo (cola de uso diário)

```powershell
cd C:\Projetos\empresa-x-powerbi
.\.venv\Scripts\Activate.ps1
python -m streamlit run app\streamlit_app.py --browser.gatherUsageStats false     # abrir o app (Ctrl+C para fechar)
python -m pytest tests -q                                                          # testes (app fechado)
```

**Próximo passo depois de abrir o Streamlit com sucesso:** validação das 29 medidas DAX no Power BI Desktop (`docs\POWERBI_ROTEIRO_DE_CONSTRUCAO.md`).
