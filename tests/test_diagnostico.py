"""Testes da Etapa 1: o diagnóstico é reproduzível e as premissas dos dados brutos se confirmam."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import diagnostico as dg  # noqa: E402


@pytest.fixture(scope="module")
def R():
    return dg.checagens(dg.carregar())


def test_todas_as_13_tabelas_presentes(R):
    assert len(R["tabelas"]) == 13


def test_chaves_primarias_unicas(R):
    assert {n: t["pk_duplicada"] for n, t in R["tabelas"].items() if t["pk_duplicada"]} == {}


def test_sem_linhas_duplicadas(R):
    assert sum(t["duplicadas"] for t in R["tabelas"].values()) == 0


def test_relacionamentos_sem_orfaos(R):
    assert {k: x for k, x in R["fk_orfas"].items() if x} == {}


def test_receita_reconcilia(R):
    f = R["fin"]
    assert f["bruta_ne_qtd_x_preco"] == f["desconto_ne_bruta_x_pct"] == f["liquida_ne_bruta_menos_desc_imp"] == 0
    assert f["valores_nao_positivos"] == 0


def test_volumes_informados_no_projeto(R):
    assert R["tabelas"]["fact_vendas"]["linhas"] == 59_365
    assert R["tabelas"]["fact_despesas"]["linhas"] == 7_075


def test_pedido_item_e_unico(R):
    assert R["gran"]["pedido_produto_duplicado"] == 0
    assert R["gran"]["pedido_com_atributos_divergentes"] == 0


def test_markdown_gerado(R):
    md = dg.para_markdown(R)
    assert "fact_vendas" in md and "Devolvido" in md
