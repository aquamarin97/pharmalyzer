# app/logging/setup.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app_name: str = "pharmalizer") -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        f"logs/{app_name}.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
