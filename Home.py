# ========================================================================
# IMPORTAÇÃO DE BIBLIOTECAS E CONFIGURAÇÃO INICIAL
# ========================================================================
import streamlit as st                   # Framework para criação do dashboard web
import mysql.connector                  # Conexão com banco de dados MySQL
import pandas as pd                     # Manipulação de dados com DataFrames
from datetime import datetime           # Trabalhar com datas
from dateutil.relativedelta import relativedelta  # Subtrair/Adicionar meses facilmente
import os                               # Manipulação de diretórios e caminhos
import configparser                     # Leitura de configurações externas (como config.ini)
from funcoes import carregar_empresas   # Função customizada para carregar as empresas

# Define layout da página como "wide" (amplo)
st.set_page_config(layout="wide")

# ========================================================================
# ESTILIZAÇÃO DA SIDEBAR
# ========================================================================
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #2E2E2E;  /* Cor de fundo da sidebar */
        }
        [data-testid="stSidebar"] * {
            color: white;  /* Cor do texto da sidebar */
        }
    </style>
""", unsafe_allow_html=True)

# ========================================================================
# LOGO E TÍTULO
# ========================================================================
logo_path = os.path.join("assets", "logo.png")  # Caminho da imagem do logo
st.sidebar.image(logo_path, width=100)          # Exibe logo na sidebar
st.title("Visão Geral - KPIs de Vendas")        # Título principal da página

# ========================================================================
# SELEÇÃO DA EMPRESA (usando função personalizada)
# ========================================================================
empresas = carregar_empresas()  # Carrega dicionário: {cod: nome}
cod_empresa = st.selectbox(
    "🏢 Selecione a Empresa:",
    options=list(empresas.keys()),
    format_func=lambda x: empresas[x]  # Exibe nome em vez do código
)

# Define cores fixas por empresa (opcional)
cores_empresas = {
    1: '#6ABCB5',
    2: '#4C72B0',
    3: '#F5D547'
}
empresa_cor = cores_empresas.get(cod_empresa, '#000000')  # Cor padrão: preto
empresa_nome = empresas[cod_empresa]                      # Nome da empresa selecionada

# Exibe nome da empresa com cor customizada
st.markdown(f"<h3 style='color:{empresa_cor}'>{empresa_nome}</h3>", unsafe_allow_html=True)

# ========================================================================
# CONEXÃO COM O BANCO DE DADOS
# ========================================================================
caminho_atual = os.path.dirname(os.path.abspath(__file__))            # Caminho atual do script
caminho_config = os.path.join(caminho_atual, 'config.ini')            # Caminho do arquivo config.ini

config = configparser.ConfigParser()
config.read(caminho_config)  # Lê configurações de conexão

# Extrai dados do arquivo .ini
db_config = {
    'host': config['mysql']['host'],
    'port': int(config['mysql']['port']),
    'user': config['mysql']['user'],
    'password': config['mysql']['password'],
    'database': config['mysql']['database']
}

# Conecta ao banco e traz os dados da view de vendas
try:
    conexao = mysql.connector.connect(**db_config)
    cursor = conexao.cursor()
    cursor.execute(
        'SELECT Data, ClienteApelido, TotalProdutos FROM view_vendas_vendedores WHERE CodEmpresa = %s',
        (cod_empresa,)
    )
    resultado = cursor.fetchall()
except mysql.connector.Error as e:
    st.error(f"❌ Erro ao conectar com o banco de dados:\n\n{e}")
    st.stop()

# ========================================================================
# CRIAÇÃO DO DATAFRAME COM OS DADOS DE VENDAS
# ========================================================================
df = pd.DataFrame(resultado, columns=['Data', 'ClienteApelido', 'TotalProdutos'])  # Converte resultados em DataFrame

# Verifica se há dados disponíveis
if df.empty:
    st.warning("⚠️ Nenhum dado encontrado para esta empresa.")
    st.stop()

# Conversões e colunas auxiliares
df['Data'] = pd.to_datetime(df['Data'])            # Converte datas para datetime
df['TotalProdutos'] = df['TotalProdutos'].astype(float)
df['Ano'] = df['Data'].dt.year
df['Mes'] = df['Data'].dt.month
df['Dia'] = df['Data'].dt.day

# ========================================================================
# FUNÇÕES PARA KPIs
# ========================================================================
def kpi_card(titulo, valor_atual, valor_anterior, prefixo="R$"):
    """
    Exibe um card com valor atual + delta comparativo com o valor anterior.
    Ex: ▲ R$2.000,00 ou ▼ R$1.200,00
    """
    diferenca = valor_atual - valor_anterior
    seta      = "▲" if diferenca >= 0 else "▼"
    delta_txt = f"{seta} {prefixo}{abs(diferenca):,.2f}" if prefixo else f"{seta} {abs(diferenca):,.0f}"
    cor       = "normal" if diferenca >= 0 else "inverse"
    st.metric(label=titulo, value=f"{prefixo}{valor_atual:,.2f}" if prefixo else f"{valor_atual:,.0f}", delta=delta_txt, delta_color=cor)

def kpi_card_duplo(titulo, valor_a, valor_b, prefixo="R$"):
    """
    Exibe KPI com comparação entre dois períodos personalizados.
    Mostra valor B (atual) e variação em relação ao valor A (base).
    """
    diferenca = valor_b - valor_a
    seta = "▲" if diferenca >= 0 else "▼"
    cor  = "normal" if diferenca >= 0 else "inverse"
    delta_txt = f"{seta} {prefixo}{abs(diferenca):,.2f}" if prefixo else f"{seta} {abs(diferenca):,.0f}"
    help_txt  = f"Período A: {prefixo}{valor_a:,.2f}\nPeríodo B: {prefixo}{valor_b:,.2f}" if prefixo else f"Período A: {valor_a:,.0f}\nPeríodo B: {valor_b:,.0f}"
    st.metric(label=titulo, value=f"{prefixo}{valor_b:,.2f}" if prefixo else f"{valor_b:,.0f}", delta=delta_txt, delta_color=cor, help=help_txt)

def calcular_kpis(df_base):
    """
    Calcula os principais KPIs:
    - Faturamento total
    - Ticket médio
    - Quantidade de pedidos
    """
    faturamento  = df_base['TotalProdutos'].sum()
    ticket_medio = df_base['TotalProdutos'].mean() if not df_base.empty else 0
    pedidos      = len(df_base)
    return faturamento, ticket_medio, pedidos

# ========================================================================
# DEFINIÇÃO DE DATAS DE REFERÊNCIA
# ========================================================================
hoje = datetime.today()
dia_atual = hoje.day
mes_atual = hoje.month
ano_atual = hoje.year
data_mes_anterior = hoje - relativedelta(months=1)
mes_anterior = data_mes_anterior.month
ano_anterior = data_mes_anterior.year

# ========================================================================
# CRIAÇÃO DOS DATAFRAMES FILTRADOS POR PERÍODO
# ========================================================================
df_atual_dia    = df[(df['Mes'] == mes_atual) & (df['Ano'] == ano_atual) & (df['Dia'] <= dia_atual)]
df_anterior_dia = df[(df['Mes'] == mes_anterior) & (df['Ano'] == ano_anterior) & (df['Dia'] <= dia_atual)]
df_ano_passado  = df[(df['Mes'] == mes_atual) & (df['Ano'] == ano_atual-1) & (df['Dia'] <= dia_atual)]

# Calcula KPIs para cada um dos períodos
fat_atual, ticket_atual, pedidos_atual = calcular_kpis(df_atual_dia)
fat_anterior, ticket_anterior, pedidos_anterior = calcular_kpis(df_anterior_dia)
fat_ano_passado, _, _ = calcular_kpis(df_ano_passado)

# ========================================================================
# 1. COMPARAÇÃO: MÊS ATUAL vs MÊS ANTERIOR
# ========================================================================
with st.container():
    st.subheader(f"📊 KPIs - Mês Atual vs Mês Passado (até o dia {dia_atual})")
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Faturamento (R$)", fat_atual, fat_anterior)
    with c2: kpi_card("Ticket Médio (R$)", ticket_atual, ticket_anterior)
    with c3: kpi_card("Qtd. de Pedidos", pedidos_atual, pedidos_anterior, prefixo="")

# ========================================================================
# 2. COMPARAÇÃO: MESMO MÊS DO ANO PASSADO
# ========================================================================
with st.container():
    st.subheader("📅 Faturamento - Comparação com mesmo mês do ano anterior")
    kpi_card("Faturamento vs Ano Passado", fat_atual, fat_ano_passado)

# ========================================================================
# 3. SELEÇÃO PERSONALIZADA DE PERÍODOS
# ========================================================================
with st.container():
    st.subheader("🗂️ Comparação Personalizada: Mês/Ano")

    # Gera lista de opções disponíveis para seleção de períodos
    opcoes_periodo = (
        df[['Mes', 'Ano']].drop_duplicates().sort_values(['Ano', 'Mes'])
    )
    opcoes_formatadas = (
        opcoes_periodo.apply(lambda r: f"{r['Mes']:02d}/{r['Ano']}", axis=1).tolist()[::-1]
    )

    st.markdown("---")

    col_a, col_b = st.columns(2)

    # Define índices padrão com base nos períodos atuais
    try:
        idx_b = opcoes_formatadas.index(f"{mes_atual:02d}/{ano_atual}")
    except ValueError:
        idx_b = 0

    try:
        idx_a = opcoes_formatadas.index(f"{mes_anterior:02d}/{ano_anterior}")
    except ValueError:
        idx_a = min(1, len(opcoes_formatadas)-1)

    with col_a:
        periodo_a = st.selectbox("Período A (Mês/Ano)", opcoes_formatadas, index=idx_a)
    with col_b:
        periodo_b = st.selectbox("Período B (Mês/Ano)", opcoes_formatadas, index=idx_b)

    # Extrai mês e ano das seleções
    mes_a, ano_a = map(int, periodo_a.split("/"))
    mes_b, ano_b = map(int, periodo_b.split("/"))

    # Filtra dados para os períodos selecionados
    df_a = df[(df['Mes'] == mes_a) & (df['Ano'] == ano_a)]
    df_b = df[(df['Mes'] == mes_b) & (df['Ano'] == ano_b)]

    # Calcula KPIs dos períodos selecionados
    fat_a, ticket_a, pedidos_a = calcular_kpis(df_a)
    fat_b, ticket_b, pedidos_b = calcular_kpis(df_b)

# ========================================================================
# 4. EXIBE COMPARAÇÃO PERSONALIZADA
# ========================================================================
with st.container():
    st.subheader(f"📊 Comparando {periodo_b} vs {periodo_a}")
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card_duplo("Faturamento (R$)", fat_a, fat_b)
    with c2: kpi_card_duplo("Ticket Médio (R$)", ticket_a, ticket_b)
    with c3: kpi_card_duplo("Qtd. de Pedidos", pedidos_a, pedidos_b, prefixo="")

# Fecha a conexão com o banco
conexao.close()
cursor.close()