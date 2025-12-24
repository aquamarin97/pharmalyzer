# app/services/regression_plot_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

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
    PyQtGraph bağımlılığı yoktur.
    """

    REQUIRED = ["hex_end_rfu", "fam_end_rfu", "Kuyu No", "Nihai Sonuç", "Regresyon"]
    ALLOWED_CLASSES = ["Sağlıklı", "Taşıyıcı", "Belirsiz"]

    # legacy ile uyum (CalculateRegration içindeki 2.2*sigma bandı)
    BAND_SIGMA = 2.2

    @staticmethod
    def build(df: pd.DataFrame) -> RegressionPlotData:
        RegressionPlotService._validate(df)

        # Sadece ihtiyaç duyulan kolonlarla çalış (kopya hafif olsun)
        work = df.loc[:, RegressionPlotService.REQUIRED].copy()

        # numeric kolonları güvenli şekilde sayısala çevir
        work["fam_end_rfu"] = pd.to_numeric(work["fam_end_rfu"], errors="coerce")
        work["hex_end_rfu"] = pd.to_numeric(work["hex_end_rfu"], errors="coerce")

        # zorunlu alanlar
        work.dropna(subset=["hex_end_rfu", "fam_end_rfu", "Kuyu No", "Nihai Sonuç"], inplace=True)

        # çizimde gösterilecek sınıflar
        mask = work["Nihai Sonuç"].isin(RegressionPlotService.ALLOWED_CLASSES)

        # Model sadece "Güvenli Bölge" satırları ile fit olur (legacy preprocess)
        train = work.loc[mask].copy()
        train = train.loc[train["Regresyon"] == "Güvenli Bölge"].copy()

        empty = np.array([], dtype=float)

        if train.empty:
            return RegressionPlotData(
                safe_band=SafeBand(empty, empty, empty),
                reg_line=RegressionLine(empty, empty),
                series=[],
            )

        fam_train = train["fam_end_rfu"].astype(float).to_numpy()
        hex_train = train["hex_end_rfu"].astype(float).to_numpy()

        X_train = fam_train.reshape(-1, 1)
        y_train = hex_train

        lr = LinearRegression()
        lr.fit(X_train, y_train)

        # çizimde kullanılacak tüm noktalar (allowed class)
        fam_all = work.loc[mask, "fam_end_rfu"].astype(float).to_numpy()
        hex_all = work.loc[mask, "hex_end_rfu"].astype(float).to_numpy()
        wells_all = work.loc[mask, "Kuyu No"].astype(str).to_numpy()
        sonuc_all = work.loc[mask, "Nihai Sonuç"].astype(str).to_numpy()

        if fam_all.size == 0:
            return RegressionPlotData(
                safe_band=SafeBand(empty, empty, empty),
                reg_line=RegressionLine(empty, empty),
                series=[],
            )

        # sigma (train residuals)
        y_pred_train = lr.predict(X_train)
        residuals = y_train - y_pred_train
        sigma = float(np.std(residuals)) if residuals.size else 0.0

        X_all = fam_all.reshape(-1, 1)
        y_pred_all = lr.predict(X_all)

        band = RegressionPlotService.BAND_SIGMA * sigma
        safe_upper = y_pred_all + band
        safe_lower = y_pred_all - band

        sort_idx = np.argsort(fam_all)
        xf = fam_all[sort_idx]

        safe_band_obj = SafeBand(
            x_sorted=xf,
            upper=safe_upper[sort_idx],
            lower=safe_lower[sort_idx],
        )
        reg_line_obj = RegressionLine(
            x_sorted=xf,
            y_pred_sorted=y_pred_all[sort_idx],
        )

        # series (legend/renk için label)
        series: List[ScatterSeries] = []
        for label in RegressionPlotService.ALLOWED_CLASSES:
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
            safe_band=safe_band_obj,
            reg_line=reg_line_obj,
            series=series,
        )

    @staticmethod
    def _validate(df: pd.DataFrame) -> None:
        if df is None or df.empty:
            raise ValueError("Regresyon grafiği için DataFrame boş.")
        missing = [c for c in RegressionPlotService.REQUIRED if c not in df.columns]
        if missing:
            raise ValueError(f"Regresyon grafiği için eksik kolon(lar): {missing}")
