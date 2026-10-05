// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "fact_orcamento.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"mes", type date}, {"id_departamento", Int64.Type}, {"id_categoria_despesa", Int64.Type}, {"id_filial", Int64.Type}, {"valor_orcado", type number}}, "en-US")
in
    Tipos
