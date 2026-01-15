# app\views\plotting\pcr_graph_pg\styles.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore

PenKey = Tuple[str, float, float, QtCore.Qt.PenStyle]

_PEN_CACHE: Dict[PenKey, QtGui.QPen] = {}


@dataclass
class InteractionStyleChange:
    base_dirty: bool
    overlay_dirty: bool
    hover_segments: List[np.ndarray]
    preview_segments: List[np.ndarray]


@dataclass
class StyleState:
    prev_selected: Set[str] = field(default_factory=set)
    prev_preview: Set[str] = field(default_factory=set)
    prev_hover: Optional[str] = None
    initialized: bool = False


def build_pen(color: str, width: float, alpha: float, style: QtCore.Qt.PenStyle = QtCore.Qt.SolidLine) -> QtGui.QPen:
    key = (color, width, alpha, style)
    if key in _PEN_CACHE:
        return _PEN_CACHE[key]

    color_obj = QtGui.QColor(color)
    color_obj.setAlphaF(alpha)
    # Hint: Cosmetice True yaparak zoom yapsan da çizgi kalınlığının sabit kalmasını sağlıyoruz
    pen = pg.mkPen(color=color_obj, width=width, style=style)
    pen.setCosmetic(True)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)
    _PEN_CACHE[key] = pen
    return pen


def apply_interaction_styles(r, hovered: Optional[str], selected: Set[str], preview: Set[str]) -> InteractionStyleChange:
    if not r._fam_items and not r._hex_items:
        return InteractionStyleChange(False, False, [], [])

    if r._style_state is None:
        r._style_state = StyleState()
    state: StyleState = r._style_state

    base_dirty = _update_interaction_styles(r, selected, preview, state)

    hover_segments = _build_segments_for_wells(r, [hovered] if hovered else [])
    preview_segments: List[np.ndarray] = []
    overlay_dirty = base_dirty or state.prev_hover != hovered

    state.prev_hover = hovered
    state.prev_preview = set(preview)
    state.prev_selected = set(selected)

    return InteractionStyleChange(
        base_dirty=base_dirty,
        overlay_dirty=overlay_dirty,
        hover_segments=hover_segments,
        preview_segments=preview_segments,
    )


def _update_interaction_styles(r, selected: Set[str], preview: Set[str], state: StyleState) -> bool:
    if not state.initialized:
        changed = set(r._fam_items.keys()) | set(r._hex_items.keys())
        state.initialized = True
    else:
        changed = (
            state.prev_selected.symmetric_difference(selected)
            | state.prev_preview.symmetric_difference(preview)
        )

    if not changed:
        return False

    for well in changed:
        _style_well(r, well, selected, preview)
    return True

def _style_well(r, well: str, selected: Set[str], preview: Set[str]) -> None:
    is_selected = well in selected
    is_preview = well in preview
    any_selection = len(selected) > 0

    if is_selected:
        target_alpha = 1.0  # %100 görünürlük
        target_width = r._style.selected_width
        z_value = 100 # En üst katman
        target_style = QtCore.Qt.SolidLine
    elif is_preview:
        target_alpha = 1.0
        target_width = r._style.overlay_preview_width
        z_value = 80
        target_style = QtCore.Qt.DashLine
    elif any_selection:
        target_alpha = r._style.inactive_alpha  # %15 opaklık
        target_width = r._style.base_width
        z_value = 1  # En alt katman
        target_style = QtCore.Qt.SolidLine
    else:
        # Hiçbir seçim yoksa herkes eşit ve orta görünürlükte
        target_alpha = 0.8
        target_width = r._style.base_width
        z_value = 10
        target_style = QtCore.Qt.SolidLine

    # FAM Uygulaması
    fam_item = r._fam_items.get(well)
    if fam_item:
        pen = build_pen(r._style.fam_color, target_width, target_alpha, target_style)
        fam_item.setPen(pen)
        fam_item.setZValue(z_value)
        fam_item.setVisible(r._fam_visible and bool(fam_item.property("has_data")))

    # HEX Uygulaması
    hex_item = r._hex_items.get(well)
    if hex_item:
        pen = build_pen(r._style.hex_color, target_width, target_alpha, target_style)
        hex_item.setPen(pen)
        hex_item.setZValue(z_value)

def _build_segments_for_wells(r, wells: Iterable[str]) -> List[np.ndarray]:
    segments: List[np.ndarray] = []
    for well in wells:
        coords = r._well_geoms.get(well)
        if not coords:
            continue
        if r._fam_visible and coords.get("fam") is not None and coords["fam"].size > 0:
            segments.append(coords["fam"])
        if r._hex_visible and coords.get("hex") is not None and coords["hex"].size > 0:
            segments.append(coords["hex"])
    return segments


def set_channel_visibility(r, fam_visible: bool | None = None, hex_visible: bool | None = None) -> bool:
    fam_changed = fam_visible is not None and bool(fam_visible) != r._fam_visible
    hex_changed = hex_visible is not None and bool(hex_visible) != r._hex_visible
    if not fam_changed and not hex_changed:
        return False

    if fam_changed:
        r._fam_visible = bool(fam_visible)
    if hex_changed:
        r._hex_visible = bool(hex_visible)

    for item in r._fam_items.values():
        item.setVisible(r._fam_visible and bool(item.property("has_data")))
    for item in r._hex_items.values():
        item.setVisible(r._hex_visible and bool(item.property("has_data")))

    return True
