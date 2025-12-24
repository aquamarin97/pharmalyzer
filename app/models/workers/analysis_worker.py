from __future__ import annotations
import time

import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class AnalysisWorker(QObject):
    finished = pyqtSignal(bool)
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
                logger.exception("AnalysisService.cancel() failed")

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

        t0 = time.perf_counter()
        logger.info("[PERF] Worker.run started")

        try:
            self._progress(1, "Analiz başlatılıyor...")

            success = self._service.run(
                progress_cb=self._progress,
                is_cancelled=self._is_cancelled,
            )

            self._progress(100, "Tamamlandı.")
            self.finished.emit(bool(success))

        except Exception as e:
            tb = traceback.format_exc()
            logger.error("Analysis failed: %s\n%s", e, tb)
            self.error.emit(str(e))
            self.finished.emit(False)

        finally:
            t1 = time.perf_counter()
            logger.info("[PERF] Worker.run total %.0f ms", (t1 - t0) * 1000)
            self._running = False
