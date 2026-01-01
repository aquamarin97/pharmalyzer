from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"

    @classmethod
    def parse(cls, value: str | None) -> "Environment":
        raw = (value or "").strip().lower()
        if raw in {"prod", "production", "release"}:
            return cls.PRODUCTION
        if raw in {"test", "testing"}:
            return cls.TEST
        return cls.DEVELOPMENT


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


@dataclass(frozen=True, slots=True)
class AppSettings:
    app_name: str = "pharmalizer"
    environment: Environment = Environment.DEVELOPMENT

    # Features
    warmup_enabled: bool = True
    license_required: bool = False

    # Logging
    log_level: str = "INFO"
    log_dir: Path = Path("logs")
    log_to_console: bool = True

    @staticmethod
    def from_env() -> "AppSettings":
        env = Environment.parse(os.getenv("ENVIRONMENT"))

        warmup_enabled = _parse_bool(os.getenv("WARMUP"), True)
        license_required = (env == Environment.PRODUCTION)

        log_level = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
        log_dir = Path(os.getenv("LOG_DIR") or "logs")
        # Default: prod’da console kapalı, dev’de açık
        log_to_console = _parse_bool(
            os.getenv("LOG_TO_CONSOLE"),
            default=(env != Environment.PRODUCTION),
        )

        return AppSettings(
            environment=env,
            warmup_enabled=warmup_enabled,
            license_required=license_required,
            log_level=log_level,
            log_dir=log_dir,
            log_to_console=log_to_console,
        )
