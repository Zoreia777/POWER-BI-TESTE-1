"""Captura as telas REAIS do aplicativo Streamlit (navegador Chromium via Playwright) em reports/app_evidencias/.

Uso (com o aplicativo já rodando em outro terminal):
    pip install playwright && python -m playwright install chromium     # só para este script; não faz parte de requirements.txt
    streamlit run app/streamlit_app.py            # terminal 1
    python scripts/capturar_evidencias_app.py     # terminal 2  (opcional: --url http://localhost:8501)

O script só LÊ o aplicativo (não escreve no banco). Se alguma página exibir uma exceção do Streamlit, ele aborta com erro.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "reports" / "app_evidencias"
PAGINAS = [("01_visao_geral", "Visão Geral"), ("02_filiais", "Filiais"), ("03_produtos", "Produtos e Margem"),
           ("04_orcamento", "Orçamento"), ("05_investigacoes", "Investigações")]
ABAS_INV = [("05b_smartphone", "Smartphone X Max"), ("05c_pvm", "Preço, volume e mix"), ("05d_achados", "Todos os achados")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8501")
    url = ap.parse_args().url
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright não instalado (veja o topo deste arquivo).", file=sys.stderr)
        return 2
    SAIDA.mkdir(parents=True, exist_ok=True)

    def sem_excecao(pg, onde):
        n = pg.locator('[data-testid="stException"]').count()
        if n:
            raise SystemExit(f"Exceção do Streamlit em {onde}: {pg.locator('[data-testid=stException]').first.inner_text()[:300]}")

    def ir(pg, nome):
        pg.get_by_role("link", name=nome).first.click()
        pg.wait_for_timeout(3500)
        sem_excecao(pg, nome)

    def foto(pg, arq):
        pg.screenshot(path=str(SAIDA / f"{arq}.png"))
        print("ok", arq)

    with sync_playwright() as p:
        b = p.chromium.launch()
        # viewport alto: o Streamlit rola dentro de um contêiner, então full_page não captura a página inteira
        pg = b.new_page(viewport={"width": 1440, "height": 2400})
        pg.goto(url, wait_until="networkidle")
        pg.wait_for_timeout(2500)
        for arq, nome in PAGINAS:
            ir(pg, nome)
            foto(pg, arq)
        for arq, aba in ABAS_INV:
            pg.get_by_role("tab", name=aba).click()
            pg.wait_for_timeout(3000)
            sem_excecao(pg, aba)
            foto(pg, arq)
        ir(pg, "Visão Geral")
        pg.get_by_label("Filiais").click()
        pg.keyboard.type("Porto Alegre")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(3500)
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(800)
        sem_excecao(pg, "filtro Porto Alegre")
        foto(pg, "06_filtro_porto_alegre")
        m = b.new_page(viewport={"width": 390, "height": 2000})
        m.goto(url, wait_until="networkidle")
        m.wait_for_timeout(3500)
        sem_excecao(m, "mobile")
        foto(m, "08_mobile_visao_geral")
        b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
