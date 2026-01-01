from __future__ import annotations

import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    app_name: str
    level: int = logging.INFO
    log_dir: Path = Path("logs")
    to_console: bool = True
    max_bytes: int = 2_000_000
    backup_count: int = 5


_CONFIGURED_FLAG = "_pharmalizer_logging_configured_v2"


def setup_logging(cfg: LoggingConfig) -> None:
    """
    Idempotent logging setup. Safe to call multiple times.
    """
    root = logging.getLogger()

    if getattr(root, _CONFIGURED_FLAG, False):
        return
    setattr(root, _CONFIGURED_FLAG, True)

    root.setLevel(cfg.level)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    log_file = cfg.log_dir / f"{cfg.app_name}.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=cfg.max_bytes,
        backupCount=cfg.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(cfg.level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    if cfg.to_console:
        console = logging.StreamHandler()
        console.setLevel(cfg.level)
        console.setFormatter(fmt)
        root.addHandler(console)


def reset_logging_for_tests() -> None:
    """
    Testlerde handler temizliği için. Prod kodda çağırma.
    """
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass
    if hasattr(root, _CONFIGURED_FLAG):
        delattr(root, _CONFIGURED_FLAG)
