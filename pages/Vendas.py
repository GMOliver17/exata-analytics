# Importa as bibliotecas necessárias
import streamlit as st  # Para criar a interface web com Streamlit
import mysql.connector  # Para conectar com o banco de dados MySQL
import plotly.express as px  # Para criação de gráficos interativos
from datetime import datetime  # Para trabalhar com datas e horas
import pandas as pd  # Para manipulação de dados em DataFrame
import os  # Para lidar com caminhos e arquivos do sistema operacional
import configparser  # Para ler arquivos de configuração (.ini)
from funcoes import carregar_empresas  # Importa função personalizada que carrega empresas
from funcoes import gerar_mapa_vendas_por_estado  # Chama função gerar mapa

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Monitoramento Vendas – Exata",
                   layout="wide")  # Define o título e o layout da página

# Título principal da página
st.title("💰 Monitoramento Vendas – Visão Geral")

# Aplica estilo customizado na barra lateral (deixa azul escuro com texto branco)
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #2E2E2E;  /* azul escuro */
        }
        [data-testid="stSidebar"] * {
            color: white;  /* deixa o texto branco */
        }
    </style>
""", unsafe_allow_html=True)

# Caminho relativo para o logo da empresa
logo_path = os.path.join("assets", "logo.png")

# Mostra a imagem (logo) no topo da barra lateral
st.sidebar.image(logo_path, width=100)

# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# SELEÇÃO DE EMPRESA (usando função)
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Carrega o dicionário de empresas usando a função personalizada
empresas = carregar_empresas()

# Selectbox para o usuário escolher a empresa
cod_empresa = st.selectbox(
    "🏢 Selecione a Empresa:",  # Texto que aparece para o usuário
    options=list(empresas.keys()),  # Chaves do dicionário são os valores internos
    format_func=lambda x: empresas[x]  # Mostra o nome da empresa no menu
)

# Dicionário de cores associadas a cada empresa (opcional)
cores_empresas = {
    1: '#6ABCB5',
    2: '#4C72B0',
    3: '#F5D547'
}

# Obtém a cor da empresa selecionada ou usa preto como padrão
empresa_cor = cores_empresas.get(cod_empresa, '#000000')

# Obtém o nome da empresa com base no código selecionado
empresa_nome = empresas[cod_empresa]

# Mostra o nome da empresa com a cor correspondente no cabeçalho
st.markdown(f"<h3 style='color:{empresa_cor}'>{empresa_nome}</h3>", unsafe_allow_html=True)

# Define a cor final a ser usada nos elementos visuais
cor_empresa = cores_empresas.get(cod_empresa, '#000000')

# Função para carregar os dados do banco de dados
def carregar_dados():
    try:
        # Determina o caminho atual do arquivo
        caminho_atual = os.path.dirname(os.path.abspath(__file__))
        # Caminho completo do arquivo de configuração
        caminho_config = os.path.join(caminho_atual, 'config.ini')

        # Lê o arquivo .ini para obter as credenciais de conexão
        config = configparser.ConfigParser()
        config.read(caminho_config)

        # Extrai as configurações do banco de dados
        db_config = {
            'host': config['mysql']['host'],
            'port': int(config['mysql']['port']),
            'user': config['mysql']['user'],
            'password': config['mysql']['password'],
            'database': config['mysql']['database']
        }

        # Estabelece a conexão com o banco de dados
        conn = mysql.connector.connect(**db_config)

        # Consulta SQL para obter os dados da view
        query = f"""
            SELECT CodEmpresa, Data, TotalProdutos, ClienteNome, municipio, ClienteEstado, ClienteApelido
            FROM view_vendas_vendedores
            WHERE CodEmpresa = {cod_empresa}
        """

        # Lê o resultado da query em um DataFrame
        df = pd.read_sql(query, conn)

        # Fecha a conexão
        conn.close()

        # Retorna o DataFrame
        return df

    except mysql.connector.Error as e:
        # Mostra erro caso falhe a conexão com o banco
        st.error(f"❌ Erro ao conectar com o banco de dados:\n\n{e}")
        st.stop()

    except Exception as e:
        # Mostra erro inesperado
        st.error(f"❌ Erro inesperado ao carregar os dados:\n\n{e}")
        st.stop()

# Carrega os dados e armazena no DataFrame
df = carregar_dados()

# :::::::::::::::::::::::::::::::::::::::::::::::::::::
# PRÉ-PROCESSAMENTO DOS DADOS
# :::::::::::::::::::::::::::::::::::::::::::::::::::::

# Garante que 'TotalProdutos' é numérico e arredonda para 1 casa
df['TotalProdutos'] = df['TotalProdutos'].astype(float).round(1)

# Converte coluna 'Data' para datetime
df['Data'] = pd.to_datetime(df['Data'])

# Cria colunas separadas para ano e mês da data
df['Ano'] = df['Data'].dt.year
df['Mes'] = df['Data'].dt.month

# Ordena os dados por data
df = df.sort_values("Data")

# Trata os apelidos: remove espaços, substitui vazios/nulos pelo nome do cliente, e formata capitalizado
df['ClienteApelido'] = df['ClienteApelido'].astype(str).str.strip()
df['ClienteApelido'] = df['ClienteApelido'].replace('', pd.NA)
df['ClienteApelido'] = df['ClienteApelido'].fillna(df['ClienteNome'])
df['ClienteApelido'] = df['ClienteApelido'].str.title()

# Dicionário para nomear os meses
meses_nomes = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
               7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

# Captura o ano e mês atual
ano_atual = datetime.now().year
mes_atual = datetime.now().month

# Cria um DataFrame com ano/mês únicos, exceto o mês/ano atual
df_unicos = df.drop_duplicates(subset=['Ano', 'Mes'], keep='last').sort_values(['Ano', 'Mes'], ascending=True)
df_unicos = df_unicos[(df_unicos['Ano'] != ano_atual) | (df_unicos['Mes'] != mes_atual)]

# Define o último ano/mês disponíveis para usar como sugestão no selectbox
if not df_unicos.empty:
    ultimo_ano = df_unicos.iloc[-1]['Ano']
    ultimo_mes = df_unicos.iloc[-1]['Mes']
else:
    ultimo_ano = ano_atual
    ultimo_mes = mes_atual

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# FILTROS DE ANO E MÊS SELECIONADO PELO USUÁRIO
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Lista de anos disponíveis no DataFrame, ordenada decrescente
anos = sorted(df['Ano'].unique(), reverse=True)

# Lista dos 12 meses
meses = list(range(1, 13))

# Selectbox para o usuário escolher o ano, com default no último disponível
ano_selecionado = st.selectbox("📅 Ano", anos, index=anos.index(ultimo_ano))

# Selectbox para o usuário escolher o mês, com nome e default no último disponível
mes_selecionado = st.selectbox("📅 Mês", meses,
                               format_func=lambda x: meses_nomes[x],
                               index=meses.index(int(ultimo_mes)))

# Filtra o DataFrame conforme os filtros de ano e mês escolhidos
df_filtered = df[(df['Ano'] == ano_selecionado) & (df['Mes'] == mes_selecionado)]

# Checar se há dados filtrados para o período e empresa selecionada
if df_filtered.empty:
    st.warning("⚠️ Nenhum dado encontrado para este período e empresa selecionada.")  # Alerta se não houver dados
    st.stop()  # Interrompe a execução do app

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# KPIs (Indicadores de desempenho)
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Cria quatro colunas lado a lado para exibir os KPIs
colKPI1, colKPI2, colKPI3, colKPI4 = st.columns(4)

# Calcula o total vendido no período filtrado
total_vendido = df_filtered['TotalProdutos'].sum()

# Calcula o total de compras (quantidade de registros)
total_compras = df_filtered.shape[0]

# Calcula o ticket médio por compra
ticket_medio = total_vendido / total_compras if total_compras > 0 else 0

# Calcula o número de clientes únicos (ativos)
clientes_ativos = df_filtered['ClienteNome'].nunique()

# Exibe os KPIs
colKPI1.metric("💰 Total Vendido (R$)", f"{total_vendido:,.2f}")
colKPI2.metric("📦 Total de Compras", f"{total_compras}")
colKPI3.metric("🧾 Ticket Médio (R$)", f"{ticket_medio:,.2f}")
colKPI4.metric("👥 Clientes Ativos", f"{clientes_ativos}")

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Gráfico e tabela – Top clientes por valor comprado
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Agrupa os dados pelo apelido do cliente e soma o total vendido
df_agrupado = df_filtered.groupby(['ClienteApelido'], as_index=False)['TotalProdutos'].sum()

# Ordena do maior para o menor valor vendido
df_agrupado = df_agrupado.sort_values(by='TotalProdutos', ascending=False)

# Divide o layout em duas colunas (seleção e tabela)
colSelect, colTable = st.columns(2)

with colSelect:
    # Dropdown para selecionar quantos clientes exibir no gráfico
    limite = st.selectbox("Mostrar Top Clientes:", [5, 10, 20], index=1)

    # Criação do gráfico de barras com os clientes que mais compraram
    fig4 = px.bar(
        df_agrupado.head(limite),
        x='ClienteApelido',
        y='TotalProdutos',
        title='Total Comprado por Cliente',
        color_discrete_sequence=[cor_empresa],  # Usa a cor da empresa selecionada
        labels={'TotalProdutos': 'Total R$'},
        text_auto=True  # Exibe valores nas barras
    )
    fig4.update_layout(xaxis_tickangle=-45)  # Inclina os nomes do eixo X
    st.plotly_chart(fig4, use_container_width=True)  # Exibe o gráfico

with colTable:
    # Título da tabela
    st.subheader("👥 Top 10 Clientes por Total Comprado")

    # Seleciona os 10 primeiros clientes e formata os valores
    df_top10 = df_agrupado[['ClienteApelido', 'TotalProdutos']].head(10).reset_index(drop=True)
    df_top10['TotalProdutos'] = df_top10['TotalProdutos'].map('R$ {:,.2f}'.format)
    df_top10.index += 1  # Ajusta índice para começar em 1
    st.dataframe(df_top10, use_container_width=True)  # Exibe a tabela

st.markdown("---")  # Linha divisória

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Gráfico – Quantidade de Compras por Cliente
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Dropdown para definir quantos clientes exibir no gráfico
top_clientes = st.selectbox("📊 Top clientes por quantidade de compras", options=[5, 10, 15, 20], index=1)

# Agrupa por cliente e calcula quantidade de compras
df_qtd_compras = df_filtered.groupby('ClienteApelido', as_index=False).agg(
    QtdeVendas=('TotalProdutos', 'count')
)

# Ordena pelo maior número de compras e limita ao top selecionado
df_qtd_compras = df_qtd_compras.sort_values('QtdeVendas', ascending=False).head(top_clientes)

# Calcula o valor máximo de compras para ajustar o eixo Y
max_compras = df_qtd_compras['QtdeVendas'].max()

# Cria gráfico de barras da quantidade de compras por cliente
fig1 = px.bar(
    df_qtd_compras,
    x='ClienteApelido',
    y='QtdeVendas',
    title='📦 Quantidade de Compras por Cliente',
    color_discrete_sequence=[cor_empresa],
    labels={'QtdeVendas': 'Quantidade de Compras', 'ClienteApelido': 'Cliente'},
    text='QtdeVendas'
)

# Personaliza a aparência dos textos nas barras
fig1.update_traces(texttemplate='%{text}', textposition='outside')

# Ajusta o eixo Y para não cortar os textos no topo
fig1.update_layout(
    xaxis_tickangle=-45,
    yaxis_range=[0, max_compras * 1.15]  # 15% acima do maior valor
)

# Exibe o gráfico
st.plotly_chart(fig1, use_container_width=True)
st.markdown("---")  # Linha divisória

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Gráficos de Participação – Município e Estado
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Seleção de top municípios para gráfico de pizza
top_municipio = st.selectbox("Top municípios Participação nas vendas", options=[5, 10, 15, 20], index=1)

# Agrupa os dados por município e soma as vendas
df_municipio = df_filtered.groupby('municipio', as_index=False)['TotalProdutos'].sum()
df_municipio = df_municipio.sort_values('TotalProdutos', ascending=False).head(top_municipio)

# Gráfico de pizza por município
fig2 = px.pie(
    df_municipio,
    names='municipio',
    values='TotalProdutos',
    title='🚚 Participação nas Vendas por Município',
)

# Agrupa os dados por estado e soma as vendas
df_estado = df_filtered.groupby('ClienteEstado', as_index=False)['TotalProdutos'].sum()

# Usa o gráfico de mapa no lugar do gráfico de pizza
fig3 = gerar_mapa_vendas_por_estado(df_estado)

# Coloca os dois gráficos lado a lado
col2, col3 = st.columns(2)
col2.plotly_chart(fig2, use_container_width=True)
col3.plotly_chart(fig3, use_container_width=True)

st.markdown("---")  # Linha divisória

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Gráfico – Evolução das Vendas no Mês
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Agrupa por data e soma o total vendido
fig5 = px.line(
    df_filtered.groupby('Data', as_index=False)['TotalProdutos'].sum(),
    x='Data',
    y='TotalProdutos',
    title='📊 Evolução das Vendas no Mês',
    color_discrete_sequence=[cor_empresa],
    markers=True  # Adiciona marcadores nos pontos
)
fig5.update_layout(xaxis_title='Data', yaxis_title='Total Vendido (R$)')  # Títulos dos eixos

# Exibe o gráfico de linha
st.subheader("Evolução das Vendas no Mês")
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")  # Linha divisória

# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Gráfico – Evolução Anual das Vendas (Extra)
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Filtra o DataFrame original para o ano selecionado
df_ano = df[df['Ano'] == ano_selecionado]

# Agrupa por mês e soma o total vendido
df_evolucao = df_ano.groupby('Mes', as_index=False)['TotalProdutos'].sum()

# Cria gráfico de barras da evolução mensal
fig_evolucao = px.bar(
    df_evolucao,
    x='Mes',
    y='TotalProdutos',
    title='📈 Evolução Mensal das Vendas no Ano',
    labels={'Mes': 'Mês', 'TotalProdutos': 'Total Vendido (R$)'},
    color_discrete_sequence=[cor_empresa]
)

# Ajusta os rótulos do eixo X para nomes dos meses
fig_evolucao.update_xaxes(
    tickmode='array',
    tickvals=list(range(1, 13)),
    ticktext=[meses_nomes[m] for m in range(1, 13)]
)

# Exibe o gráfico
st.plotly_chart(fig_evolucao, use_container_width=True)
