// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "dim_cliente.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_cliente", Int64.Type}, {"nome_cliente", type text}, {"segmento", type text}, {"cidade", type text}, {"uf", type text}, {"regiao", type text}, {"data_cadastro", type date}, {"data_primeira_compra", type date}}, "en-US")
in
    Tipos
