// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "dim_categoria_despesa.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_categoria_despesa", Int64.Type}, {"categoria_despesa", type text}, {"grupo_dre", type text}, {"tipo_custo", type text}, {"ordem_dre", Int64.Type}}, "en-US")
in
    Tipos
