# app\services\analysis_service.py
# app/services/analysis_service.py

from dataclasses import dataclass

from app.services.pipeline import Pipeline
from app.services.analysis_steps.calculate_with_referance import CalculateWithReferance
from app.services.analysis_steps.calculate_regration import CalculateRegration
from app.services.analysis_steps.calculate_without_referance import CalculateWithoutReferance
from app.services.analysis_steps.configurate_result_csv import ConfigurateResultCSV
from app.services.analysis_steps.csv_processor import CSVProcessor


@dataclass
class AnalysisConfig:
    referance_well: str = "F12"
    checkbox_status: bool = True
    carrier_range: float = 0.5999
    uncertain_range: float = 0.6199


class AnalysisService:
    def __init__(self, config: AnalysisConfig | None = None):
        self.config = config or AnalysisConfig()

    def set_referance_well(self, v: str):
        self.config.referance_well = v

    def set_checkbox_status(self, v: bool):
        self.config.checkbox_status = v

    def set_carrier_range(self, v: float):
        v = float(v)
        if v >= float(self.config.uncertain_range):
            raise ValueError("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")
        self.config.carrier_range = v

    def set_uncertain_range(self, v: float):
        v = float(v)
        if v <= float(self.config.carrier_range):
            raise ValueError("Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır.")
        self.config.uncertain_range = v

    def run(self) -> bool:
        """
        Pipeline'ı çalıştırır. DataStore üzerinde çalıştığı varsayımıyla True/False döner.
        """
        try:
            ref_step = CalculateWithReferance(
                self.config.referance_well,
                self.config.carrier_range,
                self.config.uncertain_range,
            )
            reg_step = CalculateRegration()
            sw_step = CalculateWithoutReferance()
            post_step = ConfigurateResultCSV(self.config.checkbox_status)

            Pipeline.run([
                CSVProcessor.process,
                ref_step.process,
                reg_step.process,
                sw_step.process,
                post_step.process,
            ])

            # referans kuyusu boşsa checkbox zorla True
            if not ref_step.last_success:
                self.config.checkbox_status = True

            return True
        except Exception as e:
            print(f"[AnalysisService] hata: {e}")
            return False
