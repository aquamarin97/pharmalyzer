# app/exceptions/handler.py
from __future__ import annotations

import logging
import traceback
from typing import Optional

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QMessageBox

from app.i18n import t
from .types import AppError

logger = logging.getLogger(__name__)


def _safe_format(text: str, params: Optional[dict]) -> str:
    try:
        return text.format(**(params or {}))
    except Exception:
        return text


def _is_main_gui_thread(app: QApplication) -> bool:
    # Qt tarafında UI işlemleri ana thread'de olmalı
    return QThread.currentThread() == app.thread()


def _show_message_box(
    title: str,
    message: str,
    details: Optional[str] = None,
    *,
    allow_ui: bool = True,
) -> None:
    if not allow_ui:
        return

    app = QApplication.instance()
    if app is None or app.closingDown():
        return

    # Thread güvenliği
    if not _is_main_gui_thread(app):
        return

    parent = app.activeWindow()
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    if details:
        box.setDetailedText(details)
    box.exec_()


def handle_exception(exc: BaseException, *, allow_ui: bool = True) -> int:
    """
    Exceptions için tek giriş noktası.
    - allow_ui=False ise UI göstermez; sadece loglar ve exit code döndürür.
    """
    if isinstance(exc, AppError):
        title = _safe_format(t(exc.title_key), exc.params)
        message = _safe_format(t(exc.message_key), exc.params)
        details = exc.details
        exit_code = int(exc.exit_code)

        level = getattr(logging, str(exc.log_level).upper(), logging.ERROR)
        logger.log(level, "AppError: %s", exc.message_key, exc_info=True)

        _show_message_box(title, message, details, allow_ui=allow_ui)
        return exit_code

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.critical("Unhandled exception: %s", type(exc).__name__, exc_info=True)

    _show_message_box(
        t("title_error"),
        _safe_format(
            t("error_unexpected_with_type"),
            {"type": type(exc).__name__, "msg": str(exc)},
        ),
        tb,
        allow_ui=allow_ui,
    )
    return 1
