"""Higiene de publicação: o repositório precisa funcionar em qualquer máquina e não pode expor caminhos pessoais, segredos ou arquivos enormes."""
import hashlib
import re

import pytest

from conftest import DATA, RAIZ

IGNORAR = {"warehouse", "logs", "__pycache__", ".pytest_cache", ".git", ".venv", "venv", "dados", "graficos"}
TEXTO = {".py", ".md", ".sql", ".json", ".txt", ".toml", ".cfg", ".yml", ".yaml", ".html", ".gitignore", ".gitattributes", ".pq", ".m"}


def arquivos():
    for p in RAIZ.rglob("*"):
        if p.is_file() and not (set(p.relative_to(RAIZ).parts) & IGNORAR):
            yield p


def texto(p):
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def test_checksums_dos_13_csvs_originais():
    linhas = (DATA / "CHECKSUMS.sha256").read_text(encoding="utf-8").strip().splitlines()
    esperado = {l.split()[1]: l.split()[0] for l in linhas}
    reais = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.glob("*.csv")}
    assert len(esperado) == 13 and reais == esperado


def test_nenhum_caminho_absoluto_ou_pessoal():
    ruim = re.compile(r"C:\\Users|/home/\w|/Users/\w|joao\.pereira|/tmp/claude|/root/")
    achados = []
    for p in arquivos():
        if p.name == "test_publicacao.py" or p.suffix not in TEXTO:
            continue
        t = texto(p)
        if t and (m := ruim.search(t)):
            achados.append(f"{p.relative_to(RAIZ)}: {m.group(0)}")
    assert not achados, achados


def test_nenhum_segredo_aparente():
    padroes = [re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY"),
               re.compile(r"sk-[A-Za-z0-9]{20,}"), re.compile(r"(?i)(api[_-]?key|secret|passw(or)?d|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")]
    achados = []
    for p in arquivos():
        if p.name == "test_publicacao.py" or p.suffix not in TEXTO:
            continue
        t = texto(p)
        for r in padroes:
            if t and (m := r.search(t)):
                achados.append(f"{p.relative_to(RAIZ)}: {m.group(0)[:30]}")
    assert not achados, achados


def test_nenhum_arquivo_versionavel_passa_de_20_mb():
    grandes = [p.relative_to(RAIZ) for p in arquivos() if p.stat().st_size > 20 * 2**20]
    assert not grandes, f"{grandes} (limite de 100 MB do GitHub; aqui o teto é 20 MB)"


def test_gitignore_cobre_artefatos_gerados():
    g = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    for item in ("warehouse/*.duckdb", "__pycache__/", ".venv/", "powerbi/dados/", ".pytest_cache/", "logs/*.log", "checklist_preenchido"):
        assert item in g, item


def test_dependencias_declaradas_e_travadas():
    req = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    lock = (RAIZ / "requirements-lock.txt").read_text(encoding="utf-8")
    diretas = [l.split(">=")[0].strip() for l in req.splitlines() if l and not l.startswith("#")]
    assert {"numpy", "pandas", "scipy", "duckdb", "plotly", "streamlit", "pytest"} <= set(diretas)
    travados = {l.split("==")[0].lower() for l in lock.splitlines() if "==" in l}
    assert set(diretas) <= travados
    assert all("==" in l for l in lock.splitlines() if l and not l.startswith("#"))


def test_todo_import_de_terceiros_esta_em_requirements():
    import ast
    import sys
    req = (RAIZ / "requirements.txt").read_text(encoding="utf-8").lower()
    permitidos = {"numpy", "pandas", "duckdb", "plotly", "streamlit", "pytest", "scipy"}
    local = {"empresax", "componentes", "paginas", "conftest", "oraculos", "mini_mart", "diagnostico", "modelo", "relatorio"}
    opcionais = {"playwright", "jsonschema", "referencing"}  # scripts opcionais, documentados
    for p in arquivos():
        if p.suffix != ".py":
            continue
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            nomes = [a.name.split(".")[0] for a in n.names] if isinstance(n, ast.Import) else [n.module.split(".")[0]] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module else []
            for m in nomes:
                if m in sys.stdlib_module_names or m in local or m in opcionais:
                    continue
                assert m in permitidos and m in req, f"{p.relative_to(RAIZ)} importa {m} sem declarar em requirements.txt"


def test_readme_tem_as_secoes_obrigatorias_e_imagens_existentes():
    r = (RAIZ / "README.md").read_text(encoding="utf-8")
    for s in ("100% fictícios", "Problema de negócio", "Arquitetura", "Tecnologias", "Principais resultados", "Estudos de caso",
              "Instalação e execução no Windows", "Como executar os testes", "Limitações e premissas", "Documentação detalhada",
              "NÃO foram executadas no Power BI Desktop"):
        assert s in r, s
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", r)
    assert len(imgs) >= 4
    for i in imgs:
        assert (RAIZ / i).is_file(), i


@pytest.mark.parametrize("md", ["README.md", *[f"docs/{p.name}" for p in (RAIZ / "docs").glob("*.md")], "docs/legado/FASE1_BANCO_E_POWERBI.md"])
def test_links_relativos_dos_documentos_existem(md):
    p = RAIZ / md
    for alvo in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", p.read_text(encoding="utf-8")):
        if alvo.startswith(("http", "mailto")):
            continue
        assert (p.parent / alvo).exists(), f"{md}: link quebrado {alvo}"
