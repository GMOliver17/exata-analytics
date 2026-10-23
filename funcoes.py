import streamlit as st
import mysql.connector
import os
import configparser
import requests
import pandas as pd
import plotly.express as px
import json

def carregar_empresas():
    """
    Carrega as empresas diretamente do banco de dados
    e retorna um dicionário {CodEmpresa: NomeEmpresaLogin}
    """
    caminho_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_config = os.path.join(caminho_atual, 'config.ini')

    config = configparser.ConfigParser()
    config.read(caminho_config)

    db_config = {
        'host': config['mysql']['host'],
        'port': int(config['mysql']['port']),
        'user': config['mysql']['user'],
        'password': config['mysql']['password'],
        'database': config['mysql']['database']
    }

    try:
        conexao = mysql.connector.connect(**db_config)
        cursor = conexao.cursor()
        cursor.execute("SELECT Codigo, NomeEmpresaLogin FROM empresa")
        empresas_raw = cursor.fetchall()
        conexao.close()

        return {cod: nome for cod, nome in empresas_raw}

    except mysql.connector.Error as e:
        st.error(f"❌ Erro ao conectar com o banco de dados:\n\n{e}")
        st.stop()


def gerar_mapa_vendas_por_estado(df_estado, cor_escala='plasma'):
    import plotly.express as px
    import requests
    import pandas as pd
    import plotly.colors as pc

    # GeoJSON dos estados brasileiros
    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson_estados = requests.get(geojson_url).json()

    # Dicionário de siglas para nomes dos estados
    sigla_para_nome = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia', 'CE': 'Ceará',
        'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
        'SE': 'Sergipe', 'TO': 'Tocantins'
    }

    # Converte siglas para nomes dos estados
    df_estado['EstadoNome'] = df_estado['ClienteEstado'].map(sigla_para_nome)

    # Garante que todos os estados existam no DataFrame
    todos_estados = pd.DataFrame(list(sigla_para_nome.values()), columns=['EstadoNome'])
    df_completo = todos_estados.merge(df_estado[['EstadoNome', 'TotalProdutos']], on='EstadoNome', how='left')
    df_completo['TotalProdutos'] = df_completo['TotalProdutos'].fillna(0)

    # Escala de cores personalizada
    plasma_colors = pc.get_colorscale(cor_escala)
    custom_colorscale = [
        [0.0, '#d3d3d3'],   # cinza claro para zero
        [0.00001, plasma_colors[0][1]]  # do primeiro valor > 0 em diante, começa o gradiente
    ] + plasma_colors[1:]  # continua a escala original

    # Gera o mapa
    fig = px.choropleth(
        df_completo,
        geojson=geojson_estados,
        locations='EstadoNome',
        featureidkey='properties.name',
        color='TotalProdutos',
        color_continuous_scale=custom_colorscale,
        labels={'TotalProdutos': 'Vendas'},
        title='🗺️ Vendas por Estado'
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    return fig
