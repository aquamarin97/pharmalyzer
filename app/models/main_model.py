# app/models/main_model.py
from dataclasses import dataclass
import pandas as pd
from dataclasses import dataclass
from app.services.rdml_service import RDMLService
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.willbedeleted.handlers.colored_box_handler import ColoredBoxHandler
from app.willbedeleted.handlers.analyze_button import AnalyzeButton
from app.willbedeleted.managers.pcr_graph_manager import DataManager
from app.willbedeleted.scripts.pcr_graph_drawer import GraphDrawer
from app.willbedeleted.controllers.regression_controller import RegressionGraphViewer
from app.willbedeleted.managers.csv_manager import CSVManager
from app.willbedeleted.utils.file_utils.rdml_processor import UtilsRDMLProcessor

from app.models.workers.analysis_worker import AnalysisWorker


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
        self.colored_box_handler = ColoredBoxHandler()
        self.analyze_button = AnalyzeButton()
        self.data_manager = DataManager()

        # Grafik bileşenleri (container'lar controller/view tarafında bağlanıyor)
        self.graph_drawer: GraphDrawer | None = None
        self.regression_graph_manager: RegressionGraphViewer | None = None

        # --- Async analysis altyapısı ---
        self._analysis_thread = QThread(
            self
        )  # parent ver ki life-cycle daha güvenli olsun
        self._worker = AnalysisWorker(self.analyze_button)
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
        CSVManager.clear_csv_file_path()
        CSVManager.clear_csv_df()


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
    def process_rdml_to_csv(self, file_path: str):
        UtilsRDMLProcessor.process(file_path)

    # ---- Cleanup (opsiyonel ama iyi pratik) ----
    def shutdown(self):
        """
        Uygulama kapanırken çağırırsan thread temiz kapanır.
        """
        self._analysis_thread.quit()
        self._analysis_thread.wait()
