// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "dim_filial.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_filial", Int64.Type}, {"filial", type text}, {"cidade", type text}, {"uf", type text}, {"regiao", type text}, {"tipo", type text}, {"data_abertura", type date}, {"latitude", type number}, {"longitude", type number}}, "en-US")
in
    Tipos
