# rpi_search/structured_rm.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Optional

from lxml import etree


@dataclass
class RMRecord:
    revista_numero: str
    revista_data: str

    processo_numero: str
    data_deposito: Optional[str]
    data_concessao: Optional[str]
    data_vigencia: Optional[str]

    despacho_codigo: Optional[str]
    despacho_nome: Optional[str]

    titular_nome: Optional[str]
    titular_pais: Optional[str]
    titular_uf: Optional[str]

    apresentacao: Optional[str]
    natureza: Optional[str]
    elemento_nominativo: Optional[str]

    ncl: Optional[str]
    status: Optional[str]
    especificacao: Optional[str]

    procurador: Optional[str]


def especificacao_preview(full: Optional[str]) -> str:
    """
    Retorna apenas a primeira frase/segmento da especificação:
    - até o primeiro ';' (ponto e vírgula), mantendo ';' no final
    - se não houver ';', devolve um trecho curto.
    """
    if not full:
        return ""
    text = re.sub(r"\s+", " ", full).strip()
    if ";" in text:
        return text.split(";", 1)[0].strip() + ";"
    return (text[:180] + "…") if len(text) > 180 else text


def iter_rm_records(xml_bytes: bytes, max_records: int = 200000) -> Iterator[RMRecord]:
    """
    Parser determinístico para XML de Marcas no padrão RM####.xml (RPI - Seção V).

    Produz 1 registro por (processo × classe-nice), pois a especificação/status
    ficam dentro de cada <classe-nice>.

    Estrutura esperada (padrão observado):
      <revista numero="####" data="dd/mm/aaaa">
        <processo numero="..." data-deposito="...">
          <despachos><despacho codigo="..." nome="..."/></despachos>
          <titulares><titular nome-razao-social="..." pais="..." uf="..."/></titulares>
          <marca apresentacao="..." natureza="..."><nome>...</nome></marca>
          <lista-classe-nice>
            <classe-nice codigo="...">
              <especificacao>...</especificacao>
              <status>...</status>
            </classe-nice>
            ...
          </lista-classe-nice>
          <procurador>...</procurador>
        </processo>
      </revista>
    """
    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(xml_bytes, parser=parser)

    revista_numero = root.get("numero", "") or ""
    revista_data = root.get("data", "") or ""

    count = 0

    for proc in root.iterfind("processo"):
        processo_numero = proc.get("numero", "") or ""
        data_deposito = proc.get("data-deposito")
        data_concessao = proc.get("data-concessao")
        data_vigencia = proc.get("data-vigencia")

        # despacho (primeiro)
        despacho_codigo = despacho_nome = None
        desp = proc.find("despachos/despacho")
        if desp is not None:
            despacho_codigo = desp.get("codigo")
            despacho_nome = desp.get("nome")

        # titular (primeiro)
        titular_nome = titular_pais = titular_uf = None
        tit = proc.find("titulares/titular")
        if tit is not None:
            titular_nome = tit.get("nome-razao-social")
            titular_pais = tit.get("pais")
            titular_uf = tit.get("uf")

        # marca
        apresentacao = natureza = elemento = None
        marca = proc.find("marca")
        if marca is not None:
            apresentacao = marca.get("apresentacao")
            natureza = marca.get("natureza")
            nome_el = marca.find("nome")
            if nome_el is not None and (nome_el.text or "").strip():
                elemento = (nome_el.text or "").strip()

        # procurador
        procurador = None
        proc_el = proc.find("procurador")
        if proc_el is not None and (proc_el.text or "").strip():
            procurador = (proc_el.text or "").strip()

        # classes NICE -> 1 record por classe-nice
        lista = proc.find("lista-classe-nice")
        if lista is None:
            continue

        for cn in lista.findall("classe-nice"):
            ncl = cn.get("codigo")

            especificacao = None
            esp_el = cn.find("especificacao")
            if esp_el is not None and (esp_el.text or "").strip():
                especificacao = (esp_el.text or "").strip()

            status_txt = None
            st_el = cn.find("status")
            if st_el is not None and (st_el.text or "").strip():
                status_txt = (st_el.text or "").strip()

            yield RMRecord(
                revista_numero=revista_numero,
                revista_data=revista_data,
                processo_numero=processo_numero,
                data_deposito=data_deposito,
                data_concessao=data_concessao,
                data_vigencia=data_vigencia,
                despacho_codigo=despacho_codigo,
                despacho_nome=despacho_nome,
                titular_nome=titular_nome,
                titular_pais=titular_pais,
                titular_uf=titular_uf,
                apresentacao=apresentacao,
                natureza=natureza,
                elemento_nominativo=elemento,
                ncl=ncl,
                status=status_txt,
                especificacao=especificacao,
                procurador=procurador,
            )

            count += 1
            if count >= max_records:
                return

