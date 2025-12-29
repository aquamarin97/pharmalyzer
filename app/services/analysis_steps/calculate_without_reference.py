from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.cluster import KMeans


@dataclass(frozen=True)
class ClusterInfo:
    center: float
    count: int


class CalculateWithoutReference:
    """
    Reference'sız (static) değer optimizasyonu yapar, istatistik oranını hesaplar,
    hasta sınıflandırmasını üretir ve istatistik oranlarını gradyant düzeltmeyle iyileştirir.
    """

    def __init__(self, carrier_range: float, uncertain_range: float, cluster_number: int = 5) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.carrier_range = float(carrier_range)
        self.uncertain_range = float(uncertain_range)
        self.cluster_number = int(cluster_number)

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None:
            raise ValueError("process() Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        self.df = df
        valid_for_stats, _ = self._validate_input_df(df)

        if valid_for_stats.empty:
            return df

        static_value = self.optimize_static_value(valid_for_stats)

        valid_mask = df["Uyarı"] != "Boş Kuyu"
        valid_data = df.loc[valid_mask].copy()
        invalid_data = df.loc[~valid_mask].copy()

        valid_data = self.finalize_data(valid_data, static_value)
        return pd.concat([valid_data, invalid_data], ignore_index=True)

    def finalize_data(self, valid_data: pd.DataFrame, static_value: float) -> pd.DataFrame:
        """Verileri hesaplar, sınıflandırır ve istatistiksel düzeltme yapar."""
        df = self._calculate_statistics(valid_data, static_value)
        df["Yazılım Hasta Sonucu"] = self._classify_patients(df)

        df = self._adjust_statistics(df)
        df["Yazılım Hasta Sonucu"] = self._classify_patients(df)

        return df

    def optimize_static_value(self, valid_data: pd.DataFrame) -> float:
        if valid_data.empty:
            return 2.00

        clusters, clustered_df = self._cluster_delta_ct(valid_data)
        initial_static = self._compute_initial_static_value(clusters, clustered_df)

        optimized = self._optimize_delta_ct(clustered_df, initial_static)
        return float(optimized)

    @staticmethod
    def objective(x: float, df: pd.DataFrame, use_log_mse: bool = True) -> float:
        temp = df.copy()
        temp["Δ_Δ Ct"] = temp["Δ Ct"] - x
        temp["İstatistik Oranı"] = 2 ** -temp["Δ_Δ Ct"]

        if use_log_mse:
            log_ratios = np.log2(temp["İstatistik Oranı"])
            mse = np.mean((log_ratios - 0.0) ** 2)
        else:
            mse = np.mean((temp["İstatistik Oranı"] - 1.0) ** 2)

        return float(mse)

    def penalize_third_center(
        self,
        third_center: float,
        min_center: float,
        min_count: int,
        valid_data: pd.DataFrame,
        alpha: float = 1.0,
        threshold: float = 1.4,
        exp_base: float = 1.1,
    ) -> float:
        ratio = third_center / min_center if min_center else float("inf")
        ct_std = float(np.std(valid_data["Δ Ct"]))
        beta = 1.0 + (ct_std / 2.0)
        exp_penalty_factor = float(exp_base ** min_count)

        if ratio <= threshold:
            return float(third_center)

        penalty = alpha * ((ratio - threshold) ** beta) * min_center * exp_penalty_factor
        new_center = third_center - penalty
        return float(new_center)

    def _validate_input_df(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        required_cols = {"Regresyon", "Uyarı", "Δ Ct"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Eksik kolon(lar): {sorted(missing)}")

        valid_mask = (df["Regresyon"] == "Güvenli Bölge") & (
            df["Uyarı"].isnull() | (df["Uyarı"] == "Düşük RFU Değeri")
        )
        return df.loc[valid_mask].copy(), df.loc[~valid_mask].copy()

    def _cluster_delta_ct(self, valid_data: pd.DataFrame) -> Tuple[list[ClusterInfo], pd.DataFrame]:
        delta_ct_values = valid_data[["Δ Ct"]].to_numpy()

        kmeans = KMeans(n_clusters=self.cluster_number, random_state=42)
        df = valid_data.copy()
        df["Cluster"] = kmeans.fit_predict(delta_ct_values)

        centers = kmeans.cluster_centers_.flatten()
        counts = df["Cluster"].value_counts().sort_index()

        clusters = sorted(
            [ClusterInfo(center=float(c), count=int(counts[i])) for i, c in enumerate(centers)],
            key=lambda x: x.center,
        )

        return clusters, df

    def _compute_initial_static_value(self, clusters: list[ClusterInfo], valid_data: pd.DataFrame) -> float:
        if len(clusters) < 3:
            centers = [c.center for c in clusters]
            fallback = float(np.mean(centers)) if centers else 2.00
            return fallback

        min_c, second_c, third_c = clusters[0], clusters[1], clusters[2]

        third_adjusted = self.penalize_third_center(
            third_center=third_c.center,
            min_center=min_c.center,
            min_count=min_c.count,
            valid_data=valid_data,
        )

        numerator = (
            (min_c.center * min_c.count)
            + (second_c.center * second_c.count)
            + (third_adjusted * third_c.count)
        )
        denominator = (min_c.count + second_c.count + third_c.count) or 1
        weighted_avg = float(numerator / denominator)

        return weighted_avg

    def _optimize_delta_ct(self, valid_data: pd.DataFrame, initial_static_value: float) -> float:
        temp = valid_data.copy()
        temp["Δ_Δ Ct"] = temp["Δ Ct"] - initial_static_value
        temp["İstatistik Oranı"] = (2 ** -temp["Δ_Δ Ct"]).round(6)

        filtered = temp[temp["İstatistik Oranı"].between(0.8, 1.2)]
        if filtered.empty:
            return float(initial_static_value)

        result = minimize(
            lambda arr: self.objective(float(arr[0]), filtered, use_log_mse=True),
            x0=np.array([initial_static_value], dtype=float),
            bounds=[(-4.0, 4.0)],
            method="L-BFGS-B",
        )

        optimized = float(round(float(result.x[0]), 6))
        return optimized

    def _calculate_statistics(self, df: pd.DataFrame, static_value: float) -> pd.DataFrame:
        out = df.copy()
        out["Δ_Δ Ct"] = out["Δ Ct"] - static_value
        out["İstatistik Oranı"] = 2 ** -out["Δ_Δ Ct"]
        return out

    def _classify_patients(self, df: pd.DataFrame) -> pd.Series:
        def classify(val: float) -> str:
            if pd.isna(val):
                return ""
            if val > self.uncertain_range:
                return "Sağlıklı"
            if self.carrier_range < val <= self.uncertain_range:
                return "Belirsiz"
            if 0.1 < val <= self.carrier_range:
                return "Taşıyıcı"
            return "Tekrar"

        return df["İstatistik Oranı"].apply(classify)

    def _adjust_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        healthy_mask = (
            (out["Yazılım Hasta Sonucu"] == "Sağlıklı")
            & (out["Regresyon"] == "Güvenli Bölge")
            & (out["İstatistik Oranı"].between(0.8, 1.2))
        )
        healthy_series = out.loc[healthy_mask, "İstatistik Oranı"]

        carrier_mask = (out["Yazılım Hasta Sonucu"] == "Taşıyıcı") & (out["Regresyon"] == "Güvenli Bölge")
        carrier_series = out.loc[carrier_mask, "İstatistik Oranı"]

        if healthy_series.empty:
            return out

        attraction_strength = 0.5

        def calculate_gradient_value(val: float) -> float:
            if pd.isna(val):
                return val

            if 0.25 <= val <= 0.5:
                target, max_dist = 0.5, 0.25
            elif 0.5 < val < 0.65:
                target, max_dist = 0.5, 0.15
            elif 0.78 <= val <= 1.0:
                target, max_dist = 1.0, 0.22
            elif 1.0 < val <= 1.25:
                target, max_dist = 1.0, 0.25
            elif 1.25 < val <= 1.75:
                target, max_dist = 1.5, 0.25
            else:
                return val

            distance = abs(val - target)
            if max_dist > 0:
                ratio = min(1.0, distance / max_dist)
                weight = ratio ** (1.0 / (attraction_strength + 0.5))
                return val + (target - val) * weight * attraction_strength

            return val

        out["İstatistik Oranı"] = out["İstatistik Oranı"].apply(calculate_gradient_value)
        return out

