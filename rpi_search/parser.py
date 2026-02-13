# rpi_search/parser.py
from __future__ import annotations

import io
import zipfile
from typing import Tuple


def read_xml_bytes(uploaded_bytes: bytes, filename: str) -> Tuple[bytes, str]:
    """
    Lê o conteúdo enviado pelo usuário e retorna (xml_bytes, xml_filename).

    Aceita:
      - .xml (XML puro)
      - .zip (ZIP contendo 1+ arquivos .xml; retorna o primeiro .xml encontrado)

    Observações:
      - O RM do INPI costuma vir como RM####.zip, contendo RM####.xml.
      - Esta função é intencionalmente "strict": se não for XML/ZIP válido, lança ValueError.
    """
    if not uploaded_bytes:
        raise ValueError("Arquivo vazio ou inválido.")

    lower = (filename or "").lower().strip()

    if lower.endswith(".xml"):
        return uploaded_bytes, filename

    if lower.endswith(".zip"):
        try:
            z = zipfile.ZipFile(io.BytesIO(uploaded_bytes))
        except zipfile.BadZipFile as e:
            raise ValueError("ZIP inválido ou corrompido.") from e

        xml_names = [n for n in z.namelist() if n.lower().endswith(".xml")]

        if not xml_names:
            preview = ", ".join(z.namelist()[:30])
            raise ValueError(
                f"ZIP não contém nenhum arquivo .xml. Arquivos internos (parcial): {preview}"
            )

        # Escolha determinística: primeiro XML da lista
        xml_name = xml_names[0]
        return z.read(xml_name), xml_name

    raise ValueError("Formato inválido. Envie um arquivo .xml ou .zip (com XML dentro).")
