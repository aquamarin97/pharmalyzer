# app\willbedeleted\managers\csv_manager.py
import threading

import pandas as pd
import warnings

from app.willbedeleted.utils.file_utils.csv_utils import UtilsCSV

from app.services.data_store import DataStore
from app.services.rdml_service import DEFAULT_HEADERS
class CSVManager:
    """
    Legacy compatibility layer that proxies all access to the in-memory DataStore.
    """
    _lock = threading.RLock()


    @staticmethod
    def set_csv_file_path(file_path: str):
        """Deprecated: path-based storage is no longer used."""
        warnings.warn("CSV file paths are deprecated; data is kept in-memory.", DeprecationWarning)

    def get_csv_file_path() -> str | None:
        """Deprecated: path-based storage is no longer used."""
        warnings.warn("CSV file paths are deprecated; data is kept in-memory.", DeprecationWarning)
        return None

    @staticmethod
    def clear_csv_file_path():
        """Deprecated: path-based storage is no longer used."""
        warnings.warn("CSV file paths are deprecated; data is kept in-memory.", DeprecationWarning)

    @staticmethod
    def set_csv_df(df: pd.DataFrame):
        """Store DataFrame in the shared DataStore."""
        DataStore.set_df(df)


    @staticmethod
    def get_csv_df() -> pd.DataFrame:
        """Retrieve the stored DataFrame."""
        df = DataStore.get_df()
        if df is None:
            raise ValueError("Merkezi DataFrame ayarlanmamış.")
        return df
    
    @staticmethod
    def clear_csv_df():
        """Clear the stored DataFrame."""
        DataStore.clear()

    @staticmethod
    def update_csv_df() -> pd.DataFrame:
        """
        Stabilize columns without touching disk.
        Ensures DEFAULT_HEADERS exist and returns the refreshed DataFrame.
        """
        with CSVManager._lock:
            df = DataStore.get_df()
            if df is None:
                raise ValueError("Merkezi DataFrame ayarlanmamış.") 
            for header in DEFAULT_HEADERS:
                if header not in df.columns:
                    df[header] = ""
            DataStore.set_df(df)
            return df
