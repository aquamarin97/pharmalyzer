# app\views\plotting\pcr_graph_pg\axes.py
from __future__ import annotations

from typing import List, Tuple

import pyqtgraph as pg

from app.constants.pcr_graph_style import AxesStyle


def apply_axes_style(
    plot_widget: pg.PlotWidget,
    plot_item: pg.PlotItem,
    view_box: pg.ViewBox,
    style_axes: AxesStyle,
    title: str,
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
) -> None:
    plot_widget.getAxis("bottom").setPen(pg.mkPen(style_axes.tick_color, width=style_axes.tick_width))
    plot_widget.getAxis("left").setPen(pg.mkPen(style_axes.tick_color, width=style_axes.tick_width))
    plot_widget.getAxis("bottom").setTextPen(pg.mkPen(style_axes.label_color))
    plot_widget.getAxis("left").setTextPen(pg.mkPen(style_axes.label_color))
    view_box.setBackgroundColor(style_axes.ax_facecolor)
    plot_widget.showGrid(x=True, y=True, alpha=0.55)
    plot_item.addItem(pg.InfiniteLine(angle=0, pen=pg.mkPen(style_axes.grid_color, width=1)))
    plot_item.addItem(pg.InfiniteLine(angle=90, pen=pg.mkPen(style_axes.grid_color, width=1)))
    plot_item.getAxis("left").setStyle(tickTextOffset=3)
    plot_item.getAxis("bottom").setStyle(tickTextOffset=3)
    plot_item.setLabel("bottom", "Cycle", color=style_axes.label_color)
    plot_item.setLabel("left", "Fluorescence", color=style_axes.label_color)
    plot_item.setTitle(title, color=style_axes.title_color)
    apply_axis_ranges(plot_item, view_box, xlim=xlim, ylim=ylim)


def set_axis_ticks(plot_item: pg.PlotItem, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> None:
    bottom_axis = plot_item.getAxis("bottom")
    left_axis = plot_item.getAxis("left")

    x_range = xlim[1] - xlim[0]
    x_step = max(1, round(x_range / 10))

    y_range = ylim[1] - ylim[0]
    y_raw_step = y_range / 10

    if y_range > 5000:
        y_step = max(1000, round(y_raw_step / 1000) * 1000)
    elif y_range > 1000:
        y_step = max(500, round(y_raw_step / 500) * 500)
    else:
        y_step = max(100, round(y_raw_step / 100) * 100)

    bottom_axis.setTicks([build_ticks(xlim, step=x_step)])
    left_axis.setTicks([build_ticks(ylim, step=y_step)])


def build_ticks(axis_range: Tuple[float, float], step: float) -> List[tuple[float, str]]:
    start, end = axis_range
    ticks: List[tuple[float, str]] = []

    current = float(start)
    eps = step * 0.01

    while current < end - eps:
        ticks.append((current, format_tick_value(current)))
        current += step

    ticks.append((float(end), format_tick_value(end)))
    return ticks


def format_tick_value(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def apply_axis_ranges(
    plot_item: pg.PlotItem,
    view_box: pg.ViewBox,
    *,
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
) -> None:
    plot_item.enableAutoRange(x=False, y=False)
    view_box.disableAutoRange(axis=view_box.XAxis)
    view_box.disableAutoRange(axis=view_box.YAxis)

    y_span = (ylim[1] - ylim[0]) if (ylim[1] - ylim[0]) else 1.0
    plot_item.setLimits(
        xMin=xlim[0],
        xMax=xlim[1],
        yMin=ylim[0] - y_span * 0.05,
        yMax=ylim[1] * 1.1,
    )

    view_box.setRange(
        xRange=(xlim[0], xlim[1]),
        yRange=(ylim[0], ylim[1]),
        padding=0.0,
        update=True,
        disableAutoRange=True,
    )

    set_axis_ticks(plot_item, xlim=xlim, ylim=ylim)
    view_box.updateViewRange()
    view_box.updateMatrix()