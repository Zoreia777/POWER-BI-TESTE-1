// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "fact_despesas.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_despesa", Int64.Type}, {"data", type date}, {"id_departamento", Int64.Type}, {"id_categoria_despesa", Int64.Type}, {"id_filial", Int64.Type}, {"fornecedor", type text}, {"valor", type number}}, "en-US")
in
    Tipos
