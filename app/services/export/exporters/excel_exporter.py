# app/services/export/exporters/excel_exporter.py

from __future__ import annotations

import pandas as pd


class ExcelExporter:
    def export(self, df: pd.DataFrame, file_path: str, *, include_headers: bool, include_index: bool) -> None:
        if df is None or df.empty:
            raise ValueError("Export edilecek DataFrame boş.")
        if not file_path.lower().endswith(".xlsx"):
            raise ValueError("Excel export için dosya uzantısı .xlsx olmalı.")

        df.to_excel(file_path, index=include_index, header=include_headers)
