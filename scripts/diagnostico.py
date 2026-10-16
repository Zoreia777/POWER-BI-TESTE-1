#!/usr/bin/env python3
"""Diagnóstico dos dados brutos da Empresa X (Projeto 01 · Etapa 1).

Somente LEITURA: não altera nenhum arquivo em data/. Gera docs/DIAGNOSTICO.md
com resultados medidos (nada é escrito à mão), e devolve a lista de checagens
para uso pelos testes.

    python scripts/diagnostico.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
SAIDA = RAIZ / "docs" / "DIAGNOSTICO.md"

# chave primária declarada (None = tabela fato sem PK natural, usa chave composta)
PK = {
    "dim_calendario": ["data"], "dim_canal": ["id_canal"],
    "dim_categoria_despesa": ["id_categoria_despesa"], "dim_cliente": ["id_cliente"],
    "dim_departamento": ["id_departamento"], "dim_filial": ["id_filial"],
    "dim_produto": ["id_produto"], "dim_vendedor": ["id_vendedor"],
    "fact_vendas": ["id_venda"], "fact_despesas": ["id_despesa"],
    "fact_orcamento": ["mes", "id_departamento", "id_categoria_despesa", "id_filial"],
    "fact_metas_vendas": ["mes", "id_filial"],
    "fact_rh_mensal": ["data_referencia", "id_departamento", "id_filial"],
}
# (tabela_fato, coluna, dimensao, coluna_dimensao) - relacionamentos A VALIDAR
FKS = [
    ("fact_vendas", "id_cliente", "dim_cliente", "id_cliente"),
    ("fact_vendas", "id_produto", "dim_produto", "id_produto"),
    ("fact_vendas", "id_filial", "dim_filial", "id_filial"),
    ("fact_vendas", "id_vendedor", "dim_vendedor", "id_vendedor"),
    ("fact_vendas", "id_canal", "dim_canal", "id_canal"),
    ("fact_vendas", "data", "dim_calendario", "data"),
    ("fact_despesas", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_despesas", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
    ("fact_despesas", "id_filial", "dim_filial", "id_filial"),
    ("fact_despesas", "data", "dim_calendario", "data"),
    ("fact_orcamento", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_orcamento", "id_categoria_despesa", "dim_categoria_despesa", "id_categoria_despesa"),
    ("fact_orcamento", "id_filial", "dim_filial", "id_filial"),
    ("fact_metas_vendas", "id_filial", "dim_filial", "id_filial"),
    ("fact_rh_mensal", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_rh_mensal", "id_filial", "dim_filial", "id_filial"),
]


def carregar() -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_csv(p) for p in sorted(DADOS.glob("*.csv"))}


def checagens(T: dict[str, pd.DataFrame]) -> dict:
    """Calcula todas as métricas do diagnóstico e devolve em um dicionário."""
    R: dict = {}
    R["tabelas"] = {
        n: {
            "linhas": len(d), "colunas": d.shape[1],
            "duplicadas": int(d.duplicated().sum()),
            "pk_duplicada": int(d.duplicated(PK[n]).sum()),
            "nulos": {c: int(k) for c, k in d.isna().sum().items() if k},
        } for n, d in T.items()
    }
    R["fk_orfas"] = {
        f"{a}.{b} -> {c}.{e}": int((~T[a][b].isin(T[c][e])).sum()) for a, b, c, e in FKS
    }
    v = T["fact_vendas"]
    tol = 0.02
    R["fin"] = {
        "bruta_ne_qtd_x_preco": int(((v.quantidade * v.preco_unitario - v.receita_bruta).abs() > tol).sum()),
        "desconto_ne_bruta_x_pct": int(((v.receita_bruta * v.desconto_pct - v.desconto_valor).abs() > tol).sum()),
        "liquida_ne_bruta_menos_desc_imp": int(
            ((v.receita_bruta - v.desconto_valor - v.impostos_valor - v.receita_liquida).abs() > tol).sum()),
        "valores_nao_positivos": int((v[["quantidade", "preco_unitario", "receita_liquida", "custo_total"]] <= 0).sum().sum()),
        "linhas_margem_negativa": int((v.custo_total > v.receita_liquida).sum()),
        "linhas_devolvidas": int((v.status == "Devolvido").sum()),
        "receita_devolvida": float(v.loc[v.status == "Devolvido", "receita_liquida"].sum()),
        "receita_liquida_total": float(v.receita_liquida.sum()),
        "preco_diferente_da_lista": int(
            (v.merge(T["dim_produto"][["id_produto", "preco_lista"]], on="id_produto")
             .eval("preco_unitario != preco_lista")).sum()),
    }
    # granularidade
    R["gran"] = {
        "pedidos": int(v.id_pedido.nunique()),
        "max_linhas_por_pedido": int(v.groupby("id_pedido").size().max()),
        "pedido_produto_duplicado": int(v.duplicated(["id_pedido", "id_produto"]).sum()),
        "pedido_com_atributos_divergentes": int(
            (v.groupby("id_pedido")[["id_cliente", "id_filial", "data"]].nunique() > 1).any(axis=1).sum()),
    }
    # coberturas temporais
    e, o, m, r = T["fact_despesas"], T["fact_orcamento"], T["fact_metas_vendas"], T["fact_rh_mensal"]
    R["cobertura"] = {
        "vendas": (v.data.min(), v.data.max()),
        "despesas": (e.data.min(), e.data.max()),
        "orcamento": (o.mes.min(), o.mes.max()),
        "metas": (m.mes.min(), m.mes.max()),
        "rh": (r.data_referencia.min(), r.data_referencia.max()),
    }
    ult = e.data.str[:7].max()
    R["orc_sem_realizado"] = {
        "linhas_orcamento_apos_ultimo_mes_realizado": int((o.mes.str[:7] > ult).sum()),
        "linhas_orcamento_ate_ultimo_mes_sem_despesa": int(
            (~o[o.mes.str[:7] <= ult].set_index(["mes"] + PK["fact_orcamento"][1:]).index.isin(
                e.assign(mes=e.data.str[:7] + "-01").groupby(["mes", "id_departamento", "id_categoria_despesa", "id_filial"]).size().index)).sum()),
        "ultimo_mes_realizado": ult,
    }
    # integridade temporal
    vv = v.merge(T["dim_filial"][["id_filial", "data_abertura"]], on="id_filial").merge(
        T["dim_cliente"][["id_cliente", "data_cadastro"]], on="id_cliente")
    R["temporal"] = {
        "vendas_antes_abertura_filial": int((vv.data < vv.data_abertura).sum()),
        "vendas_antes_cadastro_cliente": int((vv.data < vv.data_cadastro).sum()),
        "clientes_sem_venda": int((~T["dim_cliente"].id_cliente.isin(v.id_cliente)).sum()),
    }
    # sazonalidade / quedas
    mm = v.assign(ym=v.data.str[:7]).groupby("ym").receita_liquida.sum()
    var = mm.pct_change()
    R["quedas_mom_maiores_15pct"] = {k: round(float(x), 3) for k, x in var[var < -0.15].items()}
    d = v[v.status == "Entregue"].merge(T["dim_produto"][["id_produto", "produto"]], on="id_produto") \
        .groupby("produto")[["receita_liquida", "custo_total"]].sum()
    d["margem"] = 1 - d.custo_total / d.receita_liquida
    R["menores_margens"] = d.sort_values("margem").head(3)["margem"].round(3).to_dict()
    return R


def para_markdown(R: dict) -> str:
    L = ["# Diagnóstico dos dados brutos — Empresa X", "",
         "> Gerado por `scripts/diagnostico.py`. Todos os números abaixo foram medidos nos CSVs de `data/`; "
         "os dados são **fictícios** (gerados com semente fixa por `scripts/gerar_dados.py`).", "",
         "## 1. Tabelas, chaves e qualidade", "",
         "| Tabela | Linhas | Colunas | Linhas duplicadas | Chave duplicada | Nulos |", "|---|---:|---:|---:|---:|---|"]
    for n, t in R["tabelas"].items():
        L.append(f"| {n} | {t['linhas']:,} | {t['colunas']} | {t['duplicadas']} | {t['pk_duplicada']} | {t['nulos'] or '—'} |")
    L += ["", "## 2. Relacionamentos validados (registros órfãos)", "", "| Relacionamento | Órfãos |", "|---|---:|"]
    L += [f"| {k} | {x} |" for k, x in R["fk_orfas"].items()]
    f, g = R["fin"], R["gran"]
    L += ["", "## 3. Consistência financeira (`fact_vendas`, tolerância R$ 0,02)", "",
          f"- receita_bruta ≠ quantidade × preço: **{f['bruta_ne_qtd_x_preco']}**",
          f"- desconto_valor ≠ bruta × desconto_pct: **{f['desconto_ne_bruta_x_pct']}**",
          f"- receita_líquida ≠ bruta − desconto − impostos: **{f['liquida_ne_bruta_menos_desc_imp']}**",
          f"- valores ≤ 0 (qtd, preço, receita, custo): **{f['valores_nao_positivos']}**",
          f"- linhas com margem negativa (custo > receita líquida): **{f['linhas_margem_negativa']:,}**",
          f"- linhas com preço ≠ preço de lista: **{f['preco_diferente_da_lista']:,}**",
          f"- linhas `Devolvido`: **{f['linhas_devolvidas']:,}** — receita líquida associada R$ {f['receita_devolvida']:,.2f} "
          f"({f['receita_devolvida'] / f['receita_liquida_total']:.2%} do total), **registrada com sinal positivo**", "",
          "## 4. Granularidade", "",
          f"- `fact_vendas`: 1 linha por **item de pedido** ({g['pedidos']:,} pedidos, até {g['max_linhas_por_pedido']} itens cada); "
          f"pedido+produto duplicado: {g['pedido_produto_duplicado']}; pedidos com cliente/filial/data divergentes: {g['pedido_com_atributos_divergentes']}",
          "- `fact_despesas`: 1 linha por lançamento (data × departamento × categoria × filial × fornecedor)",
          "- `fact_orcamento`: mensal × departamento × categoria × filial · `fact_metas_vendas`: mensal × filial · `fact_rh_mensal`: fim de mês × departamento × filial",
          "", "## 5. Cobertura temporal", "", "| Fato | Início | Fim |", "|---|---|---|"]
    L += [f"| {k} | {a} | {b} |" for k, (a, b) in R["cobertura"].items()]
    o = R["orc_sem_realizado"]
    t = R["temporal"]
    L += ["", f"- Último mês realizado: **{o['ultimo_mes_realizado']}**. Linhas de orçamento posteriores a ele: **{o['linhas_orcamento_apos_ultimo_mes_realizado']}** "
          "(comparar orçado × realizado exige limitar ao período realizado).",
          f"- Linhas de orçamento até o último mês realizado sem despesa correspondente: **{o['linhas_orcamento_ate_ultimo_mes_sem_despesa']}**.",
          f"- Vendas antes da abertura da filial: {t['vendas_antes_abertura_filial']} · antes do cadastro do cliente: {t['vendas_antes_cadastro_cliente']} · clientes sem nenhuma venda: {t['clientes_sem_venda']}",
          "", "## 6. Pontos de atenção para análise (observações, ainda não explicações)", "",
          f"- Quedas mensais de receita > 15 %: {R['quedas_mom_maiores_15pct']}",
          f"- Menores margens por produto (apenas `Entregue`): {R['menores_margens']}"]
    return "\n".join(L) + "\n"


def main() -> None:
    R = checagens(carregar())
    SAIDA.write_text(para_markdown(R), encoding="utf-8")
    print(f"Diagnóstico gravado em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
