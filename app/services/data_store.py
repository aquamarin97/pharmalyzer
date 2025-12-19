# app\services\data_store.py
import threading
from typing import Optional

import pandas as pd


class DataStore:
    """
    In-memory, thread-safe DataFrame store used as the single source of truth.
    """

    _lock = threading.RLock()
    _df: Optional[pd.DataFrame] = None

    @classmethod
    def set_df(cls, df: pd.DataFrame) -> None:
        """
        Persist a DataFrame in memory.

        Args:
            df: Data to store.
        """
        if df is None:
            raise ValueError("DataFrame cannot be None.")

        with cls._lock:
            cls._df = df.copy(deep=True)

    @classmethod
    def get_df(cls) -> Optional[pd.DataFrame]:
        """
        Retrieve the stored DataFrame reference.

        Returns:
            The stored DataFrame or None when not set.
        """
        with cls._lock:
            return cls._df

    @classmethod
    def get_df_copy(cls) -> Optional[pd.DataFrame]:
        """
        Retrieve a deep copy of the stored DataFrame.

        Returns:
            A copied DataFrame or None when not set.
        """
        with cls._lock:
            return cls._df.copy(deep=True) if cls._df is not None else None

    @classmethod
    def clear(cls) -> None:
        """Remove the stored DataFrame."""
        with cls._lock:
            cls._df = None

    @classmethod
    def has_df(cls) -> bool:
        """Check if a DataFrame has been stored."""
        with cls._lock:
            return cls._df is not None