# app/views/plotting/pcr_graph_pg/overlays_pg.py
from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui


def build_overlay(*, pen: QtGui.QPen) -> pg.PlotDataItem:
    item = pg.PlotDataItem(pen=pen, connect="finite")
    item.setZValue(30)
    item.setVisible(False)
    return item


def segments_to_xy_with_nans(segments: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    if not segments:
        return np.array([]), np.array([])

    xs_list = []
    ys_list = []
    for seg in segments:
        if seg is None or seg.size == 0:
            continue
        xs_list.append(seg[:, 0])
        ys_list.append(seg[:, 1])
        xs_list.append(np.array([np.nan]))
        ys_list.append(np.array([np.nan]))

    if not xs_list:
        return np.array([]), np.array([])
    return np.concatenate(xs_list), np.concatenate(ys_list)


def update_overlays(renderer, change) -> None:
    """
    renderer._hover_overlay ve renderer._preview_overlay update eder.
    """
    if change.hover_segments:
        xs, ys = segments_to_xy_with_nans(change.hover_segments)
        renderer._hover_overlay.setData(xs, ys)
        renderer._hover_overlay.setVisible(True)
    else:
        renderer._hover_overlay.setData([], [])
        renderer._hover_overlay.setVisible(False)

    if change.preview_segments:
        xs, ys = segments_to_xy_with_nans(change.preview_segments)
        renderer._preview_overlay.setData(xs, ys)
        renderer._preview_overlay.setVisible(True)
    else:
        renderer._preview_overlay.setData([], [])
        renderer._preview_overlay.setVisible(False)


def make_hover_pen(renderer) -> QtGui.QPen:
    return pg.mkPen(renderer._style.overlay_color, width=renderer._style.overlay_hover_width)  # noqa


def make_preview_pen(renderer) -> QtGui.QPen:
    return pg.mkPen(
        renderer._style.overlay_color,
        width=renderer._style.overlay_preview_width,
        style=QtCore.Qt.DashLine,
    )
