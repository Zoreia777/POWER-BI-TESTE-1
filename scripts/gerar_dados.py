#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de dados sintéticos da EMPRESA X
=========================================

Cria um modelo estrela completo (dimensões + fatos) para alimentar o Power BI:

  * data/*.csv                      -> tabelas prontas para importar
  * database/empresa_x.db           -> o mesmo conteúdo em SQLite (com views)
  * powerbi/consultas_m/**/*.pq     -> consultas Power Query (GitHub e pasta local)

Tudo é reproduzível (semente fixa). Para gerar tudo de novo:

    pip install -r requirements.txt
    python scripts/gerar_dados.py

Os dados são 100% fictícios. Alguns "easter eggs" foram plantados de propósito
(veja o README) para que os dashboards tenham histórias para contar.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuração geral
# --------------------------------------------------------------------------- #
SEED = 2026
rng = np.random.default_rng(SEED)

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"
PASTA_BANCO = RAIZ / "database"
PASTA_SQL = RAIZ / "sql"
PASTA_M = RAIZ / "powerbi" / "consultas_m"

DATA_INICIO = date(2024, 1, 1)
DATA_CORTE = date(2026, 9, 30)      # último dia "realizado"
DATA_FIM = date(2026, 12, 31)       # calendário/orçamento/metas vão até aqui
N_MESES_REAL = 33                   # jan/2024 .. set/2026

N_CLIENTES = 650
PEDIDOS_BASE_DIA = 34.0             # calibrado para ~R$ 3-5 mi/mês de receita líquida
CRESCIMENTO_MENSAL = 0.011
SAZONALIDADE = {1: 0.88, 2: 0.84, 3: 0.95, 4: 0.97, 5: 1.00, 6: 0.97,
                7: 0.98, 8: 1.02, 9: 1.03, 10: 1.08, 11: 1.38, 12: 1.30}
DOW = [1.0, 1.08, 1.08, 1.05, 1.0, 0.60, 0.28]   # seg..dom

# Parâmetros de custo (ajustados após calibração)
DIV_COM = 500_000      # 1 vendedor/atendente a cada R$ 500 mil de receita esperada/mês
DIV_OPS = 800_000
PCT_COMISSAO = 0.018
PCT_MARKETING = 0.034
PCT_EVENTOS = 0.009
PCT_VIAGENS = 0.009


# --------------------------------------------------------------------------- #
# Utilidades de data
# --------------------------------------------------------------------------- #
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
DIAS_ABREV = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def primeiro_dia(d: date) -> date:
    return date(d.year, d.month, 1)


def add_meses(d: date, n: int) -> date:
    k = d.year * 12 + (d.month - 1) + n
    return date(k // 12, k % 12 + 1, 1)


def ultimo_dia(d: date) -> date:
    return add_meses(primeiro_dia(d), 1) - timedelta(days=1)


def lista_meses(ini: date, fim: date) -> list[date]:
    out, d = [], primeiro_dia(ini)
    while d <= fim:
        out.append(d)
        d = add_meses(d, 1)
    return out


def idx_mes(d: date) -> int:
    return (d.year - DATA_INICIO.year) * 12 + d.month - 1


def pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados(ano: int) -> dict[date, str]:
    p = pascoa(ano)
    return {
        date(ano, 1, 1): "Confraternização Universal",
        p - timedelta(days=48): "Carnaval",
        p - timedelta(days=47): "Carnaval",
        p - timedelta(days=2): "Sexta-feira Santa",
        date(ano, 4, 21): "Tiradentes",
        date(ano, 5, 1): "Dia do Trabalho",
        p + timedelta(days=60): "Corpus Christi",
        date(ano, 9, 7): "Independência do Brasil",
        date(ano, 10, 12): "Nossa Senhora Aparecida",
        date(ano, 11, 2): "Finados",
        date(ano, 11, 15): "Proclamação da República",
        date(ano, 11, 20): "Consciência Negra",
        date(ano, 12, 25): "Natal",
    }


FERIADOS: dict[date, str] = {}
for _a in range(DATA_INICIO.year, DATA_FIM.year + 1):
    FERIADOS.update(feriados(_a))


def black_friday(ano: int) -> date:
    d = date(ano, 11, 30)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


BLACK_FRIDAYS = {black_friday(a) for a in range(DATA_INICIO.year, DATA_FIM.year + 1)}


# --------------------------------------------------------------------------- #
# Dimensões
# --------------------------------------------------------------------------- #
def construir_calendario() -> pd.DataFrame:
    linhas = []
    d = DATA_INICIO
    while d <= DATA_FIM:
        fer = FERIADOS.get(d, "")
        fds = int(d.weekday() >= 5)
        linhas.append({
            "data": d,
            "ano": d.year,
            "semestre": f"S{(d.month - 1) // 6 + 1}",
            "trimestre": f"T{(d.month - 1) // 3 + 1}",
            "mes_num": d.month,
            "mes_nome": MESES[d.month - 1].capitalize(),
            "mes_abrev": MESES_ABREV[d.month - 1].capitalize(),
            "ano_mes": f"{d.year}-{d.month:02d}",
            "mes_ano": f"{MESES_ABREV[d.month - 1]}/{str(d.year)[2:]}",
            "ordem_ano_mes": d.year * 100 + d.month,
            "dia": d.day,
            "dia_semana_num": d.weekday() + 1,
            "dia_semana": DIAS[d.weekday()].capitalize(),
            "dia_semana_abrev": DIAS_ABREV[d.weekday()].capitalize(),
            "semana_do_ano": d.isocalendar()[1],
            "fim_de_semana": fds,
            "feriado": fer,
            "dia_util": int(not fds and not fer),
            "realizado": int(d <= DATA_CORTE),
            "status_periodo": "Realizado" if d <= DATA_CORTE else "Projetado",
            "primeiro_dia_mes": primeiro_dia(d),
        })
        d += timedelta(days=1)
    return pd.DataFrame(linhas)


FILIAIS = [
    # id, nome, cidade, uf, região, tipo, abertura, lat, lon, peso
    (1, "São Paulo (Matriz)", "São Paulo", "SP", "Sudeste", "Matriz", date(2019, 3, 1), -23.5505, -46.6333, 0.30),
    (2, "Rio de Janeiro", "Rio de Janeiro", "RJ", "Sudeste", "Filial", date(2020, 8, 3), -22.9068, -43.1729, 0.15),
    (3, "Belo Horizonte", "Belo Horizonte", "MG", "Sudeste", "Filial", date(2021, 2, 1), -19.9167, -43.9345, 0.11),
    (4, "Curitiba", "Curitiba", "PR", "Sul", "Filial", date(2021, 9, 1), -25.4284, -49.2733, 0.10),
    (5, "Porto Alegre", "Porto Alegre", "RS", "Sul", "Filial", date(2022, 4, 1), -30.0346, -51.2177, 0.08),
    (6, "Brasília", "Brasília", "DF", "Centro-Oeste", "Filial", date(2022, 11, 1), -15.7939, -47.8828, 0.09),
    (7, "Salvador", "Salvador", "BA", "Nordeste", "Filial", date(2025, 2, 3), -12.9714, -38.5014, 0.09),
    (8, "Recife", "Recife", "PE", "Nordeste", "Filial", date(2024, 6, 3), -8.0476, -34.8770, 0.08),
]
FIL = [dict(id=f[0], nome=f[1], cidade=f[2], uf=f[3], regiao=f[4], tipo=f[5],
            abertura=f[6], lat=f[7], lon=f[8], peso=f[9]) for f in FILIAIS]
FIL_POR_ID = {f["id"]: f for f in FIL}

CIDADES_UF = {
    "SP": ["Campinas", "Santos", "Ribeirão Preto", "São José dos Campos", "Sorocaba"],
    "RJ": ["Niterói", "Petrópolis", "Volta Redonda"],
    "MG": ["Contagem", "Uberlândia", "Juiz de Fora"],
    "PR": ["Londrina", "Maringá", "Ponta Grossa"],
    "RS": ["Canoas", "Caxias do Sul", "Pelotas"],
    "DF": ["Taguatinga", "Águas Claras", "Ceilândia"],
    "BA": ["Feira de Santana", "Lauro de Freitas", "Vitória da Conquista"],
    "PE": ["Olinda", "Jaboatão dos Guararapes", "Caruaru"],
}

CANAIS = [(1, "Loja Física", "Físico"), (2, "E-commerce", "Digital"),
          (3, "Televendas B2B", "Remoto"), (4, "Marketplace", "Digital")]

DEPARTAMENTOS = [
    (1, "Comercial", "CC-100", "Área-fim"),
    (2, "Marketing", "CC-200", "Área-fim"),
    (3, "Tecnologia da Informação", "CC-300", "Suporte"),
    (4, "Recursos Humanos", "CC-400", "Suporte"),
    (5, "Financeiro", "CC-500", "Suporte"),
    (6, "Operações & Logística", "CC-600", "Área-fim"),
    (7, "Administrativo", "CC-700", "Suporte"),
    (8, "Pesquisa & Desenvolvimento", "CC-800", "Área-fim"),
]

CATEGORIAS_DESPESA = [
    # id, categoria, grupo DRE, tipo de custo, ordem no DRE
    (1, "Salários", "Despesas com Pessoal", "Fixa", 1),
    (2, "Encargos Sociais", "Despesas com Pessoal", "Fixa", 1),
    (3, "Benefícios", "Despesas com Pessoal", "Fixa", 1),
    (4, "Comissões", "Despesas Comerciais", "Variável", 2),
    (5, "Marketing Digital", "Despesas Comerciais", "Variável", 2),
    (6, "Eventos & Patrocínios", "Despesas Comerciais", "Variável", 2),
    (7, "Frete & Logística", "Despesas Operacionais", "Variável", 3),
    (8, "Manutenção & Reparos", "Despesas Operacionais", "Fixa", 3),
    (9, "Aluguel", "Despesas Administrativas", "Fixa", 4),
    (10, "Energia, Água & Internet", "Despesas Administrativas", "Fixa", 4),
    (11, "Software & Licenças", "Despesas Administrativas", "Fixa", 4),
    (12, "Consultoria & Terceiros", "Despesas Administrativas", "Variável", 4),
    (13, "Viagens & Deslocamentos", "Despesas Administrativas", "Variável", 4),
    (14, "Treinamento", "Despesas Administrativas", "Variável", 4),
    (15, "Seguros", "Despesas Administrativas", "Fixa", 4),
    (16, "Material de Escritório", "Despesas Administrativas", "Variável", 4),
    (17, "Tarifas de Pagamento & Marketplace", "Despesas Financeiras", "Variável", 5),
    (18, "Juros & Tarifas Bancárias", "Despesas Financeiras", "Fixa", 5),
]

PRIMEIROS = ["Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela",
             "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia", "Paulo", "Queila", "Rafael",
             "Sofia", "Thiago", "Úrsula", "Vinícius", "Wesley", "Yasmin", "Zeca", "Beatriz", "Caio",
             "Débora", "Eduardo", "Fernanda", "Gustavo", "Helena", "Igor", "Juliana", "Leonardo"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Rodrigues", "Almeida", "Nascimento",
              "Lima", "Araújo", "Fernandes", "Carvalho", "Gomes", "Martins", "Rocha", "Ribeiro", "Alves",
              "Monteiro", "Mendes", "Barros", "Freitas", "Barbosa", "Pinto", "Moreira", "Cavalcanti",
              "Dias", "Castro", "Campos", "Cardoso"]
PREFIXOS_EMP = ["Aurora", "Vértice", "Nexo", "Horizonte", "Atlas", "Prisma", "Orbital", "Sigma", "Delta", "Alfa",
                "Bússola", "Cadência", "Domínio", "Estrela", "Fênix", "Granito", "Helix", "Íris", "Jaguar",
                "Kappa", "Lumen", "Mosaico", "Nimbus", "Ômega", "Pioneira", "Quasar", "Radar", "Solaris",
                "Topázio", "Unidade", "Vanguarda", "Zênite"]
SUFIXOS_EMP = ["Tecnologia", "Engenharia", "Consultoria", "Comércio", "Serviços", "Logística", "Educação",
               "Saúde", "Construções", "Alimentos", "Advocacia", "Contabilidade", "Agro", "Digital", "Indústria"]
FORMAS_EMP = ["Ltda", "S.A.", "ME", "EPP"]


def nome_pessoa(usados: set[str]) -> str:
    while True:
        n = f"{rng.choice(PRIMEIROS)} {rng.choice(SOBRENOMES)}"
        if rng.random() < 0.6:
            n += f" {rng.choice(SOBRENOMES)}"
        if n not in usados:
            usados.add(n)
            return n


def nome_empresa(usados: set[str]) -> str:
    while True:
        n = f"{rng.choice(PREFIXOS_EMP)} {rng.choice(SUFIXOS_EMP)} {rng.choice(FORMAS_EMP)}"
        if n not in usados:
            usados.add(n)
            return n


# --- Produtos ---------------------------------------------------------------
PREFIXO_SKU = {"Eletrônicos": "ELE", "Escritório": "ESC", "Casa & Conforto": "CAS",
               "Software & Assinaturas": "SFT", "Serviços": "SRV"}
ALIQUOTA = {"Eletrônicos": 0.18, "Escritório": 0.17, "Casa & Conforto": 0.17,
            "Software & Assinaturas": 0.09, "Serviços": 0.08}
DEV_BASE = {"Eletrônicos": 0.025, "Escritório": 0.020, "Casa & Conforto": 0.030,
            "Software & Assinaturas": 0.010, "Serviços": 0.005}


def P(cat, nome, sub, preco, ratio, pop, ic=0.0015, ip=0.0015, dev=None):
    return dict(cat=cat, nome=nome, sub=sub, preco=preco, ratio=ratio, pop=pop,
                ic=ic, ip=ip, dev=DEV_BASE[cat] if dev is None else dev)


CATALOGO = [
    # ---- Eletrônicos
    P("Eletrônicos", 'Notebook Pro 14"', "Computadores", 7490, 0.62, 3, ic=0.0045, ip=0.0020),
    P("Eletrônicos", 'Notebook Essencial 15"', "Computadores", 3890, 0.62, 5),
    P("Eletrônicos", 'Monitor 24" Full HD', "Monitores", 1090, 0.60, 6),
    P("Eletrônicos", 'Monitor 27" 4K', "Monitores", 2490, 0.60, 3),
    P("Eletrônicos", "Teclado Mecânico Pro", "Periféricos", 490, 0.55, 6),
    P("Eletrônicos", "Mouse Ergonômico Sem Fio", "Periféricos", 220, 0.52, 7),
    P("Eletrônicos", "Webcam Full HD", "Periféricos", 260, 0.55, 4),
    P("Eletrônicos", "Headset Profissional", "Áudio", 390, 0.56, 5),
    P("Eletrônicos", "Smartphone X Lite", "Smartphones", 1890, 0.64, 6, dev=0.040),
    P("Eletrônicos", "Smartphone X Max", "Smartphones", 5290, 0.64, 4, ic=0.0100, ip=0.0),
    P("Eletrônicos", 'Tablet 10"', "Tablets", 1790, 0.62, 4),
    P("Eletrônicos", "Impressora Multifuncional", "Impressão", 1390, 0.60, 3),
    # ---- Escritório
    P("Escritório", "Cadeira Ergonômica Presidente", "Mobiliário", 1790, 0.46, 6),
    P("Escritório", "Mesa Regulável Elétrica", "Mobiliário", 2490, 0.46, 4),
    P("Escritório", "Mesa de Reunião 8 Lugares", "Mobiliário", 3890, 0.48, 2),
    P("Escritório", "Armário Arquivo 4 Gavetas", "Mobiliário", 890, 0.45, 3),
    P("Escritório", "Luminária LED de Mesa", "Iluminação", 190, 0.42, 6),
    P("Escritório", "Suporte Articulado p/ Monitor", "Acessórios", 290, 0.40, 6),
    P("Escritório", "Kit Papelaria Premium", "Papelaria", 120, 0.40, 8),
    P("Escritório", "Quadro Branco Magnético", "Acessórios", 390, 0.44, 4),
    P("Escritório", "Divisória Acústica", "Mobiliário", 690, 0.46, 3),
    # ---- Casa & Conforto
    P("Casa & Conforto", "Cafeteira Expresso Automática", "Eletroportáteis", 1690, 0.53, 5),
    P("Casa & Conforto", "Purificador de Água", "Eletroportáteis", 990, 0.52, 5),
    P("Casa & Conforto", "Ar-condicionado Split 12000 BTU", "Climatização", 2890, 0.56, 4),
    P("Casa & Conforto", "Ventilador Torre Silencioso", "Climatização", 390, 0.52, 6),
    P("Casa & Conforto", "Aspirador Robô", "Eletroportáteis", 1890, 0.55, 3),
    P("Casa & Conforto", "Fritadeira Elétrica 6L", "Eletroportáteis", 490, 0.50, 6),
    P("Casa & Conforto", "Kit Smart Lâmpadas (4un)", "Casa Inteligente", 290, 0.48, 5),
    P("Casa & Conforto", "Cadeira Gamer Reclinável", "Mobiliário", 1490, 0.50, 5, dev=0.090),
    # ---- Software & Assinaturas
    P("Software & Assinaturas", "Licença Office Suite (anual)", "Produtividade", 690, 0.15, 8),
    P("Software & Assinaturas", "Antivírus Corporativo (anual)", "Segurança", 290, 0.14, 7),
    P("Software & Assinaturas", "ERP Lite (mensalidade)", "Gestão", 890, 0.20, 5),
    P("Software & Assinaturas", "Backup em Nuvem 1TB (anual)", "Nuvem", 590, 0.22, 5),
    P("Software & Assinaturas", "Plataforma de Videoconferência (anual)", "Colaboração", 490, 0.18, 5),
    # ---- Serviços
    P("Serviços", "Instalação & Montagem", "Instalação", 350, 0.38, 7),
    P("Serviços", "Suporte Técnico Mensal", "Suporte", 1200, 0.40, 5),
    P("Serviços", "Consultoria de Layout", "Consultoria", 2800, 0.36, 2),
    P("Serviços", "Manutenção Preventiva", "Manutenção", 780, 0.38, 4),
    P("Serviços", "Treinamento de Equipe", "Treinamento", 1800, 0.35, 2),
]

SEGMENTOS = ["Consumidor Final", "Pequena Empresa", "Média Empresa", "Corporativo"]
SEG_P = [0.55, 0.25, 0.15, 0.05]
SEG_PESO_PEDIDO = [1.0, 2.5, 5.0, 9.0]
SEG_QTD = [0.25, 0.8, 1.6, 3.2]
SEG_DESC = [0.0, 0.0, 0.015, 0.03]
QTD_LAMBDA = {"Eletrônicos": 0.9, "Escritório": 0.8, "Casa & Conforto": 0.5,
              "Software & Assinaturas": 3.5, "Serviços": 0.4}
SEG_TILT = {
    "Consumidor Final": {"Eletrônicos": 1.4, "Escritório": 0.7, "Casa & Conforto": 1.6, "Software & Assinaturas": 0.5, "Serviços": 0.4},
    "Pequena Empresa": {"Eletrônicos": 1.0, "Escritório": 1.1, "Casa & Conforto": 0.8, "Software & Assinaturas": 1.0, "Serviços": 1.0},
    "Média Empresa": {"Eletrônicos": 0.9, "Escritório": 1.3, "Casa & Conforto": 0.6, "Software & Assinaturas": 1.4, "Serviços": 1.4},
    "Corporativo": {"Eletrônicos": 0.8, "Escritório": 1.6, "Casa & Conforto": 0.3, "Software & Assinaturas": 1.8, "Serviços": 1.9},
}

# canais: Loja, E-commerce, Televendas, Marketplace
CANAL_INI = np.array([0.40, 0.30, 0.22, 0.08])
CANAL_FIM = np.array([0.28, 0.30, 0.18, 0.24])
CANAL_SEG = {"Consumidor Final": np.array([1.0, 1.2, 0.15, 1.3]),
             "Pequena Empresa": np.array([0.9, 0.9, 1.2, 0.8]),
             "Média Empresa": np.array([0.8, 0.7, 1.8, 0.5]),
             "Corporativo": np.array([0.6, 0.5, 2.4, 0.3])}
CANAL_BF = np.array([0.6, 1.8, 0.5, 1.8])
DESC_CANAL = [0.03, 0.05, 0.04, 0.07]
PAGTO = ["PIX", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência"]
PAGTO_P = {1: [0.25, 0.40, 0.25, 0.05, 0.05], 2: [0.35, 0.50, 0.05, 0.10, 0.0],
           3: [0.10, 0.15, 0.0, 0.40, 0.35], 4: [0.20, 0.65, 0.05, 0.10, 0.0]}

FRETE = {1: 0.003, 2: 0.038, 3: 0.026, 4: 0.042}
TARIFA_PAG = {1: 0.013, 2: 0.022, 3: 0.008, 4: 0.0}
COMISSAO_MKT = 0.11


# --------------------------------------------------------------------------- #
# Fatos de vendas
# --------------------------------------------------------------------------- #
def lam_base(f: dict, d: date) -> float:
    """Pedidos esperados no dia para a filial (sem eventos extraordinários)."""
    ab = f["abertura"]
    if d < ab:
        return 0.0
    meses_aberta = (d.year - ab.year) * 12 + d.month - ab.month
    rampa = min(1.0, 0.35 + 0.65 * meses_aberta / 9)
    lam = (PEDIDOS_BASE_DIA * f["peso"] * rampa * SAZONALIDADE[d.month]
           * (1 + CRESCIMENTO_MENSAL) ** idx_mes(d) * DOW[d.weekday()])
    if d in FERIADOS:
        lam *= 0.25
    if d in BLACK_FRIDAYS:
        lam *= 2.2
    return lam


def fator_historia(fid: int, d: date) -> float:
    """Eventos reais que o orçamento NÃO previu (easter eggs)."""
    fa = 1.0
    if fid == 5 and date(2025, 6, 1) <= d <= date(2025, 8, 31):
        fa *= 0.82          # concorrente agressivo em Porto Alegre
    if fid == 2 and date(2025, 3, 1) <= d <= date(2025, 3, 31):
        fa *= 0.78          # chuvas fortes no Rio
    if fid == 6 and date(2026, 3, 1) <= d <= date(2026, 6, 30):
        fa *= 1.18          # contrato de órgão público em Brasília
    return fa


def construir_dimensoes():
    cal = construir_calendario()

    dim_filial = pd.DataFrame([{
        "id_filial": f["id"], "filial": f["nome"], "cidade": f["cidade"], "uf": f["uf"],
        "regiao": f["regiao"], "tipo": f["tipo"], "data_abertura": f["abertura"],
        "latitude": f["lat"], "longitude": f["lon"]} for f in FIL])

    prods = []
    for i, p in enumerate(CATALOGO, start=1):
        p["id"] = i
        p["custo_base"] = round(p["preco"] * p["ratio"], 2)
        prods.append({
            "id_produto": i,
            "sku": f"{PREFIXO_SKU[p['cat']]}-{i:03d}",
            "produto": p["nome"],
            "categoria": p["cat"],
            "subcategoria": p["sub"],
            "preco_lista": float(p["preco"]),
            "custo_unitario_base": p["custo_base"],
            "margem_lista_pct": round(1 - p["ratio"], 4),
            "aliquota_imposto": ALIQUOTA[p["cat"]],
        })
    dim_produto = pd.DataFrame(prods)

    dim_canal = pd.DataFrame(CANAIS, columns=["id_canal", "canal", "tipo_canal"])

    usados: set[str] = set()
    gerentes = [nome_pessoa(usados) for _ in DEPARTAMENTOS]
    dim_departamento = pd.DataFrame([{
        "id_departamento": d[0], "departamento": d[1], "centro_custo": d[2],
        "responsavel": gerentes[i], "tipo_area": d[3]} for i, d in enumerate(DEPARTAMENTOS)])

    dim_categoria = pd.DataFrame(CATEGORIAS_DESPESA, columns=[
        "id_categoria_despesa", "categoria_despesa", "grupo_dre", "tipo_custo", "ordem_dre"])

    # Vendedores (23 presenciais/televendas + 1 digital)
    n_por_filial = {1: 5, 2: 3, 3: 3, 4: 3, 5: 2, 6: 3, 7: 2, 8: 2}
    vend, vid = [], 1
    vendedores_filial: dict[int, list[tuple[int, float]]] = {}
    for f in FIL:
        vendedores_filial[f["id"]] = []
        for _ in range(n_por_filial[f["id"]]):
            adm = f["abertura"] if f["abertura"] >= DATA_INICIO else date(
                int(rng.integers(2019, 2024)), int(rng.integers(1, 13)), 1)
            vend.append({"id_vendedor": vid, "nome_vendedor": nome_pessoa(usados),
                         "equipe": f"Equipe {f['cidade']}",
                         "cargo": str(rng.choice(["Júnior", "Pleno", "Sênior"], p=[0.3, 0.45, 0.25])),
                         "data_admissao": adm})
            vendedores_filial[f["id"]].append((vid, float(rng.lognormal(0, 0.5))))
            vid += 1
    ID_DIGITAL = vid
    vend.append({"id_vendedor": ID_DIGITAL, "nome_vendedor": "Atendimento Digital",
                 "equipe": "Equipe Digital", "cargo": "Pleno", "data_admissao": date(2021, 1, 1)})
    dim_vendedor = pd.DataFrame(vend)

    # Estrela de vendas: um vendedor com resultado muito acima da média
    vendedores_filial[1][0] = (vendedores_filial[1][0][0], 3.2)

    # Clientes
    clientes, nomes_usados = [], set()
    pesos_filial = np.array([f["peso"] for f in FIL])
    pesos_filial = pesos_filial / pesos_filial.sum()
    for cid in range(1, N_CLIENTES + 1):
        seg_i = int(rng.choice(4, p=SEG_P))
        seg = SEGMENTOS[seg_i]
        nome = nome_pessoa(nomes_usados) if seg_i == 0 else nome_empresa(nomes_usados)
        home = int(rng.choice([f["id"] for f in FIL], p=pesos_filial))
        fh = FIL_POR_ID[home]
        cidade = fh["cidade"] if rng.random() < 0.7 else str(rng.choice(CIDADES_UF[fh["uf"]]))
        clientes.append({"id_cliente": cid, "nome_cliente": nome, "segmento": seg,
                         "cidade": cidade, "uf": fh["uf"], "regiao": fh["regiao"],
                         "_home": home, "_seg_i": seg_i,
                         "_peso": float(rng.lognormal(0, 1.0)) * SEG_PESO_PEDIDO[seg_i]})
    cli_df = pd.DataFrame(clientes)
    return cal, dim_filial, dim_produto, dim_canal, dim_departamento, dim_categoria, \
        dim_vendedor, cli_df, vendedores_filial, ID_DIGITAL


def gerar_vendas(cli_df, vendedores_filial, id_digital):
    ids_cli = cli_df["id_cliente"].to_numpy()
    seg_cli = cli_df["_seg_i"].to_numpy()
    home_cli = cli_df["_home"].to_numpy()
    peso_cli = cli_df["_peso"].to_numpy()

    def pool(mask):
        ids = ids_cli[mask]
        p = peso_cli[mask]
        return ids, np.cumsum(p / p.sum())

    pool_global = pool(np.ones(len(ids_cli), dtype=bool))
    pool_filial = {f["id"]: pool(home_cli == f["id"]) for f in FIL}

    n_prod = len(CATALOGO)
    pop = np.array([p["pop"] for p in CATALOGO], dtype=float)
    cats = [p["cat"] for p in CATALOGO]
    cache_pesos: dict = {}

    def pesos_prod(seg_i, d):
        k = (seg_i, d.year, d.month)
        if k not in cache_pesos:
            w = pop * np.array([SEG_TILT[SEGMENTOS[seg_i]][c] for c in cats])
            if (d.year, d.month) == (2025, 8):
                w[0] *= 0.10      # ruptura de estoque do Notebook Pro 14" em ago/2025
            cache_pesos[k] = w / w.sum()
        return cache_pesos[k]

    vend_ids = {fid: (np.array([v[0] for v in lst]),
                      np.cumsum(np.array([v[1] for v in lst]) / sum(v[1] for v in lst)))
                for fid, lst in vendedores_filial.items()}

    registros = []
    pedido_n = venda_n = 0
    esp_pedidos: dict[tuple[int, date], float] = {}

    d = DATA_INICIO
    while d <= DATA_FIM:
        mes = primeiro_dia(d)
        for f in FIL:
            lb = lam_base(f, d)
            if lb > 0:
                esp_pedidos[(f["id"], mes)] = esp_pedidos.get((f["id"], mes), 0.0) + lb
        d += timedelta(days=1)

    d = DATA_INICIO
    while d <= DATA_CORTE:
        t = min(1.0, idx_mes(d) / (N_MESES_REAL - 1))
        canal_base = (1 - t) * CANAL_INI + t * CANAL_FIM
        eh_bf = d in BLACK_FRIDAYS
        for f in FIL:
            lb = lam_base(f, d)
            if lb <= 0:
                continue
            n = int(rng.poisson(lb * fator_historia(f["id"], d)))
            for _ in range(n):
                pedido_n += 1
                # cliente
                ids, cum = pool_filial[f["id"]] if rng.random() < 0.85 else pool_global
                k = min(int(np.searchsorted(cum, rng.random())), len(ids) - 1)
                cid = int(ids[k])
                seg_i = int(seg_cli[cid - 1])
                seg = SEGMENTOS[seg_i]
                # canal
                pc = canal_base * CANAL_SEG[seg] * (CANAL_BF if eh_bf else 1.0)
                pc = pc / pc.sum()
                canal = int(rng.choice(4, p=pc)) + 1
                # vendedor
                if canal in (1, 3):
                    vids, vcum = vend_ids[f["id"]]
                    vid = int(vids[min(int(np.searchsorted(vcum, rng.random())), len(vids) - 1)])
                else:
                    vid = id_digital
                # desconto-base do pedido
                desc_ped = DESC_CANAL[canal - 1] + SEG_DESC[seg_i]
                if d.month == 11:
                    desc_ped += 0.05
                if eh_bf:
                    desc_ped += 0.08
                desc_ped += float(rng.normal(0, 0.015))
                pagto = str(rng.choice(PAGTO, p=PAGTO_P[canal]))
                n_lin = int(rng.choice([1, 2, 3, 4], p=[0.50, 0.28, 0.15, 0.07]))
                escolhidos = rng.choice(n_prod, size=n_lin, replace=False,
                                        p=pesos_prod(seg_i, d))
                for pi in escolhidos:
                    p = CATALOGO[int(pi)]
                    venda_n += 1
                    qtd = 1 + int(rng.poisson(QTD_LAMBDA[p["cat"]] * SEG_QTD[seg_i]))
                    meses = idx_mes(d)
                    preco = round(p["preco"] * (1 + p["ip"]) ** meses, 2)
                    custo = round(p["custo_base"] * (1 + p["ic"]) ** meses * float(rng.uniform(0.985, 1.015)), 2)
                    pct = float(np.clip(desc_ped + rng.normal(0, 0.01), 0, 0.30))
                    pct = round(pct, 2)
                    bruta = round(qtd * preco, 2)
                    desc = round(bruta * pct, 2)
                    base = bruta - desc
                    imp = round(base * ALIQUOTA[p["cat"]], 2)
                    liq = round(base - imp, 2)
                    status = "Devolvido" if rng.random() < p["dev"] else "Entregue"
                    registros.append((venda_n, f"PED-{pedido_n:06d}", d, cid, p["id"], f["id"], vid,
                                      canal, qtd, preco, pct, bruta, desc, imp, liq,
                                      round(qtd * custo, 2), pagto, status))
        d += timedelta(days=1)

    vendas = pd.DataFrame(registros, columns=[
        "id_venda", "id_pedido", "data", "id_cliente", "id_produto", "id_filial", "id_vendedor",
        "id_canal", "quantidade", "preco_unitario", "desconto_pct", "receita_bruta",
        "desconto_valor", "impostos_valor", "receita_liquida", "custo_total",
        "forma_pagamento", "status"])
    return vendas, esp_pedidos, pedido_n


# --------------------------------------------------------------------------- #
# Despesas, orçamento, metas, RH
# --------------------------------------------------------------------------- #
SAL = {1: 4200, 2: 7000, 3: 10500, 4: 6200, 5: 7800, 6: 3400, 7: 3900, 8: 11500}
TURNOVER = {1: 0.022, 2: 0.012, 3: 0.015, 4: 0.010, 5: 0.008, 6: 0.030, 7: 0.012, 8: 0.010}
REAJUSTES = {2024: 0.045, 2025: 0.050, 2026: 0.048}
ENCARGOS = 0.36
BENEFICIO_BASE = 1150.0
ALUGUEL = {1: 30000, 2: 15000, 3: 10000, 4: 9500, 5: 8500, 6: 10500, 7: 8500, 8: 8500}
META_MARGEM = {1: 0.38, 2: 0.37, 3: 0.36, 4: 0.37, 5: 0.36, 6: 0.35, 7: 0.36, 8: 0.36}

FORN = {
    7: ["TransLog Express", "RodoFácil Transportes", "Correios Corporativo"],
    5: ["Google Ads", "Meta Ads", "TikTok Ads", "Influenciadores & Afiliados"],
    6: ["Feira Office Brasil", "Congresso Varejo Tech", "Patrocínio Esporte Local"],
    8: ["Manutec Serviços", "ClimaFix", "Predial Total"],
    11: ["CloudSoft Infra", "Licenças Corp Brasil", "DevTools Pro"],
    12: ["Consultoria Alvo", "Contabilidade & Cia", "Agência Pixel"],
    13: ["Agência de Viagens Rota", "Locadora Frota Viva"],
    14: ["Academia Corporativa", "Instituto Aprender"],
    15: ["Seguradora Aliança"],
    16: ["Papelaria Central", "OfficeMax Atacado"],
    18: ["Banco Nacional", "Banco do Brasil Corporativo", "Cooperativa Crédito"],
}
DIA_PAGTO = {1: 5, 2: 20, 3: 1, 9: 10, 10: 15, 15: 12, 18: 25, 11: 8}


def fator_reajuste(m: date) -> float:
    f = 1.0
    for ano, r in REAJUSTES.items():
        if m >= date(ano, 3, 1):
            f *= 1 + r
    return f


def gerar_financeiro(vendas, esp_pedidos, pedido_n):
    MES_CORTE = primeiro_dia(DATA_CORTE)
    meses_todos = lista_meses(DATA_INICIO, DATA_FIM)
    meses_real = [m for m in meses_todos if m <= MES_CORTE]

    ok = vendas[vendas["status"] == "Entregue"].copy()
    ok["mes"] = ok["data"].map(primeiro_dia)
    net_por_pedido = ok["receita_liquida"].sum() / pedido_n
    ped_filial = vendas.groupby("id_filial")["id_pedido"].nunique()
    npp_filial = (ok.groupby("id_filial")["receita_liquida"].sum() / ped_filial).to_dict()

    # Receita esperada (base do orçamento) = pedidos esperados × ticket médio de referência da filial
    E = {k: v * npp_filial.get(k[0], net_por_pedido) for k, v in esp_pedidos.items()}
    A = ok.groupby(["id_filial", "mes"])["receita_liquida"].sum().to_dict()
    AC = ok.groupby(["id_filial", "mes", "id_canal"])["receita_liquida"].sum().to_dict()

    mix_real = ok.groupby(["mes", "id_canal"])["receita_liquida"].sum().unstack(fill_value=0)
    mix_real = mix_real.div(mix_real.sum(axis=1), axis=0)
    ultimos3 = mix_real.tail(3).mean()
    mix_esp = {m: (mix_real.loc[m] if m in mix_real.index else ultimos3) for m in meses_todos}

    def taxa(mix, tab):
        return float(sum(mix.get(c, 0.0) * tab.get(c, 0.0) for c in (1, 2, 3, 4)))

    def ativa(f, m):
        return m >= add_meses(primeiro_dia(f["abertura"]), -1)

    desp_rows, orc_rows, rh_rows, meta_rows = [], [], [], []

    def lanc(mes, dep, cat, fil, orc, real, forn):
        if orc is not None and orc > 0:
            orc_rows.append({"mes": mes, "id_departamento": dep, "id_categoria_despesa": cat,
                             "id_filial": fil, "valor_orcado": round(float(orc), 2)})
        if real is None or real <= 0 or mes > MES_CORTE:
            return
        ult = ultimo_dia(mes).day
        for nome, share in forn:
            v = round(float(real) * share, 2)
            if v <= 0:
                continue
            dia = DIA_PAGTO.get(cat) or int(rng.integers(1, ult + 1))
            dia = min(dia, ult)
            dt = min(date(mes.year, mes.month, dia), DATA_CORTE)
            desp_rows.append({"data": dt, "id_departamento": dep, "id_categoria_despesa": cat,
                              "id_filial": fil, "fornecedor": nome, "valor": v})

    def hc_plano(dep, f, mes, e):
        fid = f["id"]
        if dep == 1:
            return max(2, int(round(e / DIV_COM)))
        if dep == 6:
            return max(2, int(round(e / DIV_OPS)))
        if dep == 7:
            return 3 if fid == 1 else 1
        if fid != 1:
            return 0
        if dep == 2:
            return 4 if mes < date(2025, 7, 1) else 6
        if dep == 3:
            return 4 if mes < date(2025, 3, 1) else (5 if mes < date(2026, 3, 1) else 7)
        if dep == 4:
            return 3
        if dep == 5:
            return 4
        if dep == 8:
            return 5 if mes < date(2025, 1, 1) else 6
        return 0

    hc_prev: dict[tuple[int, int], int] = {}
    delta_estado: dict[tuple[int, int], int] = {}
    forn_uf = lambda uf: [(f"Concessionária Local {uf}", 1.0)]  # noqa: E731

    for mes in meses_todos:
        realizado = mes <= MES_CORTE
        ativas = [f for f in FIL if ativa(f, mes)]
        soma_e = sum(E.get((f["id"], mes), 0.0) for f in ativas)
        mix = mix_esp[mes]
        idx = idx_mes(mes)
        reaj = fator_reajuste(mes)
        benef = BENEFICIO_BASE * (1.03 if mes.year >= 2025 else 1.0) * (1.03 if mes.year >= 2026 else 1.0)
        verao = 1.18 if mes.month in (12, 1, 2, 3) else 1.0

        # --- metas de vendas ---
        for f in ativas:
            e = E.get((f["id"], mes), 0.0)
            if e > 0:
                meta = round(e * 1.03, -3)
                meta_rows.append({"mes": mes, "id_filial": f["id"], "meta_receita_liquida": float(meta),
                                  "meta_margem_bruta_pct": META_MARGEM[f["id"]],
                                  "meta_lucro_bruto": float(round(meta * META_MARGEM[f["id"]], -2))})

        # --- marketing & eventos (rateio por participação na receita esperada) ---
        boost = {10: 1.25, 11: 1.45, 12: 1.10, 1: 0.85}.get(mes.month, 1.0)
        mkt_total = PCT_MARKETING * soma_e * boost
        ev_total = PCT_EVENTOS * soma_e * (1.0 if mes.month in (3, 6, 9, 11) else 0.0)

        for f in ativas:
            fid = f["id"]
            e = E.get((fid, mes), 0.0)
            a = A.get((fid, mes), 0.0)

            # ---------------- PESSOAL + RH ----------------
            for dep in range(1, 9):
                plano = hc_plano(dep, f, mes, e)
                if plano <= 0:
                    continue
                sal = SAL[dep] * reaj
                lanc_orc = {1: plano * sal, 2: plano * sal * ENCARGOS, 3: plano * benef}
                if realizado:
                    # desvio do quadro em relação ao plano é persistente (muda raramente)
                    delta = delta_estado.get((dep, fid), 0)
                    if rng.random() < 0.10:
                        if plano >= 5:
                            delta = int(rng.choice([-1, 0, 0, 1]))
                        elif plano >= 3:
                            delta = int(rng.choice([0, 0, -1]))
                        else:
                            delta = 0
                        delta_estado[(dep, fid)] = delta
                    hc = max(0, plano + delta)
                    prev = hc_prev.get((dep, fid), hc)
                    desl = int(rng.binomial(prev, TURNOVER[dep])) if prev > 0 else 0
                    adm = hc - prev + desl
                    if adm < 0:
                        desl += -adm
                        adm = 0
                    hc_prev[(dep, fid)] = hc
                    rh_rows.append({"data_referencia": ultimo_dia(mes), "id_departamento": dep,
                                    "id_filial": fid, "headcount": hc, "headcount_planejado": plano,
                                    "admissoes": adm, "desligamentos": desl})
                    real_sal = hc * sal * float(rng.uniform(0.995, 1.010))
                    real = {1: real_sal, 2: real_sal * ENCARGOS, 3: hc * benef * float(rng.uniform(0.98, 1.02))}
                else:
                    real = {1: None, 2: None, 3: None}
                nomes = {1: "Folha de Pagamento", 2: "INSS / FGTS / Encargos",
                         3: "Benefícios Corporativos (VR/VA/Plano)"}
                for cat in (1, 2, 3):
                    lanc(mes, dep, cat, fid, lanc_orc[cat], real[cat], [(nomes[cat], 1.0)])

            # ---------------- COMISSÕES ----------------
            real_com = None
            if realizado:
                uplift = 1.25 if mes.month == 11 else 1.0
                real_com = PCT_COMISSAO * a * uplift * float(rng.uniform(0.98, 1.02))
            lanc(mes, 1, 4, fid, PCT_COMISSAO * e, real_com, [("Folha de Comissões", 1.0)])

            # ---------------- MARKETING / EVENTOS ----------------
            if soma_e > 0 and e > 0:
                share_f = e / soma_e
                real_m = None
                if realizado:
                    real_m = mkt_total * share_f * float(rng.uniform(0.94, 1.06))
                    if date(2025, 10, 1) <= mes <= date(2025, 12, 1):
                        real_m *= 1.28            # estouro de verba de marketing no 4T25
                lanc(mes, 2, 5, fid, mkt_total * share_f, real_m,
                     list(zip(FORN[5], [0.42, 0.33, 0.15, 0.10])))
                if ev_total > 0:
                    real_e = ev_total * share_f * float(rng.uniform(0.9, 1.2)) if realizado else None
                    lanc(mes, 2, 6, fid, ev_total * share_f, real_e,
                         [(FORN[6][int(rng.integers(0, 3))], 1.0)])

            # ---------------- FRETE ----------------
            real_fr = None
            if realizado:
                base_fr = sum(AC.get((fid, mes, c), 0.0) * FRETE[c] for c in (1, 2, 3, 4))
                real_fr = base_fr * (1.15 if mes.month == 11 else 1.0) * float(rng.uniform(0.97, 1.03))
            lanc(mes, 6, 7, fid, e * taxa(mix, FRETE), real_fr,
                 list(zip(FORN[7], [0.5, 0.3, 0.2])))

            # ---------------- TARIFAS DE PAGAMENTO / MARKETPLACE ----------------
            orc_tar = e * (taxa(mix, TARIFA_PAG) + float(mix.get(4, 0.0)) * COMISSAO_MKT)
            real_tar, forn_tar = None, [("Adquirentes (cartão/PIX)", 1.0)]
            if realizado:
                card = sum(AC.get((fid, mes, c), 0.0) * TARIFA_PAG[c] for c in (1, 2, 3, 4))
                mk = AC.get((fid, mes, 4), 0.0) * COMISSAO_MKT
                real_tar = card + mk
                if real_tar > 0:
                    forn_tar = [("Adquirentes (cartão/PIX)", card / real_tar),
                                ("Comissão de Marketplaces", mk / real_tar)]
            lanc(mes, 5, 17, fid, orc_tar, real_tar, forn_tar)

            # ---------------- CUSTOS FIXOS DA FILIAL ----------------
            aluguel = ALUGUEL[fid] * (1.042 ** max(0, mes.year - 2024))
            lanc(mes, 7, 9, fid, aluguel, aluguel if realizado else None,
                 [(f"Locadora Imóveis {f['cidade']}", 1.0)])

            en_base = (3500 + 28000 * f["peso"]) * (1.05 ** max(0, mes.year - 2024))
            lanc(mes, 7, 10, fid, en_base,
                 en_base * verao * float(rng.uniform(0.95, 1.08)) if realizado else None,
                 forn_uf(f["uf"]))

            seg = (1200 + 12000 * f["peso"])
            lanc(mes, 7, 15, fid, seg, seg if realizado else None, [(FORN[15][0], 1.0)])

            mat = 800 + 5000 * f["peso"]
            lanc(mes, 7, 16, fid, mat, mat * float(rng.uniform(0.7, 1.3)) if realizado else None,
                 [(FORN[16][int(rng.integers(0, 2))], 1.0)])

            man = 2500 + 15000 * f["peso"]
            lanc(mes, 6, 8, fid, man, man * float(rng.uniform(0.55, 1.45)) if realizado else None,
                 [(FORN[8][int(rng.integers(0, 3))], 1.0)])

            if e > 0:
                viag = PCT_VIAGENS * e
                lanc(mes, 1, 13, fid, viag, viag * float(rng.uniform(0.6, 1.4)) if realizado else None,
                     [(FORN[13][int(rng.integers(0, 2))], 1.0)])

        # ---------------- CUSTOS CORPORATIVOS (Matriz) ----------------
        soft = 38000 * (1 + 0.004 * idx)
        real_soft = None
        if realizado:
            real_soft = soft
            if mes.year == 2026:
                real_soft *= 1 + 0.035 * mes.month      # custo de nuvem fugindo do controle em 2026
        lanc(mes, 3, 11, 1, soft, real_soft, [(n, s) for n, s in zip(FORN[11], [0.55, 0.30, 0.15])])

        for dep, orc in ((5, 12000), (3, 15000), (2, 10000)):
            real_c = None
            if realizado and rng.random() > 0.15:
                real_c = orc * float(rng.uniform(0.4, 1.6))
            lanc(mes, dep, 12, 1, orc, real_c, [(FORN[12][int(rng.integers(0, 3))], 1.0)])

        tre = 20000 if mes.month in (2, 8) else 5000
        lanc(mes, 4, 14, 1, tre, tre * float(rng.uniform(0.8, 1.2)) if realizado else None,
             [(FORN[14][int(rng.integers(0, 2))], 1.0)])

        juros = 13000.0
        real_j = None
        if realizado:
            real_j = juros
            if mes >= date(2025, 3, 1):
                real_j = juros * (1 + 0.02 * ((mes.year - 2025) * 12 + mes.month - 2))
            real_j *= float(rng.uniform(0.97, 1.03))
        lanc(mes, 5, 18, 1, juros, real_j, [(n, s) for n, s in zip(FORN[18], [0.5, 0.3, 0.2])])

    despesas = pd.DataFrame(desp_rows).sort_values(["data", "id_filial", "id_departamento"]).reset_index(drop=True)
    despesas.insert(0, "id_despesa", range(1, len(despesas) + 1))
    orcamento = pd.DataFrame(orc_rows)
    metas = pd.DataFrame(meta_rows)
    rh = pd.DataFrame(rh_rows)
    return despesas, orcamento, metas, rh, net_por_pedido


# --------------------------------------------------------------------------- #
# Saída: CSV, SQLite, Power Query
# --------------------------------------------------------------------------- #
COLUNAS_DATA = {"data", "primeiro_dia_mes", "data_abertura", "data_cadastro", "data_primeira_compra",
                "data_admissao", "mes", "data_referencia"}


def tipo_m(col: str, serie: pd.Series) -> str:
    if col in COLUNAS_DATA:
        return "type date"
    if pd.api.types.is_integer_dtype(serie):
        return "Int64.Type"
    if pd.api.types.is_float_dtype(serie):
        return "type number"
    return "type text"


def consulta_m(nome: str, df: pd.DataFrame, origem: str) -> str:
    tipos = ", ".join(f'{{"{c}", {tipo_m(c, df[c])}}}' for c in df.columns)
    if origem == "github":
        fonte = f'Web.Contents(BaseUrl & "{nome}.csv")'
        cab = "// Parâmetro necessário: BaseUrl (texto)\n// Ex.: https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/data/\n"
    else:
        fonte = f'File.Contents(PastaLocal & "{nome}.csv")'
        cab = "// Parâmetro necessário: PastaLocal (texto)\n// Ex.: C:\\\\projetos\\\\empresa-x-powerbi\\\\data\\\\\n"
    return (f"{cab}let\n"
            f"    Fonte = Csv.Document({fonte}, [Delimiter = \",\", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),\n"
            f"    Cabecalho = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),\n"
            f"    Tipos = Table.TransformColumnTypes(Cabecalho, {{{tipos}}}, \"en-US\")\n"
            f"in\n    Tipos\n")


def para_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if c in COLUNAS_DATA:
            out[c] = out[c].map(lambda x: x.isoformat() if pd.notna(x) else None)
    return out


def main():
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    PASTA_BANCO.mkdir(parents=True, exist_ok=True)

    (cal, dim_filial, dim_produto, dim_canal, dim_departamento, dim_categoria,
     dim_vendedor, cli_df, vend_filial, id_digital) = construir_dimensoes()

    vendas, esp_pedidos, pedido_n = gerar_vendas(cli_df, vend_filial, id_digital)
    despesas, orcamento, metas, rh, net_por_pedido = gerar_financeiro(vendas, esp_pedidos, pedido_n)

    # data_cadastro / data_primeira_compra dos clientes
    prim = vendas.groupby("id_cliente")["data"].min()
    cli = cli_df.drop(columns=["_home", "_seg_i", "_peso"]).copy()
    cli["data_primeira_compra"] = cli["id_cliente"].map(prim)
    def cadastro(r):
        if pd.isna(r["data_primeira_compra"]):
            return date(2023, int(rng.integers(1, 13)), int(rng.integers(1, 28)))
        return max(date(2023, 1, 1), r["data_primeira_compra"] - timedelta(days=int(rng.integers(0, 21))))
    cli["data_cadastro"] = cli.apply(cadastro, axis=1)
    cli = cli[["id_cliente", "nome_cliente", "segmento", "cidade", "uf", "regiao",
               "data_cadastro", "data_primeira_compra"]]

    tabelas = {
        "dim_calendario": cal, "dim_filial": dim_filial, "dim_produto": dim_produto,
        "dim_cliente": cli, "dim_vendedor": dim_vendedor, "dim_canal": dim_canal,
        "dim_departamento": dim_departamento, "dim_categoria_despesa": dim_categoria,
        "fact_vendas": vendas, "fact_despesas": despesas, "fact_orcamento": orcamento,
        "fact_metas_vendas": metas, "fact_rh_mensal": rh,
    }

    for nome, df in tabelas.items():
        df.to_csv(PASTA_DADOS / f"{nome}.csv", index=False, encoding="utf-8")

    # Power Query
    for origem in ("github", "local"):
        pasta = PASTA_M / origem
        pasta.mkdir(parents=True, exist_ok=True)
        for nome, df in tabelas.items():
            (pasta / f"{nome}.pq").write_text(consulta_m(nome, df, origem), encoding="utf-8")

    # SQLite
    caminho_db = PASTA_BANCO / "empresa_x.db"
    if caminho_db.exists():
        caminho_db.unlink()
    con = sqlite3.connect(caminho_db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((PASTA_SQL / "schema.sql").read_text(encoding="utf-8"))
    for nome, df in tabelas.items():
        para_sqlite(df).to_sql(nome, con, if_exists="append", index=False)
    con.executescript((PASTA_SQL / "views.sql").read_text(encoding="utf-8"))
    viol = con.execute("PRAGMA foreign_key_check").fetchall()
    con.commit()
    con.close()

    # ----------------------------------------------------------------- resumo
    ok = vendas[vendas["status"] == "Entregue"].copy()
    ok["ano"] = pd.to_datetime(ok["data"]).dt.year
    d = despesas.copy()
    d["ano"] = pd.to_datetime(d["data"]).dt.year
    print("\n=== LINHAS POR TABELA ===")
    for nome, df in tabelas.items():
        print(f"  {nome:24s} {len(df):>8,d}")
    print(f"\nViolações de chave estrangeira no SQLite: {len(viol)}")
    print("\n=== DRE ANUAL (R$ mi) ===")
    for ano in (2024, 2025, 2026):
        v = ok[ok["ano"] == ano]
        rl, cmv = v["receita_liquida"].sum(), v["custo_total"].sum()
        desp = d[d["ano"] == ano]["valor"].sum()
        print(f"  {ano}: rec.líq {rl/1e6:6.2f} | lucro bruto {(rl-cmv)/1e6:6.2f} ({(rl-cmv)/rl:5.1%}) "
              f"| despesas {desp/1e6:6.2f} ({desp/rl:5.1%}) | resultado op. {(rl-cmv-desp)/1e6:6.2f} "
              f"({(rl-cmv-desp)/rl:5.1%})")
    print("\n=== RESULTADO OPERACIONAL POR MÊS (R$ mil) ===")
    ok["mes"] = ok["data"].map(primeiro_dia)
    d["mes"] = d["data"].map(primeiro_dia)
    rm = ok.groupby("mes")[["receita_liquida", "custo_total"]].sum()
    rm["desp"] = d.groupby("mes")["valor"].sum()
    rm["res"] = rm["receita_liquida"] - rm["custo_total"] - rm["desp"]
    rm["marg"] = rm["res"] / rm["receita_liquida"]
    for m, r in rm.iterrows():
        print(f"  {m:%Y-%m}: rec {r['receita_liquida']/1e3:8.0f} | res {r['res']/1e3:7.0f} ({r['marg']:6.1%})")
    print(f"\nTicket líquido por pedido: R$ {net_por_pedido:,.0f}")


if __name__ == "__main__":
    main()
