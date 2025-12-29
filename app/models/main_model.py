# app\models\main_model.py
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
    Thread-per-analysis: her analizde yeni QThread + worker.
    """

    analysis_busy = pyqtSignal(bool)
    analysis_progress = pyqtSignal(int, str)
    analysis_finished = pyqtSignal(bool)
    analysis_summary_ready = pyqtSignal(object)
    analysis_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.state = MainState()
        self.rdml_df: Optional[pd.DataFrame] = None

        self.colored_box_controller = ColoredBoxController()
        self.analysis_service = AnalysisService()
        self.data_manager = PCRDataService()

        # Thread-per-analysis state
        self._analysis_thread: Optional[QThread] = None
        self._worker: Optional[AnalysisWorker] = None
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

    # ---------------- Analysis (thread-per-run) ----------------
    def run_analysis(self) -> None:
        if self._busy:
            return

        self._busy = True
        self.analysis_busy.emit(True)

        self._start_new_analysis_thread()

    def cancel_analysis(self) -> None:
        # cooperative cancel
        if self._worker is not None:
            try:
                self._worker.cancel()
            except Exception:
                pass

    def _start_new_analysis_thread(self) -> None:
        # Defensive: önce eski kaynaklar varsa temizle
        self._cleanup_analysis_thread(non_blocking=True)

        thread = QThread(self)
        worker = AnalysisWorker(self.analysis_service)
        worker.moveToThread(thread)

        # signals
        worker.progress.connect(self.analysis_progress)
        worker.error.connect(self.analysis_error)
        worker.finished.connect(self._on_worker_finished)

        # thread start -> worker.run (queued)
        thread.started.connect(worker.run)

        # yaşam döngüsü: thread bitince worker silinsin
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._analysis_thread = thread
        self._worker = worker

        thread.start()

    def _on_worker_finished(self, success: bool, summary) -> None:
        # UI'ye durum bildir (önce)
        self._busy = False
        self.analysis_busy.emit(False)
        self.analysis_finished.emit(bool(success))
        if summary is not None:
            self.analysis_summary_ready.emit(summary)
        # Thread'i kapat (non-blocking)
        self._cleanup_analysis_thread(non_blocking=True)

    def _cleanup_analysis_thread(self, *, non_blocking: bool) -> None:
        """
        non_blocking=True:
          - quit çağırır, beklemez (UI donmasın)
        non_blocking=False:
          - quit + wait ile kapanışı garanti eder (shutdown için)
        """
        thread = self._analysis_thread
        if thread is None:
            self._worker = None
            return

        try:
            if thread.isRunning():
                thread.quit()
                if not non_blocking:
                    thread.wait(3000)
        except RuntimeError:
            # Qt objesi zaten silinmiş olabilir
            pass

        # referansları bırak
        self._analysis_thread = None
        self._worker = None

    # ---------------- Shutdown ----------------
    def shutdown(self) -> None:
        """
        Release-grade kapanış:
        - cancel iste
        - thread varsa kapanmasını garanti et
        """
        try:
            self.cancel_analysis()
        except Exception:
            pass

        self._cleanup_analysis_thread(non_blocking=False)

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
