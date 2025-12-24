# app/services/pipeline.py
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable
from typing import Callable, Optional

import pandas as pd

from app.services.data_store import DataStore

# Tip tanımlamaları (Type Hinting)
Transform = Callable[[pd.DataFrame], pd.DataFrame]
ProgressCb = Callable[[int, str], None]
IsCancelled = Callable[[], bool]

class CancelledError(RuntimeError):
    """Pipeline kullanıcı tarafından iptal edildiğinde fırlatılan özel hata."""
    pass

@dataclass(frozen=True)
class Step:
    """Pipeline içindeki her bir analiz adımını temsil eder."""
    name: str
    fn: Transform

class Pipeline:
    """
    DataFrame üzerinde sıralı işlemler yapan üretim bandı yapısı.
    Her adım bir önceki adımın çıktısını girdi olarak alır.
    """
    
    @staticmethod
    def apply(step: Step, copy_input: bool = False) -> pd.DataFrame:
        """DataStore'daki mevcut veriyi alır ve adımı uygular."""
        df = DataStore.get_df_copy() if copy_input else DataStore.get_df()
        
        # Fonksiyonu çalıştır ve sonucu al
        result_df = step.fn(df)
        
        # Sonucu DataStore'a geri yaz
        DataStore.set_df(result_df)
        return result_df

    @staticmethod
    def run(
        steps: Iterable[Step],
        *,
        progress_cb: Optional[ProgressCb] = None,
        is_cancelled: Optional[IsCancelled] = None,
        copy_input_each_step: bool = False,
    ) -> pd.DataFrame:
        """
        Tüm adımları sırayla çalıştırır, ilerlemeyi raporlar ve iptalleri denetler.
        """
        steps_list = list(steps)
        if not steps_list:
            raise ValueError("Pipeline adımı bulunamadı.")

        total = len(steps_list)

        def report(i: int, msg: str) -> None:
            """GUI ilerleme çubuğunu ve mesajını günceller."""
            if progress_cb:
                # 0 ile 100 arasında kalmasını garanti altına al (Clamping)
                percent = int((max(0, min(i, total)) / total) * 100)
                progress_cb(percent, msg)

        last_df: Optional[pd.DataFrame] = None

        for idx, step in enumerate(steps_list):
            # İptal kontrolü
            if is_cancelled and is_cancelled():
                report(idx, "İptal edildi.")
                raise CancelledError("Pipeline iptal edildi.")

            # Adım başlıyor raporu
            report(idx, f"Başlıyor: {step.name}")
            
            # Adımı icra et
            last_df = Pipeline.apply(step, copy_input=copy_input_each_step)
            
            # Adım bitti raporu
            report(idx + 1, f"Bitti: {step.name}")

        report(total, "Pipeline tamamlandı.")
        return last_df