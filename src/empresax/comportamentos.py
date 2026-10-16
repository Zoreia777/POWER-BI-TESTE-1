"""Registro dos comportamentos PROGRAMADOS no gerador de dados sintéticos.

Os dados da Empresa X são fictícios: vários padrões (sazonalidade, quedas, margens, devoluções)
foram colocados de propósito em scripts/gerar_dados.py. Este registro separa, de forma explícita,
  * o que foi PROGRAMADO (causa conhecida: parâmetro e linha do gerador), de
  * o que é RESULTADO medido por consulta analítica (efeito observável nos dados).
Nenhum desses padrões é evidência sobre o mercado real.
Colunas: (id, comportamento, parametro_no_gerador, linha_gerador, tabela_afetada)
"""
from __future__ import annotations

COMPORTAMENTOS: list[tuple[str, str, str, int, str]] = [
    ("P01", "Sazonalidade mensal de pedidos (nov 1,38x; dez 1,30x; jan 0,88x; fev 0,84x)", "SAZONALIDADE", 50, "fact_vendas"),
    ("P02", "Sazonalidade por dia da semana (sáb 0,60x; dom 0,28x)", "DOW", 52, "fact_vendas"),
    ("P03", "Feriados reduzem pedidos a 25%", "FERIADOS / lam_base", 131, "fact_vendas"),
    ("P04", "Black Friday: pedidos 2,2x, desconto maior e mix de canais diferente", "BLACK_FRIDAYS / CANAL_BF / lam_base", 143, "fact_vendas"),
    ("P05", "Crescimento tendencial de 1,1% ao mês", "CRESCIMENTO_MENSAL", 49, "fact_vendas"),
    ("P06", "Reajuste mensal de preço por produto (preço praticado sobe acima do preço de lista cadastrado)", "p['ip']", 571, "fact_vendas"),
    ("P07", "Reajuste mensal de custo por produto (Smartphone X Max: custo +1%/mês, preço fixo)", "ic=0.0100, ip=0.0", 304, "fact_vendas"),
    ("P08", "Taxa de devolução por produto (Cadeira Gamer ~9%); status sorteado por linha, sem data de devolução", "p['dev']", 580, "fact_vendas"),
    ("P09", "Ruptura de estoque do Notebook Pro 14 em ago/2025", "w[0] *= 0.10", 506, "fact_vendas"),
    ("P10", "Concorrente em Porto Alegre jun-ago/2025 (-18%); chuvas no Rio mar/2025 (-22%); contrato público em Brasília mar-jun/2026 (+18%)", "fator_historia", 391, "fact_vendas"),
    ("P11", "Filiais novas com rampa de vendas (Recife jun/2024, Salvador fev/2025)", "rampa", 381, "fact_vendas"),
    ("P12", "Mix de canais migra para marketplace (comissão de 11%)", "CANAL_INI/CANAL_FIM/COMISSAO_MKT", 355, "fact_vendas, fact_despesas"),
    ("P13", "Um vendedor de São Paulo vende ~3x mais que a média", "vendedores_filial[1][0] peso 3,2", 460, "fact_vendas"),
    ("P14", "Marketing estoura o orçamento no 4T/2025 (+28%)", "real_m *= 1.28", 782, "fact_despesas"),
    ("P15", "Software & Licenças (TI) cresce acima do orçado em 2026", "real_soft *= 1 + 0.035 * mes", 842, "fact_despesas"),
    ("P16", "Juros bancários sobem desde mar/2025", "real_j", 860, "fact_despesas"),
    ("P17", "Turnover por departamento (TI e Operações lideram)", "TURNOVER", 598, "fact_rh_mensal"),
]
