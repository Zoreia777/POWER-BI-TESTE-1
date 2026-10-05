#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta o protótipo interativo do dashboard (HTML único, sem servidor).

Lê o banco SQLite, agrega os números e injeta em scripts/prototipo_template.html,
gerando docs/prototipo_dashboard.html. É só uma prévia do que será construído no
Power BI, usando exatamente os mesmos dados.

    python scripts/gerar_prototipo.py
"""
import json
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "database" / "empresa_x.db"
MODELO = Path(__file__).resolve().parent / "prototipo_template.html"
SAIDA = RAIZ / "docs" / "prototipo_dashboard.html"

con = sqlite3.connect(BANCO)

filiais = [r[0] for r in con.execute("SELECT filial FROM dim_filial ORDER BY id_filial")]
cats = ["Eletrônicos", "Escritório", "Casa & Conforto", "Software & Assinaturas", "Serviços"]
canais = [r[0] for r in con.execute("SELECT canal FROM dim_canal ORDER BY id_canal")]
grupos = [r[0] for r in con.execute(
    "SELECT grupo_dre FROM dim_categoria_despesa GROUP BY grupo_dre ORDER BY MIN(ordem_dre)")]

meses = [r[0] for r in con.execute(
    "SELECT DISTINCT ano_mes FROM dim_calendario ORDER BY ano_mes")]
mi = {m: i for i, m in enumerate(meses)}
corte = max(r[0] for r in con.execute(
    "SELECT DISTINCT ano_mes FROM dim_calendario WHERE realizado = 1"))

vendas = []
for ym, f, cat, canal, br, ds, im, rl, cmv in con.execute("""
    SELECT substr(v.data,1,7), v.id_filial, p.categoria, v.id_canal,
           SUM(v.receita_bruta), SUM(v.desconto_valor), SUM(v.impostos_valor),
           SUM(v.receita_liquida), SUM(v.custo_total)
    FROM fact_vendas v JOIN dim_produto p USING (id_produto)
    WHERE v.status = 'Entregue'
    GROUP BY 1, 2, 3, 4"""):
    vendas.append([mi[ym], f - 1, cats.index(cat), canal - 1,
                   round(br), round(ds), round(im), round(rl), round(cmv)])

tipo = {"Fixa": 0, "Variável": 1}
desp = {}
for ym, f, g, t, v in con.execute("""
    SELECT substr(d.data,1,7), d.id_filial, c.grupo_dre, c.tipo_custo, SUM(d.valor)
    FROM fact_despesas d JOIN dim_categoria_despesa c USING (id_categoria_despesa)
    GROUP BY 1, 2, 3, 4"""):
    desp.setdefault((mi[ym], f - 1, grupos.index(g), tipo[t]), [0, 0])[0] = round(v)
for ym, f, g, t, v in con.execute("""
    SELECT substr(o.mes,1,7), o.id_filial, c.grupo_dre, c.tipo_custo, SUM(o.valor_orcado)
    FROM fact_orcamento o JOIN dim_categoria_despesa c USING (id_categoria_despesa)
    GROUP BY 1, 2, 3, 4"""):
    desp.setdefault((mi[ym], f - 1, grupos.index(g), tipo[t]), [0, 0])[1] = round(v)
despesas = [[*k, *v] for k, v in sorted(desp.items())]

metas = [[mi[ym], f - 1, round(v)] for ym, f, v in con.execute(
    "SELECT substr(mes,1,7), id_filial, meta_receita_liquida FROM fact_metas_vendas")]

dados = {"meses": meses, "corteIdx": mi[corte], "filiais": filiais, "cats": cats,
         "canais": canais, "grupos": grupos, "vendas": vendas, "desp": despesas, "metas": metas}

html = MODELO.read_text(encoding="utf-8").replace("/*__DADOS__*/null", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text("<!doctype html>\n<html lang=\"pt-BR\"><head>\n" + html.split("<!--FIM-HEAD-->")[0]
                 + "</head><body>\n" + html.split("<!--FIM-HEAD-->")[1] + "\n</body></html>\n", encoding="utf-8")
print("linhas:", len(vendas), len(despesas), len(metas), "| tamanho:", SAIDA.stat().st_size // 1024, "KB")
