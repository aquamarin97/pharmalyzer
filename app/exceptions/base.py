from __future__ import annotations

import os
import sys
import threading

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from .handler import handle_exception


def _should_ignore(exc: BaseException) -> bool:
    return isinstance(exc, (SystemExit, KeyboardInterrupt))


def _can_show_ui(app: QApplication | None) -> bool:
    if app is None:
        return False
    if app.closingDown():
        return False
    return QThread.currentThread() == app.thread()


def _should_show_traceback() -> bool:
    # prod'da UI'da traceback gösterme
    env = (os.getenv("ENVIRONMENT") or "development").strip().lower()
    return env != "production"


def install_global_exception_hook() -> None:
    show_tb = _should_show_traceback()

    def excepthook(exc_type, exc, tb):
        if _should_ignore(exc):
            return
        app = QApplication.instance()
        handle_exception(exc, allow_ui=_can_show_ui(app), show_traceback=show_tb)

    sys.excepthook = excepthook

    if hasattr(threading, "excepthook"):
        def thread_hook(args):
            if _should_ignore(args.exc_value):
                return
            # Thread exception'larında UI göstermeyi kapat (daha güvenli)
            handle_exception(args.exc_value, allow_ui=False, show_traceback=show_tb)

        threading.excepthook = thread_hook
