"""Gera o projeto Power BI (PBIP) completo da Empresa X.

Uso:
    python gerar_pbip.py <pasta_saida> [<pasta_dos_csv_no_windows>]

Saída:
    <pasta_saida>/EmpresaX.pbip              -> abra este arquivo no Power BI Desktop
    <pasta_saida>/EmpresaX.SemanticModel/    -> modelo (tabelas, relações, medidas)
    <pasta_saida>/EmpresaX.Report/           -> relatório (7 páginas, tema, menu)
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import modelo  # noqa: E402
import relatorio  # noqa: E402

NAME = "EmpresaX"


def main(out, pasta_dados):
    os.makedirs(out, exist_ok=True)

    def wj(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # .pbip
    wj(os.path.join(out, f"{NAME}.pbip"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })

    # modelo semântico
    sm = os.path.join(out, f"{NAME}.SemanticModel")
    if os.path.exists(sm):
        shutil.rmtree(sm)
    wj(os.path.join(sm, "definition.pbism"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "settings": {},
    })
    wj(os.path.join(sm, ".platform"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": "3c2f8f1e-6a0d-4b6e-8f3e-5b8d7e2a9c01"},
    })
    problems = modelo.check_dax_balance()
    if problems:
        raise SystemExit("Problemas no DAX:\n" + "\n".join(problems))
    wj(os.path.join(sm, "model.bim"), modelo.build_model(pasta_dados))

    # relatório
    rep, npages, nvis = relatorio.write_report(out, NAME, f"{NAME}.SemanticModel",
                                               os.path.join(HERE, "CY24SU10.json"))
    # gitignore do PBIP
    with open(os.path.join(out, ".gitignore"), "w") as f:
        f.write("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print(f"OK: {npages} páginas, {nvis} visuais, {len(modelo.MEASURES)} medidas -> {out}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Uso: python gerar_pbip.py <pasta_de_saida> <pasta_dos_csv_no_seu_PC>\n"
                 "Exemplo (Windows): python gerar_pbip.py EmpresaX_PowerBI C:\\caminho\\para\\empresa-x-powerbi\\data\\")
    main(sys.argv[1], sys.argv[2])
