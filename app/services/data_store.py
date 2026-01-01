# # app\services\data_store.py
# import threading
# from typing import Optional
# import pandas as pd


# class DataStore:
#     _lock = threading.RLock()
#     _df: Optional[pd.DataFrame] = None

#     @classmethod
#     def set_df(cls, df: pd.DataFrame, *, copy: bool = False) -> None:
#         if df is None:
#             raise ValueError("DataFrame cannot be None.")
#         with cls._lock:
#             cls._df = df.copy(deep=True) if copy else df

#     @classmethod
#     def get_df(cls) -> Optional[pd.DataFrame]:
#         with cls._lock:
#             return cls._df

#     @classmethod
#     def get_df_copy(cls) -> Optional[pd.DataFrame]:
#         with cls._lock:
#             return cls._df.copy(deep=True) if cls._df is not None else None

#     @classmethod
#     def clear(cls) -> None:
#         with cls._lock:
#             cls._df = None

#     @classmethod
#     def has_df(cls) -> bool:
#         with cls._lock:
#             return cls._df is not None
