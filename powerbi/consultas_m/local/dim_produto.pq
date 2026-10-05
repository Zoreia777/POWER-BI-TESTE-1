// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "dim_produto.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_produto", Int64.Type}, {"sku", type text}, {"produto", type text}, {"categoria", type text}, {"subcategoria", type text}, {"preco_lista", type number}, {"custo_unitario_base", type number}, {"margem_lista_pct", type number}, {"aliquota_imposto", type number}}, "en-US")
in
    Tipos
