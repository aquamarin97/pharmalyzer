from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd


@dataclass
class ColoredBoxConfig:
    homozigot_well: str = "F12"
    heterozigot_well: str = "G12"
    ntc_well: str = "H12"
    use_statistic_column: bool = True
    carrier_threshold: float = 0.5999  # istersen burayı modelden beslersin


class ColoredBoxService:
    STAT_COL = "İstatistik Oranı"
    REF_COL = "Standart Oranı"
    WELL_COL = "Kuyu No"
    WARN_COL = "Uyarı"

    def compute(self, df: Optional[pd.DataFrame], cfg: ColoredBoxConfig) -> List[bool]:
        if df is None or df.empty:
            return [False, False, False]

        needed = {self.WELL_COL, self.WARN_COL}
        col = self.STAT_COL if cfg.use_statistic_column else self.REF_COL
        needed.add(col)

        missing = [c for c in needed if c not in df.columns]
        if missing:
            # eksik kolon varsa güvenli fallback
            return [False, False, False]

        return [
            self._check_homozigot(df, col, cfg.homozigot_well, cfg.carrier_threshold),
            self._check_heterozigot(df, col, cfg.heterozigot_well, cfg.carrier_threshold),
            self._check_ntc(df, cfg.ntc_well),
        ]

    def _check_homozigot(self, df: pd.DataFrame, col: str, well: str, th: float) -> bool:
        row = df[df[self.WELL_COL] == well]
        if row.empty:
            return False
        try:
            return float(row[col].iloc[0]) >= th
        except (TypeError, ValueError):
            return False

    def _check_heterozigot(self, df: pd.DataFrame, col: str, well: str, th: float) -> bool:
        row = df[df[self.WELL_COL] == well]
        if row.empty:
            return False
        try:
            return float(row[col].iloc[0]) < th
        except (TypeError, ValueError):
            return False

    def _check_ntc(self, df: pd.DataFrame, well: str) -> bool:
        row = df[df[self.WELL_COL] == well]
        if row.empty:
            return False
        return row[self.WARN_COL].iloc[0] == "Yetersiz DNA"
