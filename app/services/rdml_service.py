# app/services/rdml_service.py
from __future__ import annotations

import logging
import os
from typing import Any

import pandas as pd

from app.utils.rdml.rdml_reader import read_rdml_root
from app.utils.rdml.rdml_parser import merge_fam_hex_rows

logger = logging.getLogger(__name__)


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
    """
    RDML -> DataFrame dönüşüm boundary servisi.
    UI bağımlılığı yoktur.
    """

    @staticmethod
    def rdml_to_dataframe(file_path: str) -> pd.DataFrame:
        RDMLService._validate_path(file_path)

        root = read_rdml_root(file_path)
        rows = merge_fam_hex_rows(root)

        if rows is None:
            raise ValueError("RDML parse sonucu boş döndü (rows=None).")

        df = pd.DataFrame(rows)

        # Kolonları stabilize et (eksikse ekle) - tip dostu defaultlar
        RDMLService._ensure_columns(df)

        # Sıralama sabit
        df = df[DEFAULT_HEADERS]

        if df.empty:
            raise ValueError("RDML içinden veri üretilemedi (DataFrame boş).")

        # Hafif normalize (agresif değil)
        df = RDMLService._light_normalize(df)

        logger.info("RDML okundu: %s (rows=%d)", os.path.basename(file_path), len(df))
        return df

    @staticmethod
    def _validate_path(file_path: str) -> None:
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("RDML dosya yolu geçersiz (boş).")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"RDML dosyası bulunamadı: {file_path}")

        # Uzantı kontrolü: strict değil ama uyarı iyi
        if not file_path.lower().endswith(".rdml"):
            logger.warning("Dosya uzantısı .rdml değil: %s", file_path)

    @staticmethod
    def _ensure_columns(df: pd.DataFrame) -> None:
        # Text columns
        for col in ("Barkot No", "Hasta Adı"):
            if col not in df.columns:
                df[col] = ""

        # Numeric-ish Ct columns: NA daha sağlıklı
        for col in ("FAM Ct", "HEX Ct"):
            if col not in df.columns:
                df[col] = pd.NA

        # React ID numeric olmalı: NA ile başla
        if "React ID" not in df.columns:
            df["React ID"] = pd.NA

        # Coord list columns: string "[]" downstream için daha stabil (CSVProcessor literal_eval yapıyor)
        for col in ("FAM koordinat list", "HEX koordinat list"):
            if col not in df.columns:
                df[col] = "[]"

        # Eğer ileride yeni kolonlar gelirse df içinde kalabilir ama biz sadece DEFAULT_HEADERS basıyoruz.

    @staticmethod
    def _light_normalize(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy(deep=False)

        # React ID: numeric'e dönüştür (bozamıyorsa NA)
        out["React ID"] = pd.to_numeric(out["React ID"], errors="coerce")

        # Ct: numeric'e dönüştür (bozamıyorsa NA)
        out["FAM Ct"] = pd.to_numeric(out["FAM Ct"], errors="coerce")
        out["HEX Ct"] = pd.to_numeric(out["HEX Ct"], errors="coerce")

        # Coord list: None/NA ise "[]"
        for c in ("FAM koordinat list", "HEX koordinat list"):
            out[c] = out[c].fillna("[]").astype(str)

        # Text: None/NA -> ""
        for c in ("Barkot No", "Hasta Adı"):
            out[c] = out[c].fillna("").astype(str)

        return out
