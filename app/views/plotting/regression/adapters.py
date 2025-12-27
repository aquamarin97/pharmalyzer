# app\views\plotting\regression\adapters.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyqtgraph as pg

from app.i18n import t
from app.services.regression_plot_service import RegressionPlotData, RegressionLine, SafeBand, ScatterSeries
from app.views.plotting.regression.styles import (
    RegressionPlotStyle,
    get_series_style,
    make_brush,
    make_pen,
)


@dataclass
class ScatterHandle:
    item: pg.ScatterPlotItem
    x: np.ndarray
    y: np.ndarray
    wells: np.ndarray
    base_brush: tuple[int, ...]
    base_pen: tuple[int, ...]


@dataclass
class HoverPoints:
    x: np.ndarray
    y: np.ndarray
    wells: np.ndarray

    @classmethod
    def empty(cls) -> "HoverPoints":
        return cls(
            x=np.array([], dtype=float),
            y=np.array([], dtype=float),
            wells=np.array([], dtype=str),
        )

    @property
    def is_empty(self) -> bool:
        return self.x.size == 0


@dataclass
class SeriesBuildResult:
    scatter_items: list[pg.ScatterPlotItem]
    scatter_handles: list[ScatterHandle]
    hover_points: HoverPoints


def build_safe_band_items(safe_band: SafeBand, style: RegressionPlotStyle) -> list[pg.GraphicsObject]:
    upper_curve = pg.PlotDataItem(
        safe_band.x_sorted,
        safe_band.upper,
        pen=make_pen((255, 255, 255, 0)),
    )
    lower_curve = pg.PlotDataItem(
        safe_band.x_sorted,
        safe_band.lower,
        pen=make_pen((255, 255, 255, 0)),
    )

    fill = pg.FillBetweenItem(
        upper_curve,
        lower_curve,
        brush=make_brush(style.safe_band_brush_rgba),
    )
    fill.setZValue(0)
    return [upper_curve, lower_curve, fill]


def build_regression_line_item(reg_line: RegressionLine, style: RegressionPlotStyle) -> pg.PlotDataItem:
    line = pg.PlotDataItem(
        reg_line.x_sorted,
        reg_line.y_pred_sorted,
        pen=make_pen(style.reg_line_pen, width=style.reg_line_width),
        name=t("regression.plot.regression_line"),
    )
    line.setZValue(2)
    return line


def _translate_label(label: str) -> str:
    return {
        "Sağlıklı": t("regression.plot.legend.healthy"),
        "Taşıyıcı": t("regression.plot.legend.carrier"),
        "Belirsiz": t("regression.plot.legend.uncertain"),
    }.get(label, label)


def build_series_items(series: list[ScatterSeries], style: RegressionPlotStyle) -> SeriesBuildResult:
    scatter_items: list[pg.ScatterPlotItem] = []
    scatter_handles: list[ScatterHandle] = []

    hover_x: list[np.ndarray] = []
    hover_y: list[np.ndarray] = []
    hover_wells: list[np.ndarray] = []

    for s in series:
        series_style = get_series_style(style, s.label)

        if series_style is None:
            brush = (200, 200, 200)
            pen = (255, 255, 255)
        else:
            brush = series_style.brush
            pen = series_style.pen

        sc = pg.ScatterPlotItem(
            x=s.x,
            y=s.y,
            size=style.scatter_size,
            brush=make_brush(brush),
            pen=make_pen(pen, width=style.scatter_pen_width),
            name=_translate_label(s.label),
        )
        sc.setZValue(3)
        scatter_items.append(sc)

        hx = np.asarray(s.x, dtype=float)
        hy = np.asarray(s.y, dtype=float)
        hw = np.asarray(s.wells, dtype=str)

        hover_x.append(hx)
        hover_y.append(hy)
        hover_wells.append(hw)

        scatter_handles.append(
            ScatterHandle(
                item=sc,
                x=hx,
                y=hy,
                wells=hw,
                base_brush=brush,
                base_pen=pen,
            )
        )

    hover_points = HoverPoints.empty()
    if hover_x:
        hover_points = HoverPoints(
            x=np.concatenate(hover_x),
            y=np.concatenate(hover_y),
            wells=np.concatenate(hover_wells),
        )

    return SeriesBuildResult(
        scatter_items=scatter_items,
        scatter_handles=scatter_handles,
        hover_points=hover_points,
    )