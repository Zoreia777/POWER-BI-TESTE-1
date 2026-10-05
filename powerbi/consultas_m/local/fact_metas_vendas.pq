// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "fact_metas_vendas.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"mes", type date}, {"id_filial", Int64.Type}, {"meta_receita_liquida", type number}, {"meta_margem_bruta_pct", type number}, {"meta_lucro_bruto", type number}}, "en-US")
in
    Tipos
