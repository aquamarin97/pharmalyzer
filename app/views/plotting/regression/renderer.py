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

        for handle in self._scatter_handles:
            # ---- Selected overlay ----
            if selected_wells:
                idxs: list[int] = []
                for w in selected_wells:
                    i = handle.well_to_index.get(w)
                    if i is not None:
                        idxs.append(i)

                if idxs:
                    sel_x = handle.x[idxs]
                    sel_y = handle.y[idxs]

                    base = handle.base_brush
                    if len(base) == 4:
                        r, g, b, a = base
                        bright = (min(r + 60, 255), min(g + 60, 255), min(b + 60, 255), a)
                    else:
                        r, g, b = base
                        bright = (min(r + 60, 255), min(g + 60, 255), min(b + 60, 255))

                    handle.selected_item.setData(
                        x=sel_x,
                        y=sel_y,
                        size=self._style.scatter_size + 4,
                        brush=make_brush(bright),
                        pen=make_pen(handle.selection_pen, width=4),
                    )
                else:
                    handle.selected_item.setData(x=[], y=[])
            else:
                handle.selected_item.setData(x=[], y=[])

            # ---- Hover overlay (single point) ----
            if hover_well is not None:
                hi = handle.well_to_index.get(hover_well)
                if hi is not None:
                    base = handle.base_brush
                    if len(base) == 4:
                        r, g, b, a = base
                        bright = (min(r + 80, 255), min(g + 80, 255), min(b + 80, 255), a)
                    else:
                        r, g, b = base
                        bright = (min(r + 80, 255), min(g + 80, 255), min(b + 80, 255))

                    handle.hover_item.setData(
                        x=[float(handle.x[hi])],
                        y=[float(handle.y[hi])],
                        size=self._style.scatter_size + 7,
                        brush=make_brush(bright),
                        pen=make_pen(handle.selection_pen, width=4),
                    )
                else:
                    handle.hover_item.setData(x=[], y=[])
            else:
                handle.hover_item.setData(x=[], y=[])
