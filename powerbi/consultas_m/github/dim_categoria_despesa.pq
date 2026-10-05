// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "dim_categoria_despesa.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"id_categoria_despesa", Int64.Type}, {"categoria_despesa", type text}, {"grupo_dre", type text}, {"tipo_custo", type text}, {"ordem_dre", Int64.Type}}, "en-US")
in
    Tipos
