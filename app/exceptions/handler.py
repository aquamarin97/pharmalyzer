# app\exceptions\handler.py
from __future__ import annotations

import os
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
    return QThread.currentThread() == app.thread()


def _is_production() -> bool:
    return (os.getenv("ENVIRONMENT") or "development").strip().lower() == "production"


def _normalize_level(level) -> str:
    # Enum da gelebilir, str da gelebilir
    if hasattr(level, "value"):
        level = level.value
    return str(level).strip().lower()


def _icon_for_level(level) -> QMessageBox.Icon:
    lvl = _normalize_level(level)
    if lvl == "warning":
        return QMessageBox.Warning
    if lvl == "info":
        return QMessageBox.Information
    return QMessageBox.Critical


def _show_message_box(
    title: str,
    message: str,
    *,
    icon: QMessageBox.Icon,
    details: Optional[str] = None,
    allow_ui: bool = True,
) -> None:
    if not allow_ui:
        return

    app = QApplication.instance()
    if app is None or app.closingDown():
        return
    if not _is_main_gui_thread(app):
        return

    parent = app.activeWindow()
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(message)

    # details verilirse Qt otomatik "Show Details" butonu ekler.
    if details:
        box.setDetailedText(details)

    box.exec_()


def handle_exception(
    exc: BaseException,
    *,
    allow_ui: bool = True,
    show_traceback: bool = False,  # dev için True, prod için False
) -> int:
    """
    Exceptions için tek giriş noktası.
    - allow_ui=False => sadece log + exit code
    - show_traceback=True => UI'da stack trace "details" göster (sadece dev)
    """
    # SystemExit yakalanırsa exit code'a çevir
    if isinstance(exc, SystemExit):
        code = exc.code
        return int(code) if isinstance(code, int) else 0

    is_prod = _is_production()

    # ---- Controlled app errors ----
    if isinstance(exc, AppError):
        title = _safe_format(t(exc.title_key), dict(exc.params))
        message = _safe_format(t(exc.message_key), dict(exc.params))
        exit_code = int(getattr(exc, "exit_code", 1))

        py_level = getattr(logging, str(getattr(exc, "log_level", "error")).upper(), logging.ERROR)

        # log: her zaman detaylı
        if getattr(exc, "cause", None) is not None:
            logger.log(py_level, "AppError: %s", exc.message_key, exc_info=exc.cause)
        else:
            logger.log(py_level, "AppError: %s", exc.message_key, exc_info=True)

        # UI details: prod’da asla gösterme
        details: Optional[str] = None
        if not is_prod and show_traceback:
            details = exc.details or "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )

        _show_message_box(
            title,
            message,
            icon=_icon_for_level(getattr(exc, "log_level", "error")),
            details=details,
            allow_ui=allow_ui,
        )
        return exit_code

    # ---- Unhandled exceptions ----
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.critical("Unhandled exception: %s", type(exc).__name__, exc_info=True)

    title = t("errors.title")

    if is_prod:
        # Release: teknik detay ve İngilizce exception msg göstermeyelim
        message = t("errors.unexpected")
        details = None
    else:
        # Dev: tip + msg göstermek OK, details de gösterilebilir
        message = _safe_format(
            t("errors.unexpected_with_type"),
            {"type": type(exc).__name__, "msg": str(exc)},
        )
        details = tb if show_traceback else None

    _show_message_box(
        title,
        message,
        icon=QMessageBox.Critical,
        details=details,
        allow_ui=allow_ui,
    )
    return 1
