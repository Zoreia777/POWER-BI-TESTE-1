-- Documentação dentro do próprio banco (visível via duckdb_columns().comment).
COMMENT ON COLUMN mart.kpi_vendas_mes.receita_reconhecida_provisoria IS 'AJUSTADA/PROVISÓRIA e NÃO oficial: = vendas_entregues. Aplica PN-DEV-01 (devolução cancela a receita) por mês da venda original. Não é receita contábil oficialmente reconhecida.';
COMMENT ON COLUMN mart.kpi_vendas_mes.devolucoes IS 'Receita líquida das linhas Devolvido, agrupada pelo MÊS DA VENDA ORIGINAL (não existe data de devolução; PN-DEV-03). Valor original, positivo.';
COMMENT ON COLUMN mart.kpi_vendas_mes.custo_reconhecido_provisorio IS 'Hipótese PN-DEV-02 (não comprovada): custo da linha devolvida é recuperável e fica fora do custo ajustado.';
COMMENT ON COLUMN mart.kpi_vendas_mes.lucro_bruto_se_custo_nao_recuperado IS 'Sensibilidade: lucro bruto ajustado se o custo das devoluções NÃO fosse recuperado.';
COMMENT ON COLUMN mart.fact_vendas.linha_csv_origem IS 'Número da linha em data/fact_vendas.csv (cabeçalho = linha 1): rastreabilidade ao registro original.';
COMMENT ON COLUMN mart.meta_vs_realizado_mensal.atingimento_provisorio_pct IS 'Meta x vendas entregues (indicador ajustado e não oficial; PN-DEV-01/03).';
