# rpi_search/structured.py
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from lxml import etree


# ----------------------------
# Normalização
# ----------------------------
def norm_text(s: str) -> str:
    s = (s or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


# ----------------------------
# Modelo genérico (heurístico)
# ----------------------------
@dataclass
class MarcaRecord:
    processo: Optional[str]
    marca: Optional[str]
    titular: Optional[str]
    classe: Optional[str]
    despacho: Optional[str]
    natureza: Optional[str]
    especificacao: Optional[str]
    procurador: Optional[str]
    raw_text: str

    def to_dict(self) -> Dict:
        return asdict(self)


# ----------------------------
# Aliases de campos (heurístico)
# ----------------------------
FIELD_TAG_ALIASES = {
    "processo": [
        "processo",
        "numeroprocesso",
        "numero_processo",
        "nprocesso",
        "processonumero",
    ],
    "marca": [
        "marca",
        "denominacao",
        "denominação",
        "apresentacao",
        "nome",
        "sinal",
        "sinaldistintivo",
    ],
    "titular": [
        "titular",
        "requerente",
        "depositante",
        "razaosocial",
        "nome_razao_social",
    ],
    "classe": [
        "classe",
        "classenice",
        "nice",
        "classificacao",
        "classe_nice",
    ],
    "despacho": [
        "despacho",
        "codigodespacho",
        "codigo_despacho",
        "evento",
        "decisao",
    ],
    "natureza": [
        "natureza",
        "tipo",
        "modalidade",
    ],
    "especificacao": [
        "especificacao",
        "especificação",
        "produtos_servicos",
        "servicos_produtos",
        "lista_produtos",
    ],
    "procurador": [
        "procurador",
        "representante",
        "agente",
        "mandatario",
        "mandatário",
    ],
}

RECORD_CONTAINER_HINTS = [
    "processo",
    "pedido",
    "registro",
    "marca",
    "despacho",
    "requerimento",
]


def _tag_localname(el: etree._Element) -> str:
    if el.tag is None:
        return ""
    return etree.QName(el).localname.lower()


def _find_first_text_by_aliases(container: etree._Element, aliases: List[str]) -> Optional[str]:
    for el in container.iter():
        name = _tag_localname(el)
        if any(alias in name for alias in aliases):
            txt = (el.text or "").strip()
            if txt:
                return txt
    return None


def _container_score(el: etree._Element) -> int:
    score = 0
    names = [_tag_localname(x) for x in el.iter()]
    joined = " ".join(names)
    for hint in RECORD_CONTAINER_HINTS:
        if hint in joined:
            score += 1
    return score


def extract_records(xml_bytes: bytes, max_records: int = 200000) -> List[MarcaRecord]:
    """
    Parser heurístico genérico para XML de marcas.
    Mantido por compatibilidade.
    Para RM####.xml específico, usar structured_rm.py.
    """
    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(xml_bytes, parser=parser)

    candidates: List[etree._Element] = []

    for el in root.iter():
        lname = _tag_localname(el)
        if any(h in lname for h in ["processo", "pedido", "registro", "requerimento"]):
            candidates.append(el)

    if not candidates:
        for el in root.iter():
            if _container_score(el) >= 3:
                candidates.append(el)

    records: List[MarcaRecord] = []
    seen = set()

    for el in candidates:
        if len(records) >= max_records:
            break

        processo = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["processo"])
        marca = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["marca"])
        titular = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["titular"])
        classe = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["classe"])
        despacho = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["despacho"])
        natureza = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["natureza"])
        especificacao = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["especificacao"])
        procurador = _find_first_text_by_aliases(el, FIELD_TAG_ALIASES["procurador"])

        if not any([processo, marca, titular, classe, despacho]):
            continue

        raw_text = " ".join(t.strip() for t in el.itertext() if t and t.strip())
        raw_text = re.sub(r"\s+", " ", raw_text).strip()

        sig = (
            norm_text(processo or ""),
            norm_text(marca or ""),
            norm_text(titular or ""),
            norm_text(classe or ""),
            norm_text(despacho or ""),
        )
        if sig in seen:
            continue
        seen.add(sig)

        records.append(
            MarcaRecord(
                processo=processo,
                marca=marca,
                titular=titular,
                classe=classe,
                despacho=despacho,
                natureza=natureza,
                especificacao=especificacao,
                procurador=procurador,
                raw_text=raw_text[:2000],
            )
        )

    return records
