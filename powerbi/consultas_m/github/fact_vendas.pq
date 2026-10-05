// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "fact_vendas.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_venda", Int64.Type}, {"id_pedido", type text}, {"data", type date}, {"id_cliente", Int64.Type}, {"id_produto", Int64.Type}, {"id_filial", Int64.Type}, {"id_vendedor", Int64.Type}, {"id_canal", Int64.Type}, {"quantidade", Int64.Type}, {"preco_unitario", type number}, {"desconto_pct", type number}, {"receita_bruta", type number}, {"desconto_valor", type number}, {"impostos_valor", type number}, {"receita_liquida", type number}, {"custo_total", type number}, {"forma_pagamento", type text}, {"status", type text}}, "en-US")
in
    Tipos
