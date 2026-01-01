from __future__ import annotations

import sys
from pathlib import Path


def _runtime_base_dir() -> Path:
    """
    - PyInstaller: sys._MEIPASS
    - Normal: project working dir (or script dir fallback)
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    # Daha stabil: çalıştırılan script’in bulunduğu yer
    return Path(sys.argv[0]).resolve().parent


def resource_path(relative_path: str) -> str:
    base = _runtime_base_dir()
    # relative_path zaten absolute ise bozmadan dön
    p = Path(relative_path)
    if p.is_absolute():
        return str(p)
    return str(base / relative_path)
