# app\services\regression_plot_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


@dataclass(frozen=True)
class ScatterSeries:
    label: str
    x: np.ndarray
    y: np.ndarray
    wells: np.ndarray  # hover için "Kuyu No"


@dataclass(frozen=True)
class SafeBand:
    x_sorted: np.ndarray
    upper: np.ndarray
    lower: np.ndarray


@dataclass(frozen=True)
class RegressionLine:
    x_sorted: np.ndarray
    y_pred_sorted: np.ndarray


@dataclass(frozen=True)
class RegressionPlotData:
    safe_band: SafeBand
    reg_line: RegressionLine
    series: List[ScatterSeries]


class RegressionPlotService:
    """
    df -> regression çizim datası üretir.
    PyQtGraph yok.
    """

    REQUIRED = ["hex_end_rfu", "fam_end_rfu", "Kuyu No", "Nihai Sonuç", "Regresyon"]
    ALLOWED_CLASSES = ["Sağlıklı", "Taşıyıcı", "Belirsiz"]

    @staticmethod
    def build(df: pd.DataFrame) -> RegressionPlotData:
        RegressionPlotService._validate(df)

        work = df.copy()
        work.dropna(subset=["hex_end_rfu", "fam_end_rfu", "Kuyu No", "Nihai Sonuç"], inplace=True)

        mask = work["Nihai Sonuç"].isin(RegressionPlotService.ALLOWED_CLASSES)

        # Model "Güvenli Bölge" satırlarıyla fit oluyor (legacy preprocess)
        train = work.loc[mask].copy()
        train = train[train["Regresyon"] == "Güvenli Bölge"].copy()

        if train.empty:
            # hiç safe yoksa: boş data döndürmek daha iyi
            empty = np.array([], dtype=float)
            return RegressionPlotData(
                safe_band=SafeBand(empty, empty, empty),
                reg_line=RegressionLine(empty, empty),
                series=[],
            )

        fam_train = pd.to_numeric(train["fam_end_rfu"], errors="coerce").astype(float).to_numpy()
        hex_train = pd.to_numeric(train["hex_end_rfu"], errors="coerce").astype(float).to_numpy()

        X = fam_train.reshape(-1, 1)
        y = hex_train

        lr = LinearRegression()
        lr.fit(X, y)

        # çizimde kullanılacak tüm noktalar
        fam_all = work.loc[mask, "fam_end_rfu"].astype(float).to_numpy()
        hex_all = work.loc[mask, "hex_end_rfu"].astype(float).to_numpy()
        wells_all = work.loc[mask, "Kuyu No"].astype(str).to_numpy()
        sonuc_all = work.loc[mask, "Nihai Sonuç"].astype(str).to_numpy()

        # pred ve safe band sigma (train residuals)
        y_pred_train = lr.predict(X)
        residuals = y - y_pred_train
        sigma = float(np.std(residuals)) if len(residuals) else 0.0

        x_all = fam_all.reshape(-1, 1)
        y_pred_all = lr.predict(x_all)

        safe_upper = y_pred_all + 2.2 * sigma
        safe_lower = y_pred_all - 2.2 * sigma

        sort_idx = np.argsort(fam_all)
        xf = fam_all[sort_idx]

        safe_band = SafeBand(
            x_sorted=xf,
            upper=safe_upper[sort_idx],
            lower=safe_lower[sort_idx],
        )
        reg_line = RegressionLine(
            x_sorted=xf,
            y_pred_sorted=y_pred_all[sort_idx],
        )

        # series'ler
        series: List[ScatterSeries] = []
        for label in ["Sağlıklı", "Taşıyıcı", "Belirsiz"]:
            idx = (sonuc_all == label)
            if not np.any(idx):
                continue
            series.append(
                ScatterSeries(
                    label=label,
                    x=fam_all[idx],
                    y=hex_all[idx],
                    wells=wells_all[idx],
                )
            )

        return RegressionPlotData(
            safe_band=safe_band,
            reg_line=reg_line,
            series=series,
        )

    @staticmethod
    def _validate(df: pd.DataFrame) -> None:
        if df is None or df.empty:
            raise ValueError("Regresyon grafiği için DataFrame boş.")
        missing = [c for c in RegressionPlotService.REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"Regresyon grafiği için eksik kolon(lar): {missing}")
