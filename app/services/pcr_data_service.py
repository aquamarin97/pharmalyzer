# app\services\pcr_data_service.py

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

import pandas as pd

from app.services.data_store import DataStore


Coord = Tuple[int, float]


@dataclass(frozen=True)
class PCRCoords:
    fam: List[Coord]
    hex: List[Coord]


class PCRDataService:
    """
    Grafik için gerekli koordinat verilerini DataStore'dan okur.
    UI/Qt bağımlılığı yoktur.
    """

    HASTA_NO_COL = "Hasta No"
    FAM_COL = "FAM koordinat list"
    HEX_COL = "HEX koordinat list"

    @staticmethod
    def get_coords(patient_no: Any) -> PCRCoords:
        """
        Hasta No -> (FAM coords, HEX coords)

        Returns:
            PCRCoords(fam=[(cyc, fluor), ...], hex=[(cyc, fluor), ...])
        """
        df = DataStore.get_df_copy()
        if df is None or df.empty:
            raise ValueError("DataStore boş. Veri yüklenmedi.")

        PCRDataService._validate_columns(df)

        pn = PCRDataService._normalize_patient_no(patient_no)

        row = PCRDataService._find_row_by_patient_no(df, pn)
        fam_coords = PCRDataService._parse_coords(row.iloc[0][PCRDataService.FAM_COL], label="FAM")
        hex_coords = PCRDataService._parse_coords(row.iloc[0][PCRDataService.HEX_COL], label="HEX")

        return PCRCoords(fam=fam_coords, hex=hex_coords)

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        missing = [c for c in (PCRDataService.HASTA_NO_COL, PCRDataService.FAM_COL, PCRDataService.HEX_COL) if c not in df.columns]
        if missing:
            raise ValueError(f"DataFrame içinde eksik kolon(lar) var: {missing}")

    @staticmethod
    def _normalize_patient_no(patient_no: Any) -> int:
        try:
            pn = int(float(patient_no))
        except (TypeError, ValueError):
            raise ValueError(f"Geçersiz Hasta No: {patient_no}")

        # İstersen sınır koy (plate 1..96 varsayımı)
        if pn < 1 or pn > 96:
            # sınırı esnetmek istersen bu check'i kaldırabilirsin
            raise ValueError(f"Hasta No aralık dışı: {pn} (beklenen 1..96)")

        return pn

    @staticmethod
    def _find_row_by_patient_no(df: pd.DataFrame, pn: int) -> pd.DataFrame:
        hasta_no_series = pd.to_numeric(df[PCRDataService.HASTA_NO_COL], errors="coerce").astype("Int64")
        row = df[hasta_no_series == pn]
        if row.empty:
            raise ValueError(f"Hasta No '{pn}' için bir kayıt bulunamadı.")
        return row

    @staticmethod
    def _parse_coords(raw: Any, label: str) -> List[Coord]:
        # raw string ise parse et, list ise olduğu gibi al
        try:
            coords = ast.literal_eval(raw) if isinstance(raw, str) else raw
        except Exception as e:
            raise ValueError(f"{label} koordinat listesi parse edilemedi: {e}")

        if coords is None:
            return []

        if not isinstance(coords, list):
            raise ValueError(f"{label} koordinat listesi list formatında değil: {type(coords)}")

        # normalize + validate: [(int, float), ...]
        out: List[Coord] = []
        for item in coords:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                # örn: [(cyc, fluor), ...] bekleniyor
                continue
            try:
                cyc = int(item[0])
                fluor = float(item[1])
                out.append((cyc, fluor))
            except (TypeError, ValueError):
                continue

        return out
