# app\models\workers\analysis_worker.py
from __future__ import annotations
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import pandas as pd

from app.services.analysis_summary import AnalysisSummary
from app.services.summary_calc import build_summary_from_df


class AnalysisWorker(QObject):
    finished = pyqtSignal(bool, object)  # (success, summary_or_none)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, analysis_service):
        super().__init__()
        self._service = analysis_service
        self._running = False
        self._cancel_requested = False

    @pyqtSlot()
    def cancel(self) -> None:
        """
        Request cancellation. The long-running AnalysisService.run(...)
        must cooperatively check `is_cancelled()` and exit.
        """
        self._cancel_requested = True

        # Optional: if service exposes cancel(), call it.
        cancel_fn = getattr(self._service, "cancel", None)
        if callable(cancel_fn):
            try:
                cancel_fn()
            except Exception:
                return

    def _is_cancelled(self) -> bool:
        return self._cancel_requested

    def _progress(self, percent: int, message: str) -> None:
        # Cancel is requested -> don't spam progress
        if not self._cancel_requested:
            self.progress.emit(int(percent), str(message))

    @pyqtSlot()
    def run(self) -> None:
        if self._running:
            return

        self._running = True
        self._cancel_requested = False

        try:
            self._progress(1, "Analiz başlatılıyor...")

            success = self._service.run(
                progress_cb=self._progress,
                is_cancelled=self._is_cancelled,
            )

            final_df = getattr(self._service, "last_df", None)
            config = getattr(self._service, "config", None)
            use_without_reference = bool(getattr(config, "checkbox_status", False))

            summary: AnalysisSummary | None = None
            if isinstance(final_df, pd.DataFrame):
                summary = build_summary_from_df(
                    final_df,
                    use_without_reference=use_without_reference,
                )

            self._progress(100, "Tamamlandı.")
            self.finished.emit(bool(success), summary)

        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n{tb}")
            self.finished.emit(False, None)

        finally:

            self._running = False