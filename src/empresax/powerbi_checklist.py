"""Conferidor do checklist de validação das medidas DAX no Power BI (Revisão final, item 5).

O desenvolvedor NÃO tem o Power BI neste ambiente: quem executa as medidas é o usuário, que preenche a coluna `valor_powerbi` de
`powerbi/referencia/checklist_validacao.csv` com o que os cartões mostram. Este módulo apenas COMPARA, de forma determinística e
testável, o que foi preenchido com os valores de referência independentes (calculados direto dos CSVs). Ele não valida DAX por si:
sem a planilha preenchida, o resultado é sempre 'NÃO APROVADO – pendente'.

Convenções da planilha (documentadas no roteiro):
  * número exatamente como o cartão mostra, com a localidade informada (pt: 1.234,56 · en: 1,234.56); "R$" e espaços são ignorados;
  * indicadores em % exigem o símbolo % (41,25%); indicadores que não são % não podem tê-lo;
  * medida que mostra vazio: escreva (vazio);   célula em branco = ainda NÃO conferido (pendente).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

TOL_VALOR = 0.01      # R$ 0,01 (ou 0,01 unidade)
TOL_PERCENTUAL = 1e-4  # 0,01 ponto percentual, em razão (0,0001)
EPS = 1e-6  # ruído de ponto flutuante (valores chegam a 1e8; 1 ulp ≈ 1,5e-8)
TOKENS_VAZIO = {"(vazio)", "vazio", "(blank)", "blank", "(em branco)"}
RE_NUM = {"pt": re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$"), "en": re.compile(r"^-?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")}
COLUNAS = ["contexto_id", "indicador_id", "formato", "valor_esperado", "valor_powerbi"]

OK, DIVERGE, PENDENTE, INVALIDO = "OK", "DIVERGE", "PENDENTE", "INVÁLIDO"


class ValorInvalido(ValueError):
    pass


def parse_valor(texto: str, *, percentual: bool, localidade: str = "pt"):
    """Texto do cartão → float (razão, se percentual), None se 'vazio'. Levanta ValorInvalido com mensagem em português."""
    if localidade not in RE_NUM:
        raise ValueError("localidade deve ser 'pt' ou 'en'")
    t = (texto or "").strip().replace(" ", " ")
    if t.lower() in TOKENS_VAZIO:
        return None
    t = t.replace("−", "-")
    t = re.sub(r"^(-?)\s*R\$\s*", r"\1", t)  # "R$ -5" e "-R$ 5" → "-5"
    t = re.sub(r"^R\$\s*(-?)", r"\1", t)
    tem_pct = t.endswith("%")
    if percentual and not tem_pct:
        raise ValorInvalido("indicador em %: escreva o valor com o símbolo % (ex.: 41,25%)")
    if not percentual and tem_pct:
        raise ValorInvalido("este indicador não é percentual: remova o símbolo %")
    if tem_pct:
        t = t[:-1]
    t = t.replace(" ", "")
    if re.search(r"[A-Za-z]", t):
        raise ValorInvalido("há letras no valor (ex.: 'mi', 'mil'): no Power BI defina Unidades de exibição = Nenhuma e 2 casas decimais")
    if not RE_NUM[localidade].match(t):
        raise ValorInvalido(f"número fora do padrão da localidade '{localidade}' ({'1.234,56' if localidade == 'pt' else '1,234.56'})")
    v = float(t.replace(".", "").replace(",", ".") if localidade == "pt" else t.replace(",", ""))
    return v / 100 if tem_pct else v


@dataclass(frozen=True)
class Linha:
    contexto_id: str
    indicador_id: str
    status: str
    esperado: float | None
    obtido: float | None
    diferenca: float | None
    mensagem: str = ""


@dataclass(frozen=True)
class Resultado:
    linhas: tuple
    erros_estrutura: tuple

    def contagem(self) -> dict:
        c = {OK: 0, DIVERGE: 0, PENDENTE: 0, INVALIDO: 0}
        for l in self.linhas:
            c[l.status] += 1
        return c

    @property
    def aprovado(self) -> bool:
        c = self.contagem()
        return not self.erros_estrutura and len(self.linhas) == 290 and c[OK] == 290


def _num(x: str):
    x = (x or "").strip()
    return None if x == "" else float(x)


def _ler(caminho: Path) -> pd.DataFrame:
    """CSV como texto. Aceita BOM (UTF-8-sig) e ';' como separador, que é o que o Excel em português grava por padrão."""
    cab = Path(caminho).read_text(encoding="utf-8-sig").split("\n", 1)[0]
    sep = ";" if cab.count(";") > cab.count(",") else ","
    return pd.read_csv(caminho, dtype=str, keep_default_na=False, sep=sep, encoding="utf-8-sig")


def conferir(checklist: Path, referencia: Path, localidade: str = "pt") -> Resultado:
    """Compara a planilha preenchida com os valores de referência. A estrutura também é conferida: ninguém 'ajusta' o esperado."""
    chk = _ler(checklist)
    ref = _ler(referencia)
    erros = []
    faltam = [c for c in COLUNAS if c not in chk.columns]
    if faltam:
        return Resultado((), (f"colunas ausentes no checklist: {faltam}",))
    chave = lambda d: (d.contexto_id + "|" + d.indicador_id)  # noqa: E731
    if len(chk) != len(ref) or set(chave(chk)) != set(chave(ref)) or chave(chk).duplicated().any():
        erros.append(f"o checklist não tem exatamente as {len(ref)} combinações contexto × indicador da referência")
    esp_ref = dict(zip(chave(ref), ref.valor_esperado))
    linhas = []
    for r in chk.itertuples(index=False):
        k = f"{r.contexto_id}|{r.indicador_id}"
        esperado = _num(r.valor_esperado)
        if k in esp_ref and _num(esp_ref[k]) != esperado and not (
                esperado is not None and _num(esp_ref[k]) is not None and abs(esperado - _num(esp_ref[k])) < 1e-6):
            erros.append(f"{k}: valor_esperado do checklist difere da referência (não altere o esperado; corrija a medida)")
        if (r.valor_powerbi or "").strip() == "":
            linhas.append(Linha(r.contexto_id, r.indicador_id, PENDENTE, esperado, None, None, "ainda não conferido"))
            continue
        pct = "%" in r.formato
        try:
            obtido = parse_valor(r.valor_powerbi, percentual=pct, localidade=localidade)
        except ValorInvalido as e:
            linhas.append(Linha(r.contexto_id, r.indicador_id, INVALIDO, esperado, None, None, str(e)))
            continue
        if esperado is None or obtido is None:
            if esperado is None and obtido is None:
                linhas.append(Linha(r.contexto_id, r.indicador_id, OK, None, None, None, "vazio como esperado"))
            else:
                linhas.append(Linha(r.contexto_id, r.indicador_id, DIVERGE, esperado, obtido, None,
                                    "deveria ser (vazio)" if esperado is None else "deveria ter valor, mas veio (vazio)"))
            continue
        tol = TOL_PERCENTUAL if pct else TOL_VALOR
        dif = obtido - esperado
        ok = abs(dif) <= tol + EPS and not math.isnan(dif)
        linhas.append(Linha(r.contexto_id, r.indicador_id, OK if ok else DIVERGE, esperado, obtido, dif, "" if ok else f"fora da tolerância ({tol:g})"))
    return Resultado(tuple(linhas), tuple(erros))


def relatorio_md(res: Resultado, localidade: str) -> str:
    c = res.contagem()
    sit = "APROVADO: 290/290 conferem" if res.aprovado else "NÃO APROVADO"
    L = [f"# Conferência das medidas DAX no Power BI — {sit}", "",
         f"Localidade usada na leitura: `{localidade}`. Linhas: OK={c[OK]} · DIVERGE={c[DIVERGE]} · PENDENTE={c[PENDENTE]} · INVÁLIDO={c[INVALIDO]} (total {len(res.linhas)}).", ""]
    if res.erros_estrutura:
        L += ["## Problemas na planilha", ""] + [f"- {e}" for e in res.erros_estrutura] + [""]
    ruins = [l for l in res.linhas if l.status in (DIVERGE, INVALIDO)]
    if ruins:
        L += ["## Divergências e valores inválidos", "", "| Contexto | Indicador | Situação | Esperado | Obtido | Mensagem |", "|---|---|---|---|---|---|"]
        L += [f"| {l.contexto_id} | {l.indicador_id} | {l.status} | {l.esperado} | {l.obtido} | {l.mensagem} |" for l in ruins]
        L.append("")
    if c[PENDENTE]:
        por_ctx = {}
        for l in res.linhas:
            if l.status == PENDENTE:
                por_ctx[l.contexto_id] = por_ctx.get(l.contexto_id, 0) + 1
        L += ["## Pendentes por contexto", "", ", ".join(f"{k}: {v}" for k, v in sorted(por_ctx.items())), ""]
    return "\n".join(L)
