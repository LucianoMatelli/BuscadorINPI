import streamlit as st

from rpi_search.parser import read_xml_bytes
from rpi_search.search import search_keyword_in_xml

st.set_page_config(page_title="Buscador RPI (INPI) — Seção V Marcas", layout="wide")

st.title("🔎 Buscador de Palavra-chave na RPI (INPI) — Seção V (Marcas)")
st.caption("Fluxo: baixe o arquivo do INPI (XML ou ZIP com XML), faça upload aqui, informe a palavra-chave e execute a busca.")

with st.expander("✅ Como usar", expanded=True):
    st.markdown(
        """
        1) Acesse a RPI no site do INPI e baixe o arquivo da seção de Marcas (normalmente `RM####.zip`) ou o XML (se disponível).  
        2) Faça upload abaixo.  
        3) Digite a palavra-chave (ex.: **ITA AÇOS**).  
        4) Clique em **Pesquisar**.  
        """
    )

uploaded = st.file_uploader("Upload do arquivo (XML ou ZIP com XML)", type=["xml", "zip"])
keyword = st.text_input("Palavra-chave", placeholder="Ex.: ITA AÇOS")

col1, col2, col3 = st.columns([1,1,2])
with col1:
    window = st.number_input("Contexto (caracteres)", min_value=80, max_value=800, value=220, step=20)
with col2:
    max_hits = st.number_input("Máx. ocorrências", min_value=10, max_value=2000, value=200, step=10)

btn = st.button("🔍 Pesquisar", type="primary", use_container_width=True)

if btn:
    if not uploaded:
        st.error("Envie um arquivo XML ou ZIP (com XML) para continuar.")
        st.stop()
    if not keyword.strip():
        st.error("Informe a palavra-chave para pesquisa.")
        st.stop()

    try:
        xml_bytes, inner_name = read_xml_bytes(uploaded.getvalue(), uploaded.name)
    except Exception as e:
        st.error(f"Falha ao ler o arquivo: {e}")
        st.stop()

    hits = search_keyword_in_xml(xml_bytes, keyword=keyword, window=int(window), max_hits=int(max_hits))

    if not hits:
        st.warning("❌ Termo não encontrado.")
    else:
        st.success(f"✅ Encontrado: {len(hits)} ocorrência(s).")
        st.caption(f"Arquivo processado: {uploaded.name} → {inner_name}")

        # Lista de resultados
        for i, h in enumerate(hits[:50], start=1):
            with st.expander(f"Ocorrência #{i} (posição aproximada: {h.index})", expanded=(i <= 3)):
                st.code(h.context)

        if len(hits) > 50:
            st.info(f"Mostrando as primeiras 50 ocorrências. Total encontrado: {len(hits)}.")
