# app/exceptions/base.py
from __future__ import annotations
import sys
import threading
from PyQt5.QtWidgets import QApplication
from .handler import handle_exception

def _should_ignore(exc: BaseException) -> bool:
    # Normal çıkış akışları
    if isinstance(exc, (SystemExit, KeyboardInterrupt)):
        return True
    return False

def install_global_exception_hook() -> None:
    def excepthook(exc_type, exc, tb):
        if _should_ignore(exc):
            return

        # App kapanırken dialog açmaya çalışma
        app = QApplication.instance()
        if app is not None and app.closingDown():
            # Sadece loglamak istersen handler içinde UI'yi kapatacağız (aşağıda)
            handle_exception(exc)
            return

        handle_exception(exc)

    sys.excepthook = excepthook

    if hasattr(threading, "excepthook"):
        def thread_hook(args):
            if _should_ignore(args.exc_value):
                return

            app = QApplication.instance()
            if app is not None and app.closingDown():
                handle_exception(args.exc_value)
                return

            handle_exception(args.exc_value)

        threading.excepthook = thread_hook
