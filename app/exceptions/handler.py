# app\exceptions\handler.py
from __future__ import annotations
import logging
import traceback
from typing import Optional

from PyQt5.QtWidgets import QApplication, QMessageBox
from app.i18n import t  # Translator.t alias
from .types import AppError

logger = logging.getLogger(__name__)

def _safe_format(text: str, params: dict) -> str:
    # params yoksa düz döndür, varsa format dene
    try:
        return text.format(**(params or {}))
    except Exception:
        return text

def _show_message_box(title: str, message: str, details: Optional[str] = None) -> None:
    app = QApplication.instance()
    if app is None or app.closingDown():
        return
    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    if details:
        box.setDetailedText(details)
    box.exec_()

def handle_exception(exc: BaseException) -> int:
    if isinstance(exc, AppError):
        title = _safe_format(t(exc.title_key), exc.params)
        message = _safe_format(t(exc.message_key), exc.params)
        details = exc.details
        exit_code = exc.exit_code

        level = getattr(logging, exc.log_level.upper(), logging.ERROR)
        logger.log(level, "AppError: %s", exc.message_key, exc_info=True)

        _show_message_box(title, message, details)
        return int(exit_code)

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.critical("Unhandled exception", exc_info=True)
    _show_message_box(
        t("title_error"),
        _safe_format(t("error_unexpected_with_type"), {"type": type(exc).__name__, "msg": str(exc)}),
        tb,
    )
    return 1
