"""Testes de mutação PERMANENTES do aplicativo (Revisão final, item 3).

Cada 'mutante' é uma cópia do projeto com UM defeito de negócio injetado por substituição de texto no código-fonte.
A suíte de dados do aplicativo (tests/test_app.py) roda num subprocesso sobre a cópia e DEVE falhar; sobre o original, deve passar.
Se algum mutante sobreviver, os testes deixaram de proteger aquela regra.

As cópias vivem em pasta temporária; o projeto original e os 13 CSVs (ligados por link simbólico, somente leitura) não são alterados.
"""
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from conftest import RAIZ

PASTAS = ("src", "app", "tests", "scripts", "sql")
ALVO = "tests/test_app.py"

# (nome, arquivo, texto original (único no arquivo), texto com defeito, regra que deve ser protegida)
MUTANTES = [
    ("margem_sobre_registrada", "src/empresax/app/consultas.py",
     'k["margem_bruta"] = razao(aj - cus, aj)', 'k["margem_bruta"] = razao(aj - cus, reg)',
     "margem bruta é sobre a receita AJUSTADA (PN-DEV-01), não a registrada"),
    ("taxa_devolucao_sobre_ajustada", "src/empresax/app/consultas.py",
     'k["taxa_devolucao"] = razao(dev, reg)', 'k["taxa_devolucao"] = razao(dev, aj)',
     "taxa de devolução = devoluções ÷ receita registrada"),
    ("filtro_de_canal_ignorado", "src/empresax/app/filtros.py",
     "(self.produtos, col_produto), (self.canais, col_canal))", "(self.produtos, col_produto), (self.canais, None))",
     "o filtro de canal precisa restringir as consultas"),
    ("orcamento_anual_so_ano_final", "src/empresax/app/consultas.py",
     "pf + [f.inicio.year, f.fim.year]", "pf + [f.fim.year, f.fim.year]",
     "orçamento anual soma todos os anos do período"),
    ("yoy_com_11_meses", "src/empresax/app/consultas.py",
     "base_f = f.deslocado(-12)", "base_f = f.deslocado(-11)",
     "comparação anual usa o período equivalente de exatamente 12 meses antes"),
    ("conexao_com_escrita", "src/empresax/app/base.py",
     "duckdb.connect(str(caminho), read_only=True)", "duckdb.connect(str(caminho), read_only=False)",
     "o aplicativo só abre o warehouse em modo somente leitura"),
    ("desconto_sobre_liquida", "src/empresax/app/consultas.py",
     'k["desconto_efetivo"] = razao(desc, bru)', 'k["desconto_efetivo"] = razao(desc, aj)',
     "desconto efetivo = desconto ÷ receita bruta"),
    ("lucro_com_registrada", "src/empresax/app/consultas.py",
     'k["lucro_bruto"] = aj - cus', 'k["lucro_bruto"] = reg - cus',
     "lucro bruto = receita ajustada − custo ajustado"),
]


def _copiar(destino: Path) -> None:
    for p in PASTAS:
        shutil.copytree(RAIZ / p, destino / p, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    try:
        (destino / "data").symlink_to(RAIZ / "data", target_is_directory=True)
    except OSError:  # Windows sem Modo de Desenvolvedor/administrador não cria link simbólico: copia (≈ 7 MB)
        shutil.copytree(RAIZ / "data", destino / "data")


def _rodar(raiz: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "EMPRESAX_MUTACAO": "1", "PYTHONUTF8": "1"}  # trava de recursão
    return subprocess.run([sys.executable, "-m", "pytest", ALVO, "-x", "-q", "-p", "no:cacheprovider", "--no-header"],
                          cwd=raiz, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)


pytestmark = pytest.mark.skipif(os.environ.get("EMPRESAX_MUTACAO") == "1", reason="executando dentro de um mutante")


def test_mutantes_estao_aplicaveis():
    """Cada substituição encontra o texto original (senão o mutante seria um 'não-teste'); todas as ocorrências são trocadas."""
    for nome, arq, velho, novo, _ in MUTANTES:
        fonte = (RAIZ / arq).read_text(encoding="utf-8")
        assert fonte.count(velho) >= 1, f"{nome}: texto original não encontrado em {arq}"
        assert velho != novo


def test_mutantes_sao_detectados(tmp_path):
    ctrl = tmp_path / "controle"
    _copiar(ctrl)
    mut = {}
    for nome, arq, velho, novo, _ in MUTANTES:
        d = tmp_path / nome
        _copiar(d)
        f = d / arq
        f.write_text(f.read_text(encoding="utf-8").replace(velho, novo), encoding="utf-8")
        mut[nome] = d
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 2)) as ex:
        futuros = {"controle": ex.submit(_rodar, ctrl), **{n: ex.submit(_rodar, d) for n, d in mut.items()}}
        res = {n: f.result() for n, f in futuros.items()}
    assert res["controle"].returncode == 0, "a cópia SEM defeito deve passar:\n" + res["controle"].stdout[-2000:]
    sobreviventes = [(n, regra) for (n, _, _, _, regra) in MUTANTES if res[n].returncode == 0]
    assert not sobreviventes, "mutantes que os testes NÃO detectaram: " + "; ".join(f"{n} ({r})" for n, r in sobreviventes)
