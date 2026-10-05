// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "fact_rh_mensal.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"data_referencia", type date}, {"id_departamento", Int64.Type}, {"id_filial", Int64.Type}, {"headcount", Int64.Type}, {"headcount_planejado", Int64.Type}, {"admissoes", Int64.Type}, {"desligamentos", Int64.Type}}, "en-US")
in
    Tipos
