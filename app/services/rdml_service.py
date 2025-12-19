# app\services\rdml_service.py
import pandas as pd
from app.utils.rdml.rdml_reader import read_rdml_root
from app.utils.rdml.rdml_parser import merge_fam_hex_rows


DEFAULT_HEADERS = [
    "React ID",
    "Barkot No",
    "Hasta Adı",
    "FAM Ct",
    "HEX Ct",
    "FAM koordinat list",
    "HEX koordinat list",
]


class RDMLService:
    @staticmethod
    def rdml_to_dataframe(file_path: str) -> pd.DataFrame:
        root = read_rdml_root(file_path)
        rows = merge_fam_hex_rows(root)
        df = pd.DataFrame(rows)

        # kolonları stabilize et (eksikse ekle)
        for h in DEFAULT_HEADERS:
            if h not in df.columns:
                df[h] = ""

        df = df[DEFAULT_HEADERS]  # sıralama
        if df.empty:
            raise ValueError("RDML içinden veri üretilemedi (DataFrame boş).")
        return df
