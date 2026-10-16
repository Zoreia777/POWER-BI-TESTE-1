"""Etapa 5 — execução REAL da interface com streamlit.testing (AppTest): cada página roda sem exceção, premissas aparecem onde são
necessárias, filtros mudam os números, estados vazios não mostram indicadores, e falhas do banco geram mensagem clara.
Limite: AppTest executa o script e inspeciona os elementos, mas NÃO renderiza pixels; a conferência visual é feita com o servidor e um navegador."""
import sys
from datetime import date

import pytest
import plotly.graph_objects as go
import streamlit as st
from streamlit.testing.v1 import AppTest

from conftest import RAIZ
from empresax.app import graficos as G, textos

sys.path.insert(0, str(RAIZ / "app"))
APP = str(RAIZ / "app" / "streamlit_app.py")


@pytest.fixture(autouse=True)
def _limpa_caches():
    st.cache_data.clear()
    st.cache_resource.clear()
    yield


@pytest.fixture()
def banco(bi_db, monkeypatch):
    monkeypatch.setenv("EMPRESAX_BANCO", str(bi_db))
    return bi_db


def _pagina(nome, ini, fim, fil, prod, can):
    """Roda UMA página (função render) com filtros fixos. Executada pelo AppTest (por isso os imports ficam aqui dentro)."""
    import importlib
    from datetime import date as d
    from componentes import Contexto
    from empresax.app.base import abrir, assinatura, caminho_banco
    from empresax.app.consultas import Repositorio
    from empresax.app.filtros import Filtros
    caminho = caminho_banco()
    repo = Repositorio(abrir(caminho))
    f = repo.validar(Filtros(d.fromisoformat(ini), d.fromisoformat(fim), tuple(fil), tuple(prod), tuple(can)))
    nomes = dict(filiais="teste", produtos="teste", canais="teste")
    importlib.import_module(f"paginas.{nome}").render(Contexto(repo, assinatura(caminho), f, nomes))


def rodar(nome, ini="2026-01-01", fim="2026-09-01", fil=(), prod=(), can=()):
    at = AppTest.from_function(_pagina, args=(nome, ini, fim, fil, prod, can), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def texto(at) -> str:
    partes = [m.value for m in at.markdown] + [c.value for c in at.caption] + [e.value for e in at.error] + [w.value for w in at.warning] + [i.value for i in at.info] + [s.value for s in at.success]
    partes += [e.label for e in at.expander] + [m.label for m in at.metric] + [m.value for m in at.metric] + [m.delta or "" for m in at.metric]
    return "\n".join(str(p) for p in partes).replace("\\$", "$")


PAGINAS = ["visao_geral", "filiais", "produtos", "orcamento", "investigacoes"]


# ===================================================================== 1. cada página executa
@pytest.mark.parametrize("nome", PAGINAS)
def test_pagina_roda_sem_excecao_e_tem_titulo(banco, nome):
    at = rodar(nome)
    assert at.title and len(texto(at)) > 200


@pytest.mark.parametrize("nome", PAGINAS)
def test_pagina_roda_com_filtros_combinados(banco, nome):
    at = rodar(nome, "2025-03-01", "2026-06-01", fil=(5, 2), prod=(10, 1, 3), can=(1, 4))
    assert not at.exception


@pytest.mark.parametrize("nome", PAGINAS)
def test_pagina_roda_em_periodo_de_um_mes_e_no_primeiro_periodo(banco, nome):
    rodar(nome, "2026-09-01", "2026-09-01")
    rodar(nome, "2024-01-01", "2024-03-01")


# ===================================================================== 2. premissas onde necessárias
PREMISSAS_POR_PAGINA = {"visao_geral": ["PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-MRG-01", "PN-SIN-01"], "filiais": ["PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-SIN-01"],
                        "produtos": ["PN-DEV-01", "PN-DEV-02", "PN-MRG-01", "PN-SIN-01"], "orcamento": ["PN-ORC-01", "PN-SIN-01"],
                        "investigacoes": ["PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-MRG-01", "PN-SIN-01"]}


@pytest.mark.parametrize("nome", PAGINAS)
def test_premissas_aparecem_na_pagina(banco, nome):
    t = texto(rodar(nome))
    for p in PREMISSAS_POR_PAGINA[nome]:
        assert p in t, (nome, p)


def test_premissas_aparecem_mesmo_sem_resultados(banco):
    t = texto(rodar("visao_geral", "2024-01-01", "2024-12-01", fil=(7,)))
    assert "PN-DEV-01" in t and "PN-DEV-03" in t


def test_receita_ajustada_sempre_rotulada_como_provisoria_e_reconciliada(banco):
    at = rodar("visao_geral")
    assert any("provisória" in m.label for m in at.metric)
    t = texto(at)
    assert "registrada" in t.lower() and "devoluções" in t.lower() and "Diferença de reconciliação" in t and "R$ 0,00" in t
    assert "não é lucro líquido contábil" in t.lower()


def test_nenhuma_data_de_devolucao_e_exibida(banco):
    t = texto(rodar("visao_geral")).lower()
    assert "data de devolução" in t and "nenhuma data de estorno é inventada" in t


def test_hipoteses_aparecem_com_aviso_de_nao_comprovada(banco):
    at = rodar("investigacoes")
    t = texto(at)
    assert "HIPÓTESE" in t and "NÃO comprovada" in t
    assert "PADRÃO PROGRAMADO" in t
    assert "Padrão programado (P06/P07)" in t


def test_estudo_smartphone_mostra_numeros_do_relatorio(banco):
    t = texto(rodar("investigacoes"))
    for esperado in ("R$ 5.290", "+37,1%", "-13,7%", "607"):
        assert esperado in t, esperado
    assert "NÃO é recomendação de preço" in t


def test_estudo_porto_alegre_mostra_pedidos_linhas_e_receita_por_linha(banco):
    at = rodar("investigacoes")
    rot = {m.label for m in at.metric}
    assert {"Pedidos", "Linhas de pedido", "Receita por linha", "Receita ajustada"} <= rot
    t = texto(at)
    assert "-48,9%" in t and "-6,6%" in t and "+2,9%" in t and "-50,4%" in t


# ===================================================================== 3. filtros mudam números e estados vazios
def _metrica(at, rotulo):
    return next(m.value for m in at.metric if m.label.startswith(rotulo))


def test_valores_da_visao_geral_e_filtro_de_filial(banco):
    assert _metrica(rodar("visao_geral"), "Receita ajustada") == "R$ 41,29 mi"
    assert _metrica(rodar("visao_geral", fil=(5,)), "Receita ajustada") == "R$ 2,97 mi"
    assert _metrica(rodar("visao_geral", prod=(10,)), "Pedidos") != _metrica(rodar("visao_geral"), "Pedidos")


def test_filtro_sem_resultado_nao_mostra_indicadores(banco):
    at = rodar("visao_geral", "2024-01-01", "2024-12-01", fil=(7,))
    assert any(textos.SEM_RESULTADO in w.value for w in at.warning)
    assert not any("Receita ajustada" in m.label for m in at.metric)


@pytest.mark.parametrize("nome", ["filiais", "produtos"])
def test_outras_paginas_tambem_tratam_recorte_vazio(banco, nome):
    at = rodar(nome, "2024-01-01", "2024-12-01", fil=(7,))
    assert any(textos.SEM_RESULTADO in w.value for w in at.warning)


def test_produto_ou_canal_escondem_despesas_e_avisam(banco):
    at = rodar("visao_geral", prod=(10,))
    assert any(textos.DESPESAS_INDISPONIVEIS in i.value for i in at.info)
    assert not any(m.label.startswith("Resultado operacional") for m in at.metric)
    at2 = rodar("filiais", can=(2,))
    assert any(textos.DESPESAS_INDISPONIVEIS in i.value for i in at2.info)


def test_orcamento_avisa_que_ignora_produto_e_canal(banco):
    assert any(textos.ORCAMENTO_FILTROS in i.value for i in rodar("orcamento", prod=(1,)).info)
    assert not any(textos.ORCAMENTO_FILTROS in i.value for i in rodar("orcamento").info)


def test_orcamento_mostra_execucao_correta_e_leitura_ingenua(banco):
    at = rodar("orcamento")
    assert _metrica(at, "Execução") == "100,5%"
    t = texto(at)
    assert "71,8%" in t and "não existe" in t and "R$ 19,67 mi" in t


def test_orcamento_vazio(banco):
    at = rodar("orcamento", "2024-01-01", "2024-03-01", fil=(7,))
    assert any("Não há orçamento" in w.value for w in at.warning)


def test_comparacao_anual_so_com_periodo_equivalente(banco):
    at = rodar("visao_geral")
    delta = next(m.delta for m in at.metric if m.label.startswith("Receita ajustada"))
    assert "+20,4%" in delta and "jan/25 a set/25" in delta
    at24 = rodar("visao_geral", "2024-01-01", "2024-06-01")
    assert next(m.delta for m in at24.metric if m.label.startswith("Receita ajustada")) in (None, "")
    assert "Sem comparação anual" in texto(at24)


def test_pvm_da_pagina_reconcilia(banco):
    at = rodar("investigacoes")
    t = texto(at)
    assert "resíduo R$ 0,00" in t


def test_pvm_base_anterior_aos_dados_gera_aviso(banco):
    at = rodar("investigacoes", "2024-01-01", "2024-06-01")
    assert any("começa antes dos dados" in w.value for w in at.warning)


# ===================================================================== 4. aplicativo completo (navegação, filtros da barra lateral, falhas)
def test_app_completo_executa_com_cinco_paginas(banco):
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception and not at.error
    fonte = open(APP, encoding="utf-8").read()
    for titulo in ("Visão Geral", "Filiais", "Produtos e Margem", "Orçamento", "Investigações"):
        assert f'title="{titulo}"' in fonte
    assert _metrica(at, "Receita ajustada") == "R$ 41,29 mi"
    assert "Fonte: warehouse DuckDB" in texto(at) and "Dados fictícios" in texto(at) and "set/26" in texto(at)


def test_app_filtro_da_barra_lateral_muda_o_resultado(banco):
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.multiselect(key="f_filial").set_value(["Porto Alegre"]).run()
    assert not at.exception
    assert _metrica(at, "Receita ajustada") == "R$ 2,97 mi"
    assert "filiais: Porto Alegre" in texto(at)


def test_app_periodo_personalizado_e_recorte_vazio(banco):
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.selectbox(key="atalho").set_value("Personalizado").run()
    at.select_slider(key="meses").set_value((date(2024, 1, 1), date(2024, 12, 1))).run()
    at.multiselect(key="f_filial").set_value(["Salvador"]).run()
    assert not at.exception
    assert any(textos.SEM_RESULTADO in w.value for w in at.warning)


def test_app_sem_banco_mostra_mensagem_clara(monkeypatch, tmp_path):
    monkeypatch.setenv("EMPRESAX_BANCO", str(tmp_path / "nao_existe.duckdb"))
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert at.error and "run_etl.py" in at.error[0].value and "run_powerbi.py" in at.error[0].value


def test_app_banco_sem_views_bi_orienta(monkeypatch, etl):
    monkeypatch.setenv("EMPRESAX_BANCO", str(etl["cfg"].arquivo_banco))
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception and "run_powerbi.py" in at.error[0].value


def test_abrir_o_app_nao_altera_o_banco_nem_os_csvs(banco, etl):
    s0 = (banco.stat().st_mtime_ns, banco.stat().st_size)
    AppTest.from_file(APP, default_timeout=120).run()
    assert (banco.stat().st_mtime_ns, banco.stat().st_size) == s0
    assert etl["csv_inalterados"] is True


# ===================================================================== 5. gráficos
def test_graficos_vazios_tem_mensagem_e_nao_numeros():
    import pandas as pd
    f = G.tendencia(pd.DataFrame(columns=["mes", "ajustada", "registrada", "devolucoes", "margem_bruta"]))
    assert isinstance(f, go.Figure) and "Sem vendas" in f.layout.annotations[0].text
    assert "Sem dados" in G.ranking(pd.DataFrame({"nome": [], "x": []}), "x", "t").layout.annotations[0].text
    assert "base comparável" in G.mapa_yoy(pd.DataFrame()).layout.annotations[0].text


def test_graficos_usam_formato_ptbr_e_unidades(banco):
    import pandas as pd
    from empresax.app.base import abrir
    from empresax.app.consultas import Repositorio
    from empresax.app.filtros import Filtros
    from empresax.app import casos
    repo = Repositorio(abrir(banco))
    f = Filtros(date(2026, 1, 1), date(2026, 9, 1))
    figs = [G.tendencia(repo.serie_mensal(f)), G.ranking(repo.por_dimensao(f, "filial"), "ajustada", "t"), G.ranking(repo.por_dimensao(f, "filial"), "margem_bruta", "t", "pct"),
            G.mapa_yoy(repo.matriz_yoy_filial(f)), G.bolhas_produtos(repo.por_dimensao(f, "produto")), G.execucao_orcamento(repo.orcamento_por(f, "departamento"), "t"),
            G.curva_orcamento(repo.orcamento_mensal(f)), G.sp_preco_custo(casos.smartphone_serie(repo)), G.sp_linhas_negativas(casos.smartphone_serie(repo)),
            G.pa_serie(casos.porto_alegre_serie(repo), pd.Timestamp("2026-02-01"))]
    res, por = repo.pvm_periodo(f, f.deslocado(-12))
    figs += [G.cascata_pvm(res, "t", "a", "b"), G.contribuicao_produtos(por)]
    for fig in figs:
        assert fig.layout.separators == ",." and fig.layout.title.text
        for tr in fig.data:
            h = getattr(tr, "hovertemplate", None) or ""
            assert "nan" not in h.lower()
            assert h == "" or "R$" in h or "%" in h or "Linhas" in h or "Variação" in h
            for attr in ("text",):
                v = getattr(tr, attr, None)
                if v is not None and not isinstance(v, str):
                    assert not any("nan" in str(x).lower() for x in v)


def test_cascata_fecha_na_receita_do_periodo_atual(banco):
    from empresax.app.base import abrir
    from empresax.app.consultas import Repositorio
    from empresax.app.filtros import Filtros
    repo = Repositorio(abrir(banco))
    f = Filtros(date(2026, 1, 1), date(2026, 9, 1), (5,))
    res, _ = repo.pvm_periodo(f, f.deslocado(-12))
    w = G.cascata_pvm(res, "t", "a", "b").data[0]
    assert abs(sum(w.y[:-1]) - w.y[-1]) < 1                 # base + efeitos = receita ajustada atual (total)
    assert w.measure[0] == "absolute" and w.measure[-1] == "total"


def test_textos_de_premissas_completos():
    assert set(textos.PREMISSAS) >= {"PN-DEV-01", "PN-DEV-02", "PN-DEV-03", "PN-MRG-01", "PN-ORC-01", "PN-SIN-01"}
    for k, v in textos.PREMISSAS.items():
        assert v.startswith(f"**{k}**")


# ===================================================================== 6. regressões encontradas na inspeção visual
@pytest.mark.parametrize("nome", PAGINAS)
def test_cifrao_nao_vira_formula_markdown(banco, nome):
    """Dois 'R$' sem escape no mesmo texto são lidos como LaTeX pelo Streamlit (achado da conferência visual). Todo texto deve ter no máximo 1 '$' sem escape."""
    import re
    at = rodar(nome, "2026-01-01", "2026-09-01")
    elementos = list(at.markdown) + list(at.caption) + list(at.success) + list(at.info) + list(at.warning) + list(at.error)
    for el in elementos:
        livres = re.findall(r"(?<!\\)\$", str(el.value))
        assert len(livres) <= 1, str(el.value)[:200]


def test_barras_tem_espaco_para_o_rotulo_da_maior():
    import pandas as pd
    d = pd.DataFrame({"nome": ["A", "B"], "x": [100.0, 40.0]})
    fig = G.ranking(d, "x", "t")
    assert fig.layout.xaxis.range[1] > 100


def test_cascata_amplia_eixo_e_avisa_quando_efeitos_sao_pequenos(banco):
    from empresax.app.base import abrir
    from empresax.app.consultas import Repositorio
    from empresax.app.filtros import Filtros
    repo = Repositorio(abrir(banco))
    f = Filtros(date(2026, 1, 1), date(2026, 9, 1))
    res, _ = repo.pvm_periodo(f, f.deslocado(-12))
    fig = G.cascata_pvm(res, "t", "a", "b")
    assert fig.layout.yaxis.range[0] > 0 and any("não começa em zero" in a.text for a in fig.layout.annotations)


def test_investigacoes_nao_repete_o_bloco_de_premissas(banco):
    at = rodar("investigacoes")
    assert sum(1 for e in at.expander if e.label.startswith("Premissas e limitações")) == 1
