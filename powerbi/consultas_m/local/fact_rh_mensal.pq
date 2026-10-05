// Parâmetro necessário: PastaLocal (texto)
// Ex.: C:\\projetos\\empresa-x-powerbi\\data\\
let
    Fonte = Csv.Document(File.Contents(PastaLocal & "fact_rh_mensal.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalho, {{"data_referencia", type date}, {"id_departamento", Int64.Type}, {"id_filial", Int64.Type}, {"headcount", Int64.Type}, {"headcount_planejado", Int64.Type}, {"admissoes", Int64.Type}, {"desligamentos", Int64.Type}}, "en-US")
in
    Tipos
