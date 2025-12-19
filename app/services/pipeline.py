# app\services\pipeline.py
from collections.abc import Iterable
from typing import Callable

import pandas as pd

from app.services.data_store import DataStore

Transform = Callable[[pd.DataFrame], pd.DataFrame]


class Pipeline:
    """
    Transformation pipeline that applies functions to the central DataFrame.
    Each transform must follow the signature: pd.DataFrame -> pd.DataFrame.
    """

    @staticmethod
    def apply(transform_fn: Transform) -> pd.DataFrame:
        df = DataStore.get_df()
        if df is None:
            raise ValueError("DataStore boş. Pipeline çalıştırılamıyor.")

        next_df = transform_fn(df.copy(deep=True))
        if next_df is None:
            raise ValueError("Pipeline adımı DataFrame döndürmedi.")

        DataStore.set_df(next_df)
        return next_df

    @staticmethod
    def run(steps: Iterable[Transform]) -> pd.DataFrame:
        last_df: pd.DataFrame | None = None
        for step in steps:
            last_df = Pipeline.apply(step)
        if last_df is None:
            raise ValueError("Pipeline adımı bulunamadı.")
        return last_df