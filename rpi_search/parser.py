import io
import zipfile
from typing import Tuple, Optional

def read_xml_bytes(uploaded_bytes: bytes, filename: str) -> Tuple[bytes, str]:
    """
    Aceita:
      - XML puro (.xml)
      - ZIP contendo XML (.zip) (ex.: RM####.zip)
    Retorna: (xml_bytes, xml_filename)
    """
    lower = (filename or "").lower()

    if lower.endswith(".xml"):
        return uploaded_bytes, filename

    if lower.endswith(".zip"):
        z = zipfile.ZipFile(io.BytesIO(uploaded_bytes))
        xml_names = [n for n in z.namelist() if n.lower().endswith(".xml")]
        if not xml_names:
            raise ValueError(f"ZIP não contém XML. Arquivos internos: {z.namelist()[:30]}")
        xml_name = xml_names[0]
        return z.read(xml_name), xml_name

    raise ValueError("Formato inválido. Envie um arquivo .xml ou .zip (com XML dentro).")
