# app/logging/setup.py
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app_name: str = "pharmalizer") -> None:
    root = logging.getLogger()

    # setup iki kere çağrılırsa handler çoğalmasın
    if getattr(root, "_pharmalizer_logging_configured", False):
        return
    root._pharmalizer_logging_configured = True

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    os.makedirs("logs", exist_ok=True)

    file_handler = RotatingFileHandler(
        os.path.join("logs", f"{app_name}.log"),
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Dev için console; prod'da kapatılabilir
    if os.getenv("ENVIRONMENT") != "production":
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(fmt)
        root.addHandler(console)
