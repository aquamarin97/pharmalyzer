# app\services\export\export_service.py
# app/services/export/export_service.py

from __future__ import annotations

import pandas as pd

from app.constants.export_presets import EXPORT_PRESETS
from app.services.export.export_options import ExportOptions
from app.services.export.exporters.excel_exporter import ExcelExporter
from app.services.export.exporters.tsv_exporter import TSVExporter


class ExportService:
    def __init__(self):
        self._excel = ExcelExporter()
        self._tsv = TSVExporter()

    def export_dataframe(self, df: pd.DataFrame, file_path: str, options: ExportOptions) -> None:
        if df is None or df.empty:
            raise ValueError("Export edilecek DataFrame boş.")

        df2 = self._apply_preset(df, options.preset)

        if options.fmt == "xlsx":
            self._excel.export(
                df2,
                file_path,
                include_headers=options.include_headers,
                include_index=options.include_index,
            )
            return

        if options.fmt == "tsv":
            self._tsv.export(
                df2,
                file_path,
                include_headers=options.include_headers,
                include_index=options.include_index,
                encoding=options.tsv_encoding,
            )
            return

        raise ValueError(f"Desteklenmeyen export formatı: {options.fmt}")

    def _apply_preset(self, df: pd.DataFrame, preset: str) -> pd.DataFrame:
        if preset not in EXPORT_PRESETS:
            raise ValueError(f"Bilinmeyen export preset: {preset}")

        cols = EXPORT_PRESETS[preset]
        if cols is None:
            return df.copy()

        # df'de olmayan kolonları sessizce atla (stabil)
        existing = [c for c in cols if c in df.columns]
        if not existing:
            raise ValueError(f"Preset '{preset}' için DataFrame'de hiçbir kolon bulunamadı.")

        return df[existing].copy()
