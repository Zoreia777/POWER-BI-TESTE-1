"""Conferidor do checklist do Power BI: leitura de números (pt/en), tolerâncias, vazios, pendências e adulteração do esperado.
A ferramenta só compara números — estes testes provam que a comparação é correta; NÃO validam nenhuma medida DAX."""
import os
import subprocess
import sys

import pandas as pd
import pytest

from conftest import RAIZ
from empresax.powerbi_checklist import DIVERGE, INVALIDO, OK, PENDENTE, ValorInvalido, conferir, parse_valor, relatorio_md

ENV_UTF8 = {**os.environ, "PYTHONUTF8": "1"}
CHK = RAIZ / "powerbi" / "referencia" / "checklist_validacao.csv"
REF = RAIZ / "powerbi" / "referencia" / "valores_referencia.csv"


def _fmt(v, formato, loc):
    if pd.isna(v) or v == "":
        return "(vazio)"
    v = float(v)
    if "%" in formato:
        s = f"{v * 100:,.2f}%"
    else:
        s = f"{v:,.2f}"
        s = ("R$ " + s) if "R$" in formato else s
    return s.replace(",", "X").replace(".", ",").replace("X", ".") if loc == "pt" else s


def _preenchido(tmp_path, loc="pt"):
    d = pd.read_csv(CHK, dtype=str, keep_default_na=False)
    d["valor_powerbi"] = [_fmt(e if e != "" else None, f, loc) for e, f in zip(d.valor_esperado, d.formato)]
    p = tmp_path / "chk.csv"
    d.to_csv(p, index=False)
    return p, d


@pytest.mark.parametrize("txt,pct,loc,esperado", [
    ("R$ 1.234,56", False, "pt", 1234.56), ("1.234.567,89", False, "pt", 1234567.89), ("R$ 1,234.56", False, "en", 1234.56),
    ("33.209", False, "pt", 33209), ("33,209", False, "en", 33209), ("-R$ 5,00", False, "pt", -5.0), ("R$ -5,00", False, "pt", -5.0),
    ("−12,5", False, "pt", -12.5), ("41,25%", True, "pt", 0.4125), ("41.25%", True, "en", 0.4125), ("-1,50 %", True, "pt", -0.015),
    ("(vazio)", False, "pt", None), ("BLANK", True, "en", None), ("0", False, "pt", 0.0)])
def test_parse_aceita_formatos_do_power_bi(txt, pct, loc, esperado):
    r = parse_valor(txt, percentual=pct, localidade=loc)
    assert r == pytest.approx(esperado) if esperado is not None else r is None


@pytest.mark.parametrize("txt,pct,loc", [
    ("136,51 mi", False, "pt"), ("R$ 1.2k", False, "pt"), ("41,25", True, "pt"), ("41,25%", False, "pt"),
    ("1234.56", False, "pt"), ("1,234.56", False, "pt"), ("1.234,56", False, "en"), ("1.2345,6", False, "pt"), ("abc", False, "pt"), ("1,,2", False, "pt")])
def test_parse_rejeita_o_que_e_ambiguo_ou_fora_do_padrao(txt, pct, loc):
    with pytest.raises(ValorInvalido):
        parse_valor(txt, percentual=pct, localidade=loc)


def test_planilha_nao_preenchida_nao_e_aprovada():
    r = conferir(CHK, REF)
    assert not r.aprovado and r.contagem()[PENDENTE] == 290 and not r.erros_estrutura


@pytest.mark.parametrize("loc", ["pt", "en"])
def test_planilha_perfeita_aprova_290_de_290(tmp_path, loc):
    p, d = _preenchido(tmp_path, loc)
    r = conferir(p, REF, loc)
    assert r.aprovado and r.contagem()[OK] == 290
    assert (d.valor_esperado == "").sum() == r.contagem()[OK] - (d.valor_esperado != "").sum()  # 42 vazios aceitos como vazios


def test_localidade_errada_nao_aprova(tmp_path):
    p, _ = _preenchido(tmp_path, "pt")
    r = conferir(p, REF, "en")
    assert not r.aprovado


def _alterar(tmp_path, mudanca):
    p, d = _preenchido(tmp_path)
    i = mudanca(d)
    d.to_csv(p, index=False)
    return conferir(p, REF), i


def test_diferenca_de_um_centavo_passa_e_de_dois_centavos_falha(tmp_path):
    # A leitura vem arredondada em 2 casas; 'esperado + 0,01' está no limite da tolerância e 'esperado + 0,02' fora dela.
    def m(d, delta):
        i = d.index[(d.formato == "R$ #,0") & (d.valor_esperado != "")][0]
        v = round(float(d.valor_esperado[i]), 2) + delta
        d.loc[i, "valor_powerbi"] = _fmt(v, "R$ #,0", "pt")
        return i
    r, _ = _alterar(tmp_path, lambda d: m(d, 0.01))
    assert r.aprovado
    r, i = _alterar(tmp_path, lambda d: m(d, 0.02))
    assert not r.aprovado and r.contagem()[DIVERGE] == 1


def test_percentual_tolerancia_de_001_pp(tmp_path):
    def m(d, delta_pp):
        i = d.index[(d.formato == "0.0%") & (d.valor_esperado != "")][0]
        d.loc[i, "valor_powerbi"] = _fmt(round(float(d.valor_esperado[i]), 4) + delta_pp / 100, "0.0%", "pt")
        return i
    assert _alterar(tmp_path, lambda d: m(d, 0.01))[0].aprovado
    r, _ = _alterar(tmp_path, lambda d: m(d, 0.03))
    assert not r.aprovado and r.contagem()[DIVERGE] == 1


def test_vazio_esperado_com_numero_e_numero_esperado_com_vazio_divergem(tmp_path):
    def m1(d):
        i = d.index[d.valor_esperado == ""][0]
        d.loc[i, "valor_powerbi"] = "R$ 0,00"
    r, _ = _alterar(tmp_path, m1)
    assert r.contagem()[DIVERGE] == 1 or r.contagem()[INVALIDO] == 1
    assert not r.aprovado

    def m2(d):
        i = d.index[(d.valor_esperado != "") & (d.formato == "#,0")][0]
        d.loc[i, "valor_powerbi"] = "(vazio)"
    r, _ = _alterar(tmp_path, m2)
    assert r.contagem()[DIVERGE] == 1 and not r.aprovado


def test_uma_pendencia_impede_a_aprovacao(tmp_path):
    r, _ = _alterar(tmp_path, lambda d: d.__setitem__("valor_powerbi", d.valor_powerbi.where(d.index != 5, "")))
    assert not r.aprovado and r.contagem()[PENDENTE] == 1 and r.contagem()[OK] == 289


def test_adulterar_o_valor_esperado_e_detectado(tmp_path):
    p, d = _preenchido(tmp_path)
    i = d.index[d.valor_esperado != ""][3]
    d.loc[i, "valor_esperado"] = str(float(d.valor_esperado[i]) + 123.0)
    d.loc[i, "valor_powerbi"] = _fmt(float(d.valor_esperado[i]), d.formato[i], "pt")  # "ajusta" os dois lados para fingir que confere
    d.to_csv(p, index=False)
    r = conferir(p, REF)
    assert not r.aprovado and any("difere da referência" in e for e in r.erros_estrutura)


def test_linha_removida_ou_duplicada_e_detectada(tmp_path):
    p, d = _preenchido(tmp_path)
    d.iloc[1:].to_csv(p, index=False)
    assert not conferir(p, REF).aprovado
    pd.concat([d, d.iloc[[0]]]).to_csv(p, index=False)
    assert not conferir(p, REF).aprovado


def test_relatorio_lista_divergencias_e_pendentes(tmp_path):
    r, _ = _alterar(tmp_path, lambda d: d.__setitem__("valor_powerbi", d.valor_powerbi.where(d.index != 0, "R$ 1,00")))
    md = relatorio_md(r, "pt")
    assert "NÃO APROVADO" in md and "Divergências" in md and "C01" in md


def test_script_codigos_de_saida(tmp_path):
    s = RAIZ / "scripts" / "conferir_powerbi.py"
    nao = subprocess.run([sys.executable, str(s)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV_UTF8)
    assert nao.returncode == 1 and "NÃO VALIDADAS" in nao.stdout
    p, _ = _preenchido(tmp_path)
    ok = subprocess.run([sys.executable, str(s), str(p), "--relatorio", str(tmp_path / "r.md")], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV_UTF8)
    assert ok.returncode == 0 and "APROVADO" in ok.stdout and (tmp_path / "r.md").exists()
    assert subprocess.run([sys.executable, str(s), str(tmp_path / "nao_existe.csv")], capture_output=True, env=ENV_UTF8).returncode == 2


def test_aceita_csv_do_excel_em_portugues_ponto_e_virgula_com_bom(tmp_path):
    _, d = _preenchido(tmp_path)
    p = tmp_path / "excel.csv"
    p.write_text(d.to_csv(index=False, sep=";"), encoding="utf-8-sig")
    assert conferir(p, REF).aprovado
