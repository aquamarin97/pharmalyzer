# app/willbedeleted/scripts/calculate_with_referance/calculate_with_referance.py
import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMessageBox


class CalculateWithReferance:
    def __init__(self, referance_well, carrier_range: float, uncertain_range: float):
        self.df = None
        self.referance_well = referance_well
        self.carrier_range = float(carrier_range)
        self.uncertain_range = float(uncertain_range)
        self.last_success = True

    def process(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CalculateWithReferance.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        self.df = df.copy(deep=True)
        is_success = self.set_referance_value()
        self.last_success = is_success

        valid_mask = (self.df["Uyarı"].isnull()) | (self.df["Uyarı"] == "Düşük RFU Değeri")
        valid_data = self.df[valid_mask].copy()
        invalid_data = self.df[~valid_mask].copy()

        valid_data = self.finalize_data(valid_data)
        self.df = pd.concat([valid_data, invalid_data], ignore_index=True)
        return self.df
    
    def set_referance_value(self):
        """Referans kuyu Δ Ct değerini alır ve initial_static_value olarak atar."""
        if not self.referance_well or pd.isna(self.referance_well):
            self.show_warning("Lütfen geçerli bir referans kuyu giriniz!")
            raise ValueError("Referans kuyu boş.")

        if self.referance_well not in self.df["Kuyu No"].values:
            self.show_warning(f"Referans kuyu '{self.referance_well}' bulunamadı.")
            raise ValueError(f"Referans kuyu '{self.referance_well}' bulunamadı.")

        self.initial_static_value = self.df.loc[
            self.df["Kuyu No"] == self.referance_well, "Δ Ct"
        ].values[0]
        print(f"Standart Delta Ct Değeri: {self.initial_static_value}")
        if pd.isna(self.initial_static_value):
            self.show_warning(
                f"Referans kuyu '{self.referance_well}' için Δ Ct değeri boş."
            )

            return False
        else:
            return True

    def finalize_data(self, valid_data):
        """Hesaplama sonuçlarını oluşturur."""
        valid_data["Δ_Δ Ct"] = valid_data["Δ Ct"] - self.initial_static_value
        valid_data["Standart Oranı"] = 2 ** -valid_data["Δ_Δ Ct"]
        valid_data.loc[
            valid_data["Standart Oranı"] <= 0.7,
            "Standart Oranı",
        ] -= 0.00

        # Değişkenleri lambda içine geçir
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

    def show_warning(self, message):
        """PyQt5 ile uyarı mesajı gösterir."""
        app = QApplication.instance()  # PyQt5 uygulama instance kontrolü
        if not app:
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
