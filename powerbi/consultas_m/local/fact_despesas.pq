// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "fact_despesas.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_despesa", Int64.Type}, {"data", type date}, {"id_departamento", Int64.Type}, {"id_categoria_despesa", Int64.Type}, {"id_filial", Int64.Type}, {"fornecedor", type text}, {"valor", type number}}, "en-US")
in
    Tipos
