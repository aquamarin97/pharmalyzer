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


class AnalyzeButton(QObject):
    """
    Analiz işlemini yürüten sınıf.
    """

    analysisCompleted = pyqtSignal(str)  # Dosya yolunu yayımlayan sinyal

    def __init__(self):
        super().__init__()
        # self.csv_file_path = CSVManager.get_csv_file_path()  # İşlenecek dosyanın yolu
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
        try:
            if carrier_range < self.uncertain_range:
                self.carrier_range = carrier_range
                print(self.carrier_range)
            else:
                ValueError
        except:
            print("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")

    def set_uncertain_range(self, uncertain_range):
        self.uncertain_range = uncertain_range

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
            # --- CSV manager df bilgisini güncelle
            CSVManager.update_csv_df()

            # --- İşlem başlat # Release Öncesi ekstra kayıt işlemlerini kontrol et
            CSVProcessor.process()

            # --- Referanslı hesaplama için Sınıfı başlat
            print(f"gönderilen: {self.carrier_range}")
            referance_calculation = CalculateWithReferance(
                self.referance_well, self.carrier_range, self.uncertain_range
            )
            is_succesful = referance_calculation.process()
            if is_succesful == False:
                self.set_checkbox_status(True)
                print(self.checkbox_status)
                
            # --- Regresyon Hesaplaması
            regration_calculation = CalculateRegration()
            regration_calculation.process()

            # --- Yazılım Hesaplaması
            software_calculation = CalculateWithoutReferance()
            software_calculation.process()


            # --- Configurate Result CSV
            configurate_csv = ConfigurateResultCSV(self.checkbox_status)
            configurate_csv.process()

            # --- İşlem tamamlandığında sinyal yayımlayın
            csv_file_path = CSVManager.get_csv_file_path()
            self.analysisCompleted.emit(csv_file_path)

            return True
        except ValueError as e:
            print(f"Hata: {e}")
            return False
        except Exception as e:
            print(f"Bilinmeyen hata: {e}")
            return False
