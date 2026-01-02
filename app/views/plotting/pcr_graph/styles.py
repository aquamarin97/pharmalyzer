# app\views\plotting\pcr_graph\styles.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Set

import numpy as np

from matplotlib.lines import Line2D

from . import drawing


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


def apply_interaction_styles(r, hovered: Optional[str], selected: Set[str], preview: Set[str]) -> InteractionStyleChange:
    """
    Diff-based stil güncellemeleri.
    - Kalıcı seçimler için yalnızca değişen line'lar güncellenir.
    - Hover/preview overlay segmentleri hesaplanır (base line'a dokunmadan).
    """
    if not r._fam_lines and not r._hex_lines:
        return InteractionStyleChange(False, False, [], [])

    if r._style_state is None:
        r._style_state = StyleState()
    state: StyleState = r._style_state

    base_dirty, _ = _update_selection_styles(r, selected, state)

    hover_segments = _build_segments_for_wells(r, [hovered] if hovered else [])
    preview_segments = _build_segments_for_wells(r, preview)
    overlay_dirty = base_dirty or state.prev_hover != hovered or state.prev_preview != preview

    state.prev_hover = hovered
    state.prev_preview = set(preview)
    state.prev_selected = set(selected)

    return InteractionStyleChange(
        base_dirty=base_dirty,
        overlay_dirty=overlay_dirty,
        hover_segments=hover_segments,
        preview_segments=preview_segments,
    )


def _update_selection_styles(r, selected: Set[str], state: StyleState) -> tuple[bool, Set[str]]:
    changed: Set[str]
    if not state.initialized:
        changed = set(r._fam_lines.keys()) | set(r._hex_lines.keys())
        state.initialized = True
    else:
        changed = state.prev_selected.symmetric_difference(selected)

    if not changed:
        return False, changed

    for well in changed:
        _style_well(r, well, selected)
    return True, changed


def _style_well(r, well: str, selected: Set[str]) -> None:
    for line in _iter_lines_for_well(r, well):
        _style_line(r, line, is_selected=well in selected)


def _style_line(r, line: Line2D, is_selected: bool) -> None:
    is_fam = line in r._fam_lines.values()
    style_pen = r._style.fam_pen if is_fam else r._style.hex_pen
    color = r._style.fam_color if is_fam else r._style.hex_color

    base_alpha = style_pen.get("alpha", 1.0)
    base_width = float(style_pen.get("linewidth", 0.05))

    line.set_color(color)
    if is_selected:
        line.set_alpha(1.0)
        line.set_linewidth(base_width + 0.1)
        line.set_zorder(10)
    else:
        line.set_alpha(base_alpha)
        line.set_linewidth(base_width)
        line.set_zorder(1)


def _iter_lines_for_well(r, well: str) -> Iterable[Line2D]:
    fam = r._fam_lines.get(well)
    hex_line = r._hex_lines.get(well)
    if fam is not None:
        yield fam
    if hex_line is not None:
        yield hex_line


def _build_segments_for_wells(r, wells: Iterable[str]) -> List[np.ndarray]:
    segments: List[np.ndarray] = []
    for well in wells:
        coords = r._well_geoms.get(well)
        if not coords:
            continue
        if r._fam_visible and coords["fam"].size > 0:
            segments.append(coords["fam"])
        if r._hex_visible and coords["hex"].size > 0:
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

    for line in r._fam_lines.values():
        line.set_visible(r._fam_visible)
    for line in r._hex_lines.values():
        line.set_visible(r._hex_visible)

    drawing.refresh_legend(r)
    return True


def set_title(r, title: str) -> None:
    r._title = title
    r.ax.set_title(r._title)