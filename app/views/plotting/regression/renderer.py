# app\views\plotting\regression\renderer.py
from __future__ import annotations

from dataclasses import dataclass

import pyqtgraph as pg

from app.services.regression_plot_service import RegressionPlotData
from app.views.plotting.regression.adapters import (
    HoverPoints,
    ScatterHandle,
    SeriesBuildResult,
    build_regression_line_item,
    build_safe_band_items,
    build_series_items,
)
from app.views.plotting.regression.styles import RegressionPlotStyle, make_brush, make_pen


@dataclass
class RegressionRenderResult:
    items: list[pg.GraphicsObject]
    hover_points: HoverPoints
    scatter_handles: list[ScatterHandle]


class RegressionRenderer:
    def __init__(self, style: RegressionPlotStyle):
        self._style = style
        self._scatter_handles: list[ScatterHandle] = []
        self._hover_points: HoverPoints = HoverPoints.empty()

    @property
    def hover_points(self) -> HoverPoints:
        return self._hover_points

    def render(self, data: RegressionPlotData) -> RegressionRenderResult:
        self._scatter_handles = []
        self._hover_points = HoverPoints.empty()

        if data.reg_line.x_sorted.size == 0:
            return RegressionRenderResult(items=[], hover_points=self._hover_points, scatter_handles=[])

        items: list[pg.GraphicsObject] = []

        items.extend(build_safe_band_items(data.safe_band, self._style))
        items.append(build_regression_line_item(data.reg_line, self._style))

        series_result: SeriesBuildResult = build_series_items(data.series, self._style)
        items.extend(series_result.scatter_items)
        self._scatter_handles = series_result.scatter_handles
        self._hover_points = series_result.hover_points

        return RegressionRenderResult(
            items=items,
            hover_points=self._hover_points,
            scatter_handles=self._scatter_handles,
        )

    def update_styles(self, selected_wells: set[str] | None, hover_well: str | None) -> None:
        selected_wells = selected_wells or set()
        hover_well = hover_well or None

        for handle in self._scatter_handles:
            brushes = []
            pens = []
            sizes = []
            for idx, well in enumerate(handle.wells):
                is_selected = well in selected_wells
                is_hovered = hover_well == well

                size = self._style.scatter_size
                if is_hovered:
                    size += 3
                elif is_selected:
                    size += 1.5

                if is_hovered:
                    pen = make_pen((255, 59, 48), width=max(2, self._style.scatter_pen_width + 1))
                elif is_selected:
                    pen = make_pen((58, 122, 254), width=max(2, self._style.scatter_pen_width + 1))
                else:
                    pen = make_pen(handle.base_pen, width=self._style.scatter_pen_width)

                brush = make_brush(handle.base_brush)

                brushes.append(brush)
                pens.append(pen)
                sizes.append(size)

            handle.item.setData(
                x=handle.x,
                y=handle.y,
                brush=brushes,
                pen=pens,
                size=sizes,
            )