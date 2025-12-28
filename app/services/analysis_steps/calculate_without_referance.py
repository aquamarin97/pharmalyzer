# app\services\analysis_steps\calculate_without_referance.py
# app/services/analysis_steps/calculate_without_referance.py
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.cluster import KMeans


class CalculateWithoutReferance:
    def __init__(self, carrier_range: float, uncertain_range: float):
        self.df: pd.DataFrame | None = None
        self.carrier_range = float(carrier_range)
        self.uncertain_range = float(uncertain_range)
        self.cluster_number = 7

# --- 2. Core Analysis (Process) ---
# Ana iş akışını yöneten process fonksiyonu.

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        # Girdi kontrolü ve ayrıştırma
        valid_data, invalid_data = self._validate_input_df(df)
        self.df = df # Referans tutma

        print(f"İstatistik oranı hesaplanıyor. Geçerli satır: {len(valid_data)}")

        if not valid_data.empty:
            new_static_value = self.optimize_static_value(valid_data)
            valid_data = self.finalize_data(valid_data, new_static_value)
        else:
            print("Uyarı: Analiz edilecek geçerli veri bulunamadı!")

        # Verileri birleştir
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
        print("  > penalty params")
        params = {
                    "beta": beta,
                    "std": ct_std,
                    "ratio": ratio,
                    "min_count": min_count,
                    "factor": exp_penalty_factor
                }
        for name, value in params.items():
                    print(f"     > {name:<10} = {value}")

        if ratio <= threshold:
            return third_center

        penalty = alpha * ((ratio - threshold) ** beta) * min_center * exp_penalty_factor
        return third_center - penalty

    # ############################################################
    # --- SECTION 3: OPTIMIZATION & CLUSTERING ---
    # ############################################################

    def optimize_static_value(self, valid_data: pd.DataFrame) -> float:
        """
        K-Means ve optimizasyon döngülerini kullanarak ideal Delta Ct referansını hesaplar.
        """
        # 1. Kenar Durum Kontrolü
        if valid_data.empty:
            print(" [!] Uyarı: Geçerli veri yok, varsayılan değer (2.00) kullanılıyor.")
            return 2.00

        # 2. Kümeleme ve Başlangıç Tahmini
        # clusters: [(center, count), ...], clustered_data: DataFrame with 'Cluster' column
        clusters, clustered_data = self._cluster_ct_values(valid_data)
        
        initial_static_value = self._compute_initial_static_value(clusters, clustered_data)
        
        # 3. İnce Ayar (Optimization)
        optimized_static_value = self._optimize_delta_ct(clustered_data, initial_static_value)
        optimized_static_value = float(optimized_static_value)

        # 4. Raporlama
        self._print_optimization_summary(optimized_static_value, valid_data["Δ Ct"])

        return optimized_static_value

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


    def _cluster_ct_values(self, valid_data: pd.DataFrame, n_clusters: int = 3):
            n_clusters= self.cluster_number

            delta_ct_values = valid_data[["Δ Ct"]].values
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            valid_data = valid_data.copy()
            valid_data["Cluster"] = kmeans.fit_predict(delta_ct_values)

            centers = kmeans.cluster_centers_.flatten()
            counts = valid_data["Cluster"].value_counts().sort_index()

            sorted_clusters = sorted(zip(centers, counts), key=lambda x: x[0])
            
            # Düzenlenmiş Print Kısmı
            print(f"\n  > [K-Means] {n_clusters} küme oluşturuldu:")
            for center, count in sorted_clusters:
                print(f"     > Merkez: {center:6.2f} | Sayı: {count}")
            print("")
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

        print("\n  > Başlangıç DeltaCt (weighted): ", weighted_avg)

        return weighted_avg

    def _optimize_delta_ct(self, valid_data: pd.DataFrame, initial_static_value: float) -> float:
        temp = valid_data.copy()
        temp["Δ_Δ Ct"] = temp["Δ Ct"] - initial_static_value
        temp["İstatistik Oranı"] = (2 ** -temp["Δ_Δ Ct"]).round(6)

        filtered = temp[(temp["İstatistik Oranı"] >= 0.75) & (temp["İstatistik Oranı"] <= 1.3)]
        if filtered.empty:
            print("Optimize edilecek veri kalmadı, başlangıç değeri kullanılacak.")
            return float(initial_static_value)

        result = minimize(
            lambda x: self.objective(x, filtered, use_log_mse=True),
            initial_static_value,
            bounds=[(-4, 4)],
            method="L-BFGS-B",
        )
        optimized_value = float(round(result.x[0], 6))
        print(f"\n  > Optimize edilmiş DeltaCt: {optimized_value}")
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
        print(f"  > Healthy avg={float(healthy_avg)} diff={diff}")

        if diff > 0:
            df.loc[(df["İstatistik Oranı"] > 0.75) & (df["İstatistik Oranı"] < 1), "İstatistik Oranı"] += diff
        elif diff < 0:
            df.loc[df["İstatistik Oranı"] < 0.7, "İstatistik Oranı"] += diff  # diff negatif

        return df


# --- 1. Validation & Pre-processing ---
# Girdi verilerinin kontrolü, filtreleme (valid_mask) ve temizleme işlemleri.

    def _validate_input_df(self, df: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Girdi verilerini kontrol eder ve geçerli/geçersiz olarak ayırır.
        """
        if df is None:
            raise ValueError("CalculateWithoutReferance.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        # Maskeleme Kuralları:
        # 1. Uyarı yoksa (null)
        # 2. VEYA Uyarı "Düşük RFU Değeri" ise
        # 3. VEYA Regresyon "Güvenli Bölge" ise
        valid_mask = (df["Uyarı"].isnull()) | \
                     (df["Uyarı"] == "Düşük RFU Değeri") | \
                     (df["Regresyon"] == "Güvenli Bölge")

        valid_data = df[valid_mask].copy()
        invalid_data = df[~valid_mask].copy()

        return valid_data, invalid_data





# --- 3. Mathematical Optimization ---
# KMeans kümeleme, maliyet fonksiyonu (objective) ve minimize işlemleri.

# --- 4. Statistics & Classification ---
# Delta-Delta Ct hesaplamaları, taşıyıcı/hasta sınıflandırması ve düzeltme (adjustment) mantığı.

# --- 5. Helper Methods (Private) ---
# Sınıf içi hesaplamalara yardımcı olan, dışarıdan erişilmeyen yardımcı fonksiyonlar.

    def _print_optimization_summary(self, final_value: float, delta_ct_series: pd.Series):
            """Optimizasyon sonuçlarını ekrana formatlı basar."""
            stats = {
                "min": delta_ct_series.min(),
                "mean": delta_ct_series.mean(),
                "max": delta_ct_series.max()
            }

            print(f"\n[FINAL OPTIMIZATION RESULT]")
            print(f"  > Optimized Static Value : {final_value:.4f}")
            print(f"  > Δ Ct Statistics:")
            for key, val in stats.items():
                print(f"    - {key:<5}: {val:.4f}")
            print("-" * 30)