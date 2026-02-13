# rpi_search/matching_rm.py
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List

from rapidfuzz import fuzz

from rpi_search.structured_rm import RMRecord


def norm(s: str) -> str:
    s = (s or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


@dataclass
class Match:
    record: RMRecord
    tipo: str   # "EXATA" | "SEMELHANTE"
    score: int  # 0..100


def match_records(
    records: List[RMRecord],
    keyword: str,
    threshold: int = 90,
    enable_similar: bool = True,
) -> List[Match]:
    kw = norm(keyword)
    out: List[Match] = []

    for r in records:
        alvo = norm(r.elemento_nominativo or "")
        if not alvo:
            continue

        if kw and kw in alvo:
            out.append(Match(record=r, tipo="EXATA", score=100))
            continue

        if enable_similar:
            score = int(fuzz.token_set_ratio(kw, alvo))
            if score >= threshold:
                out.append(Match(record=r, tipo="SEMELHANTE", score=score))

    out.sort(key=lambda m: (0 if m.tipo == "EXATA" else 1, -m.score))
    return out
