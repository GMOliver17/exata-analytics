import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import os
import configparser
from funcoes import carregar_empresas

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# 1. PÁGINA & TEMA
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Define configurações da página do Streamlit (título, layout)
st.set_page_config(page_title="Logística & Estoque – Exata",
                   layout="wide")

# Título principal da página
st.title("📦 Logística & Estoque – Visão Geral")

# Estiliza a barra lateral com fundo escuro e texto branco
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #2E2E2E;
        }
        [data-testid="stSidebar"] * {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Caminho para exibir o logo na sidebar
logo_path = os.path.join("assets", "logo.png")
st.sidebar.image(logo_path, width=100)

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# SELEÇÃO DE EMPRESA (usando função)
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Carrega empresas disponíveis para o usuário selecionar
empresas = carregar_empresas()

# Cria selectbox com as empresas carregadas
cod_empresa = st.selectbox(
    "🏢 Selecione a Empresa:",
    options=list(empresas.keys()),
    format_func=lambda x: empresas[x]
)

# Define cores para cada empresa e aplica cor ao nome da empresa
cores_empresas = {
    1: '#6ABCB5',
    2: '#4C72B0',
    3: '#F5D547'
}
empresa_cor = cores_empresas.get(cod_empresa, '#000000')
empresa_nome = empresas[cod_empresa]

st.markdown(f"<h3 style='color:{empresa_cor}'>{empresa_nome}</h3>", unsafe_allow_html=True)

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Conexão com o BD usando config.ini
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
try:
    # Define o caminho para o arquivo de configuração do banco
    caminho_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_config = os.path.join(caminho_atual, 'config.ini')

    # Lê as credenciais do arquivo ini
    config = configparser.ConfigParser()
    config.read(caminho_config)

    # Define configurações da conexão
    db_config = {
        'host': config['mysql']['host'],
        'port': int(config['mysql']['port']),
        'user': config['mysql']['user'],
        'password': config['mysql']['password'],
        'database': config['mysql']['database']
    }

    # Estabelece a conexão com o banco
    dados_conexao = mysql.connector.connect(**db_config)
    cursor = dados_conexao.cursor()

# Trata possíveis erros de conexão
except mysql.connector.Error as e:
    st.error(f"❌ Erro ao conectar com o banco de dados:\n\n{e}")
    st.stop()

except Exception as e:
    st.error(f"❌ Erro inesperado na conexão com o banco:\n\n{e}")
    st.stop()

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# CONSULTAS SQL E DATAFRAMES
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Consulta do estoque atual
cursor.execute("SELECT EstoqueAtual, CodProduto FROM view_estoque WHERE CodEmpresa = %s", (cod_empresa,))
df_estoque = pd.DataFrame(cursor.fetchall(), columns=['EstoqueAtual', 'CodProduto'])

# Consulta das entradas de produtos (últimos 12 meses)
cursor.execute("SELECT CodProduto, DataEntrada, QtdEntrada FROM view_estoque_entrada WHERE CodEmpresa = %s",
               (cod_empresa,))
df_entrada = pd.DataFrame(cursor.fetchall(), columns=['CodProduto', 'DataEntrada', 'QtdEntrada'])
df_entrada['DataEntrada'] = pd.to_datetime(df_entrada['DataEntrada'])

# Consulta das saídas (vendas) de produtos (últimos 12 meses)
cursor.execute("SELECT CodVenda, DataVenda, CodProduto, Produto, QtdVendida, ValorUnitario, ValorTotal "
               "FROM view_vendas_estoque_detalhe WHERE CodEmpresa = %s"
               , (cod_empresa,))
df_vendas = pd.DataFrame(cursor.fetchall(), columns=['CodVenda', 'DataVenda', 'CodProduto', 'Produto', 'QtdVendida',
                                                     'ValorUnitario', 'ValorTotal'])
df_vendas['DataVenda'] = pd.to_datetime(df_vendas['DataVenda'])

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# FILTRO POR ANO - BASEADO NAS VIEWS LIMITADAS A 12 MESES
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Extrai os anos disponíveis nas vendas e exibe para seleção
anos = sorted(df_vendas['DataVenda'].dt.year.unique(), reverse=True)
if not anos:
    st.warning("⚠️ Dados insulficientes nos últimos 12 meses.")
    st.stop()
anoselecionado = st.selectbox("📅 Selecione o Ano para Análise:", anos)

# Filtra entradas e vendas pelo ano selecionado
filtro_entrada = df_entrada[df_entrada['DataEntrada'].dt.year == anoselecionado]
filtro_vendas = df_vendas[df_vendas['DataVenda'].dt.year == anoselecionado]

# Interrompe se algum dos dataframes estiver vazio
if df_estoque.empty or filtro_entrada.empty or filtro_vendas.empty:
    st.warning("⚠️ Dados insuficientes  para exibir os gráficos ou KPIs.")
    st.stop()

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# KPIs
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Calcula os valores para os indicadores principais
total_estoque = int(df_estoque['EstoqueAtual'].sum())
total_entrada = int(filtro_entrada['QtdEntrada'].sum())
total_saida = int(filtro_vendas['QtdVendida'].sum())
total_valor_saida = float(filtro_vendas['ValorTotal'].sum())

# Exibe os KPIs em colunas
kpis = [
    ("📦 Estoque Atual Total", f"{total_estoque:,}"),
    ("📥 Entradas no Ano", f"{total_entrada:,}"),
    ("📤 Saídas no Ano", f"{total_saida:,}"),
    ("💰 Valor Vendido", f"R$ {total_valor_saida:,.2f}")
]

for col, (label, value) in zip(st.columns(4), kpis):
    col.metric(label, value)

st.markdown("---")

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# GRÁFICOS
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

colSelect, colTable = st.columns(2)

with colSelect:
    # Seleciona quantidade de produtos para exibir no ranking
    limite = st.selectbox("Mostrar Top:", [5, 10, 15], index=1)

    # Agrupa e ordena produtos mais vendidos
    top_vendidos = (
        filtro_vendas.groupby(['CodProduto', 'Produto'])['QtdVendida']
        .sum()
        .reset_index()
        .sort_values(by='QtdVendida', ascending=False)
        .head(limite)
    )

    # Junta com dados de estoque atual
    estoque_filtrado = pd.merge(top_vendidos, df_estoque, on='CodProduto', how='left')
    estoque_filtrado = estoque_filtrado.sort_values(by='QtdVendida', ascending=False).head(limite)

    # Função para tratar valores negativos
    def formatar_estoque(qtd):
        if qtd < 0:
            return 'Negativo'
        else:
            return int(qtd)

    # Função para exibir ícones de status de estoque
    def indicador_cor(qtd):
        if qtd < 0 or qtd <= 10:
            return '🔴'
        elif qtd <= 50:
            return '🟡'
        else:
            return '🟢'

    # Aplica formatações e adiciona colunas auxiliares
    estoque_filtrado['Estoque Exibido'] = estoque_filtrado['EstoqueAtual'].apply(formatar_estoque)
    estoque_filtrado['Indicador'] = estoque_filtrado['EstoqueAtual'].apply(indicador_cor)
    estoque_filtrado.reset_index(drop=True, inplace=True)
    estoque_filtrado.index = estoque_filtrado.index + 1

    # Seleciona colunas para exibição na tabela
    tabela_exibir = estoque_filtrado[['Produto', 'Estoque Exibido', 'Indicador']]
    tabela_exibir = tabela_exibir.rename(columns={
        'Produto': 'Nome do Produto',
        'Estoque Exibido': 'Estoque Atual',
        'Indicador': 'Status'
    })

    st.subheader(f"🔍 Top {limite} Produtos Mais Vendidos (com Estoque Atual)")
    st.table(tabela_exibir)

with colTable:
    # Agrupa e ordena os produtos mais vendidos no ano
    total_vendido = (
        filtro_vendas.groupby(['CodProduto', 'Produto'])['QtdVendida']
        .sum()
        .reset_index()
        .sort_values(by='QtdVendida', ascending=False)
    )

    st.subheader("📊 Total de Produtos Vendidos (Ano)")

    # Cria gráfico de barras horizontais com Plotly
    fig_vendidos = px.bar(
        total_vendido.head(15),
        x='QtdVendida',
        y='Produto',
        orientation='h',
        labels={'QtdVendida': 'Quantidade Vendida', 'Produto': 'Produto'},
        color_discrete_sequence=['#6ABCB5'],
        title='Top Produtos por Quantidade Vendida'
    )

    # Ordena as categorias no eixo Y pelo total vendido
    fig_vendidos.update_layout(yaxis={'categoryorder':'total ascending'})

    # Exibe o gráfico
    st.plotly_chart(fig_vendidos, use_container_width=True)
    
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# GRÁFICO CUMULATIVO DE VENDAS (TOP 20 PRODUTOS AO LONGO DO ANO)
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Selecionar os 20 produtos mais vendidos no ano, somando a quantidade vendida por produto
top_20_produtos = (
    filtro_vendas.groupby('CodProduto')['QtdVendida']
    .sum()
    .sort_values(ascending=False)
    .head(20)
    .index
)

# Filtrar o DataFrame original para manter apenas os produtos do top 20
df_top_cumulativo = filtro_vendas[filtro_vendas['CodProduto'].isin(top_20_produtos)].copy()

# Garantir que a coluna QtdVendida está em formato numérico (caso tenha algum erro de leitura)
df_top_cumulativo['QtdVendida'] = pd.to_numeric(df_top_cumulativo['QtdVendida'], errors='coerce').fillna(0)

# Ordenar os dados por data de venda para que o acumulado seja calculado corretamente
df_top_cumulativo.sort_values(by='DataVenda', inplace=True)

# Calcular a quantidade vendida acumulada por produto
df_top_cumulativo['QtdVendidaAcumulada'] = (
    df_top_cumulativo.groupby('CodProduto')['QtdVendida']
    .cumsum()
)

# Criar gráfico de linha com as vendas acumuladas ao longo do tempo, separadas por produto
fig_cumulativo = px.line(
    df_top_cumulativo,
    x='DataVenda',
    y='QtdVendidaAcumulada',
    color='Produto',
    title='📈 Vendas Cumulativas – Top 20 Produtos (Ano)',
    labels={'DataVenda': 'Data', 'QtdVendidaAcumulada': 'Vendas Acumuladas'},
    hover_data={'QtdVendidaAcumulada': ':.0f'},
    color_discrete_sequence=px.colors.qualitative.Set2
)

# Exibir o gráfico no Streamlit
st.plotly_chart(fig_cumulativo, use_container_width=True)

# Separador visual
st.markdown("---")

# Merge entre entradas e produtos, para trazer o nome dos produtos nas entradas
filtro_entrada_com_nome = pd.merge(
    filtro_entrada,
    df_vendas[['CodProduto', 'Produto']].drop_duplicates(),  # Remover duplicidades para evitar duplicações no merge
    on='CodProduto',
    how='left'
)

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# AGRUPAMENTO TOTAL POR PRODUTO
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Agrupar a quantidade total de entrada por produto
df_abc = (
    filtro_entrada_com_nome.groupby(['CodProduto', 'Produto'])['QtdEntrada']
    .sum()
    .reset_index()
    .sort_values(by='QtdEntrada', ascending=False)
)

# Verificar se o DataFrame não está vazio para aplicar a lógica ABC
if not df_abc.empty:
    # Calcular a porcentagem acumulada de cada produto em relação ao total
    df_abc['PercAcumulado'] = df_abc['QtdEntrada'].cumsum() / df_abc['QtdEntrada'].sum()

    # Função para classificar o produto em categoria A, B ou C
    def classificar_abc(p):
        if p <= 0.80:
            return 'A'
        elif p <= 0.95:
            return 'B'
        else:
            return 'C'

    # Aplicar a classificação ABC
    df_abc['Categoria'] = df_abc['PercAcumulado'].apply(classificar_abc)

    # Mapear cores para cada categoria
    cores_categoria = {'A': '#6ABCB5', 'B': '#F5D547', 'C': '#A1D76A'}
    df_abc['Cor'] = df_abc['Categoria'].map(cores_categoria)

    # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    # RESUMO POR CATEGORIA (A, B, C)
    # ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

    # Agrupar a quantidade total por categoria
    df_abc_resumo = df_abc.groupby('Categoria')['QtdEntrada'].sum().reset_index()

    # Garantir que todas as categorias existam (mesmo que com zero)
    ordem_categoria = ['A', 'B', 'C']
    df_abc_resumo = df_abc_resumo.set_index('Categoria').reindex(ordem_categoria, fill_value=0).reset_index()

else:
    # Se não houver dados, cria DataFrames vazios ou zerados
    ordem_categoria = ['A', 'B', 'C']
    cores_categoria = {'A': '#6ABCB5', 'B': '#F5D547', 'C': '#A1D76A'}
    df_abc = pd.DataFrame(columns=['Produto', 'Categoria', '% nas Entradas'])
    df_abc_resumo = pd.DataFrame({
        'Categoria': ordem_categoria,
        'QtdEntrada': [0, 0, 0]
    })

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# LAYOUT EM COLUNAS
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Criar duas colunas lado a lado no layout
col1, col2 = st.columns(2)

with col1:
    # Mostrar gráfico de barras com o resumo das categorias ABC
    if not df_abc_resumo.empty:
        fig_resumo = px.bar(
            df_abc_resumo,
            x='Categoria',
            y='QtdEntrada',
            color='Categoria',
            color_discrete_map=cores_categoria,
            labels={'QtdEntrada': 'Quantidade Total de Entradas'},
            title='📊 Distribuição ABC das Entradas (Ano)'
        )
        st.plotly_chart(fig_resumo, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado disponível para gerar o gráfico de resumo ABC.")


with col2:
    st.subheader("📋 Classificação ABC dos Produtos (Ano)")

    if not df_abc.empty:
        # Calcular a porcentagem de participação de cada produto
        total_entradas = df_abc['QtdEntrada'].sum()
        df_abc['PercProduto'] = df_abc['QtdEntrada'] / total_entradas
        df_abc['% nas Entradas'] = df_abc['PercProduto'].apply(lambda x: f"{x:.1%}")

        # Selecionar colunas para a tabela
        tabela_abc = df_abc[['Produto', 'Categoria', '% nas Entradas']]
        tabela_abc.index = range(1, len(tabela_abc) + 1)  # Índice iniciando em 1

        # Função para colorir cada linha com base na categoria
        def colorir_categoria(row):
            cor = cores_categoria.get(row['Categoria'], '#FFFFFF')
            return [f'background-color: {cor}; color: black'] * len(row)

        # Exibir a tabela formatada no Streamlit
        st.dataframe(
            tabela_abc.style.apply(colorir_categoria, axis=1),
            use_container_width=True
        )
    else:
        st.warning("⚠️ Nenhum dado disponível para gerar a tabela ABC.")

st.markdown(
    "🔎 **Curva ABC:** Produtos de entrada da categoria **A** representam os responsáveis pelos **80%** do faturamento, "
    "**B** pelos próximos **15%** e **C** pelos últimos **5%**, ajudando a focar nos Produtos mais estratégicos."
)

# Separador visual
st.markdown("---")

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# CURVA ABC DAS SAÍDAS (VENDAS)
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Agrupar quantidade total vendida por produto
df_abc_saida = (
        filtro_vendas.groupby(['CodProduto', 'Produto'])['QtdVendida']
        .sum()
        .reset_index()
        .sort_values(by='QtdVendida', ascending=False)
    )

# Calcular a participação acumulada nas vendas
df_abc_saida['PercAcumulado'] = df_abc_saida['QtdVendida'].cumsum() / df_abc_saida['QtdVendida'].sum()

# Classificar os produtos vendidos em A, B, C
df_abc_saida['Categoria'] = df_abc_saida['PercAcumulado'].apply(classificar_abc)

# Aplicar cores conforme categoria
df_abc_saida['Cor'] = df_abc_saida['Categoria'].map(cores_categoria)

# Agrupar os totais por categoria
df_abc_saida_resumo = df_abc_saida.groupby('Categoria')['QtdVendida'].sum().reset_index()

# Garantir a ordem correta das categorias (A, B, C)
df_abc_saida_resumo['Categoria'] = pd.Categorical(df_abc_saida_resumo['Categoria'], categories=ordem_categoria,
                                                  ordered=True)
df_abc_saida_resumo = df_abc_saida_resumo.sort_values('Categoria')

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# LAYOUT EM COLUNAS
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Criar duas colunas lado a lado
col1, col2 = st.columns(2)

with col1:
    # Mostrar gráfico de barras com resumo das saídas por categoria ABC
    if not df_abc_saida_resumo.empty:
        fig_resumo_saida = px.bar(
            df_abc_saida_resumo,
            x='Categoria',
            y='QtdVendida',
            color='Categoria',
            color_discrete_map=cores_categoria,
            labels={'QtdVendida': 'Quantidade Total Vendida'},
            title='📊 Distribuição ABC das Saídas (Ano)'
        )
        st.plotly_chart(fig_resumo_saida, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado disponível para gerar o gráfico de resumo ABC das Saídas.")

with col2:
    st.subheader("📋 Classificação ABC dos Produtos Vendidos (Ano)")

    if not df_abc_saida.empty:
        # Calcular % de participação nas vendas
        total_vendido_saida = df_abc_saida['QtdVendida'].sum()
        df_abc_saida['PercProduto'] = df_abc_saida['QtdVendida'] / total_vendido_saida

        # Formatar a porcentagem para exibição
        df_abc_saida['% nas Saídas'] = df_abc_saida['PercProduto'].apply(lambda x: f"{x:.1%}")

        # Selecionar colunas para exibir na tabela
        tabela_abc_saida = df_abc_saida[['Produto', 'Categoria', '% nas Saídas']]
        tabela_abc_saida.index = range(1, len(tabela_abc_saida) + 1)

        # Exibir tabela com cores por categoria
        st.dataframe(
            tabela_abc_saida.style.apply(colorir_categoria, axis=1),
            use_container_width=True
        )
    else:
        st.warning("⚠️ Nenhum dado disponível para gerar a tabela ABC das Saídas.")

st.markdown(
    "🔎 **Curva ABC:** Produtos de saída da categoria **A** representam os responsáveis pelos **80%** do faturamento, "
    "**B** pelos próximos **15%** e **C** pelos últimos **5%**, ajudando a focar nos Produtos mais estratégicos."
)

# Fechar conexão com o banco de dados
cursor.close()
dados_conexao.close()
