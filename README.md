# Exata Analytics

Meu primeiro projeto de dashboard, feito há bastante tempo para acompanhar vendas e estoque. Publicado como registro da minha evolução, preservando o código e as decisões daquela época.

O projeto utiliza **Python, Streamlit, Pandas, Plotly e MySQL**. As telas apresentam indicadores de faturamento e ticket médio, comparações entre períodos, rankings de clientes e produtos, vendas por região e análises de estoque e curva ABC.

## Demonstração com dados fictícios

A pasta `demo/` contém uma base feita do zero para este repositório: **3 empresas fictícias, 24 produtos, 45 clientes fictícios, 936 vendas e 2.808 itens de venda**, além de entradas e saldos de estoque em 26 meses. Não são dados reais anonimizados. Nenhum registro do banco de uma empresa foi usado para gerá-los.

Os nomes de cidades e estados são referências geográficas públicas. As notas são apenas registros simplificados para as consultas; não são documentos fiscais válidos. Os números servem para explorar as telas, não para representar uma operação comercial real.

### Preparar o MySQL

1. Crie um banco **novo e vazio** para a demonstração, por exemplo `exata_analytics_demo`.
2. Selecione esse banco no seu cliente MySQL e execute `demo/base_ficticia.sql` inteiro. Ele cria as oito tabelas mínimas, os dados e as quatro views necessárias ao dashboard. Não execute no banco do ERP.
3. Configure um usuário com acesso de leitura às tabelas/views para o aplicativo.

As datas do SQL são relativas ao dia da importação, para que os filtros recentes tenham dados. Se quiser refazer a demonstração, utilize outro banco vazio. O script não apaga tabelas existentes. O esquema é mínimo para este dashboard, não é uma cópia completa da estrutura de um ERP.

### Executar o dashboard

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.example.ini config.ini
Copy-Item pages/config.example.ini pages/config.ini
python -m streamlit run Home.py
```

Preencha **os dois** arquivos `config.ini` com suas credenciais locais e o nome do banco de demonstração. Execute o comando a partir da pasta do projeto. As páginas originais usam configurações separadas.

O arquivo da imagem é `assets/Logo.png`, mas o código procura `assets/logo.png`. Em Linux, renomeie a imagem para `logo.png`. Os lançadores BAT/VBS antigos usam o caminho fixo `C:\Exata Analytics`; use o comando acima se a pasta estiver em outro lugar.

Para gerar novamente o SQL, sem instalar bibliotecas adicionais:

```powershell
python demo/gerar_base.py
```

## Sobre esta versão

O código original foi mantido, inclusive suas limitações. Foram acrescentados apenas esta documentação, dependências, exemplos de configuração e os dados fictícios. Arquivos com credenciais, cache e configurações da IDE ficaram fora da publicação.

A curva ABC usa quantidades, embora alguns textos da interface mencionem faturamento; o estoque analisa uma janela de 12 meses e alguns casos sem dados ainda precisam de melhorias. A seleção de empresa é um filtro, não um controle de acesso. Esta é uma versão histórica para portfólio, não um produto pronto para produção.

O arquivo `View's necessárias NF-e.txt` foi mantido como referência da integração original. Para testar com a base fictícia, basta importar `demo/base_ficticia.sql`, que já inclui essas views. As versões das dependências não foram fixadas no projeto original.
