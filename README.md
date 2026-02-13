Buscador RPI – INPI (Seção V – Marcas)

Aplicação desenvolvida em Streamlit para pesquisa estruturada na Revista da Propriedade Industrial (RPI), Seção V – Marcas, a partir do arquivo oficial RM####.xml disponibilizado pelo INPI.

Objetivo

Permitir que o usuário faça upload da revista oficial em formato XML (ou ZIP contendo XML) e realize busca por Elemento Nominativo, com identificação de correspondência exata ou semelhante.

Funcionalidades

* Upload do arquivo RM####.xml ou RM####.zip
* Extração estruturada dos registros da revista
* Busca por Elemento Nominativo
* Identificação de:

  * Correspondência Exata
  * Correspondência Semelhante (com score de similaridade)
* Exibição organizada no padrão da RPI
* Especificação resumida (primeiro trecho até o ponto e vírgula), com opção de expandir

Como executar

1. Instale as dependências:

pip install -r requirements.txt

2. Execute a aplicação:

streamlit run app.py

O navegador abrirá automaticamente.

Como usar

1. Acesse o site oficial da RPI:
   [https://revistas.inpi.gov.br/rpi/](https://revistas.inpi.gov.br/rpi/)

2. Baixe o arquivo correspondente à Seção V – Marcas (RM####.zip ou XML).

3. Faça upload do arquivo na aplicação.

4. Informe a palavra-chave desejada (exemplo: ITA AÇOS).

5. Defina se deseja buscar semelhantes e o limiar de similaridade (recomendado: 90).

6. Clique em Pesquisar.

Funcionamento técnico

O sistema realiza parsing estruturado do XML da revista, extraindo:

* Número do processo
* Data de depósito
* Titular
* Elemento nominativo
* Natureza
* Apresentação
* Classe NCL
* Especificação
* Status
* Despacho
* Procurador

Cada resultado é gerado por processo e por classe NCL.

A similaridade é calculada utilizando RapidFuzz (token_set_ratio), permitindo capturar variações como:

* Acentuação (AÇOS / ACOS)
* Singular e plural
* Pequenas variações ortográficas
* Diferenças de espaçamento

Observação

A aplicação não realiza scraping nem consome API externa. Ela apenas processa o arquivo oficial fornecido pelo usuário, garantindo reprodutibilidade e rastreabilidade da fonte.

Requisitos

* Python 3.10 ou superior
* Streamlit
* lxml
* rapidfuzz
