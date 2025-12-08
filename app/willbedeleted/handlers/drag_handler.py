import os

from PyQt5.QtCore import QEvent, QObject, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QLabel

from app.willbedeleted.utils.file_utils.rdml_processor import UtilsRDMLProcessor


class DragDropHandler(QObject):
    dropCompleted = pyqtSignal(bool, str, str)  # İşlem durumu ve dosya yolu sinyali

    def __init__(self, label: QLabel):
        super().__init__()
        self.label = label

    def setup(self):
        self.label.setAcceptDrops(True)
        self.label.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.label:
            if event.type() == QEvent.DragEnter:
                return self._drag_enter_event(event)
            elif event.type() == QEvent.Drop:
                return self._drop_event(event)
        return False

    def _drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
        return True

    def _drop_event(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) > 1:
                self.label.setText("Lütfen yalnızca bir dosya bırakın.")
                self.dropCompleted.emit(False, "")
                return False

            file_path = urls[0].toLocalFile()
            if file_path.endswith(".rdml"):
                success, extracted_path = UtilsRDMLProcessor.take_rdml_file_path(
                    file_path
                )
                file_name = os.path.basename(file_path)
                if success:
                    self.label.setText(file_name)
                else:
                    self.label.setText("RDML dosyasından XML çıkarılamadı.")

                self.dropCompleted.emit(success, extracted_path, file_name)
                return success
            else:
                self.label.setText("Sadece .rdml dosyalarına izin veriliyor.")
                self.dropCompleted.emit(False, "", "")
                return False
        return False
    def _drop_event_manual(self, file_path, file_name):
        if file_path.endswith(".rdml"):
            success, extracted_path = UtilsRDMLProcessor.take_rdml_file_path(file_path)
            if success:
                self.label.setText(file_name)
            else:
                self.label.setText("RDML dosyasından XML çıkarılamadı.")
            self.dropCompleted.emit(success, extracted_path, file_name)
        else:
            self.label.setText("Sadece .rdml dosyalarına izin veriliyor.")
            self.dropCompleted.emit(False, "", "")
