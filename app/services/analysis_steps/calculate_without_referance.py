# app\services\analysis_steps\calculate_without_referance.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.cluster import KMeans


class CalculateWithoutReferance:
    def __init__(self):
        self.df = None

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CalculateWithoutReferance.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        self.df = df.copy(deep=True)
        valid_mask = (self.df["Uyarı"].isnull()) | (self.df["Uyarı"] == "Düşük RFU Değeri")
        valid_data = self.df[valid_mask].copy()
        invalid_data = self.df[~valid_mask].copy()

        print("\n<<< İSTATİSTİK ORANI HESAPLANIYOR >>>")
        new_static_value = self.optimize_static_value(valid_data)
        valid_data = self.finalize_data(valid_data, new_static_value)

        self.df = pd.concat([valid_data, invalid_data], ignore_index=True)
        return self.df

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
        """3. kümenin etkisini azaltmak için üssel ceza fonksiyonu uygular."""
        ratio = third_center / min_center

        # NaN içeren olası değerlerden arındırılarak standart sapma hesaplanır
        ct_values = valid_data["Δ Ct"]
        ct_std = np.std(ct_values)

        beta = 1.0 + (ct_std / 2)
        exp_penalty_factor = exp_base**min_count

        print(
            f"(β: {beta:.3f}, varyans: {ct_std:.3f}, oran: {ratio:.3f}, min_count: {min_count}, ceza katsayısı: {exp_penalty_factor:.3f})"
        )

        if ratio <= threshold:
            return third_center
        else:
            penalty = (
                alpha * ((ratio - threshold) ** beta) * min_center * exp_penalty_factor
            )
            print(f"→ Dönen 3. küme değeri {third_center - penalty:.4f}")
            return third_center - penalty

    def optimize_static_value(self, valid_data):
        """Statik referans değerini optimize eder."""
        if valid_data.empty:
            print("Geçerli veri bulunamadı. Varsayılan başlangıç değeri kullanılacak.")
            return 2.00

        clusters, clustered_data = self._cluster_ct_values(valid_data)
        initial_static_value = self._compute_initial_static_value(
            clusters, clustered_data
        )
        optimized_static_value = self._optimize_delta_ct(
            clustered_data, initial_static_value
        )
        return optimized_static_value

    @staticmethod
    def objective(x, valid_data, use_log_mse=True):
        """Optimize edilecek hedef fonksiyon.
        use_log_mse=True ise log2(istatistik oranı) üzerinden MSE hesaplanır.
        """
        temp_data = valid_data.copy()
        temp_data["Δ_Δ Ct"] = temp_data["Δ Ct"] - x
        temp_data["İstatistik Oranı"] = 2 ** -temp_data["Δ_Δ Ct"]

        if use_log_mse:
            log_ratios = np.log2(temp_data["İstatistik Oranı"])
            mse = np.mean((log_ratios - 0.0) ** 2)
        else:
            mse = np.mean((temp_data["İstatistik Oranı"] - 1.0) ** 2)

        return mse

    def finalize_data(self, valid_data, new_static_value):
        """İstatistiksel analiz ve sınıflandırmayı yürüten üst düzey işlev."""
        valid_data = self._calculate_statistics(valid_data, new_static_value)
        valid_data["Yazılım Hasta Sonucu"] = self._classify_patients(valid_data)
        valid_data = self._adjust_statistics(valid_data)
        valid_data["Yazılım Hasta Sonucu"] = self._classify_patients(valid_data)
        return valid_data

    # --- Yardımcı (private) fonksiyonlar ---

    def _cluster_ct_values(self, valid_data, n_clusters=5):
        """K-means ile Ct değerlerini kümeleyerek merkez ve sayıları döner."""
        delta_ct_values = valid_data[["Δ Ct"]].values
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        valid_data["Cluster"] = kmeans.fit_predict(delta_ct_values)

        centers = kmeans.cluster_centers_.flatten()
        counts = valid_data["Cluster"].value_counts().sort_index()

        for i, count in enumerate(counts):
            print(f"Küme {i}: Merkez = {centers[i]}, Eleman sayısı = {count}")
        print(f"Kümelemenin merkezleri: {centers}\n")

        sorted_clusters = sorted(zip(centers, counts), key=lambda x: x[0])
        return sorted_clusters, valid_data

    def _compute_initial_static_value(self, clusters, valid_data):
        """İlk 3 küme merkezine göre ağırlıklı ortalama statik değeri hesaplar."""
        (min_center, min_count) = clusters[0]
        (second_center, second_count) = clusters[1]
        (third_center, third_count) = clusters[2]

        third_adjusted = self.penalize_third_center(
            third_center, min_center, min_count, valid_data, alpha=1.0, threshold=1.4
        )

        numerator = (
            min_center * min_count
            + second_center * second_count
            + third_adjusted * third_count
        )
        denominator = min_count + second_count + third_count
        weighted_avg = numerator / denominator

        print(f"Ağırlıklı başlangıç değeri (Delta Ct): {weighted_avg}\n")
        return weighted_avg

    def _optimize_delta_ct(self, valid_data, initial_static_value):
        """Optimize edilecek değer aralığında MSE minimizasyonu yapar."""
        valid_data["Δ_Δ Ct"] = valid_data["Δ Ct"] - initial_static_value
        valid_data["İstatistik Oranı"] = round(2 ** -valid_data["Δ_Δ Ct"], 6)

        filtered = valid_data[
            (valid_data["İstatistik Oranı"] >= 0.75)
            & (valid_data["İstatistik Oranı"] <= 1.3)
        ]

        if filtered.empty:
            print("Optimize edilecek veri kalmadı, başlangıç değeri kullanılacak.")
            return initial_static_value

        print(f"0.75-1.3 arasında kalan toplam veri sayısı: {len(filtered)}")

        result = minimize(
            lambda x: self.objective(x, filtered, use_log_mse=True),
            initial_static_value,
            bounds=[(-4, 4)],
            method="L-BFGS-B",
        )

        optimized_value = round(result.x[0], 6)
        print(f"Optimize edilmiş Delta Ct: {optimized_value}")
        print("------------ Analiz Sonu ------------")
        return optimized_value

    def _calculate_statistics(self, df, static_value):
        """Delta Delta Ct ve istatistik oranını hesaplar."""
        df["Δ_Δ Ct"] = df["Δ Ct"] - static_value
        df["İstatistik Oranı"] = 2 ** -df["Δ_Δ Ct"]
        df.loc[df["İstatistik Oranı"] <= 0.6999, "İstatistik Oranı"] -= 0.00
        return df

    def _classify_patients(self, df):
        """İstatistik oranına göre hastalık sınıflandırması yapar."""
        return df["İstatistik Oranı"].apply(
            lambda x: (
                "Sağlıklı"
                if x > 0.619999
                else (
                    "Belirsiz"
                    if 0.599999 < x <= 0.619999
                    else (
                        "Taşıyıcı"
                        if 0.1 < x <= 0.599999
                        else "Hasta" if x <= 0.1 else "Tekrar"
                    )
                )
            )
        )

    def _adjust_statistics(self, df):
        """Ortalama 1'den sapmışsa oranlara fark uygulayarak normalize eder."""

        healthy_avg = df.loc[
            df["Yazılım Hasta Sonucu"] == "Sağlıklı", "İstatistik Oranı"
        ].mean()
        diff = 1.0 - healthy_avg

        print(
            f"📊 Sadece 'Sağlıklı' sonuçların İstatistik Oranı ortalaması: {healthy_avg:.6f}"
        )

        if diff > 0:
            print(
                f"→ Ortalama 1'den küçük. {diff:.6f} fark 0.75 üzerindeki oranlara eklenecek."
            )
            df.loc[
                (df["İstatistik Oranı"] > 0.75) & (df["İstatistik Oranı"] < 1),
                "İstatistik Oranı",
            ] += diff

        elif diff < 0:
            print(
                f"→ Ortalama 1'den büyük. {abs(diff):.6f} fark 0.7 altındaki oranlardan çıkarılacak."
            )
            df.loc[
                df["İstatistik Oranı"] < 0.7, "İstatistik Oranı"
            ] += diff  # diff zaten negatif

        return df
