# app\views\plotting\pcr_graph_pg\legend.py
from __future__ import annotations

from typing import List, Tuple

import pyqtgraph as pg

from .styles import build_pen


def legend_entries(renderer) -> List[Tuple[str, pg.QtGui.QPen]]:
    entries: List[Tuple[str, pg.QtGui.QPen]] = []
    if any(item.isVisible() for item in renderer._fam_items.values()):
        entries.append(("FAM", build_pen(renderer._style.fam_color, renderer._style.fam_pen)))
    if any(item.isVisible() for item in renderer._hex_items.values()):
        entries.append(("HEX", build_pen(renderer._style.hex_color, renderer._style.hex_pen)))
    return entries


def refresh_legend(renderer, legend_item: pg.LegendItem) -> None:
    legend_item.clear()
    for name, pen in legend_entries(renderer):
        sample = pg.PlotDataItem(pen=pen)
        legend_item.addItem(sample, name)