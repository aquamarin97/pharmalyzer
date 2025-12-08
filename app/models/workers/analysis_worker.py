# app/models/workers/analysis_worker.py
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class AnalysisWorker(QObject):
    """
    Ağır analiz işini UI thread'den ayırmak için worker.
    NOT: analyze_button QObject değilse bile sorun yok; önemli olan run'ın worker thread'de çalışması.
    """
    finished = pyqtSignal(bool)       # success
    error = pyqtSignal(str)           # exception mesajı (opsiyonel)

    def __init__(self, analyze_button):
        super().__init__()
        self._analyze_button = analyze_button

    @pyqtSlot()
    def run(self):
        try:
            success = self._analyze_button.analyze()
            self.finished.emit(bool(success))
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)
