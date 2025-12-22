# app\willbedeleted\handlers\analyze_button.py
from PyQt5.QtCore import QObject, pyqtSignal

from app.willbedeleted.managers.csv_manager import CSVManager
from app.willbedeleted.scripts.calculate_regration.calculate_regration import CalculateRegration
from app.willbedeleted.scripts.calculate_with_referance.calculate_with_referance import \
    CalculateWithReferance
from app.willbedeleted.scripts.calculate_without_referance.calculate_without_referance import \
    CalculateWithoutReferance
from app.willbedeleted.scripts.configurate_result_csv.configurate_result_csv import \
    ConfigurateResultCSV
from app.willbedeleted.scripts.csv_processor.csv_processor import CSVProcessor
from app.services.pipeline import Pipeline


class AnalyzeButton(QObject):
    """
    Analiz işlemini yürüten sınıf.
    """

    analysisCompleted = pyqtSignal(str)  # Dosya yolunu yayımlayan sinyal

    def __init__(self):
        super().__init__()
        self.referance_well = "F12"  # Referans kuyunun varsayılan konumu
        self.checkbox_status = True
        self.carrier_range = 0.5999
        self.uncertain_range = 0.6199

    def set_referance_well(self, referance_well):
        """
        Referans kuyunun konumunu ayarlar.

        Args:
            referance_well (str): Kuyunun konumu.
        """
        self.referance_well = referance_well
        print(self.referance_well)

    def set_carrier_range(self, carrier_range):
        carrier_val = float(carrier_range)
        uncertain_val = float(self.uncertain_range)
        if carrier_val < uncertain_val:
            self.carrier_range = carrier_val
            print(self.carrier_range)
        else:
            raise ValueError("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")
        
    def set_uncertain_range(self, uncertain_range):
        uncertain_val = float(uncertain_range)
        carrier_val = float(self.carrier_range)
        if uncertain_val > carrier_val:
            self.uncertain_range = uncertain_val
        else:
            raise ValueError("Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır.") 
        
    def set_checkbox_status(self, checkbox_status):
        
        self.checkbox_status = checkbox_status
        print(
            f"analiz buton sınıfında checkbox durumu {self.checkbox_status} olarak güncellendi."
        )

    def analyze(self):
        """
        Analiz işlemini gerçekleştirir ve gerekli dosyaları işler.

        Returns:
            bool: Analiz işleminin başarı durumu.
        """
        try:
            CSVManager.update_csv_df()

            print(f"gönderilen: {self.carrier_range}")
            referance_calculation = CalculateWithReferance(
                self.referance_well, self.carrier_range, self.uncertain_range
            )

            regration_calculation = CalculateRegration()

            software_calculation = CalculateWithoutReferance()

            configurate_csv = ConfigurateResultCSV(self.checkbox_status)

            Pipeline.run(
                [
                    CSVProcessor.process,
                    referance_calculation.process,
                    regration_calculation.process,
                    software_calculation.process,
                    configurate_csv.process,
                ]
            )
            print("Pipeline.run Çalıştı")

            if not referance_calculation.last_success:
                self.set_checkbox_status(True)
            self.analysisCompleted.emit("in-memory")

            return True
        except ValueError as e:
            print(f"Hata: {e}")
            return False
        except Exception as e:
            print(f"Bilinmeyen hata: {e}")
            return False
