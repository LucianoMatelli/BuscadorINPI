import re
import unicodedata
from dataclasses import dataclass
from typing import List

@dataclass
class Hit:
    index: int
    context: str

def norm_text(s: str) -> str:
    s = (s or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s

def search_keyword_in_xml(xml_bytes: bytes, keyword: str, window: int = 220, max_hits: int = 200) -> List[Hit]:
    """
    Busca simples (texto bruto normalizado) com contexto ao redor.
    É o mesmo racional do protótipo: rápido, estável e suficiente para MVP.
    """
    raw = xml_bytes.decode("utf-8", errors="ignore")
    raw_norm = norm_text(raw)
    kw_norm = norm_text(keyword)

    if not kw_norm:
        return []

    hits: List[Hit] = []
    start = 0
    while True:
        idx = raw_norm.find(kw_norm, start)
        if idx == -1:
            break

        ctx_start = max(0, idx - window)
        ctx_end = min(len(raw_norm), idx + len(kw_norm) + window)
        ctx = raw_norm[ctx_start:ctx_end]

        hits.append(Hit(index=idx, context=ctx))
        start = idx + len(kw_norm)

        if len(hits) >= max_hits:
            break

    return hits
