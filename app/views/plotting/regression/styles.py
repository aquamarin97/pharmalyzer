# app\views\plotting\regression\styles.py
from __future__ import annotations

import pyqtgraph as pg

from app.constants.regression_plot_style import RegressionPlotStyle, SeriesStyle


def make_pen(color: tuple[int, ...], width: int = 1) -> pg.QtGui.QPen:
    return pg.mkPen(*color, width=width)


def make_brush(color: tuple[int, ...]) -> pg.QtGui.QBrush:
    return pg.mkBrush(*color)


def get_series_style(style: RegressionPlotStyle, label: str) -> SeriesStyle | None:
    return style.series.get(label)


__all__ = ["RegressionPlotStyle", "SeriesStyle", "get_series_style", "make_pen", "make_brush"]