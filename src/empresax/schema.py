"""Contrato de dados: tabelas, colunas, tipos, chaves e relacionamentos esperados.

É a única fonte de verdade para a camada staging (tipagem) e para as validações.
Tipos: INT, MONEY (DECIMAL(14,2)), PCT (DECIMAL(7,4)), DATE, DOUBLE, TEXT.
Colunas terminadas em '?' aceitam NULL; as demais são obrigatórias.
"""
from __future__ import annotations

from dataclasses import dataclass

SQL_TYPE = {
    "INT": "BIGINT", "MONEY": "DECIMAL(14,2)", "PCT": "DECIMAL(7,4)",
    "DATE": "DATE", "DOUBLE": "DOUBLE", "TEXT": "VARCHAR",
}


@dataclass(frozen=True)
class Coluna:
    nome: str
    tipo: str
    anulavel: bool = False


@dataclass(frozen=True)
class Tabela:
    nome: str
    colunas: tuple[Coluna, ...]
    pk: tuple[str, ...]

    @property
    def nomes(self) -> list[str]:
        return [c.nome for c in self.colunas]


def _t(nome: str, pk: str, spec: str) -> Tabela:
    cols = []
    for item in spec.split():
        n, t = item.split(":")
        cols.append(Coluna(n, t.rstrip("?"), t.endswith("?")))
    return Tabela(nome, tuple(cols), tuple(pk.split(",")))


TABELAS: dict[str, Tabela] = {t.nome: t for t in [
    _t("dim_calendario", "data",
       "data:DATE ano:INT semestre:TEXT trimestre:TEXT mes_num:INT mes_nome:TEXT mes_abrev:TEXT "
       "ano_mes:TEXT mes_ano:TEXT ordem_ano_mes:INT dia:INT dia_semana_num:INT dia_semana:TEXT "
       "dia_semana_abrev:TEXT semana_do_ano:INT fim_de_semana:INT feriado:TEXT? dia_util:INT "
       "realizado:INT status_periodo:TEXT primeiro_dia_mes:DATE"),
    _t("dim_canal", "id_canal", "id_canal:INT canal:TEXT tipo_canal:TEXT"),
    _t("dim_categoria_despesa", "id_categoria_despesa",
       "id_categoria_despesa:INT categoria_despesa:TEXT grupo_dre:TEXT tipo_custo:TEXT ordem_dre:INT"),
    _t("dim_cliente", "id_cliente",
       "id_cliente:INT nome_cliente:TEXT segmento:TEXT cidade:TEXT uf:TEXT regiao:TEXT "
       "data_cadastro:DATE data_primeira_compra:DATE?"),
    _t("dim_departamento", "id_departamento",
       "id_departamento:INT departamento:TEXT centro_custo:TEXT responsavel:TEXT tipo_area:TEXT"),
    _t("dim_filial", "id_filial",
       "id_filial:INT filial:TEXT cidade:TEXT uf:TEXT regiao:TEXT tipo:TEXT data_abertura:DATE "
       "latitude:DOUBLE longitude:DOUBLE"),
    _t("dim_produto", "id_produto",
       "id_produto:INT sku:TEXT produto:TEXT categoria:TEXT subcategoria:TEXT preco_lista:MONEY "
       "custo_unitario_base:MONEY margem_lista_pct:PCT aliquota_imposto:PCT"),
    _t("dim_vendedor", "id_vendedor",
       "id_vendedor:INT nome_vendedor:TEXT equipe:TEXT cargo:TEXT data_admissao:DATE"),
    _t("fact_despesas", "id_despesa",
       "id_despesa:INT data:DATE id_departamento:INT id_categoria_despesa:INT id_filial:INT "
       "fornecedor:TEXT valor:MONEY"),
    _t("fact_metas_vendas", "mes,id_filial",
       "mes:DATE id_filial:INT meta_receita_liquida:MONEY meta_margem_bruta_pct:PCT meta_lucro_bruto:MONEY"),
    _t("fact_orcamento", "mes,id_departamento,id_categoria_despesa,id_filial",
       "mes:DATE id_departamento:INT id_categoria_despesa:INT id_filial:INT valor_orcado:MONEY"),
    _t("fact_rh_mensal", "data_referencia,id_departamento,id_filial",
       "data_referencia:DATE id_departamento:INT id_filial:INT headcount:INT headcount_planejado:INT "
       "admissoes:INT desligamentos:INT"),
    _t("fact_vendas", "id_venda",
       "id_venda:INT id_pedido:TEXT data:DATE id_cliente:INT id_produto:INT id_filial:INT "
       "id_vendedor:INT id_canal:INT quantidade:INT preco_unitario:MONEY desconto_pct:PCT "
       "receita_bruta:MONEY desconto_valor:MONEY impostos_valor:MONEY receita_liquida:MONEY "
       "custo_total:MONEY forma_pagamento:TEXT status:TEXT"),
]}

# (tabela, coluna, tabela_dimensão, coluna_dimensão) — relacionamentos VALIDADOS na Etapa 1.
FKS: list[tuple[str, str, str, str]] = [
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
    ("fact_orcamento", "mes", "dim_calendario", "data"),
    ("fact_metas_vendas", "id_filial", "dim_filial", "id_filial"),
    ("fact_metas_vendas", "mes", "dim_calendario", "data"),
    ("fact_rh_mensal", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_rh_mensal", "id_filial", "dim_filial", "id_filial"),
    ("fact_rh_mensal", "data_referencia", "dim_calendario", "data"),
]

# Domínios fechados validados no staging.
DOMINIOS = {("fact_vendas", "status"): ("Entregue", "Devolvido")}
