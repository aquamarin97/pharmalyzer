# app/services/analysis_steps/calculate_without_referance.py
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


class CalculateWithoutReferance:
    def __init__(self, carrier_range: float, uncertain_range: float):
        self.df: pd.DataFrame | None = None
        self.carrier_range = float(carrier_range)
        self.uncertain_range = float(uncertain_range)

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CalculateWithoutReferance.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        self.df = df  # Pipeline kontratı: mümkünse kopyalama pipeline seviyesinde yönetilir
        valid_mask = (self.df["Uyarı"].isnull()) | (self.df["Uyarı"] == "Düşük RFU Değeri")
        valid_data = self.df[valid_mask].copy()
        invalid_data = self.df[~valid_mask].copy()

        logger.info("İstatistik oranı hesaplanıyor (referanssız). Geçerli satır: %d", len(valid_data))

        new_static_value = self.optimize_static_value(valid_data)
        valid_data = self.finalize_data(valid_data, new_static_value)

        out = pd.concat([valid_data, invalid_data], ignore_index=True)
        return out

    def penalize_third_center(
        self,
        third_center,
        min_center,
        min_count,
        valid_data,
        alpha=1.0,
        threshold=1.4,
        exp_base=1.1,
    ):
        ratio = third_center / min_center if min_center else float("inf")
        ct_values = valid_data["Δ Ct"]
        ct_std = float(np.std(ct_values))

        beta = 1.0 + (ct_std / 2)
        exp_penalty_factor = float(exp_base ** min_count)

        logger.debug(
            "penalty params beta=%.3f std=%.3f ratio=%.3f min_count=%s factor=%.3f",
            beta, ct_std, ratio, min_count, exp_penalty_factor
        )

        if ratio <= threshold:
            return third_center

        penalty = alpha * ((ratio - threshold) ** beta) * min_center * exp_penalty_factor
        return third_center - penalty

    def optimize_static_value(self, valid_data: pd.DataFrame) -> float:
        if valid_data.empty:
            logger.warning("Geçerli veri yok, varsayılan başlangıç değeri kullanılacak.")
            return 2.00

        clusters, clustered_data = self._cluster_ct_values(valid_data)
        initial_static_value = self._compute_initial_static_value(clusters, clustered_data)
        optimized_static_value = self._optimize_delta_ct(clustered_data, initial_static_value)
        return float(optimized_static_value)

    @staticmethod
    def objective(x, valid_data, use_log_mse=True):
        temp_data = valid_data.copy()
        temp_data["Δ_Δ Ct"] = temp_data["Δ Ct"] - x
        temp_data["İstatistik Oranı"] = 2 ** -temp_data["Δ_Δ Ct"]

        if use_log_mse:
            log_ratios = np.log2(temp_data["İstatistik Oranı"])
            mse = np.mean((log_ratios - 0.0) ** 2)
        else:
            mse = np.mean((temp_data["İstatistik Oranı"] - 1.0) ** 2)

        return float(mse)

    def finalize_data(self, valid_data: pd.DataFrame, new_static_value: float) -> pd.DataFrame:
        valid_data = self._calculate_statistics(valid_data, new_static_value)
        valid_data["Yazılım Hasta Sonucu"] = self._classify_patients(valid_data)
        valid_data = self._adjust_statistics(valid_data)
        valid_data["Yazılım Hasta Sonucu"] = self._classify_patients(valid_data)
        return valid_data

    # --- helpers ---

    def _cluster_ct_values(self, valid_data: pd.DataFrame, n_clusters: int = 5):
        delta_ct_values = valid_data[["Δ Ct"]].values
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        valid_data = valid_data.copy()
        valid_data["Cluster"] = kmeans.fit_predict(delta_ct_values)

        centers = kmeans.cluster_centers_.flatten()
        counts = valid_data["Cluster"].value_counts().sort_index()

        sorted_clusters = sorted(zip(centers, counts), key=lambda x: x[0])
        logger.debug("KMeans centers=%s counts=%s", centers.tolist(), counts.to_dict())
        return sorted_clusters, valid_data

    def _compute_initial_static_value(self, clusters, valid_data: pd.DataFrame) -> float:
        (min_center, min_count) = clusters[0]
        (second_center, second_count) = clusters[1]
        (third_center, third_count) = clusters[2]

        third_adjusted = self.penalize_third_center(
            third_center, min_center, int(min_count), valid_data, alpha=1.0, threshold=1.4
        )

        numerator = (min_center * min_count) + (second_center * second_count) + (third_adjusted * third_count)
        denominator = (min_count + second_count + third_count) or 1
        weighted_avg = float(numerator / denominator)

        logger.info("Başlangıç DeltaCt (weighted): %.6f", weighted_avg)
        return weighted_avg

    def _optimize_delta_ct(self, valid_data: pd.DataFrame, initial_static_value: float) -> float:
        temp = valid_data.copy()
        temp["Δ_Δ Ct"] = temp["Δ Ct"] - initial_static_value
        temp["İstatistik Oranı"] = (2 ** -temp["Δ_Δ Ct"]).round(6)

        filtered = temp[(temp["İstatistik Oranı"] >= 0.75) & (temp["İstatistik Oranı"] <= 1.3)]
        if filtered.empty:
            logger.warning("Optimize edilecek veri kalmadı, başlangıç değeri kullanılacak.")
            return float(initial_static_value)

        result = minimize(
            lambda x: self.objective(x, filtered, use_log_mse=True),
            initial_static_value,
            bounds=[(-4, 4)],
            method="L-BFGS-B",
        )
        optimized_value = float(round(result.x[0], 6))
        logger.info("Optimize edilmiş DeltaCt: %.6f", optimized_value)
        return optimized_value

    def _calculate_statistics(self, df: pd.DataFrame, static_value: float) -> pd.DataFrame:
        df = df.copy()
        df["Δ_Δ Ct"] = df["Δ Ct"] - static_value
        df["İstatistik Oranı"] = 2 ** -df["Δ_Δ Ct"]
        df.loc[df["İstatistik Oranı"] <= 0.6999, "İstatistik Oranı"] -= 0.00
        return df

    def _classify_patients(self, df: pd.DataFrame) -> pd.Series:
        carrier = float(self.carrier_range)
        uncertain = float(self.uncertain_range)

        def classify(x: float):
            if pd.isna(x):
                return ""
            if x > uncertain:
                return "Sağlıklı"
            if carrier < x <= uncertain:
                return "Belirsiz"
            if 0.1 < x <= carrier:
                return "Taşıyıcı"
            if x <= 0.1:
                return "Hasta"
            return "Tekrar"

        return df["İstatistik Oranı"].apply(classify)

    def _adjust_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        healthy_avg = df.loc[df["Yazılım Hasta Sonucu"] == "Sağlıklı", "İstatistik Oranı"].mean()
        if pd.isna(healthy_avg):
            return df

        diff = 1.0 - float(healthy_avg)
        logger.debug("Healthy avg=%.6f diff=%.6f", float(healthy_avg), diff)

        if diff > 0:
            df.loc[(df["İstatistik Oranı"] > 0.75) & (df["İstatistik Oranı"] < 1), "İstatistik Oranı"] += diff
        elif diff < 0:
            df.loc[df["İstatistik Oranı"] < 0.7, "İstatistik Oranı"] += diff  # diff negatif

        return df
