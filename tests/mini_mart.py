"""Banco miniatura para cenários injetados: cria só as tabelas `mart.*` que as análises leem,
com números escolhidos à mão para que o resultado esperado seja calculável no papel."""
import duckdb


def criar(vendas, meses, ultimo, produtos=((1, "A", "Cat"), (2, "B", "Cat")),
          filiais=((1, "Filial 1", "Filial"),), canais=((1, "Canal 1"),)):
    """vendas: lista de dicts {mes, prod, q, bruta, desc, imp, status, filial, canal, custo}."""
    con = duckdb.connect(":memory:")
    con.execute("CREATE SCHEMA mart")
    con.execute("CREATE TABLE mart.periodo_realizado (ultimo_mes_realizado DATE)")
    con.execute("INSERT INTO mart.periodo_realizado VALUES (?)", [ultimo])
    con.execute("CREATE TABLE mart.dim_calendario (primeiro_dia_mes DATE)")
    con.executemany("INSERT INTO mart.dim_calendario VALUES (?)", [[m] for m in meses])
    con.execute("CREATE TABLE mart.dim_produto (id_produto INT, produto VARCHAR, categoria VARCHAR)")
    con.executemany("INSERT INTO mart.dim_produto VALUES (?,?,?)", [list(p) for p in produtos])
    con.execute("CREATE TABLE mart.dim_filial (id_filial INT, filial VARCHAR, tipo VARCHAR)")
    con.executemany("INSERT INTO mart.dim_filial VALUES (?,?,?)", [list(f) for f in filiais])
    con.execute("CREATE TABLE mart.dim_canal (id_canal INT, canal VARCHAR)")
    con.executemany("INSERT INTO mart.dim_canal VALUES (?,?)", [list(c) for c in canais])
    con.execute("""CREATE TABLE mart.fact_vendas (id_venda INT, mes DATE, id_pedido VARCHAR, id_produto INT, id_filial INT, id_canal INT,
        quantidade BIGINT, receita_bruta DECIMAL(14,2), desconto_valor DECIMAL(14,2), impostos_valor DECIMAL(14,2),
        receita_liquida DECIMAL(14,2), receita_liquida_entregue DECIMAL(14,2), receita_liquida_devolvida DECIMAL(14,2),
        custo_total DECIMAL(14,2), custo_entregue DECIMAL(14,2), eh_devolvida BOOLEAN, flag_margem_negativa BOOLEAN)""")
    for n, v in enumerate(vendas, start=1):
        bruta, desc, imp = v["bruta"], v.get("desc", 0), v.get("imp", 0)
        liq = bruta - desc - imp
        dev = v.get("status", "Entregue") == "Devolvido"
        custo = v.get("custo", round(liq * 0.5, 2))
        con.execute("INSERT INTO mart.fact_vendas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [n, v["mes"], f"P{n}", v["prod"], v.get("filial", 1), v.get("canal", 1), v["q"], bruta, desc, imp, liq,
                     0 if dev else liq, liq if dev else 0, custo, 0 if dev else custo, dev, custo > liq])
    return con
