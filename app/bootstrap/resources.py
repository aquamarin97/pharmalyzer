# pharmalizer_v2/app/bootstrap/resources.py
import os
import sys


def resource_path(relative_path: str) -> str:
    """
    Geliştirme veya paketlenmiş (PyInstaller) ortamda resource path çözümleme.
    """
    # PyInstaller runtime
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]
    return relative_path
