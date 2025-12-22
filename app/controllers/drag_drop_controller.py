# app\controllers\drag_drop_controller.py
# app/controllers/drag_drop_controller.py

import os
from PyQt5.QtCore import QObject, QEvent, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QLabel


class DragDropController(QObject):
    """
    Drag & Drop işlevselliğini tamamen yöneten bağımsız Controller.
    Eski DragDropHandler'ın tüm mantığı buraya taşındı ve düzeltildi.
    """
    drop_completed = pyqtSignal(bool, str, str, str)
    # success, rdml_path, file_name, message

    def __init__(self, label: QLabel):
        super().__init__()
        self.label = label
        self._setup_drag_drop()

    def _setup_drag_drop(self):
        """Drag & drop'ı etkinleştirir ve event filter'ı kurar."""
        self.label.setAcceptDrops(True)
        self.label.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Tüm drag & drop olaylarını burada yakala."""
        if watched != self.label:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.DragEnter:
            self._handle_drag_enter(event)
            return True  # Olayı tükettik

        elif event.type() == QEvent.Drop:
            self._handle_drop(event)
            return True  # Olayı tükettik

        return super().eventFilter(watched, event)

    def _handle_drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  # veya event.accept()
        else:
            event.ignore()
    def _handle_drop(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            self.drop_completed.emit(False, "", "", "Geçersiz dosya.")
            return

        urls = event.mimeData().urls()
        if len(urls) != 1:
            self.drop_completed.emit(False, "", "", "Lütfen yalnızca bir dosya bırakın.")
            return

        file_path = urls[0].toLocalFile()
        file_name = os.path.basename(file_path)

        if not file_path.lower().endswith(".rdml"):
            self.drop_completed.emit(False, "", file_name, "Sadece .rdml dosyalarına izin veriliyor.")
            return

        # CMV: burada RDML zip/xml extract etmiyoruz.
        # Sadece rdml path'i yukarıya iletiyoruz.
        if not os.path.exists(file_path):
            self.drop_completed.emit(False, "", file_name, "Dosya bulunamadı.")
            return

        self.drop_completed.emit(True, file_path, file_name, file_name)

    def manual_drop(self, file_path: str, file_name: str = None):
        file_name = file_name or os.path.basename(file_path)

        if not file_path.lower().endswith(".rdml"):
            self.drop_completed.emit(False, "", file_name, "Sadece .rdml dosyalarına izin veriliyor.")
            return

        if not os.path.exists(file_path):
            self.drop_completed.emit(False, "", file_name, "Dosya bulunamadı.")
            return

        self.drop_completed.emit(True, file_path, file_name, file_name)
