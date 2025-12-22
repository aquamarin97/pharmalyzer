# app\services\pipeline.py
from collections.abc import Iterable
from typing import Callable
import traceback

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
        print("pipeline işlemi başlatıldı")
        last_df: pd.DataFrame | None = None

        for step in steps:
            step_name = getattr(step, "__qualname__", repr(step))
            print(f"[Pipeline] step 시작: {step_name}")

            try:
                last_df = Pipeline.apply(step)
            except Exception:
                print(f"[Pipeline] step hata verdi: {step_name}")
                traceback.print_exc()
                raise

        if last_df is None:
            raise ValueError("Pipeline adımı bulunamadı.")
        return last_df