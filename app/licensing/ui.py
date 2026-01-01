# app\licensing\ui.py
from __future__ import annotations

import os
from typing import Optional

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.constants.app_text_key import TextKey
from app.i18n import t
from app.licensing.manager import read_saved_license_path, save_license_path
from app.licensing.validator import validate_license_file


def ensure_license_or_exit(app: Optional[QApplication] = None) -> None:
    """
    Lisans doğrulanamazsa kullanıcıya UI ile sorar, geçerli lisans alamazsa uygulamayı kapatır.
    """
    if app is None:
        app = QApplication.instance()

    parent = app.activeWindow() if app is not None else None

    saved_path = read_saved_license_path()
    if saved_path and os.path.exists(saved_path) and validate_license_file(saved_path):
        return

    if saved_path:
        QMessageBox.warning(
            parent,
            t(TextKey.TITLE_LICENSE_ERROR),
            t(TextKey.MSG_INVALID_SAVED),
        )

    license_file, _ = QFileDialog.getOpenFileName(
        parent,
        caption=t(TextKey.TITLE_SELECT_FILE),
        directory="",
        filter=t(TextKey.FILTER_LICENSE_FILES),
    )

    if license_file and validate_license_file(license_file):
        try:
            save_license_path(license_file)
            return
        except Exception as e:
            QMessageBox.critical(
                parent,
                t(TextKey.TITLE_ERROR),
                f"{t(TextKey.MSG_PATH_SAVE_FAILED)} {e}",
            )
            raise SystemExit(1)

    QMessageBox.critical(
        parent,
        t(TextKey.TITLE_LICENSE_ERROR),
        t(TextKey.MSG_INVALID_SELECTED),
    )
    raise SystemExit(1)
