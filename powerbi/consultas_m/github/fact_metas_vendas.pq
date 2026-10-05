// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "fact_metas_vendas.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"mes", type date}, {"id_filial", Int64.Type}, {"meta_receita_liquida", type number}, {"meta_margem_bruta_pct", type number}, {"meta_lucro_bruto", type number}}, "en-US")
in
    Tipos
