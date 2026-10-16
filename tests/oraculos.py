"""Oráculos independentes: recalculam cada análise direto dos CSVs originais (pandas / Python puro)
SEM usar o banco, para comparar com o resultado do SQL. Levantam AssertionError quando divergem."""
import numpy as np
import pandas as pd

MESES_FIM = "2026-09-01"


def _near(a, b, tol=0.01):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    assert a.shape == b.shape, (a.shape, b.shape)
    assert np.nanmax(np.abs(np.where(np.isnan(a) & np.isnan(b), 0, a - b))) <= tol, np.nanmax(np.abs(a - b))
    assert (np.isnan(a) == np.isnan(b)).all()


def vendas(csv_):
    v = csv_["fact_vendas"].copy()
    v["mes"] = v.data.str[:7] + "-01"
    v["ent"] = np.where(v.status == "Entregue", v.receita_liquida, 0.0)
    v["dev"] = np.where(v.status == "Devolvido", v.receita_liquida, 0.0)
    v["custo_ent"] = np.where(v.status == "Entregue", v.custo_total, 0.0)
    return v


def meses(csv_):
    cal = csv_["dim_calendario"]
    return sorted(m for m in cal.primeiro_dia_mes.unique() if m <= MESES_FIM)


def status_e_pct(atual, base):
    if base is None or (isinstance(base, float) and np.isnan(base)):
        return "sem_base", np.nan
    if base == 0:
        return ("sem_atividade" if atual == 0 else "base_zerada"), np.nan
    return "comparavel", atual / base - 1


# ------------------------------------------------------------------ 01
def o_01a(df, csv_):
    v = vendas(csv_)
    g = v.groupby("mes")[["receita_liquida", "ent", "dev"]].sum().reindex(meses(csv_), fill_value=0.0)
    assert list(df.mes) == list(g.index)
    _near(df.receita_registrada, g.receita_liquida); _near(df.vendas_entregues, g.ent); _near(df.devolucoes, g.dev)
    _near(df.receita_ajustada, g.ent); _near(df.diferenca_reconciliacao, np.zeros(len(g)))
    ent = g.ent.values
    for i in range(len(ent)):
        for lag, st, pc in ((1, "status_mom", "variacao_mom_pct"), (12, "status_yoy", "variacao_yoy_pct")):
            s, p = status_e_pct(ent[i], ent[i - lag] if i >= lag else None)
            assert df[st].iloc[i] == s, (i, st)
            if s == "comparavel":
                assert abs(df[pc].iloc[i] - p) < 1e-6
            else:
                assert np.isnan(df[pc].iloc[i])


def o_01b(df, csv_):
    v = vendas(csv_); v["ano"] = v.mes.str[:4].astype(int); v["m"] = v.mes.str[5:7].astype(int)
    ytd = v[v.m <= 9].groupby("ano").ent.sum()
    assert list(df.ano) == [2024, 2025, 2026]
    _near(df.receita_ajustada_ytd, ytd.values)
    esp = [np.nan, ytd[2025] / ytd[2024] - 1, ytd[2026] / ytd[2025] - 1]
    _near(df.variacao_yoy_ytd_pct.values, esp, 1e-6)
    assert list(df.ano_completo) == [True, True, False] and list(df.status_yoy_ytd) == ["sem_base", "comparavel", "comparavel"]


# ------------------------------------------------------------------ 02
def o_02a(df, csv_):
    v = vendas(csv_)
    g = v.groupby("id_produto").ent.sum().reindex(csv_["dim_produto"].id_produto, fill_value=0.0).reset_index()
    g = g.sort_values(["ent", "id_produto"], ascending=[False, True]).reset_index(drop=True)
    g["part"] = g.ent / g.ent.sum(); g["acum"] = g.part.cumsum()
    g["classe"] = np.where(g.acum - g.part < 0.80, "A", np.where(g.acum - g.part < 0.95, "B", "C"))
    assert list(df.id_produto) == list(g.id_produto) and list(df.ranking) == list(range(1, len(g) + 1))
    _near(df.receita_ajustada, g.ent); _near(df.participacao_pct, g.part, 1e-6)
    assert list(df.classe_abc) == list(g.classe)


# ------------------------------------------------------------------ 03
def o_03a(df, csv_, piso):
    v = vendas(csv_)
    d = csv_["dim_produto"][["id_produto", "produto"]]
    ent = v[v.status == "Entregue"]
    g = ent.groupby("id_produto").agg(l=("id_venda", "count"), rec=("receita_liquida", "sum"), cus=("custo_total", "sum"))
    g = d.merge(g, on="id_produto", how="left").fillna({"l": 0, "rec": 0, "cus": 0})
    g = g[g.l >= piso].copy()
    g["m"] = np.where(g.rec > 0, (g.rec - g.cus) / g.rec.replace(0, np.nan), np.nan)
    g = g.sort_values(["m", "id_produto"], na_position="last").reset_index(drop=True)
    assert list(df.id_produto) == list(g.id_produto)
    _near(df.margem_bruta_ajustada_pct, g.m, 1e-6)
    texto = "sem piso" if piso == 0 else f">= {piso} linhas entregues"
    assert df.filtro_aplicado.str.contains(texto).all()


# ------------------------------------------------------------------ 04
def o_04a(df, csv_):
    d = csv_["fact_despesas"].groupby("id_filial").valor.sum()
    r = vendas(csv_).groupby("id_filial").ent.sum()
    o = pd.DataFrame({"d": d, "r": r}).reset_index().sort_values(["d", "id_filial"], ascending=[False, True])
    assert list(df.id_filial) == list(o.id_filial)
    _near(df.despesas, o.d); _near(df.participacao_nas_despesas_pct, o.d / o.d.sum(), 1e-6)
    _near(df.despesas_sobre_receita_ajustada_pct, o.d / o.r, 1e-6)
    assert df.loc[df.tipo == "Matriz", "nota_leitura"].str.contains("corporativas").all()
    assert (df.loc[df.tipo != "Matriz", "nota_leitura"].fillna("") == "").all()


# ------------------------------------------------------------------ 05
def o_05a(df, csv_):
    v = vendas(csv_); d = csv_["fact_despesas"].assign(mes=lambda x: x.data.str[:7] + "-01").groupby("mes").valor.sum()
    g = v.groupby("mes")[["ent", "custo_ent"]].sum().reindex(meses(csv_), fill_value=0.0)
    g["desp"] = d.reindex(g.index, fill_value=0.0); g["res"] = g.ent - g.custo_ent - g.desp
    _near(df.resultado_operacional_estimado, g.res)
    _near(df.margem_operacional_estimada_pct, g.res / g.ent, 1e-6)
    s3 = g.res.rolling(3).sum() / g.ent.rolling(3).sum()            # razão de somas, nunca média de %
    _near(df.margem_operacional_media_movel_3m_pct, s3, 1e-6)
    _near(df.resultado_acumulado_no_ano, g.res.groupby(g.index.str[:4]).cumsum())
    assert df.rotulo.str.contains("nao e lucro liquido contabil").all()


# ------------------------------------------------------------------ 06
def o_06c(df, csv_):
    o, e = csv_["fact_orcamento"].copy(), csv_["fact_despesas"].copy()
    o["ano"], e["ano"] = o.mes.str[:4].astype(int), e.data.str[:4].astype(int)
    for _, r in df.iterrows():
        a = int(r.ano); mref = r.mes_referencia
        anual = o[o.ano == a].valor_orcado.sum()
        acum = o[(o.ano == a) & (o.mes <= mref)].valor_orcado.sum()
        real = e[(e.ano == a) & (e.data < (pd.Timestamp(mref) + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d"))].valor.sum()
        assert abs(r.orcamento_anual - anual) < 0.01 and abs(r.orcamento_acumulado - acum) < 0.01 and abs(r.realizado_acumulado - real) < 0.01
        assert abs(r.execucao_correta_acumulado_sobre_acumulado - real / acum) < 1e-6
        assert abs(r.leitura_ingenua_acumulado_sobre_anual - real / anual) < 1e-6


# ------------------------------------------------------------------ 07
def o_07a(df, csv_, lim_mom, lim_yoy):
    ent = vendas(csv_).groupby("mes").ent.sum().reindex(meses(csv_), fill_value=0.0).values
    assert len(df) == len(ent)
    for i in range(len(ent)):
        for lag, lim, st, cl in ((1, lim_mom, "status_mom", "classificacao_mom"), (12, lim_yoy, "status_yoy", "classificacao_yoy")):
            s, p = status_e_pct(ent[i], ent[i - lag] if i >= lag else None)
            esp = s if s != "comparavel" else ("queda_relevante" if p <= lim else "sem_queda_relevante")
            assert df[cl].iloc[i] == esp and df[st].iloc[i] == s, (i, cl)


# ------------------------------------------------------------------ 08 (decomposição em Python puro)
def agregar(v):
    g = v.groupby(["mes", "id_produto"])[["quantidade", "receita_bruta", "desconto_valor", "impostos_valor"]].sum()
    return {k: dict(q=float(r.quantidade), b=float(r.receita_bruta), d=float(r.desconto_valor), i=float(r.impostos_valor))
            for k, r in g.iterrows()}


def pvm(agg, produtos, p1, p0):
    z = dict(q=0.0, b=0.0, d=0.0, i=0.0)
    L = {p: (agg.get((p1, p), z), agg.get((p0, p), z)) for p in produtos}
    cont = [p for p, (a1, a0) in L.items() if a1["q"] > 0 and a0["q"] > 0]
    Q0c = sum(L[p][1]["q"] for p in cont); Q1c = sum(L[p][0]["q"] for p in cont)
    o = dict(volume=0.0, mix=0.0, preco=0.0, desconto=0.0, impostos=0.0, novo=0.0, descontinuado=0.0, r1=0.0, r0=0.0)
    for p, (a1, a0) in L.items():
        r1, r0 = a1["b"] - a1["d"] - a1["i"], a0["b"] - a0["d"] - a0["i"]
        o["r1"] += r1; o["r0"] += r0
        if a1["q"] > 0 and a0["q"] > 0:
            P1, P0 = a1["b"] / a1["q"], a0["b"] / a0["q"]
            d1, d0 = a1["d"] / a1["b"], a0["d"] / a0["b"]
            t1, t0 = a1["i"] / (a1["b"] - a1["d"]), a0["i"] / (a0["b"] - a0["d"])
            o["volume"] += (Q1c - Q0c) * r0 / Q0c
            o["mix"] += (a1["q"] - Q1c * a0["q"] / Q0c) * (r0 / a0["q"])
            o["preco"] += a1["q"] * (P1 - P0) * (1 - d0) * (1 - t0)
            o["desconto"] += -a1["q"] * P1 * (d1 - d0) * (1 - t0)
            o["impostos"] += -a1["q"] * P1 * (1 - d1) * (t1 - t0)
        elif a1["q"] > 0:
            o["novo"] += r1
        elif a0["q"] > 0:
            o["descontinuado"] += -r0
    return o


def o_08a(df, csv_):
    v = vendas(csv_); agg = agregar(v); prods = list(csv_["dim_produto"].id_produto); ms = meses(csv_)
    cols = dict(volume="efeito_volume", mix="efeito_mix", preco="efeito_preco", desconto="efeito_desconto",
                impostos="efeito_impostos", novo="efeito_produto_novo", descontinuado="efeito_produto_descontinuado")
    validos = 0
    for _, r in df.iterrows():
        base_ok = r.periodo_base in ms
        if not base_ok:
            assert r.status_base == "sem_base" and np.isnan(r.efeito_volume) and np.isnan(r.variacao_receita_ajustada_pct)
            continue
        validos += 1
        o = pvm(agg, prods, r.periodo, r.periodo_base)
        for k, c in cols.items():
            assert abs(r[c] - o[k]) < 0.01, (r.tipo_comparacao, r.periodo, c, r[c], o[k])
        assert abs(r.residuo_registrada) < 0.01 and abs(r.residuo_ajustada) < 0.01
    assert validos == 32 + 21
