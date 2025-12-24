# app/models/main_model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.controllers.analysis.colored_box_controller import ColoredBoxController
from app.services.analysis_service import AnalysisService
from app.services.rdml_service import RDMLService
from app.services.data_store import DataStore
from app.models.workers.analysis_worker import AnalysisWorker


@dataclass
class MainState:
    file_name: str = ""
    rdml_path: str = ""


class MainModel(QObject):
    """
    Model: state + servisler + async analiz.
    UI bilmez.
    """

    analysis_busy = pyqtSignal(bool)
    analysis_progress = pyqtSignal(int, str)
    analysis_finished = pyqtSignal(bool)
    analysis_error = pyqtSignal(str)

    _start_analysis = pyqtSignal()
    _cancel_analysis = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.state = MainState()
        self.rdml_df: Optional[pd.DataFrame] = None

        self.colored_box_controller = ColoredBoxController()
        self.analysis_service = AnalysisService()

        # ---- Thread/Worker ----
        self._analysis_thread = QThread(self)
        self._worker = AnalysisWorker(self.analysis_service)
        self._worker.moveToThread(self._analysis_thread)

        # queued calls
        self._start_analysis.connect(self._worker.run)
        self._cancel_analysis.connect(self._worker.cancel)

        # worker -> model signals
        self._worker.progress.connect(self.analysis_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self.analysis_error)

        # ✅ release-grade cleanup
        self._analysis_thread.finished.connect(self._worker.deleteLater)
        self._analysis_thread.finished.connect(self._analysis_thread.deleteLater)

        self._analysis_thread.start()
        self._busy = False

    def set_file_name_from_rdml(self, file_name: str) -> None:
        if file_name.lower().endswith(".rdml"):
            file_name = file_name[:-5]
        self.state.file_name = file_name

    def reset_data(self) -> None:
        DataStore.clear()
        self.rdml_df = None
        self.state.rdml_path = ""

    def import_rdml(self, file_path: str) -> None:
        df = RDMLService.rdml_to_dataframe(file_path)
        DataStore.set_df(df)
        # ✅ PCRDataService.clear_cache() BURADA YOK (bug'a sebep oluyordu)
        self.rdml_df = df
        self.state.rdml_path = file_path

    def run_analysis(self) -> None:
        if self._busy:
            return

        # DataStore boşsa analiz başlatma (release-grade guard)
        if not DataStore.has_df():
            self.analysis_error.emit("Veri yüklenmedi. Lütfen önce RDML içe aktarın.")
            return

        self._busy = True
        self.analysis_busy.emit(True)

        if not self._analysis_thread.isRunning():
            # Thread daha önce quit edildiyse yeniden başlat
            self._analysis_thread.start()

        self._start_analysis.emit()

    def cancel_analysis(self) -> None:
        # Worker'ın cancel sonrası finished(False) emit etmesi beklenir.
        self._cancel_analysis.emit()

    def _on_worker_finished(self, success: bool) -> None:
        self._busy = False
        self.analysis_busy.emit(False)
        self.analysis_finished.emit(bool(success))

    def shutdown(self) -> None:
        """
        Uygulama kapanırken çağırılmalı.
        Controller/MainView closeEvent içinden çağırmanı öneririm.
        """
        try:
            self._cancel_analysis.emit()
        except Exception:
            pass

        if self._analysis_thread.isRunning():
            self._analysis_thread.quit()
            self._analysis_thread.wait(3000)

    # ---- Analysis config passthrough ----
    def set_checkbox_status(self, v: bool) -> None:
        self.analysis_service.set_checkbox_status(v)

    def set_referance_well(self, v: str) -> None:
        self.analysis_service.set_referance_well(v)

    def set_carrier_range(self, v: float) -> None:
        self.analysis_service.set_carrier_range(v)

    def set_uncertain_range(self, v: float) -> None:
        self.analysis_service.set_uncertain_range(v)

    def get_carrier_range(self) -> float:
        return float(self.analysis_service.config.carrier_range)

    def get_uncertain_range(self) -> float:
        return float(self.analysis_service.config.uncertain_range)
