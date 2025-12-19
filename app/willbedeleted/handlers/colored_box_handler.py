# app\willbedeleted\handlers\colored_box_handler.py
from PyQt5.QtCore import QObject, pyqtSignal

from app.willbedeleted.managers.csv_manager import CSVManager


class ColoredBoxHandler(QObject):
    calculationCompleted = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_result = []
        self.homozigot_line_edit = "F12"  # Başlangıç değeri homozigot_line_edit
        self.heterozigot_line_edit = "G12"  # Başlangıç değeri heterozigot_line_edit
        self.NTC_line_edit = "H12"  # Başlangıç değeri NTC_line_edit
        self.check_box_status = True  # QCheckBox durumu

    def set_check_box_status(self, status):
        """CheckBox durumunu günceller."""
        self.check_box_status = status
        print(f"CheckBox durumu güncellendi: {self.check_box_status}")

    def set_homozigot_line_edit(self, new_text):
        """homozigot_line_edit değerini güncelle."""
        self.homozigot_line_edit = new_text
        # print(f"homozigot_line_edit updated to: {self.homozigot_line_edit}")

    def set_heterozigot_line_edit(self, new_text):
        """heterozigot_line_edit değerini güncelle."""
        self.heterozigot_line_edit = new_text
        # print(f"heterozigot_line_edit updated to: {self.heterozigot_line_edit}")

    def set_NTC_line_edit(self, new_text):
        """NTC_line_edit değerini güncelle."""
        self.NTC_line_edit = new_text
        # print(f"NTC_line_edit updated to: {self.NTC_line_edit}")

    def _get_relevant_column(self):
        """CheckBox durumuna göre hangi sütunun kullanılacağını belirler."""
        return "İstatistik Oranı" if self.check_box_status else "Standart Oranı"

    def _check_homozigot(self, df, column_name):
        """Homozigot değerini kontrol eder."""
        homozigot_row = df[df["Kuyu No"] == self.homozigot_line_edit]
        if not homozigot_row.empty:
            yazilim_sonucu = homozigot_row[column_name].iloc[0]
            return yazilim_sonucu >= 0.5999
        return False

    def _check_heterozigot(self, df, column_name):
        """Heterozigot değerini kontrol eder."""
        heterozigot_row = df[df["Kuyu No"] == self.heterozigot_line_edit]
        if not heterozigot_row.empty:
            yazilim_sonucu = heterozigot_row[column_name].iloc[0]
            return yazilim_sonucu < 0.5999
        return False

    def _check_ntc(self, df):
        """NTC değerini kontrol eder."""
        ntc_row = df[df["Kuyu No"] == self.NTC_line_edit]
        if not ntc_row.empty:
            uyarı = ntc_row["Uyarı"].iloc[0]
            return uyarı == "Yetersiz DNA"
        return False

    def define_box_color(self):
        """Box renklerini belirler ve sinyal gönderir."""

        # CSV'den veri al
        df = CSVManager.get_csv_df()
        column_name = self._get_relevant_column()

        # Sonuçları topla
        result_list = [
            self._check_homozigot(df, column_name),
            self._check_heterozigot(df, column_name),
            self._check_ntc(df),
        ]

        # Sonuçları sakla ve sinyal gönder
        self.last_result = result_list
        self.calculationCompleted.emit(result_list)
