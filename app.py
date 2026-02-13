# app.py
from __future__ import annotations

import os
import sys
from typing import List

import streamlit as st

# Garante que o diretório do app está no PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rpi_search.parser import read_xml_bytes
from rpi_search.structured_rm import iter_rm_records, especificacao_preview, RMRecord
from rpi_search.matching_rm import match_records, Match


# ----------------------------
# Configuração da página
# ----------------------------
st.set_page_config(
    page_title="Buscador RPI INPI — Seção V (Marcas)",
    layout="wide",
)

st.title("🔎 Buscador Estruturado — RPI INPI (Seção V: Marcas)")
st.caption(
    "Upload do RM####.xml (revista de Marcas). "
    "Busca por Elemento Nominativo com correspondência exata e semelhante."
)

# ----------------------------
# Estilo
# ----------------------------
st.markdown("""
<style>
.card{
  border:1px solid rgba(49,51,63,.2);
  border-radius:14px;
  padding:18px 20px;
  margin:12px 0;
  background:rgba(250,250,255,.35)
}
.title{
  font-size:20px;
  font-weight:800;
  margin-bottom:6px;
}
.badge{
  display:inline-block;
  padding:4px 10px;
  border-radius:999px;
  font-size:12px;
  font-weight:800;
  margin-right:8px
}
.badge-exata{
  background:rgba(16,185,129,.18);
  border:1px solid rgba(16,185,129,.45)
}
.badge-sim{
  background:rgba(245,158,11,.18);
  border:1px solid rgba(245,158,11,.45)
}
.label{font-weight:800}
.small{font-size:13px;opacity:.95}
.mono{
  font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,
  Consolas,"Liberation Mono","Courier New",monospace
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Inputs
# ----------------------------
uploaded = st.file_uploader(
    "Upload da revista (RM####.xml ou .zip com XML)",
    type=["xml", "zip"],
)

keyword = st.text_input(
    "Palavra-chave (Elemento nominativo)",
    placeholder="Ex.: ITA AÇOS",
)

col1, col2 = st.columns([1, 1])

with col1:
    enable_similar = st.toggle("Buscar semelhantes", value=True)

with col2:
    threshold = st.number_input(
        "Limiar de similaridade (0–100)",
        min_value=0,
        max_value=100,
        value=90,
        step=1,
    )

run = st.button("🚀 Pesquisar", type="primary", use_container_width=True)

# ----------------------------
# Cache
# ----------------------------
@st.cache_data(show_spinner=False)
def _parse_records(file_bytes: bytes, filename: str) -> List[RMRecord]:
    xml_bytes, _ = read_xml_bytes(file_bytes, filename)
    return list(iter_rm_records(xml_bytes))


# ----------------------------
# Execução
# ----------------------------
if run:
    if not uploaded:
        st.error("Envie o arquivo RM####.xml (ou .zip com XML).")
        st.stop()

    if not keyword.strip():
        st.error("Informe a palavra-chave.")
        st.stop()

    with st.spinner("Lendo e estruturando a revista..."):
        records = _parse_records(uploaded.getvalue(), uploaded.name)

    with st.spinner("Executando matching..."):
        matches: List[Match] = match_records(
            records=records,
            keyword=keyword,
            threshold=int(threshold),
            enable_similar=enable_similar,
        )

    if not matches:
        st.warning("❌ Termo não encontrado.")
        st.stop()

    st.success(f"✅ Resultados encontrados: {len(matches)} (exibindo até 100)")

    for i, m in enumerate(matches[:100], start=1):
        r = m.record

        badge_class = "badge-exata" if m.tipo == "EXATA" else "badge-sim"
        badge_txt = (
            "CORRESPONDÊNCIA EXATA"
            if m.tipo == "EXATA"
            else f"SEMELHANTE (score={m.score})"
        )

        esp_prev = especificacao_preview(r.especificacao)

        st.markdown(f"""
        <div class="card">
          <div class="title">{r.elemento_nominativo or "-"}</div>

          <div>
            <span class="badge {badge_class}">{badge_txt}</span>
            <span class="small mono">
              RPI {r.revista_numero} ({r.revista_data})
            </span>
          </div>

          <div class="small" style="margin-top:10px;">
            <div><span class="label">Titular:</span> {r.titular_nome or "-"}</div>
            <div><span class="label">Data de depósito:</span> {r.data_deposito or "-"}</div>
            <div><span class="label">Apresentação:</span> {r.apresentacao or "-"}</div>
            <div><span class="label">Natureza:</span> {r.natureza or "-"}</div>
            <div><span class="label">NCL:</span> {r.ncl or "-"}</div>
            <div><span class="label">Despacho:</span> {r.despacho_nome or "-"} {f"({r.despacho_codigo})" if r.despacho_codigo else ""}</div>
            <div><span class="label">Status:</span> {r.status or "-"}</div>
            <div><span class="label">Procurador:</span> {r.procurador or "-"}</div>
          </div>

          <div class="small" style="margin-top:10px;">
            <div><span class="label">Especificação:</span> {esp_prev or "-"}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if (r.especificacao or "").strip():
            with st.expander("Ver especificação completa"):
                st.write(r.especificacao)
