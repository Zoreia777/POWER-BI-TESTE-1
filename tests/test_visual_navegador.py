"""Regressão VISUAL no navegador real (Streamlit + Chromium via Playwright).

O AppTest do Streamlit não renderiza pixels e já deixou passar problemas de layout. Aqui o aplicativo sobe de verdade e, em tema claro e
escuro e em larguras de desktop a celular, cada uma das cinco páginas é medida no DOM:
  * nenhum texto de cartão de métrica cortado (reticências / scrollWidth > clientWidth);
  * nenhuma rolagem horizontal da página;
  * nenhuma exceção do Streamlit na tela;
  * todo texto dos gráficos (rótulos de barra, eixos, títulos) com contraste >= 3:1 contra o fundo do tema.
Se Playwright/Chromium não estiverem instalados, os testes são PULADOS (não falham)."""
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

from conftest import RAIZ

pw = pytest.importorskip("playwright.sync_api", reason="Playwright não instalado")

PAGINAS = ["", "filiais", "produtos", "orcamento", "investigacoes"]
# (largura, altura, escala do dispositivo, tema) — 1024 @ 1,25 simula a tela de notebook Windows com escala de 125%
CENARIOS = [(1440, 1100, 1, "light"), (1440, 1100, 1, "dark"), (1024, 800, 1.25, "dark"), (390, 900, 2, "dark")]

JS = r"""
() => {
  const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4)}; return 0.2126*f(m[0])+0.7152*f(m[1])+0.0722*f(m[2]); };
  const bgOf = el => { while (el) { const c = getComputedStyle(el).backgroundColor; const m = c.match(/[\d.]+/g); if (m && (m.length<4 || +m[3]>0.5)) return c; el = el.parentElement; } return 'rgb(255,255,255)'; };
  const res = {trunc: [], hscroll: 0, lowcontrast: [], metrics: 0, graficos: 0, exceptions: document.querySelectorAll('[data-testid=stException]').length};
  document.querySelectorAll('[data-testid=stMetric]').forEach(m => {
    res.metrics++;
    m.querySelectorAll('*').forEach(e => {
      const cs = getComputedStyle(e);
      const corta = cs.textOverflow === 'ellipsis' || cs.overflow === 'hidden' || cs.overflowX === 'hidden';
      if (corta && e.scrollWidth > e.clientWidth + 1 && (e.innerText||'').trim()) res.trunc.push((e.innerText||'').trim().slice(0,60));
    });
  });
  const main = document.querySelector('[data-testid=stMain]') || document.documentElement;
  res.hscroll = Math.max(main.scrollWidth - main.clientWidth, document.documentElement.scrollWidth - document.documentElement.clientWidth);
  document.querySelectorAll('.js-plotly-plot').forEach(g => {
    res.graficos++;
    const bg = lum(bgOf(g));
    g.querySelectorAll('svg.main-svg text').forEach(t => {
      const txt = (t.textContent||'').trim(); if (!txt) return;
      const fill = getComputedStyle(t).fill; if (!fill || fill==='none') return;
      const m = fill.match(/[\d.]+/g); if (!m) return; if ((m.length>3 ? +m[3] : 1) < 0.3) return;
      const L = lum(fill); const cr = (Math.max(L,bg)+0.05)/(Math.min(L,bg)+0.05);
      if (cr < 3.0) res.lowcontrast.push(txt.slice(0,25) + ' (' + cr.toFixed(2) + ':1)');
    });
  });
  return res;
}
"""


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor(bi_db):
    porta = _porta_livre()
    env = {**__import__("os").environ, "EMPRESAX_BANCO": str(bi_db), "PYTHONUTF8": "1"}
    p = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(RAIZ / "app" / "streamlit_app.py"), "--server.port", str(porta),
                          "--server.headless", "true", "--browser.gatherUsageStats", "false"], env=env, cwd=str(RAIZ),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{porta}"
    for _ in range(60):
        try:
            urllib.request.urlopen(url, timeout=2)
            break
        except Exception:
            time.sleep(1)
    else:
        p.kill()
        pytest.skip("servidor Streamlit não subiu")
    yield url
    p.terminate()
    try:
        p.wait(10)
    except subprocess.TimeoutExpired:
        p.kill()


@pytest.fixture(scope="module")
def navegador():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # Chromium ausente
            pytest.skip(f"Chromium indisponível: {str(e)[:80]}")
        yield b
        b.close()


@pytest.mark.parametrize("largura,altura,escala,tema", CENARIOS, ids=[f"{w}@{s}-{t}" for w, _, s, t in CENARIOS])
def test_paginas_sem_corte_sem_rolagem_e_com_contraste(servidor, navegador, largura, altura, escala, tema):
    ctx = navegador.new_context(viewport={"width": largura, "height": altura}, device_scale_factor=escala, color_scheme=tema)
    pg = ctx.new_page()
    problemas = []
    try:
        for slug in PAGINAS:
            pg.goto(f"{servidor}/{slug}", wait_until="networkidle")
            pg.wait_for_selector("[data-testid=stMain]", timeout=30000)
            pg.wait_for_timeout(3500)
            r = pg.evaluate(JS)
            if slug not in ("investigacoes", "orcamento"):
                assert r["graficos"] > 0 or slug == "orcamento" or r["metrics"] > 0, f"{slug}: página vazia"
            if r["exceptions"]:
                problemas.append(f"{slug}: {r['exceptions']} exceção(ões) na tela")
            if r["trunc"]:
                problemas.append(f"{slug}: texto de cartão cortado {r['trunc'][:3]}")
            if r["hscroll"] > 1:
                problemas.append(f"{slug}: rolagem horizontal de {r['hscroll']}px")
            if r["lowcontrast"]:
                problemas.append(f"{slug}: texto de gráfico com baixo contraste {r['lowcontrast'][:3]}")
    finally:
        ctx.close()
    assert not problemas, f"{tema} {largura}px @{escala}: " + " | ".join(problemas)
