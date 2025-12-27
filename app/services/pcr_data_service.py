# app\services\pcr_data_service.py
# app/services/pcr_data_service.py
from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Tuple
import pandas as pd

from app.services.data_store import DataStore

logger = logging.getLogger(__name__)

Coord = Tuple[int, float]
from app.utils import well_mapping

@dataclass(frozen=True)
class PCRCoords:
    fam: List[Coord]
    hex: List[Coord]


class PCRDataService:
    """
    Grafik için gerekli koordinat verilerini DataStore'dan okur.
    UI/Qt bağımlılığı yoktur.

    Performans:
    - get_df_copy() yerine get_df() kullanır (kopya yok)
    - literal_eval sonuçlarını cache'ler
    """

    HASTA_NO_COL = "Hasta No"
    FAM_COL = "FAM koordinat list"
    HEX_COL = "HEX koordinat list"

    @staticmethod
    def get_coords(patient_no: Any) -> PCRCoords:
        df = DataStore.get_df()
        if df is None or df.empty:
            raise ValueError("DataStore boş. Veri yüklenmedi.")

        PCRDataService._validate_columns(df)

        pn = PCRDataService._normalize_patient_no(patient_no)
        row = PCRDataService._find_row_by_patient_no(df, pn)

        fam_raw = row.iloc[0][PCRDataService.FAM_COL]
        hex_raw = row.iloc[0][PCRDataService.HEX_COL]

        fam_coords = PCRDataService._parse_coords_cached(fam_raw, label="FAM")
        hex_coords = PCRDataService._parse_coords_cached(hex_raw, label="HEX")
        return PCRCoords(fam=fam_coords, hex=hex_coords)

    @staticmethod
    def get_coords_for_wells(wells: Iterable[str]) -> Dict[str, PCRCoords]:
        """Birden fazla kuyu için koordinatları tek seferde getirir."""
        valid_wells = [w.strip().upper() for w in wells or [] if well_mapping.is_valid_well_id(w)]
        if not valid_wells:
            return {}

        df = DataStore.get_df()
        if df is None or df.empty:
            raise ValueError("DataStore boş. Veri yüklenmedi.")

        PCRDataService._validate_columns(df)

        target_patients = {well_mapping.well_id_to_patient_no(w) for w in valid_wells}
        hasta_no_series = pd.to_numeric(df[PCRDataService.HASTA_NO_COL], errors="coerce").astype("Int64")
        filtered = df[hasta_no_series.isin(target_patients)].copy()

        coords_map: Dict[str, PCRCoords] = {}
        for _, row in filtered.iterrows():
            pn = PCRDataService._normalize_patient_no(row[PCRDataService.HASTA_NO_COL])
            well_id = well_mapping.patient_no_to_well_id(pn)
            fam_raw = row[PCRDataService.FAM_COL]
            hex_raw = row[PCRDataService.HEX_COL]

            fam_coords = PCRDataService._parse_coords_cached(fam_raw, label="FAM")
            hex_coords = PCRDataService._parse_coords_cached(hex_raw, label="HEX")
            coords_map[well_id] = PCRCoords(fam=fam_coords, hex=hex_coords)

        return coords_map

    @staticmethod
    def _validate_columns(df: pd.DataFrame) -> None:
        missing = [
            c
            for c in (PCRDataService.HASTA_NO_COL, PCRDataService.FAM_COL, PCRDataService.HEX_COL)
            if c not in df.columns
        ]
        if missing:
            raise ValueError(f"DataFrame içinde eksik kolon(lar) var: {missing}")

    @staticmethod
    def _normalize_patient_no(patient_no: Any) -> int:
        try:
            pn = int(float(patient_no))
        except (TypeError, ValueError):
            raise ValueError(f"Geçersiz Hasta No: {patient_no}")

        if pn < 1 or pn > 96:
            raise ValueError(f"Hasta No aralık dışı: {pn} (beklenen 1..96)")

        return pn

    @staticmethod
    def _find_row_by_patient_no(df: pd.DataFrame, pn: int) -> pd.DataFrame:
        # Not: Bu conversion her çağrıda yapılır; eğer çok büyük DF olursa
        # "Hasta No" kolonunu import aşamasında Int'a normalize etmek daha iyi.
        hasta_no_series = pd.to_numeric(df[PCRDataService.HASTA_NO_COL], errors="coerce").astype("Int64")
        row = df[hasta_no_series == pn]
        if row.empty:
            raise ValueError(f"Hasta No '{pn}' için bir kayıt bulunamadı.")
        return row

    @staticmethod
    @lru_cache(maxsize=4096)
    def _literal_eval_cached(raw: str) -> Any:
        # raw string için cache'li literal_eval
        return ast.literal_eval(raw)

    @staticmethod
    def _parse_coords_cached(raw: Any, label: str) -> List[Coord]:
        # raw string ise parse et (cache'li), list ise olduğu gibi al
        try:
            coords = PCRDataService._literal_eval_cached(raw) if isinstance(raw, str) else raw
        except Exception as e:
            raise ValueError(f"{label} koordinat listesi parse edilemedi: {e}")

        if coords is None:
            return []

        if not isinstance(coords, list):
            raise ValueError(f"{label} koordinat listesi list formatında değil: {type(coords)}")

        out: List[Coord] = []
        for item in coords:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            try:
                cyc = int(item[0])
                fluor = float(item[1])
                out.append((cyc, fluor))
            except (TypeError, ValueError):
                continue

        return out

    # DataStore güncellendiğinde cache temizlemek istersen:
    @staticmethod
    def clear_cache() -> None:
        PCRDataService._literal_eval_cached.cache_clear()
        logger.debug("PCRDataService literal_eval cache cleared")
