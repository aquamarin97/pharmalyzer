# app\controllers\app\drag_drop_controller.py
# app/controllers/app/drag_drop_controller.py
from __future__ import annotations

import os
import logging
from typing import Tuple
from app.i18n import t

from PyQt5.QtCore import QObject, QEvent, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QLabel

logger = logging.getLogger(__name__)


class DragDropController(QObject):
    """
    Drag & Drop işlevselliğini yöneten controller.

    Sorumluluk:
      - label üzerinde drag/drop eventlerini yakalamak
      - yalnızca 1 adet .rdml dosyasını doğrulamak
      - sonucu sinyal ile üst katmana iletmek

    NOT: RDML parse / DataStore gibi işlemler burada YOK.
    """

    # success, rdml_path, file_name, message
    drop_completed = pyqtSignal(bool, str, str, str)

    def __init__(self, label: QLabel):
        super().__init__()
        self.label = label
        self._setup_drag_drop()

    def _setup_drag_drop(self) -> None:
        self.label.setAcceptDrops(True)
        self.label.installEventFilter(self)

    # ---------------- Qt event filter ----------------
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched != self.label:
            return super().eventFilter(watched, event)

        et = event.type()

        if et == QEvent.DragEnter and isinstance(event, QDragEnterEvent):
            self._handle_drag_enter(event)
            return True

        if et == QEvent.Drop and isinstance(event, QDropEvent):
            self._handle_drop(event)
            return True

        return super().eventFilter(watched, event)

    # ---------------- Handlers ----------------
    def _handle_drag_enter(self, event: QDragEnterEvent) -> None:
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        urls = event.mimeData().urls()
        if len(urls) != 1:
            event.ignore()
            return

        file_path = urls[0].toLocalFile()
        ok, _, _ = self._validate_rdml_path(file_path)
        if ok:
            event.acceptProposedAction()
        else:
            event.ignore()

    def _handle_drop(self, event: QDropEvent) -> None:
        if not event.mimeData().hasUrls():
            self.drop_completed.emit(
    False,
    "",
    "",
    t("dragdrop.errors.invalid_file"),
)
            return

        urls = event.mimeData().urls()
        if len(urls) != 1:
            self.drop_completed.emit(False, "", "", "Lütfen yalnızca bir dosya bırakın.")
            return

        file_path = urls[0].toLocalFile()
        ok, file_name, err = self._validate_rdml_path(file_path)
        if not ok:
            self.drop_completed.emit(False, "", file_name, err)
            return

        self.drop_completed.emit(
    True,
    file_path,
    file_name,
    t("dragdrop.ready", file_name=file_name),
)


    # ---------------- Public API ----------------
    def manual_drop(self, file_path: str, file_name: str | None = None) -> None:
        # file_name dışarıdan gelirse de validate içinde normalize edelim
        ok, inferred_name, err = self._validate_rdml_path(file_path)
        if not ok:
            self.drop_completed.emit(False, "", file_name or inferred_name, err)
            return

        final_name = file_name or inferred_name
        self.drop_completed.emit(True, file_path, final_name, f"Hazır: {final_name}")

    # ---------------- Validation ----------------
    def _validate_rdml_path(self, file_path: str) -> Tuple[bool, str, str]:
        """
        Returns: (ok, file_name, error_message)
        """
        try:
            file_name = os.path.basename(file_path) if isinstance(file_path, str) else ""

            if not isinstance(file_path, str) or not file_path.strip():
                return False, file_name, t("dragdrop.errors.invalid_path")

            if not file_path.lower().endswith(".rdml"):
                # Drag-enter sırasında da kullanılacağı için kısa mesaj
                return False, file_name, t("dragdrop.errors.extension")

            if not os.path.exists(file_path):
                return False, file_name, t("dragdrop.errors.not_found")

            return True, file_name, ""
        except Exception as e:
            # ✅ Loglar ana uygulamada gösterilmeyecek; i18n'e taşımıyoruz
            logger.exception("DragDrop validate failed: %s", e)
            return False, "", t("dragdrop.errors.validation_failed")