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
        self.cluster_number = 5

    # --- 1. Public Interface & Core Workflow ---

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CalculateWithoutReferance.process Pipeline tarafından df ile çağrılmalıdır.")
        
        self.df = df
        
        # 1. ADIM: İstatistiksel hesaplama için sıkı filtreleme
        valid_data_for_stats, _ = self._validate_input_df(df)

        print(f"İstatistik değeri hesaplanıyor. Hesaplamada kullanılan kaynak satır: {len(valid_data_for_stats)}")

        if not valid_data_for_stats.empty:
            # Sağlıklı veriler üzerinden ideal referans değerini bul
            new_static_value = self.optimize_static_value(valid_data_for_stats)
            
            # 2. ADIM: Filtreyi gevşet (Boş Kuyu olmayan her şeyi dahil et)
            final_valid_mask = (df["Uyarı"] != "Boş Kuyu")
            final_valid_data = df[final_valid_mask].copy()
            final_invalid_data = df[~final_valid_mask].copy()

            print(f"Finalize ediliyor. İşlenen toplam kuyu sayısı: {len(final_valid_data)}")

            # Hesaplanan değeri tüm geçerli verilere uygula
            final_valid_data = self.finalize_data(final_valid_data, new_static_value)
            
            return pd.concat([final_valid_data, final_invalid_data], ignore_index=True)
        
        else:
            print("Uyarı: İstatistik hesaplamak için yeterli (Güvenli Bölge) veri bulunamadı!")
            return df

    def finalize_data(self, valid_data: pd.DataFrame, new_static_value: float) -> pd.DataFrame:
        """Verileri hesaplar, sınıflandırır ve istatistiksel düzeltme yapar."""
        valid_data = self._calculate_statistics(valid_data, new_static_value)
        valid_data["Yazılım Hasta Sonucu"] = self._classify_patients(valid_data)
        
        valid_data = self._adjust_statistics(valid_data)
        valid_data["Yazılım Hasta Sonucu"] = self._classify_patients(valid_data)
        
        return valid_data

    # --- 2. Optimization & Mathematical Logic ---

    def optimize_static_value(self, valid_data: pd.DataFrame) -> float:
        if valid_data.empty:
            print(" [!] Uyarı: Geçerli veri yok, varsayılan değer (2.00) kullanılıyor.")
            return 2.00

        # Kümeleme ve Başlangıç Tahmini
        clusters, clustered_data = self._cluster_ct_values(valid_data)
        initial_static_value = self._compute_initial_static_value(clusters, clustered_data)
        
        # Optimizasyon (İnce Ayar)
        optimized_static_value = self._optimize_delta_ct(clustered_data, initial_static_value)
        
        self._print_optimization_summary(optimized_static_value, valid_data["Δ Ct"])
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

    def penalize_third_center(self, third_center, min_center, min_count, valid_data, alpha=1.0, threshold=1.4, exp_base=1.1):
        ratio = third_center / min_center if min_center else float("inf")
        ct_std = float(np.std(valid_data["Δ Ct"]))

        beta = 1.0 + (ct_std / 2)
        exp_penalty_factor = float(exp_base ** min_count)
        
        print("  > penalty params")
        params = {"beta": beta, "std": ct_std, "ratio": ratio, "min_count": min_count, "factor": exp_penalty_factor}
        for name, value in params.items():
            print(f"     > {name:<10} = {value}")

        if ratio <= threshold:
            return third_center

        penalty = alpha * ((ratio - threshold) ** beta) * min_center * exp_penalty_factor
        print(f"Ceza sonrası 3. merkez = {third_center - penalty} ")
        return third_center - penalty

    # --- 3. Internal Helpers & Processing ---

    def _validate_input_df(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        valid_mask = (df["Regresyon"] == "Güvenli Bölge") & \
                    ((df["Uyarı"].isnull()) | (df["Uyarı"] == "Düşük RFU Değeri"))

        return df[valid_mask].copy(), df[~valid_mask].copy()

    def _cluster_ct_values(self, valid_data: pd.DataFrame):
        delta_ct_values = valid_data[["Δ Ct"]].values
        kmeans = KMeans(n_clusters=self.cluster_number, random_state=42)
        
        valid_data = valid_data.copy()
        valid_data["Cluster"] = kmeans.fit_predict(delta_ct_values)

        centers = kmeans.cluster_centers_.flatten()
        counts = valid_data["Cluster"].value_counts().sort_index()
        sorted_clusters = sorted(zip(centers, counts), key=lambda x: x[0])
        
        print(f"\n  > [K-Means] {self.cluster_number} küme oluşturuldu:")
        for center, count in sorted_clusters:
            print(f"     > Merkez: {center:6.2f} | Sayı: {count}")
        print("")
        
        return sorted_clusters, valid_data

    def _compute_initial_static_value(self, clusters, valid_data: pd.DataFrame) -> float:
        (min_center, min_count) = clusters[0]
        (second_center, second_count) = clusters[1]
        (third_center, third_count) = clusters[2]

        third_adjusted = self.penalize_third_center(
            third_center, min_center, int(min_count), valid_data
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
        # .loc kullanımı daha güvenlidir
        df.loc[df["İstatistik Oranı"] <= 0.6999, "İstatistik Oranı"] -= 0.00
        return df

    def _classify_patients(self, df: pd.DataFrame) -> pd.Series:
        def classify(x: float):
            if pd.isna(x): return ""
            if x > self.uncertain_range: return "Sağlıklı"
            if self.carrier_range < x <= self.uncertain_range: return "Belirsiz"
            if 0.1 < x <= self.carrier_range: return "Taşıyıcı"
            if x <= 0.1: return "Hasta"
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
            df.loc[df["İstatistik Oranı"] < 0.7, "İstatistik Oranı"] += diff

        return df

    def _print_optimization_summary(self, final_value: float, delta_ct_series: pd.Series):
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