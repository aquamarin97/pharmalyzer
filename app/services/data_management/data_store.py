# app\services\data_management\data_store.py
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional, Dict, Iterable

import pandas as pd


@dataclass(frozen=True)
class DataIndexes:
    # Hasta No -> Qt row index (0..n-1)
    patient_to_row: Dict[int, int]


class DataStore:
    _lock = threading.RLock()
    _df: Optional[pd.DataFrame] = None
    _indexes: Optional[DataIndexes] = None

    # EditableTableModel.PATIENT_NO_COL ile aynı:
    _patient_no_column: str = "Hasta No"

    @classmethod
    def configure_patient_no_column(cls, column_name: str) -> None:
        if not column_name or not isinstance(column_name, str):
            raise ValueError("column_name must be a non-empty string")
        with cls._lock:
            cls._patient_no_column = column_name

    @classmethod
    def set_df(cls, df: pd.DataFrame, *, copy: bool = False, build_indexes: bool = True) -> None:
        if df is None:
            raise ValueError("DataFrame cannot be None.")
        with cls._lock:
            cls._df = df.copy(deep=True) if copy else df
            cls._indexes = None
            if build_indexes:
                cls._indexes = cls._build_indexes_locked(cls._df)

    @classmethod
    def get_df_view(cls) -> Optional[pd.DataFrame]:
        """Copy yok. UI thread için en hızlı yol."""
        with cls._lock:
            return cls._df

    @classmethod
    def get_df_shallow(cls) -> Optional[pd.DataFrame]:
        """Deep copy yerine shallow copy."""
        with cls._lock:
            return cls._df.copy(deep=False) if cls._df is not None else None

    @classmethod
    def get_df_copy(cls) -> Optional[pd.DataFrame]:
        """Legacy deep copy."""
        with cls._lock:
            return cls._df.copy(deep=True) if cls._df is not None else None

    @classmethod
    def get_indexes(cls) -> Optional[DataIndexes]:
        with cls._lock:
            return cls._indexes

    @classmethod
    def has_df(cls) -> bool:
        with cls._lock:
            return cls._df is not None

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._df = None
            cls._indexes = None

    @classmethod
    def find_rows_by_patient_nos(cls, patient_nos: Iterable[int]) -> list[int]:
        with cls._lock:
            idx = cls._indexes
            if idx is None:
                # index yoksa üretmiyoruz (UI hot-path’te pahalı iş istemiyoruz)
                return []
            out: list[int] = []
            for pn in patient_nos:
                r = idx.patient_to_row.get(int(pn))
                if r is not None:
                    out.append(r)
            return out

    # -------------------- internal --------------------
    @classmethod
    def _build_indexes_locked(cls, df: pd.DataFrame) -> DataIndexes:
        col = cls._patient_no_column
        if col not in df.columns:
            return DataIndexes(patient_to_row={})

        s = pd.to_numeric(df[col], errors="coerce")
        arr = s.to_numpy()

        mapping: Dict[int, int] = {}
        for row_i, val in enumerate(arr):
            if pd.isna(val):
                continue
            pn = int(val)
            mapping.setdefault(pn, row_i)

        return DataIndexes(patient_to_row=mapping)
