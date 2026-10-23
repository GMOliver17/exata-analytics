"""Gera SQL sintético a partir das colunas usadas no projeto, sem ler o ERP."""
from calendar import monthrange
from datetime import date
from decimal import Decimal
from pathlib import Path
import random


def gerar_sql(hoje=None):
    hoje = hoje or date.today()
    rng = random.Random(42)
    sql = ["-- DADOS INTEIRAMENTE FICTICIOS. Nao importados nem anonimizados de um ERP.",
           "-- Execute em um banco NOVO e VAZIO selecionado no seu cliente MySQL.",
           "-- Sem DROP, sem credenciais e sem acesso ao banco real.",
           "SET NAMES utf8mb4;"]
    tabelas = {
        'empresa': 'Codigo INT PRIMARY KEY, NomeEmpresaLogin VARCHAR(100)',
        'produtos': 'Codigo INT PRIMARY KEY, Descricao VARCHAR(150), Inativo CHAR(1)',
        'municipios': 'codigo INT PRIMARY KEY, municipio VARCHAR(100)',
        'nfemitidas': 'Codigo INT PRIMARY KEY, Situacao CHAR(2)',
        'produtosestoque': 'CodEmpresa INT, CodProduto INT, EstoqueAtual DECIMAL(14,3), PRIMARY KEY (CodEmpresa, CodProduto)',
        'estoque': 'Codigo INT PRIMARY KEY, CodEmpresa INT, CodProduto INT, Data DATE, Qtde DECIMAL(14,3), TipoDoc CHAR(2)',
        'vendas': 'Codigo INT PRIMARY KEY, CodEmpresa INT, CodCliente INT, Data DATE, TotalProdutos DECIMAL(14,2), ClienteNome VARCHAR(100), ClienteEstado CHAR(2), ClienteCodMunicipio INT, ClienteApelido VARCHAR(100), DFEmitido CHAR(1), DfCodigo INT',
        'vendasprodutos': 'Codigo INT PRIMARY KEY, CodVenda INT, CodProduto INT, Quantidade DECIMAL(14,3), ValorUnitario DECIMAL(14,2), ValorTotal DECIMAL(14,2)',
    }
    for nome, cols in tabelas.items():
        sql.append(f'CREATE TABLE {nome} ({cols}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')

    def literal(v):
        if isinstance(v, str):
            return "'" + v.replace("'", "''") + "'"
        if isinstance(v, date):
            return f'DATE_SUB(CURDATE(), INTERVAL {(hoje-v).days} DAY)'
        return str(v)

    def inserir(tabela, linhas):
        # Lotes pequenos funcionam também em clientes SQL com limite de pacote baixo.
        for i in range(0, len(linhas), 150):
            sql.append(f'INSERT INTO {tabela} VALUES\n' + ',\n'.join(
                '(' + ', '.join(map(literal, linha)) + ')' for linha in linhas[i:i+150]) + ';')

    empresas = [(1, 'Empresa Demo Aurora'), (2, 'Empresa Demo Horizonte'), (3, 'Empresa Demo Vertice')]
    localidades = [('SP', 'Sao Paulo'), ('RJ', 'Rio de Janeiro'), ('MG', 'Belo Horizonte'),
                   ('PR', 'Curitiba'), ('SC', 'Florianopolis'), ('RS', 'Porto Alegre'),
                   ('BA', 'Salvador'), ('PE', 'Recife'), ('CE', 'Fortaleza'), ('GO', 'Goiania')]
    nomes = ['Parafuso', 'Porca', 'Arruela', 'Broca', 'Trena', 'Martelo', 'Alicate', 'Chave',
             'Luva', 'Oculos', 'Disco', 'Lixa', 'Pincel', 'Rolo', 'Fita', 'Cola',
             'Bucha', 'Cadeado', 'Serrote', 'Espatula', 'Nivel', 'Esquadro', 'Estilete', 'Abraçadeira']
    produtos = [(i, f'{nome} Demo {i:02d}', 'N') for i, nome in enumerate(nomes, 1)]
    precos = {i: Decimal(450 + i * 237) / 100 for i, _, _ in produtos}
    saldos = {(e, p): 0 for e, _ in empresas for p, _, _ in produtos}
    entradas, vendas, itens, notas = [], [], [], []
    for mes in range(25, -1, -1):
        ano, m0 = divmod(hoje.year * 12 + hoje.month - 1 - mes, 12)
        ultimo_dia = hoje.day if mes == 0 else monthrange(ano, m0 + 1)[1]
        for e, _ in empresas:
            for p, _, _ in produtos:
                qtd = 60 + rng.randrange(80)
                entradas.append((len(entradas)+1, e, p, date(ano, m0+1, 1), qtd, 'NE'))
                saldos[e, p] += qtd
            for n in range(12):
                dia = min(1 + n * 2, ultimo_dia)
                cliente = 1 + (n + mes) % 15
                uf, municipio = localidades[(cliente + e) % len(localidades)]
                municipio_id = next(i for i, x in enumerate(localidades, 1) if x == (uf, municipio))
                venda_id = len(vendas) + 1
                total = Decimal(0)
                for k in range(3):
                    p = 1 + (n * 3 + k + mes) % len(produtos)
                    qtd = rng.randrange(1, 9)
                    valor = precos[p] * qtd
                    itens.append((len(itens)+1, venda_id, p, qtd, precos[p], valor))
                    saldos[e, p] -= qtd
                    total += valor
                nome_cliente = f'Cliente Ficticio {e}-{cliente:02d}'
                vendas.append((venda_id, e, e*100+cliente, date(ano, m0+1, dia), total,
                               nome_cliente, uf, municipio_id, nome_cliente, 'S', venda_id))
                notas.append((venda_id, 'AU'))
    inserir('empresa', empresas)
    inserir('produtos', produtos)
    inserir('municipios', [(i, nome) for i, (_, nome) in enumerate(localidades, 1)])
    inserir('nfemitidas', notas)
    inserir('estoque', entradas)
    inserir('vendas', vendas)
    inserir('vendasprodutos', itens)
    inserir('produtosestoque', [(e, p, qtd) for (e, p), qtd in saldos.items()])
    raiz = Path(__file__).resolve().parents[1]
    views = next(raiz.glob("View*.txt")).read_text(encoding='utf-8')
    sql.append(views)
    return '\n\n'.join(sql) + '\n'


if __name__ == '__main__':
    destino = Path(__file__).with_name('base_ficticia.sql')
    destino.write_text(gerar_sql(), encoding='utf-8')
    print(f'Base ficticia gerada: {destino}')
