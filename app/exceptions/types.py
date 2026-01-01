from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(slots=True)
class AppError(Exception):
    """
    Uygulama içi kontrollü hatalar için standart exception.
    - title_key / message_key: i18n key
    - params: format parametreleri
    - details: (opsiyonel) UI'da "Details" bölümünde gösterilebilir
    - exit_code: process exit code
    - log_level: log severity
    - cause: asıl exception (exception chaining için)
    """
    title_key: str = "errors.title"
    message_key: str = "errors.unexpected"
    exit_code: int = 1
    log_level: LogLevel = LogLevel.ERROR

    details: Optional[str] = None
    params: Mapping[str, Any] = field(default_factory=dict)
    cause: Optional[BaseException] = None

    def __post_init__(self) -> None:
        # Exception message olarak message_key kalsın (debug için)
        super().__init__(self.message_key)

    @classmethod
    def wrap(
        cls,
        exc: BaseException,
        *,
        title_key: Optional[str] = None,
        message_key: Optional[str] = None,
        details: Optional[str] = None,
        params: Optional[Mapping[str, Any]] = None,
        exit_code: Optional[int] = None,
        log_level: Optional[LogLevel] = None,
    ) -> "AppError":
        """
        Harici bir exception'ı AppError'a çevirir.
        """
        inst = cls(
            title_key=title_key or cls.title_key,
            message_key=message_key or cls.message_key,
            details=details,
            params=params or {},
            cause=exc,
        )
        if exit_code is not None:
            inst.exit_code = exit_code
        if log_level is not None:
            inst.log_level = log_level
        return inst


@dataclass(slots=True)
class StartupError(AppError):
    title_key: str = "errors.startup.title"
    message_key: str = "errors.startup.failed"
    exit_code: int = 2
    log_level: LogLevel = LogLevel.CRITICAL


@dataclass(slots=True)
class LicenseError(AppError):
    title_key: str = "errors.license.title"
    message_key: str = "errors.license.missing"
    exit_code: int = 3
    log_level: LogLevel = LogLevel.WARNING
