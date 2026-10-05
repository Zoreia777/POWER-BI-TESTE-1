// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "dim_filial.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_filial", Int64.Type}, {"filial", type text}, {"cidade", type text}, {"uf", type text}, {"regiao", type text}, {"tipo", type text}, {"data_abertura", type date}, {"latitude", type number}, {"longitude", type number}}, "en-US")
in
    Tipos
