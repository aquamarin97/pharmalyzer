# app/exceptions/types.py
from __future__ import annotations
from typing import Optional, Dict, Any

class AppError(Exception):
    title_key: str = "errors.title"
    message_key: str = "errors.unexpected"
    exit_code: int = 1
    log_level: str = "error"

    def __init__(
        self,
        *,
        message_key: Optional[str] = None,
        title_key: Optional[str] = None,
        details: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message_key or self.message_key)
        self.title_key = title_key or self.title_key
        self.message_key = message_key or self.message_key
        self.details = details
        self.params = params or {}

class StartupError(AppError):
    title_key = "errors.startup.title"
    message_key = "errors.startup.failed"
    exit_code = 2
    log_level = "critical"

class LicenseError(AppError):
    title_key = "errors.license.title"
    message_key = "errors.license.missing"
    exit_code = 3
    log_level = "warning"
