from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

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
# Modelo de Registro
# ----------------------------
@dataclass
class MarcaRecord:
    processo: Optional[str]
    marca: Optional[str]
    titular: Optional[str]
    classe: Optional[str]
    despacho: Optional[str]
    natureza: Optional[str]
    raw_text: str

    def to_dict(self) -> Dict:
        return asdict(self)


# ----------------------------
# Heurísticas de tags comuns (variam entre layouts)
# ----------------------------
FIELD_TAG_ALIASES = {
    "processo": [
        "processo", "numeroprocesso", "numero_processo", "nprocesso", "processonumero"
    ],
    "marca": [
        "marca", "denominacao", "apresentacao", "nome", "sinal", "sinaldistintivo"
    ],
    "titular": [
        "titular", "requerente", "depositante", "nome_razao_social", "razaosocial"
    ],
    "classe": [
        "classe", "classenice", "nice", "classificacao", "classe_nice"
    ],
    "despacho": [
        "despacho", "codigodespacho", "codigo_despacho", "evento", "decisao"
    ],
    "natureza": [
        "natureza", "tipo", "modalidade", "apresentacao_marca"
    ],
}

# tags que tipicamente “encapsulam” um registro/processo
RECORD_CONTAINER_HINTS = [
    "processo", "pedido", "registro", "marca", "despacho", "requerimento"
]


def _tag_localname(el: etree._Element) -> str:
    # remove namespace
    if el.tag is None:
        return ""
    return etree.QName(el).localname.lower()


def _find_first_text_by_aliases(container: etree._Element, aliases: List[str]) -> Optional[str]:
    # busca por tags cujo localname contenha algum alias
    for el in container.iter():
        name = _tag_localname(el)
        if any(a in name for a in aliases):
            txt = (el.text or "").strip()
            if txt:
                return txt
    return None


def _container_score(el: etree._Element) -> int:
    # pontua containers que “parecem” registro: contém várias tags relevantes
    score = 0
    names = [_tag_localname(x) for x in el.iter()]
    joined = " ".join(names)
    for hint in RECORD_CONTAINER_HINTS:
        if hint in joined:
            score += 1
    return score


def extract_records(xml_bytes: bytes, max_records: int = 200000) -> List[MarcaRecord]:
    """
    Extrai registros da RPI (Seção V / Marcas) de forma heurística.
    """
    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(xml_bytes, parser=parser)

    # Estratégia:
    # 1) procura nós com "processo"/"pedido"/"registro" no nome da tag
    # 2) escolhe os que têm bom score e tamanho razoável
    candidates: List[etree._Element] = []
    for el in root.iter():
        lname = _tag_localname(el)
        if any(h in lname for h in ["processo", "pedido", "registro", "requerimento"]):
            candidates.append(el)

    # fallback: se não achar, tenta nós com score alto
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

        # se não tiver nada “minimamente útil”, ignora
        if not any([processo, marca, titular, classe, despacho]):
            continue

        # raw_text para contexto/lastro (curto e limpo)
        raw_text = " ".join(t.strip() for t in el.itertext() if t and t.strip())
        raw_text = re.sub(r"\s+", " ", raw_text).strip()

        # deduplicação por assinatura
        sig = (norm_text(processo or ""), norm_text(marca or ""), norm_text(titular or ""), norm_text(classe or ""), norm_text(despacho or ""))
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
                raw_text=raw_text[:2000],  # limita contexto para UI
            )
        )

    return records
