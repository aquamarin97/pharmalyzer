# app\models\main_model.py
from dataclasses import dataclass
import pandas as pd
from app.controllers.colored_box_controller import ColoredBoxController
from app.services.analysis_service import AnalysisService
from app.services.rdml_service import RDMLService
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.willbedeleted.scripts.pcr_graph_drawer import GraphDrawer
from app.services.data_store import DataStore

from app.models.workers.analysis_worker import AnalysisWorker
from app.services.pcr_data_service import PCRDataService


@dataclass
class MainState:
    file_name: str = ""


class MainModel(QObject):
    """
    Uygulamanın state'ini ve iş katmanı nesnelerini tutar.
    UI'ya dokunmaz.
    Thread yönetimi burada tutulabilir (ince şekilde).
    """

    analysis_finished = pyqtSignal(bool)  # dışarı tek sinyal verelim
    analysis_error = pyqtSignal(str)

    # worker'a "çalış" demek için sinyal (queued connection garantisi)
    _start_analysis = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.state = MainState()
        self.rdml_df: pd.DataFrame | None = None
        # İş bileşenleri
        self.colored_box_controller = ColoredBoxController()
        self.analysis_service = AnalysisService()
        self.data_manager = PCRDataService()

        # Grafik bileşenleri (container'lar controller/view tarafında bağlanıyor)
        self.graph_drawer: GraphDrawer | None = None

        # --- Async analysis altyapısı ---
        self._analysis_thread = QThread(
            self
        )  # parent ver ki life-cycle daha güvenli olsun
        self._worker = AnalysisWorker(self.analysis_service)
        self._worker.moveToThread(self._analysis_thread)

        # start signal -> worker.run (queued)
        self._start_analysis.connect(self._worker.run)

        # worker sonuçlarını model üzerinden dışarı aktar
        self._worker.finished.connect(self.analysis_finished)
        self._worker.error.connect(self.analysis_error)

        # thread'i başlat (event loop aktif)
        self._analysis_thread.start()

    # ---- State helpers ----
    def set_file_name_from_rdml(self, file_name: str):
        self.state.file_name = file_name.split(".rdml")[0]

    # ---- CSV resets ----
    def reset_data(self):
        DataStore.clear()



    # ---- Analysis (async) ----
    def run_analysis(self):
        """
        Worker thread'de analiz başlatır.
        """
        # thread durmuşsa tekrar başlat
        if not self._analysis_thread.isRunning():
            self._analysis_thread.start()

        # ÖNEMLİ: worker.run'ı doğrudan çağırmıyoruz.
        # Signal emit -> queued connection ile worker thread'inde çalışır.
        self._start_analysis.emit()

    # ---- RDML processing ----
    def import_rdml(self, file_path: str):
        """
        RDML dosyasını okuyup DataStore'a DataFrame olarak yükler.
        """
        df = RDMLService.rdml_to_dataframe(file_path)
        DataStore.set_df(df)

    # ---- Cleanup (opsiyonel ama iyi pratik) ----
    def shutdown(self):
        """
        Uygulama kapanırken çağırırsan thread temiz kapanır.
        """
        self._analysis_thread.quit()
        self._analysis_thread.wait()
    def set_checkbox_status(self, v: bool):
        self.analysis_service.set_checkbox_status(v)

    def set_referance_well(self, v: str):
        self.analysis_service.set_referance_well(v)

    def set_carrier_range(self, v: float):
        self.analysis_service.set_carrier_range(v)

    def set_uncertain_range(self, v: float):
        self.analysis_service.set_uncertain_range(v)

    def get_carrier_range(self) -> float:
        return self.analysis_service.config.carrier_range

    def get_uncertain_range(self) -> float:
        return self.analysis_service.config.uncertain_range