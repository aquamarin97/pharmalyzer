# app\utils\pandas_utils.py
import pandas as pd


def ensure_non_empty_df(df: pd.DataFrame, msg: str = "DataFrame boş.") -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError(msg)
    return df
