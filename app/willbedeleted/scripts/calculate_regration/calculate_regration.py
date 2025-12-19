# app\willbedeleted\scripts\calculate_regration\calculate_regration.py
import numpy as np
from sklearn.linear_model import LinearRegression

from app.willbedeleted.managers.csv_manager import CSVManager


class CalculateRegration:
    def __init__(self):
        self.df = CSVManager.get_csv_df()

    def process(self):
        self.calculate_regration()
        # csv dosya yolu
        file_path = CSVManager.get_csv_file_path()
        # dosyayı güncelle
        self.df.to_csv(file_path, index=False)
        # df yi güncelle
        CSVManager.update_csv_df()
        print("<<< REGRESYON ADIMI TAMAMLANDI >>>")

    def calculate_regration(self):
        """Regresyon hesaplamalarını yapar ve sonuçları kaydeder."""
        if self.df is None:
            raise ValueError("CSV dosyası okunmadı. Lütfen önce read_csv() çağırın.")

        # Gerekli sütunları kontrol et
        required_columns = ["fam_end_rfu", "hex_end_rfu"]
        for column in required_columns:
            if column not in self.df.columns:
                raise ValueError(f"{column} sütunu eksik.")

        # Boş değerleri atan satırları filtrele
        filtered_df = self.df.dropna(subset=["fam_end_rfu", "hex_end_rfu", "HEX Ct"])

        if filtered_df.empty:
            raise ValueError("Gerekli sütunlarda işlem yapılacak veri yok.")

        # Iteratif regresyon ve aykırı değer temizleme
        print("\n<<< REGRESYON ADIMI >>>")
        print(f"Regresyon modeli için filtrelenmiş veri sayısı: {len(filtered_df)}")
        if len(filtered_df)>50:
            print("Seçilen yöntem: İterative Regresyon")
            model, clean_df = self.iterative_regression(
                filtered_df, "fam_end_rfu", "hex_end_rfu"
            )
        else:
            print("Seçilen Yöntem: Mad Based Regresyon")
            model, clean_df = self.mad_based_regression(
                filtered_df, "fam_end_rfu", "hex_end_rfu"
            )
        # Safe zone kontrolü
        self.df["Regresyon"] = "Riskli Alan"  # Varsayılan değer
        self.df.loc[clean_df.index, "Regresyon"] = "Güvenli Bölge"
        # "Uyarı" sütunundaki koşullara göre "Regresyon" sütununu güncelle
        self.df.loc[
            self.df["Uyarı"].isin(["Yetersiz DNA", "Boş Kuyu"]), "Regresyon"
        ] = "-"

    def iterative_regression(self, df, x_col, y_col, threshold=2.0, max_iter=10):
        """
        Iterative outlier removal using Linear Regression.

        Parameters:
        df: DataFrame - Veri çerçevesi
        x_col: str - Bağımsız değişken sütunu
        y_col: str - Bağımlı değişken sütunu
        threshold: float - Aykırı değer sınırı (sigma cinsinden)
        max_iter: int - Maksimum iterasyon sayısı

        Returns:
        model: LinearRegression - Eğitilmiş regresyon modeli
        filtered_df: DataFrame - Aykırı değerlerden arındırılmış veri çerçevesi
        """
        filtered_df = df.copy()
        for i in range(max_iter):
            # X ve Y verilerini al
            X = filtered_df[x_col].values.reshape(-1, 1)
            y = filtered_df[y_col].values

            # Lineer regresyon modeli
            model = LinearRegression()
            model.fit(X, y)
            y_pred = model.predict(X)

            # Rezidüler (sapmalar) hesapla
            residuals = y - y_pred
            sigma = np.std(residuals)

            # Aykırı değerleri tespit et
            mask_upper = np.abs(residuals) <= (threshold + 10) + 2.2 * sigma
            mask_lower = np.abs(residuals) >= (threshold) - 2.2 * sigma
            mask = mask_upper & mask_lower

            # Aykırı olmayan verileri filtrele
            new_filtered_df = filtered_df[mask]

            # Eğer veri değişmezse iterasyonu sonlandır
            if new_filtered_df.shape[0] == filtered_df.shape[0]:
                break

            filtered_df = new_filtered_df

        return model, filtered_df

    def mad_based_regression(self, df, x_col, y_col, threshold=3.5):
        """
        MAD (Median Absolute Deviation) tabanlı aykırı değer temizleme.

        Parameters:
        df: DataFrame
        x_col, y_col: str
        threshold: float - MAD çarpanı

        Returns:
        model: LinearRegression
        filtered_df: Aykırılardan arındırılmış veri
        """
        filtered_df = df.copy()
        if filtered_df.empty:
            return LinearRegression(), filtered_df

        X = filtered_df[x_col].values.reshape(-1, 1)
        y = filtered_df[y_col].values

        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)

        residuals = y - y_pred
        median = np.median(residuals)
        abs_deviation = np.abs(residuals - median)
        mad = np.median(abs_deviation)

        if mad == 0:
            print("⚠️ MAD = 0, tüm veriler aynı. Temizleme yapılmadan geri dönülüyor.")
            return model, filtered_df

        # Modified Z-score yöntemi (robust aykırı tespiti)
        modified_z_scores = 0.6745 * (residuals - median) / mad
        mask = np.abs(modified_z_scores) <= threshold

        new_filtered_df = filtered_df[mask]

        if new_filtered_df.shape[0] < 3:
            print(f"⚠️ Yeterli güvenli örnek kalmadı: {new_filtered_df.shape[0]}")
            return model, filtered_df  # fallback: orijinal veriyle geri dön

        return model, new_filtered_df