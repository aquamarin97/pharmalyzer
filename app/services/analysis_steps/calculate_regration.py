# app\services\analysis_steps\calculate_regration.py
# app/services/analysis_steps/calculate_regration.py
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class CalculateRegration:
    def __init__(self):
        self.df: pd.DataFrame | None = None

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CalculateRegration.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        # Pipeline kontratı: df üzerinde in-place oynamak istemiyorsak burada kopyalarız
        self.df = df.copy(deep=False)
        self.calculate_regration()
        print("Regresyon adımı tamamlandı."),
        print("--------------------------")
        return self.df

    def calculate_regration(self) -> None:
        if self.df is None:
            raise ValueError("DataFrame yok.")

        required_columns = ["fam_end_rfu", "hex_end_rfu", "HEX Ct"]
        missing = [c for c in required_columns if c not in self.df.columns]
        if missing:
            raise ValueError(f"Eksik sütun(lar): {', '.join(missing)}")

        filtered_df = self.df.dropna(subset=["fam_end_rfu", "hex_end_rfu", "HEX Ct"])
        if filtered_df.empty:
            raise ValueError("Gerekli sütunlarda işlem yapılacak veri yok.")

        logger.debug("Regresyon için filtrelenmiş satır: %d", len(filtered_df))

        if len(filtered_df) > 50:
            model, clean_df = self.iterative_regression(filtered_df, "fam_end_rfu", "hex_end_rfu")
        else:
            model, clean_df = self.mad_based_regression(filtered_df, "fam_end_rfu", "hex_end_rfu")

        # Varsayılan: riskli
        self.df["Regresyon"] = "Riskli Alan"
        self.df.loc[clean_df.index, "Regresyon"] = "Güvenli Bölge"

        # Uyarı durumlarında regresyon "-"
        if "Uyarı" in self.df.columns:
            self.df.loc[self.df["Uyarı"].isin(["Yetersiz DNA", "Boş Kuyu"]), "Regresyon"] = "-"

    def iterative_regression(self, df: pd.DataFrame, x_col: str, y_col: str, threshold: float = 2.0, max_iter: int = 10):
        filtered_df = df.copy()
        model = LinearRegression()

        for _ in range(max_iter):
            X = filtered_df[x_col].values.reshape(-1, 1)
            y = filtered_df[y_col].values

            model.fit(X, y)
            y_pred = model.predict(X)

            residuals = y - y_pred
            sigma = float(np.std(residuals))

            # (Mevcut yaklaşımı koruyarak) maske
            mask_upper = np.abs(residuals) <= (threshold + 10) + 2.2 * sigma
            mask_lower = np.abs(residuals) >= (threshold) - 2.2 * sigma
            mask = mask_upper & mask_lower

            new_filtered_df = filtered_df[mask]
            if new_filtered_df.shape[0] == filtered_df.shape[0]:
                break
            filtered_df = new_filtered_df

        return model, filtered_df

    def mad_based_regression(self, df: pd.DataFrame, x_col: str, y_col: str, threshold: float = 3.5):
        filtered_df = df.copy()
        if filtered_df.empty:
            return LinearRegression(), filtered_df

        X = filtered_df[x_col].values.reshape(-1, 1)
        y = filtered_df[y_col].values

        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)

        residuals = y - y_pred
        median = float(np.median(residuals))
        abs_deviation = np.abs(residuals - median)
        mad = float(np.median(abs_deviation))

        if mad == 0:
            logger.debug("MAD=0, temizleme yapılmadan dönülüyor.")
            return model, filtered_df

        modified_z_scores = 0.6745 * (residuals - median) / mad
        mask = np.abs(modified_z_scores) <= threshold

        new_filtered_df = filtered_df[mask]
        if new_filtered_df.shape[0] < 3:
            logger.debug("Yeterli güvenli örnek kalmadı (%d). Fallback.", new_filtered_df.shape[0])
            return model, filtered_df

        return model, new_filtered_df
