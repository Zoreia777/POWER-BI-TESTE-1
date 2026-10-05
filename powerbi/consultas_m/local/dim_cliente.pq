// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "dim_cliente.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_cliente", Int64.Type}, {"nome_cliente", type text}, {"segmento", type text}, {"cidade", type text}, {"uf", type text}, {"regiao", type text}, {"data_cadastro", type date}, {"data_primeira_compra", type date}}, "en-US")
in
    Tipos
