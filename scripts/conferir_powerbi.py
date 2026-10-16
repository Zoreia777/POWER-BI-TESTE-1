"""Confere a planilha preenchida no Power BI com os valores de referência.

    python scripts/conferir_powerbi.py                       # usa powerbi/referencia/checklist_validacao.csv, números em pt-BR
    python scripts/conferir_powerbi.py minha_copia.csv --localidade en --relatorio conferencia.md

Saída 0 = APROVADO (290/290); 1 = NÃO APROVADO (divergência, valor inválido ou pendente); 2 = erro de uso/arquivo.
Esta ferramenta só compara números; ela NÃO executa DAX. Sem planilha preenchida, o resultado é 'NÃO APROVADO – pendente'.
"""
import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from empresax.powerbi_checklist import DIVERGE, INVALIDO, OK, PENDENTE, conferir, relatorio_md  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checklist", nargs="?", default=str(RAIZ / "powerbi" / "referencia" / "checklist_validacao.csv"))
    ap.add_argument("--referencia", default=str(RAIZ / "powerbi" / "referencia" / "valores_referencia.csv"))
    ap.add_argument("--localidade", choices=["pt", "en"], default="pt", help="como o seu Power BI mostra números: pt = 1.234,56 · en = 1,234.56")
    ap.add_argument("--relatorio", help="grava o relatório em Markdown neste caminho")
    a = ap.parse_args()
    for p in (a.checklist, a.referencia):
        if not Path(p).exists():
            print(f"Arquivo não encontrado: {p}", file=sys.stderr)
            return 2
    res = conferir(Path(a.checklist), Path(a.referencia), a.localidade)
    c = res.contagem()
    print(f"OK={c[OK]}  DIVERGE={c[DIVERGE]}  PENDENTE={c[PENDENTE]}  INVÁLIDO={c[INVALIDO]}  (de {len(res.linhas)})")
    for e in res.erros_estrutura:
        print("PROBLEMA NA PLANILHA:", e)
    for l in res.linhas:
        if l.status in (DIVERGE, INVALIDO):
            print(f"  {l.contexto_id} {l.indicador_id} {l.status}: esperado={l.esperado} obtido={l.obtido} — {l.mensagem}")
    if a.relatorio:
        Path(a.relatorio).write_text(relatorio_md(res, a.localidade), encoding="utf-8")
        print("Relatório:", a.relatorio)
    print("APROVADO" if res.aprovado else "NÃO APROVADO" + (" — medidas DAX continuam NÃO VALIDADAS no Power BI" if c[OK] != 290 else ""))
    return 0 if res.aprovado else 1


if __name__ == "__main__":
    sys.exit(main())
