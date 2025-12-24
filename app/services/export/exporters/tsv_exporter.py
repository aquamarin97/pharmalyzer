# app\services\export\exporters\tsv_exporter.py
# app/services/export/exporters/tsv_exporter.py

from __future__ import annotations

import pandas as pd


class TSVExporter:
    def export(
        self,
        df: pd.DataFrame,
        file_path: str,
        *,
        include_headers: bool,
        include_index: bool,
        encoding: str,
    ) -> None:
        if df is None or df.empty:
            raise ValueError("Export edilecek DataFrame boş.")
        if not file_path.lower().endswith(".tsv"):
            raise ValueError("TSV export için dosya uzantısı .tsv olmalı.")

        df.to_csv(
            file_path,
            sep="\t",
            index=include_index,
            header=include_headers,
            encoding=encoding,
        )
