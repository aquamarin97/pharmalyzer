from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.controllers.analysis.colored_box_controller import ColoredBoxController
from app.services.analysis_service import AnalysisService
from app.services.rdml_service import RDMLService
from app.services.data_store import DataStore
from app.services.pcr_data_service import PCRDataService
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
        self.data_manager = PCRDataService()

        # --- Thread / Worker ---
        self._analysis_thread = QThread(self)
        self._worker = AnalysisWorker(self.analysis_service)
        self._worker.moveToThread(self._analysis_thread)

        # queued calls
        self._start_analysis.connect(self._worker.run)
        self._cancel_analysis.connect(self._worker.cancel)

        # worker -> model
        self._worker.progress.connect(self.analysis_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self.analysis_error)

        # ❗ SADECE worker silinir, thread deleteLater YOK
        self._analysis_thread.finished.connect(self._worker.deleteLater)

        self._analysis_thread.start()
        self._busy = False

    # ---------------- State ----------------
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
        PCRDataService.clear_cache()
        self.rdml_df = df
        self.state.rdml_path = file_path

    # ---------------- Analysis ----------------
    def run_analysis(self) -> None:
        if self._busy:
            return

        self._busy = True
        self.analysis_busy.emit(True)

        if not self._analysis_thread.isRunning():
            self._analysis_thread.start()

        self._start_analysis.emit()

    def cancel_analysis(self) -> None:
        self._cancel_analysis.emit()

    def _on_worker_finished(self, success: bool) -> None:
        self._busy = False
        self.analysis_busy.emit(False)
        self.analysis_finished.emit(bool(success))

    # ---------------- Shutdown ----------------
    def shutdown(self) -> None:
        """
        Release-grade güvenli kapanış.
        QThread deleteLater kullanılmadığı için RuntimeError oluşmaz.
        """
        try:
            self._cancel_analysis.emit()
        except Exception:
            pass

        try:
            self._analysis_thread.quit()
            self._analysis_thread.wait(3000)
        except RuntimeError:
            # Thread objesi zaten Qt tarafından silinmişse sessiz geç
            pass

    # ---------------- Config passthrough ----------------
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
