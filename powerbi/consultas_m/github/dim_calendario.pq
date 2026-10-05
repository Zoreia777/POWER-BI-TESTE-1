// Parâmetro necessário: BaseUrl (texto)
// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/
let
    Fonte = Csv.Document(Web.Contents(BaseUrl & "dim_calendario.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"data", type date}, {"ano", Int64.Type}, {"semestre", type text}, {"trimestre", type text}, {"mes_num", Int64.Type}, {"mes_nome", type text}, {"mes_abrev", type text}, {"ano_mes", type text}, {"mes_ano", type text}, {"ordem_ano_mes", Int64.Type}, {"dia", Int64.Type}, {"dia_semana_num", Int64.Type}, {"dia_semana", type text}, {"dia_semana_abrev", type text}, {"semana_do_ano", Int64.Type}, {"fim_de_semana", Int64.Type}, {"feriado", type text}, {"dia_util", Int64.Type}, {"realizado", Int64.Type}, {"status_periodo", type text}, {"primeiro_dia_mes", type date}}, "en-US")
in
    Tipos
