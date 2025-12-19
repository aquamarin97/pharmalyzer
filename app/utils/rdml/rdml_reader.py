# app\utils\rdml\rdml_reader.py
import os
import zipfile
import xml.etree.ElementTree as ET


RDML_NS = {"rdml": "http://www.rdml.org"}


def read_rdml_root(file_path: str) -> ET.Element:
    """
    RDML dosyası bazen düz XML, bazen zip içinde XML olur.
    Bu fonksiyon root element döndürür.
    """
    if not file_path:
        raise ValueError("RDML dosya yolu boş.")

    # 1) Direkt XML mi?
    try:
        tree = ET.parse(file_path)
        return tree.getroot()
    except ET.ParseError:
        pass  # zip olabilir

    # 2) Zip içinden XML çıkar
    if not zipfile.is_zipfile(file_path):
        raise ValueError("RDML dosyası ne geçerli XML ne de ZIP gibi görünüyor.")

    with zipfile.ZipFile(file_path, "r") as zf:
        xml_name = next((n for n in zf.namelist() if n.lower().endswith(".xml")), None)
        if not xml_name:
            raise ValueError("RDML zip içinde .xml dosyası bulunamadı.")

        with zf.open(xml_name) as f:
            data = f.read()
            try:
                root = ET.fromstring(data)
            except ET.ParseError as e:
                raise ValueError(f"Zip içindeki XML parse edilemedi: {e}")
            return root
