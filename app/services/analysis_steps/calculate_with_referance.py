# app/services/analysis_steps/calculate_with_referance.py
from __future__ import annotations

import pandas as pd


class CalculateWithReferance:
    def __init__(self, referance_well: str, carrier_range: float, uncertain_range: float):
        self.df: pd.DataFrame | None = None
        self.referance_well = str(referance_well)
        self.carrier_range = float(carrier_range)
        self.uncertain_range = float(uncertain_range)
        self.last_success = True
        self.initial_static_value = None

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CalculateWithReferance.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        self.df = df  # Pipeline kontratı: mümkünse copy etme; pipeline yönetecek
        self.last_success = self._set_reference_value()

        valid_mask = (self.df["Uyarı"].isnull()) | (self.df["Uyarı"] == "Düşük RFU Değeri")
        valid_data = self.df[valid_mask].copy()
        invalid_data = self.df[~valid_mask].copy()

        valid_data = self._finalize_data(valid_data)
        out = pd.concat([valid_data, invalid_data], ignore_index=True)
        return out

    def _set_reference_value(self) -> bool:
        if not self.referance_well or pd.isna(self.referance_well):
            raise ValueError("Referans kuyu boş. Lütfen geçerli bir referans kuyu giriniz.")

        if self.df is None:
            raise ValueError("DataFrame yok.")

        if "Kuyu No" not in self.df.columns or "Δ Ct" not in self.df.columns:
            raise ValueError("'Kuyu No' veya 'Δ Ct' sütunu eksik.")

        if self.referance_well not in set(self.df["Kuyu No"].astype(str).values):
            raise ValueError(f"Referans kuyu '{self.referance_well}' bulunamadı.")

        vals = self.df.loc[self.df["Kuyu No"] == self.referance_well, "Δ Ct"].values
        if len(vals) == 0:
            raise ValueError(f"Referans kuyu '{self.referance_well}' için Δ Ct bulunamadı.")

        self.initial_static_value = vals[0]
        if pd.isna(self.initial_static_value):
            # referans kuyusu var ama ΔCt boş: fatal yapmayıp step başarısız sayalım
            return False
        return True

    def _finalize_data(self, valid_data: pd.DataFrame) -> pd.DataFrame:
        if self.initial_static_value is None or pd.isna(self.initial_static_value):
            # referans başarısızsa valid_data'yı bozmadan döndür
            return valid_data

        valid_data["Δ_Δ Ct"] = valid_data["Δ Ct"] - self.initial_static_value
        valid_data["Standart Oranı"] = 2 ** -valid_data["Δ_Δ Ct"]
        valid_data.loc[valid_data["Standart Oranı"] <= 0.7, "Standart Oranı"] -= 0.00

        carrier_range = self.carrier_range
        uncertain_range = self.uncertain_range

        valid_data["Referans Hasta Sonucu"] = valid_data["Standart Oranı"].apply(
            lambda x: (
                "Sağlıklı"
                if x > uncertain_range
                else (
                    "Belirsiz"
                    if carrier_range < x <= uncertain_range
                    else (
                        "Taşıyıcı"
                        if 0.1 < x <= carrier_range
                        else "Hasta" if x <= 0.1 else "Tekrar"
                    )
                )
            )
        )
        return valid_data
