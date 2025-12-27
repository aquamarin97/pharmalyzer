# app\exceptions\base.py
# app/exceptions/base.py
from __future__ import annotations

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
    # UI sadece main thread'de güvenli
    return QThread.currentThread() == app.thread()


def install_global_exception_hook() -> None:
    def excepthook(exc_type, exc, tb):
        if _should_ignore(exc):
            return
        app = QApplication.instance()
        handle_exception(exc, allow_ui=_can_show_ui(app))

    sys.excepthook = excepthook

    if hasattr(threading, "excepthook"):
        def thread_hook(args):
            if _should_ignore(args.exc_value):
                return
            app = QApplication.instance()
            # Thread exception'larında genelde UI gösterme!
            handle_exception(args.exc_value, allow_ui=_can_show_ui(app))

        threading.excepthook = thread_hook
