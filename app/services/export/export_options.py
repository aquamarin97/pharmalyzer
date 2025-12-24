# app\services\export\export_options.py
# app/services/export/export_options.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ExportFormat = Literal["xlsx", "tsv"]


@dataclass(frozen=True)
class ExportOptions:
    fmt: ExportFormat = "xlsx"
    include_headers: bool = True
    preset: str = "full"               # constants/export_presets.py içinden
    include_index: bool = False        # Excel/TSV'ye index yazılsın mı?

    # TSV için
    tsv_encoding: str = "utf-8"
