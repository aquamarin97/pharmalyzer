# app\services\pcr_data_service.py
# app/services/pcr_data_service.py
from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from app.services.data_store import DataStore

logger = logging.getLogger(__name__)

Coord = Tuple[int, float]
from app.utils import well_mapping

@dataclass(frozen=True)
class PCRCoords:
    fam: NDArray[np.float_]
    hex: NDArray[np.float_]


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

    _coords_cache: Dict[int, PCRCoords] = {}
    _cached_df_id: int | None = None
    _cache_token: int = 0

    @staticmethod
    def get_coords(patient_no: Any) -> PCRCoords:
        df = DataStore.get_df()
        if df is None or df.empty:
            raise ValueError("DataStore boş. Veri yüklenmedi.")

        PCRDataService._validate_columns(df)
        PCRDataService._ensure_cache(df)

        pn = PCRDataService._normalize_patient_no(patient_no)
        cached = PCRDataService._coords_cache.get(pn)
        if cached is None:
            raise ValueError(f"Hasta No '{pn}' için bir kayıt bulunamadı.")
        return cached

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
        PCRDataService._ensure_cache(df)

        coords_map: Dict[str, PCRCoords] = {}
        for well_id in valid_wells:
            pn = well_mapping.well_id_to_patient_no(well_id)
            cached = PCRDataService._coords_cache.get(pn)
            if cached is not None:
                coords_map[well_id] = cached

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
    @lru_cache(maxsize=4096)
    def _parse_coords_from_str(raw: str, label: str) -> NDArray[np.float_]:
        parsed = PCRDataService._literal_eval_cached(raw)
        return PCRDataService._coords_from_iterable(parsed, label)

    @staticmethod
    def _coords_from_iterable(raw: Any, label: str) -> NDArray[np.float_]:
        if raw is None:
            return np.empty((0, 2), dtype=float)

        if not isinstance(raw, (list, tuple)):
            raise ValueError(f"{label} koordinat listesi list formatında değil: {type(raw)}")

        out: List[Coord] = []
        for item in raw:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            try:
                cyc = int(item[0])
                fluor = float(item[1])
                out.append((cyc, fluor))
            except (TypeError, ValueError):
                continue

        arr = np.asarray(out, dtype=float)
        arr.setflags(write=False)
        return arr

    @staticmethod
    def _parse_coords_cached(raw: Any, label: str) -> NDArray[np.float_]:
        if isinstance(raw, str):
            try:
                return PCRDataService._parse_coords_from_str(raw, label)
            except Exception as e:
                raise ValueError(f"{label} koordinat listesi parse edilemedi: {e}")

        return PCRDataService._coords_from_iterable(raw, label)

    @staticmethod
    def _ensure_cache(df: pd.DataFrame) -> None:
        df_id = id(df)
        if PCRDataService._cached_df_id == df_id and PCRDataService._coords_cache:
            return

        PCRDataService._coords_cache.clear()
        PCRDataService._cached_df_id = df_id
        PCRDataService._cache_token += 1
        PCRDataService._literal_eval_cached.cache_clear()

        for _, row in df.iterrows():
            try:
                pn = PCRDataService._normalize_patient_no(row[PCRDataService.HASTA_NO_COL])
            except ValueError:
                continue

            fam_raw = row[PCRDataService.FAM_COL]
            hex_raw = row[PCRDataService.HEX_COL]
            fam_coords = PCRDataService._parse_coords_cached(fam_raw, label="FAM")
            hex_coords = PCRDataService._parse_coords_cached(hex_raw, label="HEX")
            PCRDataService._coords_cache[pn] = PCRCoords(fam=fam_coords, hex=hex_coords)

    @staticmethod
    def get_cache_token() -> int:
        df = DataStore.get_df()
        if df is None or df.empty:
            return PCRDataService._cache_token

        PCRDataService._validate_columns(df)
        PCRDataService._ensure_cache(df)
        return PCRDataService._cache_token

    # DataStore güncellendiğinde cache temizlemek istersen:
    @staticmethod
    def clear_cache() -> None:
        PCRDataService._literal_eval_cached.cache_clear()
        PCRDataService._coords_cache.clear()
        PCRDataService._cached_df_id = None
        PCRDataService._cache_token += 1
        logger.debug("PCRDataService literal_eval cache cleared")