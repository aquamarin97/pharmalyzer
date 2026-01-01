# app/services/data_management/data_store.py
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional, Dict, Iterable, Any

import pandas as pd


@dataclass(frozen=True)
class DataIndexes:
    """
    UI hot-path index'leri:
    - patient_no -> df row index
    """
    patient_to_row: Dict[int, int]


class DataStore:
    """
    Release-grade DataStore:
    - DF'yi tek yerde saklar (copy yapmadan).
    - UI için index/cache üretir.
    - get_df_copy yerine get_df_view / get_df_shallow tercih edilir.
    """
    _lock = threading.RLock()
    _df: Optional[pd.DataFrame] = None
    _indexes: Optional[DataIndexes] = None

    # Bu kolon adı proje içinde standart olmalı.
    # Eğer sende farklıysa, tek yerden değiştir.
    _patient_no_column: str = "patient_no"

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
        """
        Copy yapmadan df döndürür. UI thread’de pahalı kopyalardan kaçınmak için bunu kullanın.
        Not: Mutasyon yapılmamalı; read-only gibi davranın.
        """
        with cls._lock:
            return cls._df

    @classmethod
    def get_df_shallow(cls) -> Optional[pd.DataFrame]:
        """
        Deep copy yerine shallow copy: kolon objelerini paylaşır.
        Bazı senaryolarda güvenli ara çözüm.
        """
        with cls._lock:
            return cls._df.copy(deep=False) if cls._df is not None else None

    @classmethod
    def get_df_copy(cls) -> Optional[pd.DataFrame]:
        """
        Eski API uyumluluğu için bırakıldı.
        Release-grade performans için mümkünse kullanmayın.
        """
        with cls._lock:
            return cls._df.copy(deep=True) if cls._df is not None else None

    @classmethod
    def get_indexes(cls) -> Optional[DataIndexes]:
        with cls._lock:
            return cls._indexes

    @classmethod
    def ensure_indexes(cls) -> Optional[DataIndexes]:
        """
        DF varsa index yoksa üretir.
        """
        with cls._lock:
            if cls._df is None:
                return None
            if cls._indexes is None:
                cls._indexes = cls._build_indexes_locked(cls._df)
            return cls._indexes

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._df = None
            cls._indexes = None

    @classmethod
    def has_df(cls) -> bool:
        with cls._lock:
            return cls._df is not None

    # -------------------- Internal --------------------
    @classmethod
    def _build_indexes_locked(cls, df: pd.DataFrame) -> DataIndexes:
        """
        patient_no -> row mapping üretir.
        Bu mapping selection apply’de O(N) satır taramayı bitirir.

        Beklenti: df içinde patient_no kolonu var.
        Eğer modelde başka isim kullanıyorsanız configure_patient_no_column ile ayarlayın.
        """
        col = cls._patient_no_column
        if col not in df.columns:
            # Kolon adı yoksa indeks üretmiyoruz; yine de sistem çalışır ama hız kazanımı olmaz.
            return DataIndexes(patient_to_row={})

        # patient_no kolonu numeric değilse bile hızlı normalize edelim
        s = pd.to_numeric(df[col], errors="coerce")
        patient_to_row: Dict[int, int] = {}

        # enumerate ile df index bağımsız row idx alıyoruz (Qt row = 0..n-1)
        # NaN olanları at
        for row_i, val in enumerate(s.to_numpy()):
            if pd.isna(val):
                continue
            pn = int(val)
            # duplicate varsa ilkini tutuyoruz; istersen sonuncuyu aldırabilirsin.
            patient_to_row.setdefault(pn, row_i)

        return DataIndexes(patient_to_row=patient_to_row)

    @classmethod
    def find_rows_by_patient_nos(cls, patient_nos: Iterable[int]) -> list[int]:
        """
        Hot-path: patient listesi -> row listesi (O(k)).
        """
        idx = cls.ensure_indexes()
        if idx is None:
            return []
        out: list[int] = []
        for pn in patient_nos:
            r = idx.patient_to_row.get(int(pn))
            if r is not None:
                out.append(r)
        return out
