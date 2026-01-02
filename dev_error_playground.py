# dev_error_playground.py
from __future__ import annotations

import os
import sys
import threading
import time
import logging

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

from app.i18n import init_i18n
from app.exceptions.base import install_global_exception_hook
from app.exceptions.handler import handle_exception
from app.exceptions.types import AppError, StartupError, LicenseError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Playground(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Error Playground")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Butonlara basarak hata ekranlarını test et:"))

        btn_app_error = QPushButton("AppError (ERROR) göster")
        btn_app_error.clicked.connect(self.raise_app_error)

        btn_startup = QPushButton("StartupError (CRITICAL) göster")
        btn_startup.clicked.connect(self.raise_startup_error)

        btn_license = QPushButton("LicenseError (WARNING) göster")
        btn_license.clicked.connect(self.raise_license_error)

        btn_unhandled = QPushButton("Unhandled Exception (ZeroDivision) göster")
        btn_unhandled.clicked.connect(self.raise_unhandled)

        btn_thread = QPushButton("Thread Exception tetikle (UI çıkmamalı)")
        btn_thread.clicked.connect(self.raise_thread_exception)

        btn_handle_exception = QPushButton("handle_exception() direkt çağır (UI/exit_code test)")
        btn_handle_exception.clicked.connect(self.direct_handle_exception)

        layout.addWidget(btn_app_error)
        layout.addWidget(btn_startup)
        layout.addWidget(btn_license)
        layout.addWidget(btn_unhandled)
        layout.addWidget(btn_thread)
        layout.addWidget(btn_handle_exception)

    def raise_app_error(self) -> None:
        raise AppError(
            message_key="errors.unexpected_with_type",
            params={"type": "DemoError", "msg": "Bu bir test mesajıdır."},
            details="Detay örneği: kullanıcıya opsiyonel gösterilecek.",
        )

    def raise_startup_error(self) -> None:
        raise StartupError(details="StartupError detay örneği.")

    def raise_license_error(self) -> None:
        raise LicenseError(message_key="errors.license.invalid_selected")

    def raise_unhandled(self) -> None:
        1 / 0  # sys.excepthook -> handle_exception

    def raise_thread_exception(self) -> None:
        def worker():
            time.sleep(0.2)
            raise RuntimeError("Thread içinde patladım (UI çıkmamalı, log’a gitmeli).")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def direct_handle_exception(self) -> None:
        code = handle_exception(
            LicenseError(message_key="errors.license.invalid_saved"),
            allow_ui=True,
            show_traceback=True,  # dev'de detay görmek için
        )
        logger.info("handle_exception exit_code=%s", code)


def main() -> int:
    # DEV gibi davran (traceback UI'da görünsün)
    os.environ.setdefault("ENVIRONMENT", "development")

    init_i18n()
    install_global_exception_hook()

    app = QApplication(sys.argv)
    w = Playground()
    w.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
