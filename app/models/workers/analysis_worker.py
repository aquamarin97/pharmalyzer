# app\models\workers\analysis_worker.py
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class AnalysisWorker(QObject):
    """
    Ağır analiz işini UI thread'den ayırmak için worker.
    Worker sadece "callable" bir iş çalıştırır; UI bilmez.
    """

    finished = pyqtSignal(bool)  # success
    error = pyqtSignal(str)

    def __init__(self, analysis_service):
        super().__init__()
        self._service = analysis_service

    @pyqtSlot()
    def run(self):
        try:
            # AnalysisService.run() -> bool
            success = self._service.run()
            self.finished.emit(bool(success))
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)
