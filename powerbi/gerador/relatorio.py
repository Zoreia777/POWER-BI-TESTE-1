"""Relatório (PBIR) do Power BI da Empresa X: tema, menu lateral, 7 páginas."""
import json

VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json"

W, H = 1280, 720
SIDEBAR = 208
X0, X1 = 224, 1264
CW = X1 - X0

NAVY = "#0F172A"
NAVY2 = "#1E293B"
TEAL = "#0F766E"
TEXT = "#0F172A"
MUTED = "#64748B"
SOFT = "#94A3B8"
PAGE_BG = "#F1F5F9"
CARD = "#FFFFFF"
BORDER = "#E2E8F0"
GREEN, RED, AMBER = "#15803D", "#B91C1C", "#D97706"

ACCENTS = ["#0F766E", "#2563EB", "#D97706", "#7C3AED", "#059669"]

FONT = "Segoe UI"
FONT_SB = "Segoe UI Semibold"
FONT_B = "Segoe UI Bold"


# ---------------------------------------------------------------------------
# Codificação PBIR
# ---------------------------------------------------------------------------
def L(v):
    return {"expr": {"Literal": {"Value": v}}}


def S(t):
    return L("'" + str(t).replace("'", "''") + "'")


def B(b):
    return L("true" if b else "false")


def Dn(x):
    return L(f"{x}D")


def Ln(x):
    return L(f"{int(x)}L")


def C(hexc):
    return {"solid": {"color": S(hexc)}}


def MEAS(name, table="_Medidas"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def COL(table, col):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}}


def CM(name):
    """cor vinda de uma medida (field value)."""
    return {"solid": {"color": {"expr": MEAS(name)}}}


def qref(field):
    k = "Measure" if "Measure" in field else "Column"
    ent = field[k]["Expression"]["SourceRef"]["Entity"]
    return f"{ent}.{field[k]['Property']}", field[k]["Property"]


def proj(field, active=None, display=None):
    q, n = qref(field)
    p = {"field": field, "queryRef": q, "nativeQueryRef": n}
    if active is not None:
        p["active"] = active
    if display:
        p["displayName"] = display
    return p


def role(*fields, active_first=False):
    ps = []
    for i, f in enumerate(fields):
        ps.append(proj(f, active=True if (active_first and i == 0) else None))
    return {"projections": ps}


def obj(props, selector=None):
    o = {"properties": props}
    if selector is not None:
        o["selector"] = selector
    return o


DEF = {"id": "default"}


def rule_color(measure, pos_color, neg_color, neutral="#475569"):
    """Regra: >=0 -> pos_color, <0 -> neg_color (Conditional.Cases)."""
    m = MEAS(measure)
    return {"solid": {"color": {"expr": {"Conditional": {
        "Cases": [
            {"Condition": {"Comparison": {"ComparisonKind": 2, "Left": m, "Right": {"Literal": {"Value": "0D"}}}},
             "Value": {"Literal": {"Value": f"'{pos_color}'"}}},
            {"Condition": {"Comparison": {"ComparisonKind": 3, "Left": m, "Right": {"Literal": {"Value": "0D"}}}},
             "Value": {"Literal": {"Value": f"'{neg_color}'"}}},
        ],
        "DefaultValue": {"Literal": {"Value": f"'{neutral}'"}},
    }}}}}


def vco(title=None, subtitle=None, bg=True, border=True, shadow=True, pad=(8, 8, 12, 12),
        bg_color=CARD, header=True, title_size=11, extra=None):
    v = {}
    if title is None:
        v["title"] = [obj({"show": B(False)})]
    else:
        v["title"] = [obj({
            "show": B(True), "text": S(title), "fontColor": C(TEXT), "fontSize": Dn(title_size),
            "fontFamily": S(FONT_SB), "alignment": S("left"),
        })]
    if subtitle:
        v["subTitle"] = [obj({
            "show": B(True), "text": S(subtitle), "fontColor": C(MUTED), "fontSize": Dn(9),
            "fontFamily": S(FONT), "alignment": S("left"),
        })]
    v["background"] = [obj({"show": B(bg), "color": C(bg_color), "transparency": Dn(0)})] if bg else [obj({"show": B(False)})]
    if border:
        v["border"] = [obj({"show": B(True), "color": C(BORDER), "radius": Dn(10), "width": Dn(1)})]
    else:
        v["border"] = [obj({"show": B(False)})]
    if shadow:
        v["dropShadow"] = [obj({
            "show": B(True), "color": C("#0F172A"), "transparency": Ln(92), "position": S("Outer"),
            "preset": S("Custom"), "shadowBlur": Ln(12), "shadowDistance": Ln(2), "shadowSpread": Ln(0), "angle": Ln(90),
        })]
    else:
        v["dropShadow"] = [obj({"show": B(False)})]
    t, b, l, r = pad
    v["padding"] = [obj({"top": Dn(t), "bottom": Dn(b), "left": Dn(l), "right": Dn(r)})]
    if not header:
        v["visualHeader"] = [obj({"show": B(False)})]
    if extra:
        v.update(extra)
    return v


# ---------------------------------------------------------------------------
# Página e visuais
# ---------------------------------------------------------------------------
class Page:
    def __init__(self, pid, display, title, subtitle):
        self.id = pid
        self.display = display
        self.title = title
        self.subtitle = subtitle
        self.visuals = []
        self.z = 0

    def add(self, name, vtype, x, y, w, h, query=None, objects=None, vcobj=None, sync=None,
            filters=None, z=None, howCreated=None):
        self.z += 100
        visual = {"visualType": vtype}
        if query:
            visual["query"] = query
        if objects:
            visual["objects"] = objects
        if vcobj:
            visual["visualContainerObjects"] = vcobj
        if sync:
            visual["syncGroup"] = sync
        visual["drillFilterOtherVisuals"] = True
        v = {
            "$schema": VC,
            "name": name,
            "position": {"x": x, "y": y, "z": self.z if z is None else z, "height": h, "width": w,
                         "tabOrder": self.z},
            "visual": visual,
        }
        if filters:
            v["filterConfig"] = {"filters": filters}
        if howCreated:
            v["howCreated"] = howCreated
        self.visuals.append(v)
        return v


def query(roles, sort=None):
    q = {"queryState": roles}
    if sort:
        q["sortDefinition"] = {"sort": sort, "isDefaultSort": False}
    return q


def sort_by(field, desc=True):
    return {"field": field, "direction": "Descending" if desc else "Ascending"}


def textbox(page, name, x, y, w, h, paragraphs, z=None):
    paras = []
    for runs, align in paragraphs:
        paras.append({
            "textRuns": [
                {"value": txt, "textStyle": {"fontFamily": fam, "fontSize": f"{size}pt", "color": color,
                                             **({"fontWeight": "bold"} if bold else {})}}
                for txt, fam, size, color, bold in runs
            ],
            "horizontalTextAlignment": align,
        })
    return page.add(name, "textbox", x, y, w, h,
                    objects={"general": [obj({"paragraphs": paras})]},
                    vcobj=vco(bg=False, border=False, shadow=False, pad=(0, 0, 0, 0), header=False), z=z)


def shape(page, name, x, y, w, h, color, radius=0, z=None):
    shp = [obj({"tileShape": S("rectangleRounded" if radius else "rectangle"),
                **({"roundEdge": Ln(radius)} if radius else {})})]
    if radius:
        shp.append(obj({"tileShape": S("rectangleRounded")}, DEF))
    return page.add(name, "shape", x, y, w, h, objects={
        "shape": shp,
        "fill": [obj({"show": B(True), "fillColor": C(color), "transparency": Dn(0)}, DEF)],
        "outline": [obj({"show": B(False)}, DEF)],
    }, vcobj=vco(bg=False, border=False, shadow=False, pad=(0, 0, 0, 0), header=False), z=z)


# ---------------------------------------------------------------------------
# Elementos reutilizados
# ---------------------------------------------------------------------------
PAGES_META = [
    ("p01_visao_geral", "Visão Geral", "01   Visão Geral"),
    ("p02_vendas", "Vendas", "02   Vendas"),
    ("p03_gastos", "Gastos & Orçamento", "03   Gastos & Orçamento"),
    ("p04_lucratividade", "Lucratividade", "04   Lucratividade (DRE)"),
    ("p05_clientes", "Clientes", "05   Clientes & Pareto"),
    ("p06_pessoas", "Pessoas", "06   Pessoas"),
    ("p07_simulador", "Simulador", "07   Simulador de Cenários"),
]


def sidebar(page):
    shape(page, "menu_fundo", 0, 0, SIDEBAR, H, NAVY, z=0)
    shape(page, "menu_logo_marca", 20, 26, 8, 38, "#14B8A6", z=10)
    textbox(page, "menu_logo", 36, 18, 168, 56, [
        ([("EMPRESA X", FONT_B, 17, "#FFFFFF", True)], "left"),
        ([("Painel de Gestão", FONT, 9, SOFT, False)], "left"),
    ], z=20)
    shape(page, "menu_divisor", 20, 86, 168, 1, "#334155", z=30)
    for i, (pid, disp, label) in enumerate(PAGES_META):
        active = pid == page.id
        y = 102 + i * 48
        fill_default = TEAL if active else NAVY
        fill_hover = TEAL if active else NAVY2
        txt_color = "#FFFFFF" if active else "#CBD5E1"
        page.add(f"menu_btn_{i+1:02d}", "actionButton", 12, y, 184, 40, objects={
            "text": [
                obj({"show": B(True)}),
                obj({"text": S(label), "fontSize": Dn(10.5), "fontColor": C(txt_color),
                     "fontFamily": S(FONT_SB if active else FONT), "horizontalAlignment": S("left")}, DEF),
                obj({"fontColor": C("#FFFFFF")}, {"id": "hover"}),
            ],
            "icon": [
                obj({"show": B(False)}),
                obj({"shapeType": S("blank"), "placement": S("left")}, DEF),
            ],
            "fill": [
                obj({"show": B(True)}),
                obj({"fillColor": C(fill_default), "transparency": Dn(0)}, DEF),
                obj({"fillColor": C(fill_hover), "transparency": Dn(0)}, {"id": "hover"}),
            ],
            "outline": [obj({"show": B(False)})],
            "shape": [
                obj({"tileShape": S("rectangleRounded"), "roundEdge": Ln(8)}),
                obj({"tileShape": S("rectangleRounded")}, DEF),
            ],
        }, vcobj={
            "background": [obj({"show": B(False)})],
            "border": [obj({"show": B(False)})],
            "dropShadow": [obj({"show": B(False)})],
            "padding": [obj({"top": Dn(0), "bottom": Dn(0), "left": Dn(0), "right": Dn(0)})],
            "visualHeader": [obj({"show": B(False)})],
            "visualLink": [obj({
                "show": B(True), "type": S("PageNavigation"), "navigationSection": S(pid),
                "tooltip": S(f"Ir para {disp}"),
            })],
        }, howCreated="InsertVisualButton", z=40 + i)
    textbox(page, "menu_rodape", 16, 618, 180, 90, [
        ([("Base fictícia para estudo", FONT_SB, 8, SOFT, False)], "left"),
        ([("Dados realizados até 30/09/2026", FONT, 8, "#64748B", False)], "left"),
        ([("Dica: no Desktop use Ctrl + clique", FONT, 8, "#64748B", False)], "left"),
        ([("nos botões para navegar.", FONT, 8, "#64748B", False)], "left"),
    ], z=60)


def header(page, slicers):
    # segmentações à direita
    x = X1
    for key in reversed(slicers):
        spec = SLICERS[key]
        w = spec["w"]
        x -= w
        slicer(page, f"seg_{key}", x, 10, w, 66, spec)
        x -= 12
    textbox(page, "cab_titulo", X0, 12, min(620, x - X0 - 8), 60, [
        ([(page.title, FONT_B, 19, TEXT, True)], "left"),
        ([(page.subtitle, FONT, 10, MUTED, False)], "left"),
    ])


SLICERS = {
    "ano": {"w": 110, "table": "dim_calendario", "col": "ano", "label": "Ano", "single": True,
            "pre": "2026L", "sync": "sync_ano"},
    "filial": {"w": 180, "table": "dim_filial", "col": "filial", "label": "Filial", "sync": "sync_filial"},
    "canal": {"w": 160, "table": "dim_canal", "col": "canal", "label": "Canal de venda", "sync": "sync_canal"},
    "depto": {"w": 190, "table": "dim_departamento", "col": "departamento", "label": "Departamento",
              "sync": "sync_depto"},
    "tipo_custo": {"w": 130, "table": "dim_categoria_despesa", "col": "tipo_custo", "label": "Tipo de custo",
                   "sync": "sync_tipo_custo"},
}


def slicer(page, name, x, y, w, h, spec):
    field = COL(spec["table"], spec["col"])
    objects = {
        "data": [obj({"mode": S("Dropdown")})],
        "header": [obj({"show": B(True), "text": S(spec["label"]), "fontColor": C(MUTED),
                        "textSize": Dn(9), "fontFamily": S(FONT_SB)})],
        "items": [obj({"fontColor": C(TEXT), "textSize": Dn(10), "fontFamily": S(FONT)})],
        "selection": [obj({"singleSelect": B(bool(spec.get("single"))),
                           "selectAllCheckboxEnabled": B(not spec.get("single"))})],
    }
    if spec.get("pre"):
        objects["general"] = [obj({"filter": {"filter": {
            "Version": 2,
            "From": [{"Name": "c", "Entity": spec["table"], "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": spec["col"]}}],
                "Values": [[{"Literal": {"Value": spec["pre"]}}]],
            }}}],
        }}})]
    page.add(name, "slicer", x, y, w, h,
             query=query({"Values": {"projections": [proj(field, active=True)]}}),
             objects=objects,
             vcobj=vco(bg=True, border=True, shadow=False, pad=(4, 4, 10, 10), header=False),
             sync={"groupName": spec["sync"], "fieldChanges": True, "filterChanges": True})


def kpi(page, key, x, y, w, h, measure, label, accent, selo=None, bom="sobe", dec=None):
    """Cartão KPI: título pequeno, valor grande, barra de destaque e selo de variação."""
    vprops = {"fontSize": Dn(18), "fontColor": C(TEXT), "fontFamily": S(FONT_SB)}
    if dec is not None:
        vprops["labelPrecision"] = Ln(dec)
    page.add(f"kpi_{key}", "cardVisual", x, y, w, h,
             query=query({"Data": {"projections": [proj(MEAS(measure))]}}),
             objects={
                 "value": [obj(vprops, DEF)],
                 "label": [obj({"show": B(False)}, DEF)],
                 "outline": [obj({"show": B(False)}, DEF)],
                 "accentBar": [obj({"show": B(True), "position": S("Left"), "width": Dn(4),
                                    "color": C(accent)}, DEF)],
                 "padding": [obj({"paddingSelection": S("Custom"), "leftMargin": Ln(10), "rightMargin": Ln(6),
                                  "topMargin": Ln(0), "bottomMargin": Ln(0)}, DEF)],
                 "layout": [obj({"alignment": S("top"), "paddingUniform": Ln(0)}, DEF)],
                 "spacing": [obj({"verticalSpacing": Ln(0)}, DEF)],
             },
             vcobj=vco(title=label.upper(), title_size=9, shadow=True, pad=(10, 6, 6, 8), header=False,
                       extra={"title": [obj({
                           "show": B(True), "text": S(label.upper()), "fontColor": C(MUTED), "fontSize": Dn(8.5),
                           "fontFamily": S(FONT_SB), "alignment": S("left")})]}))
    if selo:
        pos, neg = (GREEN, RED) if bom == "sobe" else (RED, GREEN)
        if bom == "desce":
            # a medida "Var" é positiva quando subiu; para custos subir é ruim
            pos, neg = RED, GREEN
        page.add(f"kpi_{key}_selo", "cardVisual", x + 14, y + h - 30, min(w - 26, 132), 22,
                 query=query({"Data": {"projections": [proj(MEAS(f"Selo {selo}"))]}}),
                 objects={
                     "value": [obj({"fontSize": Dn(8.5), "fontFamily": S(FONT_SB),
                                    "fontColor": rule_color(f"Var {selo}", pos, neg)}, DEF)],
                     "label": [obj({"show": B(False)}, DEF)],
                     "outline": [obj({"show": B(False)}, DEF)],
                     "padding": [obj({"paddingSelection": S("Custom"), "leftMargin": Ln(8), "rightMargin": Ln(6),
                                      "topMargin": Ln(0), "bottomMargin": Ln(0)}, DEF)],
                     "layout": [obj({"alignment": S("middle"), "paddingUniform": Ln(0)}, DEF)],
                 },
                 vcobj={
                     "title": [obj({"show": B(False)})],
                     "background": [obj({"show": B(True), "color": CM(f"Fundo Selo {selo}"), "transparency": Dn(0)})],
                     "border": [obj({"show": B(True), "color": CM(f"Fundo Selo {selo}"), "radius": Dn(12), "width": Dn(1)})],
                     "dropShadow": [obj({"show": B(False)})],
                     "padding": [obj({"top": Dn(0), "bottom": Dn(0), "left": Dn(0), "right": Dn(0)})],
                     "visualHeader": [obj({"show": B(False)})],
                 })


MOEDA_KPIS = {"Receita Líquida", "Lucro Bruto", "Despesas Totais", "Resultado Operacional", "Receita Bruta",
              "CMV", "Despesa Orçada (realizado)", "Receita Líquida (Cenário)", "Resultado (Cenário)",
              "Δ Resultado vs Atual", "Receita por Cliente", "Ticket Médio", "Custo de Pessoal por Funcionário",
              "Receita por Funcionário", "Variação vs Orçado (R$)"}


def kpi_row(page, items, y=88, h=108, x0=X0, x1=X1):
    n = len(items)
    gap = 14
    w = (x1 - x0 - gap * (n - 1)) / n
    for i, it in enumerate(items):
        key, measure, label, selo, bom = (list(it) + [None, None, "sobe"])[:5]
        kpi(page, key, round(x0 + i * (w + gap), 1), y, round(w, 1), h, measure, label,
            ACCENTS[i % len(ACCENTS)], selo, bom or "sobe", dec=1 if measure in MOEDA_KPIS else None)


# ---------------------------------------------------------------------------
# Formatação comum de gráficos
# ---------------------------------------------------------------------------
def axis_objects(cat=True, val=True, val_show=True, legend=None, labels=False, label_units=None, cat_margin=None):
    o = {}
    if cat:
        cp = {"showAxisTitle": B(False), "fontSize": Dn(9), "labelColor": C(MUTED), "concatenateLabels": B(False)}
        if cat_margin:
            cp["maxMarginFactor"] = Ln(cat_margin)
        o["categoryAxis"] = [obj(cp)]
    if val:
        o["valueAxis"] = [obj({"show": B(val_show), "showAxisTitle": B(False), "fontSize": Dn(9),
                               "labelColor": C(SOFT), "gridlineShow": B(True), "gridlineColor": C(BORDER),
                               "gridlineStyle": S("dotted")})]
    if legend is None:
        o["legend"] = [obj({"show": B(False)})]
    else:
        o["legend"] = [obj({"show": B(True), "position": S(legend), "fontSize": Dn(9), "labelColor": C(MUTED),
                            "showTitle": B(False)})]
    if labels:
        p = {"show": B(True), "fontSize": Dn(9), "color": C("#334155")}
        if label_units:
            p["labelDisplayUnits"] = Dn(label_units)
        o["labels"] = [obj(p)]
    return o


def series_colors(colors):
    """{queryRef: cor} -> dataPoint com seletor por medida."""
    return [obj({"fill": C(c)}, {"metadata": q}) for q, c in colors.items()]


CAL_MES = COL("dim_calendario", "mes_ano")
SORT_MES = [sort_by(COL("dim_calendario", "mes_ano"), desc=False)]


def chart_line(page, name, x, y, w, h, title, measures, colors, styles=None, subtitle=None, area_first=True,
               smooth=True, markers=False):
    objs = axis_objects(legend="Top")
    objs["dataPoint"] = series_colors({f"_Medidas.{m}": colors[i] for i, m in enumerate(measures)})
    ls = [obj({"strokeWidth": Dn(2.5), "lineChartType": S("smooth" if smooth else "linear"),
               "showMarker": B(markers), "markerSize": Dn(4)})]
    if area_first:
        ls.append(obj({"areaShow": B(True), "strokeWidth": Dn(3)}, {"metadata": f"_Medidas.{measures[0]}"}))
    for m, st in (styles or {}).items():
        ls.append(obj({"lineStyle": S(st), "strokeWidth": Dn(2)}, {"metadata": f"_Medidas.{m}"}))
    objs["lineStyles"] = ls
    page.add(name, "lineChart", x, y, w, h,
             query=query({"Category": role(CAL_MES, active_first=True),
                          "Y": role(*[MEAS(m) for m in measures])}, sort=SORT_MES),
             objects=objs, vcobj=vco(title=title, subtitle=subtitle))


def chart_bar(page, name, x, y, w, h, title, cat_field, measure, color=TEAL, color_measure=None,
              tooltips=(), subtitle=None, vtype="clusteredBarChart", sort_desc=True, units=None):
    objs = axis_objects(val_show=False, labels=True, label_units=units, cat_margin=42)
    if color_measure:
        objs["dataPoint"] = [obj({"fill": CM(color_measure)},
                                 {"data": [{"dataViewWildcard": {"matchingOption": 1}}]})]
    else:
        objs["dataPoint"] = [obj({"fill": C(color)})]
    roles = {"Category": role(cat_field, active_first=True), "Y": role(MEAS(measure))}
    if tooltips:
        roles["Tooltips"] = role(*[MEAS(t) for t in tooltips])
    page.add(name, vtype, x, y, w, h,
             query=query(roles, sort=[sort_by(MEAS(measure), desc=True)] if sort_desc else
                         [sort_by(cat_field, desc=False)]),
             objects=objs, vcobj=vco(title=title, subtitle=subtitle))


def chart_columns(page, name, x, y, w, h, title, cat_field, measures, colors, subtitle=None,
                  vtype="clusteredColumnChart", series=None, legend="Top", sort=None):
    objs = axis_objects(legend=legend)
    if not series:
        objs["dataPoint"] = series_colors({f"_Medidas.{m}": colors[i] for i, m in enumerate(measures)})
    roles = {"Category": role(cat_field, active_first=True), "Y": role(*[MEAS(m) for m in measures])}
    if series:
        roles["Series"] = role(series)
    page.add(name, vtype, x, y, w, h,
             query=query(roles, sort=sort or [sort_by(cat_field, desc=False)]),
             objects=objs, vcobj=vco(title=title, subtitle=subtitle))


def chart_donut(page, name, x, y, w, h, title, cat_field, measure, subtitle=None):
    page.add(name, "donutChart", x, y, w, h,
             query=query({"Category": role(cat_field, active_first=True), "Y": role(MEAS(measure))},
                         sort=[sort_by(MEAS(measure), desc=True)]),
             objects={
                 "legend": [obj({"show": B(False)})],
                 "labels": [obj({"show": B(True), "labelStyle": S("Category, percent of total"), "fontSize": Dn(8.5),
                                 "color": C("#334155")})],
                 "slices": [obj({"innerRadiusRatio": Ln(60)})],
             },
             vcobj=vco(title=title, subtitle=subtitle))


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
ROW1_Y, ROW1_H = 88, 108
ROW2_Y, ROW2_H = 210, 254
ROW3_Y, ROW3_H = 478, 228


def cols(*widths, gap=16, x0=X0):
    """Divide a largura em colunas proporcionais -> lista de (x, w)."""
    total = X1 - x0 - gap * (len(widths) - 1)
    s = sum(widths)
    out, x = [], x0
    for wi in widths:
        w = round(total * wi / s)
        out.append((x, w))
        x += w + gap
    # ajusta a última coluna para fechar exatamente na margem
    lx, lw = out[-1]
    out[-1] = (lx, X1 - lx)
    return out


def page_visao_geral():
    p = Page("p01_visao_geral", "Visão Geral", "Visão Geral",
             "Como a empresa está?  Receita, lucro, despesas e metas em um só lugar.")
    sidebar(p)
    header(p, ["ano", "filial"])
    kpi_row(p, [
        ("receita", "Receita Líquida", "Receita líquida", "Receita"),
        ("lucro", "Lucro Bruto", "Lucro bruto", "Lucro Bruto"),
        ("despesas", "Despesas Totais", "Despesas totais", "Despesas", "desce"),
        ("resultado", "Resultado Operacional", "Resultado operacional", "Resultado"),
        ("margem", "Margem Operacional %", "Margem operacional", "Margem Op"),
    ])
    (xa, wa), (xb, wb) = cols(68, 32)
    chart_line(p, "g_receita_mensal", xa, ROW2_Y, wa, ROW2_H, "Receita líquida mês a mês",
               ["Receita Líquida", "Meta Receita", "Receita Líquida AA"],
               ["#0F766E", "#D97706", "#94A3B8"], styles={"Meta Receita": "dashed", "Receita Líquida AA": "dotted"},
               subtitle="Realizado x meta x mesmo período do ano anterior")
    p.add("g_medidor_meta", "gauge", xb, ROW2_Y, wb, ROW2_H,
          query=query({"Y": role(MEAS("Receita Líquida")),
                       "MaxValue": role(MEAS("Máximo do Medidor")),
                       "TargetValue": role(MEAS("Meta Receita (realizado)"))}),
          objects={
              "dataPoint": [obj({"fill": C(TEAL), "target": C(NAVY)})],
              "axis": [obj({"min": Dn(0)})],
              "calloutValue": [obj({"color": C(TEXT), "fontSize": Dn(20)})],
              "target": [obj({"color": C(NAVY), "fontSize": Dn(9)})],
              "labels": [obj({"color": C(SOFT), "fontSize": Dn(8)})],
          },
          vcobj=vco(title="Receita x meta do período", subtitle="O ponteiro escuro é a meta"))
    (x1, w1), (x2, w2), (x3, w3) = cols(36, 30, 34)
    chart_bar(p, "g_receita_filial", x1, ROW3_Y, w1, ROW3_H, "Receita por filial  •  cor = meta",
              COL("dim_filial", "filial"), "Receita Líquida", color_measure="Cor Atingimento",
              tooltips=("Atingimento da Meta %", "Margem Bruta %"), units=1000000)
    chart_donut(p, "g_receita_canal", x2, ROW3_Y, w2, ROW3_H, "Receita por canal",
                COL("dim_canal", "canal"), "Receita Líquida")
    p.add("c_destaques", "cardVisual", x3, ROW3_Y, w3, ROW3_H,
          query=query({"Data": role(MEAS("Melhor Filial"), MEAS("Filial em Atenção"),
                                    MEAS("Canal que Mais Cresce"), MEAS("Projeção de Receita do Ano"))}),
          objects={
              "layout": [obj({"columnCount": Ln(2), "rowCount": Ln(2), "orientation": Dn(0)}),
                         obj({"alignment": S("middle")}, DEF)],
              "value": [obj({"fontSize": Dn(13), "fontColor": C(TEXT), "fontFamily": S(FONT_SB)}, DEF)],
              "label": [obj({"show": B(True), "fontSize": Dn(8.5), "fontColor": C(MUTED)}, DEF)],
              "outline": [obj({"show": B(False)}, DEF)],
              "accentBar": [obj({"show": B(True), "position": S("Top"), "width": Dn(3), "color": C("#14B8A6")}, DEF)],
          },
          vcobj=vco(title="Destaques do período", subtitle="Gerados automaticamente pelas medidas"))
    return p


def page_vendas():
    p = Page("p02_vendas", "Vendas", "Vendas",
             "De onde vem o dinheiro?  Produtos, canais e vendedores que puxam o resultado.")
    sidebar(p)
    header(p, ["ano", "filial", "canal"])
    kpi_row(p, [
        ("pedidos", "Pedidos", "Pedidos", "Pedidos"),
        ("ticket", "Ticket Médio", "Ticket médio", "Ticket"),
        ("itens", "Itens Vendidos", "Itens vendidos", "Itens"),
        ("desconto", "Desconto Médio %", "Desconto médio", "Desconto", "desce"),
        ("devolucao", "Taxa de Devolução %", "Taxa de devolução", "Devolução", "desce"),
    ])
    (xa, wa), (xb, wb) = cols(42, 58)
    p.add("g_treemap_categorias", "treemap", xa, ROW2_Y, wa, ROW2_H,
          query=query({"Group": role(COL("dim_produto", "categoria"), active_first=True),
                       "Details": role(COL("dim_produto", "produto")),
                       "Values": role(MEAS("Receita Líquida"))},
                      sort=[sort_by(MEAS("Receita Líquida"))]),
          objects={"legend": [obj({"show": B(False)})],
                   "labels": [obj({"show": B(True), "fontSize": Dn(9)})],
                   "categoryLabels": [obj({"show": B(True), "fontSize": Dn(10)})]},
          vcobj=vco(title="Receita por categoria e produto", subtitle="Tamanho = receita líquida"))
    chart_columns(p, "g_mix_canais", xb, ROW2_Y, wb, ROW2_H, "Mix de canais mês a mês",
                  CAL_MES, ["Receita Líquida"], [], subtitle="Participação de cada canal na receita (100%)",
                  vtype="hundredPercentStackedColumnChart", series=COL("dim_canal", "canal"), legend="Top")
    (x1, w1), (x2, w2), (x3, w3) = cols(36, 30, 34)
    p.add("g_dispersao_produtos", "scatterChart", x1, ROW3_Y, w1, ROW3_H,
          query=query({"Category": role(COL("dim_produto", "produto"), active_first=True),
                       "Series": role(COL("dim_produto", "categoria")),
                       "X": role(MEAS("Receita Líquida")),
                       "Y": role(MEAS("Margem Bruta %")),
                       "Size": role(MEAS("Itens Vendidos"))}),
          objects={**axis_objects(legend="Top"),
                   "valueAxis": [obj({"showAxisTitle": B(True), "titleText": S("Margem bruta"), "fontSize": Dn(8),
                                      "labelColor": C(SOFT), "gridlineColor": C(BORDER), "gridlineStyle": S("dotted")})],
                   "categoryAxis": [obj({"showAxisTitle": B(True), "titleText": S("Receita líquida"),
                                         "fontSize": Dn(8), "labelColor": C(SOFT)})],
                   "legend": [obj({"show": B(True), "position": S("Top"), "fontSize": Dn(8), "labelColor": C(MUTED)})]},
          vcobj=vco(title="Produtos: receita x margem", subtitle="Bolha = itens vendidos"))
    chart_bar(p, "g_ranking_vendedores", x2, ROW3_Y, w2, ROW3_H, "Ranking de vendedores",
              COL("dim_vendedor", "nome_vendedor"), "Receita Líquida", color="#2563EB",
              tooltips=("Pedidos", "Ticket Médio"), units=1000000)
    p.add("g_decomposicao", "decompositionTreeVisual", x3, ROW3_Y, w3, ROW3_H,
          query=query({"Analyze": role(MEAS("Receita Líquida")),
                       "ExplainBy": role(COL("dim_canal", "canal"), COL("dim_produto", "categoria"),
                                         COL("dim_filial", "filial"), COL("dim_cliente", "segmento"))}),
          vcobj=vco(title="Explore a receita", subtitle="Clique no + para abrir por canal, categoria, filial..."))
    return p


def page_gastos():
    p = Page("p03_gastos", "Gastos & Orçamento", "Gastos & Orçamento",
             "Para onde vai o dinheiro?  Realizado x orçamento.")
    sidebar(p)
    header(p, ["ano", "filial", "depto", "tipo_custo"])
    kpi_row(p, [
        ("despesas", "Despesas Totais", "Despesas realizadas", "Despesas", "desce"),
        ("orcado", "Despesa Orçada (realizado)", "Orçado no período", "Orçado", "desce"),
        ("variacao", "Variação vs Orçado (R$)", "Variação vs orçado", "Execução"),
        ("execucao", "Execução do Orçamento %", "Execução do orçamento", "Execução"),
        ("desp_receita", "Despesas % da Receita", "Despesas / receita", "Desp Receita", "desce"),
    ])
    (xa, wa), (xb, wb) = cols(62, 38)
    chart_columns(p, "g_realizado_orcado", xa, ROW2_Y, wa, ROW2_H, "Realizado x orçado mês a mês",
                  CAL_MES, ["Despesas Totais", "Despesa Orçada"], ["#D97706", "#CBD5E1"],
                  subtitle="Meses futuros mostram só o orçamento")
    chart_donut(p, "g_grupos_dre", xb, ROW2_Y, wb, ROW2_H, "Despesas por grupo",
                COL("dim_categoria_despesa", "grupo"), "Despesas Totais")
    (x1, w1), (x2, w2) = cols(52, 48)
    heat = MEAS("Variação vs Orçado %")
    p.add("t_mapa_calor", "pivotTable", x1, ROW3_Y, w1, ROW3_H,
          query=query({"Rows": {"projections": [proj(COL("dim_departamento", "departamento"), active=True,
                                                     display="Departamento")]},
                       "Columns": {"projections": [proj(COL("dim_calendario", "trimestre"), active=True,
                                                        display="Trimestre")]},
                       "Values": {"projections": [proj(heat, display="Variação vs orçado")]}}),
          objects={
              "columnHeaders": [obj({"fontColor": C(MUTED), "backColor": C("#F8FAFC"), "fontSize": Dn(9),
                                     "columnAdjustment": S("growToFit"), "autoSizeColumnWidth": B(True)})],
              "rowHeaders": [obj({"fontColor": C(TEXT), "fontSize": Dn(9)})],
              "values": [
                  obj({"fontSize": Dn(9)}),
                  obj({"backColor": {"solid": {"color": {"expr": {"FillRule": {
                      "Input": heat,
                      "FillRule": {"linearGradient3": {
                          "min": {"color": {"Literal": {"Value": "'#99F6E4'"}}},
                          "mid": {"color": {"Literal": {"Value": "'#FFFFFF'"}}, "value": {"Literal": {"Value": "0D"}}},
                          "max": {"color": {"Literal": {"Value": "'#FCA5A5'"}}},
                          "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'noColor'"}}},
                      }}}}}}}},
                      {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "_Medidas.Variação vs Orçado %"}),
              ],
              "grid": [obj({"gridHorizontal": B(True), "gridHorizontalColor": C(BORDER), "rowPadding": Dn(4)})],
          },
          vcobj=vco(title="Mapa de calor: variação vs orçado", subtitle="Vermelho = gastou acima do orçado"))
    chart_bar(p, "g_categorias_despesa", x2, ROW3_Y, w2, ROW3_H, "Despesas por categoria",
              COL("dim_categoria_despesa", "categoria_despesa"), "Despesas Totais",
              color_measure="Cor do Orçamento", tooltips=("Execução do Orçamento %", "Despesa Orçada (realizado)"),
              subtitle="Cor = execução (vermelho acima de 105%)", units=1000)
    return p


def page_lucratividade():
    p = Page("p04_lucratividade", "Lucratividade", "Lucratividade (DRE)",
             "O que sobra?  Da receita bruta ao resultado operacional.")
    sidebar(p)
    header(p, ["ano", "filial"])
    kpi_row(p, [
        ("receita_bruta", "Receita Bruta", "Receita bruta", "Receita Bruta"),
        ("cmv", "CMV", "Custo das mercadorias", "CMV", "desce"),
        ("lucro_bruto", "Lucro Bruto", "Lucro bruto", "Lucro Bruto"),
        ("margem_bruta", "Margem Bruta %", "Margem bruta", "Margem Bruta"),
        ("margem_op", "Margem Operacional %", "Margem operacional", "Margem Op"),
    ])
    (xa, wa), (xb, wb) = cols(62, 38)
    p.add("g_cascata_dre", "waterfallChart", xa, ROW2_Y, wa, ROW2_H,
          query=query({"Category": role(COL("tbl_dre", "Linha"), active_first=True),
                       "Y": role(MEAS("Valor DRE"))},
                      sort=[sort_by(COL("tbl_dre", "Linha"), desc=False)]),
          objects={
              "sentimentColors": [obj({"increaseFill": C("#0F766E"), "decreaseFill": C("#F87171"),
                                       "totalFill": C(NAVY)})],
              "labels": [obj({"show": B(True), "labelDisplayUnits": Dn(1000000), "fontSize": Dn(8),
                              "color": C(MUTED)})],
              "legend": [obj({"show": B(False)})],
              **{k: v for k, v in axis_objects(val_show=False).items() if k != "legend"},
          },
          vcobj=vco(title="DRE em cascata", subtitle="Barra final (Total) = resultado operacional"))
    chart_line(p, "g_margens", xb, ROW2_Y, wb, ROW2_H, "Margens mês a mês",
               ["Margem Bruta %", "Margem Operacional %"], ["#0F766E", "#7C3AED"], area_first=False,
               subtitle="Bruta x operacional")
    (x1, w1), (x2, w2) = cols(38, 62)
    chart_bar(p, "g_margem_categoria", x1, ROW3_Y, w1, ROW3_H, "Margem bruta por categoria",
              COL("dim_produto", "categoria"), "Margem Bruta %", color="#7C3AED",
              tooltips=("Receita Líquida", "Lucro Bruto"))
    lucro = MEAS("Lucro Bruto")
    marg = MEAS("Margem Bruta %")
    p.add("t_produtos", "tableEx", x2, ROW3_Y, w2, ROW3_H,
          query=query({"Values": {"projections": [
              proj(COL("dim_produto", "produto"), display="Produto"),
              proj(MEAS("Receita Líquida"), display="Receita"), proj(lucro), proj(marg, display="Margem")]}},
              sort=[sort_by(lucro)]),
          objects={
              "columnHeaders": [obj({"fontColor": C(MUTED), "backColor": C("#F8FAFC"), "fontSize": Dn(9),
                                     "columnAdjustment": S("growToFit"), "autoSizeColumnWidth": B(True)})],
              "values": [
                  obj({"fontSize": Dn(9), "backColorSecondary": C("#F8FAFC")}),
                  obj({"fontColor": {"solid": {"color": {"expr": {"Conditional": {"Cases": [
                      {"Condition": {"Comparison": {"ComparisonKind": 3, "Left": marg,
                                                    "Right": {"Literal": {"Value": "0.1D"}}}},
                       "Value": {"Literal": {"Value": "'#B91C1C'"}}},
                      {"Condition": {"Comparison": {"ComparisonKind": 2, "Left": marg,
                                                    "Right": {"Literal": {"Value": "0.1D"}}}},
                       "Value": {"Literal": {"Value": "'#0F172A'"}}},
                  ]}}}}}},
                      {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "_Medidas.Margem Bruta %"}),
              ],
              "columnFormatting": [obj({"dataBars": {
                  "positiveColor": C("#99F6E4"), "negativeColor": C("#FCA5A5"), "axisColor": C(SOFT),
                  "reverseDirection": B(False), "hideText": B(False)}}, {"metadata": "_Medidas.Lucro Bruto"})],
              "grid": [obj({"gridHorizontal": B(True), "gridHorizontalColor": C(BORDER), "rowPadding": Dn(3)})],
          },
          vcobj=vco(title="Produtos por lucro bruto", subtitle="Margem abaixo de 10% em vermelho"))
    return p


def page_clientes():
    p = Page("p05_clientes", "Clientes", "Clientes & Pareto",
             "Quem paga as contas?  Concentração de receita, segmentos e novos clientes.")
    sidebar(p)
    header(p, ["ano", "filial", "canal"])
    kpi_row(p, [
        ("clientes", "Clientes Ativos", "Clientes ativos", "Clientes"),
        ("novos", "Novos Clientes", "Novos clientes"),
        ("rec_cliente", "Receita por Cliente", "Receita por cliente", "Receita Cliente"),
        ("ticket", "Ticket Médio", "Ticket médio", "Ticket"),
        ("concentracao", "Concentração Top 20 %", "Receita dos 20 maiores"),
    ])
    (xa, wa), (xb, wb) = cols(64, 36)
    top = MEAS("Receita Top 20 Clientes")
    p.add("g_pareto", "lineClusteredColumnComboChart", xa, ROW2_Y, wa, ROW2_H,
          query=query({"Category": role(COL("dim_cliente", "nome_cliente"), active_first=True),
                       "Y": role(top), "Y2": role(MEAS("% Acumulado (Top 20)"))},
                      sort=[sort_by(top)]),
          objects={**axis_objects(legend="Top"),
                   "dataPoint": series_colors({"_Medidas.Receita Top 20 Clientes": "#0F766E",
                                               "_Medidas.% Acumulado (Top 20)": "#D97706"}),
                   "lineStyles": [obj({"strokeWidth": Dn(2.5), "showMarker": B(True), "markerSize": Dn(4)})],
                   "categoryAxis": [obj({"showAxisTitle": B(False), "fontSize": Dn(8), "labelColor": C(MUTED),
                                         "maxMarginFactor": Ln(40)})]},
          vcobj=vco(title="Pareto: 20 maiores clientes", subtitle="Colunas = receita  •  linha = % acumulado da receita total"))
    chart_donut(p, "g_segmentos", xb, ROW2_Y, wb, ROW2_H, "Receita por segmento",
                COL("dim_cliente", "segmento"), "Receita Líquida")
    (x1, w1), (x2, w2) = cols(40, 60)
    chart_columns(p, "g_novos_clientes", x1, ROW3_Y, w1, ROW3_H, "Novos clientes por mês",
                  CAL_MES, ["Novos Clientes"], ["#2563EB"], legend=None)
    rec = MEAS("Receita Líquida")
    p.add("t_clientes", "tableEx", x2, ROW3_Y, w2, ROW3_H,
          query=query({"Values": {"projections": [
              proj(COL("dim_cliente", "nome_cliente"), display="Cliente"),
              proj(COL("dim_cliente", "segmento"), display="Segmento"),
              proj(COL("dim_cliente", "uf"), display="UF"), proj(rec, display="Receita"),
              proj(MEAS("Pedidos")), proj(MEAS("Classe ABC"), display="Classe")]}},
              sort=[sort_by(rec)]),
          objects={
              "columnHeaders": [obj({"fontColor": C(MUTED), "backColor": C("#F8FAFC"), "fontSize": Dn(9),
                                     "columnAdjustment": S("growToFit"), "autoSizeColumnWidth": B(True)})],
              "values": [obj({"fontSize": Dn(9), "backColorSecondary": C("#F8FAFC")})],
              "columnFormatting": [obj({"dataBars": {
                  "positiveColor": C("#BFDBFE"), "negativeColor": C("#FCA5A5"), "axisColor": C(SOFT),
                  "reverseDirection": B(False), "hideText": B(False)}}, {"metadata": "_Medidas.Receita Líquida"})],
              "grid": [obj({"gridHorizontal": B(True), "gridHorizontalColor": C(BORDER), "rowPadding": Dn(3)})],
          },
          vcobj=vco(title="Carteira de clientes", subtitle="Classe ABC pela curva de Pareto"))
    return p


def page_pessoas():
    p = Page("p06_pessoas", "Pessoas", "Pessoas",
             "Quem faz acontecer?  Quadro de funcionários, rotatividade e produtividade.")
    sidebar(p)
    header(p, ["ano", "filial", "depto"])
    kpi_row(p, [
        ("headcount", "Headcount (fim do período)", "Funcionários", "Headcount"),
        ("turnover", "Turnover %", "Turnover no período", "Turnover", "desce"),
        ("custo_func", "Custo de Pessoal por Funcionário", "Custo por funcionário", "Custo Pessoal", "desce"),
        ("receita_func", "Receita por Funcionário", "Receita por funcionário", "Receita Func"),
        ("vagas", "Vagas em Aberto", "Vagas em aberto"),
    ])
    (xa, wa), (xb, wb) = cols(62, 38)
    chart_columns(p, "g_headcount_depto", xa, ROW2_Y, wa, ROW2_H, "Funcionários por departamento",
                  CAL_MES, ["Headcount Mensal"], [], vtype="columnChart",
                  series=COL("dim_departamento", "departamento"), legend="Top",
                  subtitle="Foto do quadro no fim de cada mês")
    chart_bar(p, "g_turnover_depto", xb, ROW2_Y, wb, ROW2_H, "Turnover por departamento",
              COL("dim_departamento", "departamento"), "Turnover %", color="#DB2777",
              tooltips=("Total de Desligamentos", "Headcount Médio"))
    (x1, w1), (x2, w2) = cols(52, 48)
    chart_line(p, "g_admissoes", x1, ROW3_Y, w1, ROW3_H, "Admissões x desligamentos",
               ["Total de Admissões", "Total de Desligamentos"], ["#059669", "#DC2626"], area_first=False,
               smooth=False, markers=True)
    p.add("g_produtividade_filial", "scatterChart", x2, ROW3_Y, w2, ROW3_H,
          query=query({"Category": role(COL("dim_filial", "filial"), active_first=True),
                       "X": role(MEAS("Custo de Pessoal por Funcionário")),
                       "Y": role(MEAS("Receita por Funcionário")),
                       "Size": role(MEAS("Headcount Médio"))}),
          objects={
              "categoryAxis": [obj({"showAxisTitle": B(True), "titleText": S("Custo por funcionário"),
                                    "fontSize": Dn(8), "labelColor": C(SOFT)})],
              "valueAxis": [obj({"showAxisTitle": B(True), "titleText": S("Receita por funcionário"),
                                 "fontSize": Dn(8), "labelColor": C(SOFT), "gridlineColor": C(BORDER),
                                 "gridlineStyle": S("dotted")})],
              "categoryLabels": [obj({"show": B(True), "fontSize": Dn(8), "color": C(MUTED)})],
              "dataPoint": [obj({"fill": C("#2563EB")})],
              "legend": [obj({"show": B(False)})],
          },
          vcobj=vco(title="Produtividade por filial", subtitle="Acima e à esquerda = mais receita com menos custo"))
    return p


def page_simulador():
    p = Page("p07_simulador", "Simulador", "Simulador de Cenários",
             "E se...?  Mexa nas alavancas e veja o impacto no resultado.")
    sidebar(p)
    header(p, ["ano", "filial"])
    px, pw = X0, 290
    # painel das alavancas
    p.add("painel_alavancas", "shape", px, ROW1_Y, pw, H - ROW1_Y - 14, objects={
        "shape": [obj({"tileShape": S("rectangleRounded"), "roundEdge": Ln(10)}),
                  obj({"tileShape": S("rectangleRounded")}, DEF)],
        "fill": [obj({"show": B(True), "fillColor": C(CARD), "transparency": Dn(0)}, DEF)],
        "outline": [obj({"show": B(True), "lineColor": C(BORDER), "weight": Dn(1)}, DEF)],
    }, vcobj=vco(bg=False, border=False, shadow=True, pad=(0, 0, 0, 0), header=False))
    textbox(p, "painel_titulo", px + 16, ROW1_Y + 12, pw - 32, 52, [
        ([("Alavancas do cenário", FONT_B, 12, TEXT, True)], "left"),
        ([("Clique em um percentual para simular", FONT, 9, MUTED, False)], "left"),
    ])
    sliders = [
        ("preco", "par_preco", "Variação de Preço", "Preço de venda"),
        ("volume", "par_volume", "Variação de Volume", "Volume vendido"),
        ("custo", "par_custo", "Variação do Custo", "Custo das mercadorias"),
        ("despesa", "par_despesa", "Variação das Despesas", "Despesas"),
    ]
    for i, (k, t, c, lbl) in enumerate(sliders):
        y = ROW1_Y + 70 + i * 104
        fld = COL(t, c)
        p.add(f"alavanca_{k}", "advancedSlicerVisual", px + 12, y, pw - 24, 92,
              query=query({"Values": {"projections": [proj(fld)]}}),
              objects={
                  "layout": [obj({"rowCount": Ln(1), "columnCount": Ln(5)})],
                  "shapeCustomRectangle": [obj({"tileShape": S("rectangleRoundedByPixel"),
                                                "rectangleRoundedCurve": Ln(6)}, DEF)],
                  "fillCustom": [
                      obj({"show": B(True)}),
                      obj({"fillColor": C("#FFFFFF"), "transparency": Dn(0)}, DEF),
                      obj({"fillColor": C(TEAL), "transparency": Dn(0)}, {"id": "selection:selected"}),
                  ],
                  "value": [
                      obj({"fontColor": C("#334155"), "fontSize": Dn(10), "fontFamily": S(FONT_SB)}, DEF),
                      obj({"fontColor": C("#FFFFFF"), "bold": B(True)}, {"id": "selection:selected"}),
                  ],
                  "outline": [obj({"show": B(True), "lineColor": C(BORDER), "weight": Dn(1)}, DEF),
                              obj({"lineColor": C(TEAL)}, {"id": "selection:selected"})],
                  "selection": [obj({"singleSelect": B(True)})],
                  "general": [obj({"filter": {"filter": {
                      "Version": 2,
                      "From": [{"Name": "p", "Entity": t, "Type": 0}],
                      "Where": [{"Condition": {"In": {
                          "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "p"}}, "Property": c}}],
                          "Values": [[{"Literal": {"Value": "0D"}}]],
                      }}}],
                  }}})],
              },
              vcobj=vco(title=lbl, title_size=10, bg=True, bg_color="#F8FAFC", border=True, shadow=False,
                        pad=(6, 8, 10, 10), header=False))
    textbox(p, "painel_nota", px + 16, ROW1_Y + 70 + 4 * 104 + 6, pw - 32, 64, [
        ([("Despesas variáveis acompanham o volume; as fixas não. "
           "Simulação rápida para decisão, não projeção contábil.", FONT, 8, MUTED, False)], "left"),
    ])
    sx0 = px + pw + 16
    kpi_row(p, [
        ("rec_cenario", "Receita Líquida (Cenário)", "Receita no cenário"),
        ("res_cenario", "Resultado (Cenário)", "Resultado no cenário", "Cenário"),
        ("delta", "Δ Resultado vs Atual", "Diferença vs atual"),
        ("margem_cenario", "Margem Operacional (Cenário)", "Margem no cenário"),
    ], x0=sx0)
    sw = X1 - sx0
    p.add("g_cascata_alavancas", "waterfallChart", sx0, ROW2_Y, sw, ROW2_H,
          query=query({"Category": role(COL("tbl_alavancas", "Etapa"), active_first=True),
                       "Y": role(MEAS("Valor Alavanca"))},
                      sort=[sort_by(COL("tbl_alavancas", "Etapa"), desc=False)]),
          objects={
              "sentimentColors": [obj({"increaseFill": C("#0F766E"), "decreaseFill": C("#F87171"),
                                       "totalFill": C("#7C3AED")})],
              "labels": [obj({"show": B(True), "labelDisplayUnits": Dn(1000000), "fontSize": Dn(9),
                              "color": C(MUTED)})],
              "legend": [obj({"show": B(False)})],
              **{k: v for k, v in axis_objects(val_show=False).items() if k != "legend"},
          },
          vcobj=vco(title="Do resultado atual ao cenário", subtitle="Total = resultado no cenário simulado"))
    chart_columns(p, "g_resultado_trimestre", sx0, ROW3_Y, sw, ROW3_H, "Resultado por trimestre: atual x cenário",
                  COL("dim_calendario", "ano_tri"), ["Resultado Operacional", "Resultado (Cenário)"],
                  ["#94A3B8", "#7C3AED"])
    return p


def build_pages():
    return [page_visao_geral(), page_vendas(), page_gastos(), page_lucratividade(),
            page_clientes(), page_pessoas(), page_simulador()]


# ---------------------------------------------------------------------------
# Tema
# ---------------------------------------------------------------------------
def theme(name):
    sc = lambda c: {"solid": {"color": c}}
    return {
        "name": name,
        "dataColors": ["#0F766E", "#2563EB", "#D97706", "#7C3AED", "#DB2777", "#059669", "#EA580C",
                       "#64748B", "#0EA5E9", "#84CC16", "#F43F5E", "#A855F7"],
        "good": "#15803D", "neutral": "#D97706", "bad": "#DC2626",
        "maximum": "#0F766E", "center": "#FDE68A", "minimum": "#FCA5A5", "null": "#CBD5E1",
        "foreground": TEXT, "foregroundNeutralSecondary": MUTED, "foregroundNeutralTertiary": SOFT,
        "background": CARD, "backgroundLight": "#F8FAFC", "backgroundNeutral": BORDER,
        "tableAccent": TEAL,
        "textClasses": {
            "callout": {"fontSize": 22, "fontFace": FONT_SB, "color": TEXT},
            "title": {"fontSize": 11, "fontFace": FONT_SB, "color": TEXT},
            "header": {"fontSize": 11, "fontFace": FONT_SB, "color": TEXT},
            "label": {"fontSize": 9, "fontFace": FONT, "color": "#334155"},
        },
        "visualStyles": {
            "*": {"*": {
                "title": [{"show": True, "fontColor": sc(TEXT), "fontSize": 11, "fontFamily": FONT_SB,
                           "alignment": "left"}],
                "background": [{"show": True, "color": sc(CARD), "transparency": 0}],
                "border": [{"show": True, "color": sc(BORDER), "radius": 10, "width": 1}],
                "padding": [{"top": 8, "bottom": 8, "left": 12, "right": 12}],
                "visualHeader": [{"background": sc(CARD), "border": sc(CARD), "foreground": sc(MUTED)}],
                "visualTooltip": [{"background": sc(NAVY), "titleFontColor": sc("#CBD5E1"),
                                   "valueFontColor": sc("#FFFFFF")}],
                "outspacePane": [{"backgroundColor": sc("#FFFFFF"), "foregroundColor": sc(TEXT),
                                  "transparency": 0, "border": True, "borderColor": sc(BORDER)}],
                "filterCard": [
                    {"$id": "Applied", "backgroundColor": sc("#F0FDFA"), "foregroundColor": sc(TEXT),
                     "transparency": 0, "border": True, "borderColor": sc("#99F6E4")},
                    {"$id": "Available", "backgroundColor": sc("#FFFFFF"), "foregroundColor": sc(TEXT),
                     "transparency": 0, "border": True, "borderColor": sc(BORDER)},
                ],
            }},
            "page": {"*": {
                "background": [{"color": sc(PAGE_BG), "transparency": 0}],
                "outspace": [{"color": sc("#E2E8F0"), "transparency": 0}],
            }},
            "slicer": {"*": {
                "header": [{"fontFamily": FONT_SB, "textSize": 9, "fontColor": sc(MUTED)}],
                "items": [{"fontFamily": FONT, "textSize": 10, "fontColor": sc(TEXT)}],
            }},
            "tableEx": {"*": {
                "columnHeaders": [{"autoSizeColumnWidth": True, "columnAdjustment": "growToFit"}],
            }},
            "pivotTable": {"*": {
                "columnHeaders": [{"autoSizeColumnWidth": True, "columnAdjustment": "growToFit"}],
            }},
        },
    }


# ---------------------------------------------------------------------------
# Escrita dos arquivos
# ---------------------------------------------------------------------------
def write_report(root, report_name, model_folder, base_theme_path):
    import os
    import shutil

    def wj(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    rep = os.path.join(root, f"{report_name}.Report")
    if os.path.exists(rep):
        shutil.rmtree(rep)
    theme_file = "EmpresaX-Executivo-7b3e91c4.json"

    wj(os.path.join(rep, "definition.pbir"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{model_folder}"}},
    })
    wj(os.path.join(rep, ".platform"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": report_name},
        "config": {"version": "2.0", "logicalId": "8a1d6c52-3f0b-4f5e-9e9e-2d4d7b0c1a11"},
    })
    d = os.path.join(rep, "definition")
    wj(os.path.join(d, "version.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    })
    rv = {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"}
    wj(os.path.join(d, "report.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": rv, "type": "SharedResources"},
            "customTheme": {"name": theme_file, "reportVersionAtImport": rv, "type": "RegisteredResources"},
        },
        "objects": {"outspacePane": [obj({"expanded": B(False), "visible": B(True)})]},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": theme_file, "path": theme_file, "type": "CustomTheme"}]},
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "defaultFilterActionIsDataFilter": True,
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "allowInlineExploration": True,
            "useEnhancedTooltips": True,
        },
    })
    pages = build_pages()
    wj(os.path.join(d, "pages", "pages.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.id for p in pages],
        "activePageName": pages[0].id,
    })
    nvis = 0
    for p in pages:
        wj(os.path.join(d, "pages", p.id, "page.json"), {
            "$schema": PAGE_SCHEMA,
            "name": p.id,
            "displayName": p.display,
            "displayOption": "FitToPage",
            "height": H,
            "width": W,
            "objects": {
                "background": [obj({"color": C(PAGE_BG), "transparency": Dn(0)})],
                "outspace": [obj({"color": C("#E2E8F0"), "transparency": Dn(0)})],
            },
        })
        names = set()
        for v in p.visuals:
            assert v["name"] not in names, (p.id, v["name"])
            names.add(v["name"])
            wj(os.path.join(d, "pages", p.id, "visuals", v["name"], "visual.json"), v)
            nvis += 1
    sr = os.path.join(rep, "StaticResources")
    os.makedirs(os.path.join(sr, "SharedResources", "BaseThemes"), exist_ok=True)
    shutil.copy(base_theme_path, os.path.join(sr, "SharedResources", "BaseThemes", "CY24SU10.json"))
    wj(os.path.join(sr, "RegisteredResources", theme_file), theme(theme_file))
    return rep, len(pages), nvis
