# app\views\plotting\pcr_graph\styles.py
from __future__ import annotations

from typing import Optional, Set

from matplotlib.lines import Line2D

from . import drawing


def apply_interaction_styles(r, hovered: Optional[str], selected: Set[str], preview: Set[str]) -> None:
    if not r._fam_lines and not r._hex_lines:
        return

    for well, line in r._fam_lines.items():
        style_line(r, line, hovered, selected, preview, well, channel="fam")
    for well, line in r._hex_lines.items():
        style_line(r, line, hovered, selected, preview, well, channel="hex")


def style_line(
    r,
    line: Line2D,
    hovered: Optional[str],
    selected: Set[str],
    preview: Set[str],
    well: str,
    channel: str,
) -> None:
    is_fam = channel == "fam"
    style_pen = r._style.fam_pen if is_fam else r._style.hex_pen

    base_alpha = style_pen.get("alpha", 1.0)
    base_width = float(style_pen.get("linewidth", 0.05))
    original_color = r._style.fam_color if is_fam else r._style.hex_color

    is_hovered = well == hovered
    is_preview = well in preview
    is_selected = well in selected

    if is_hovered or is_preview:
        line.set_color("#D3D3D3")
        line.set_alpha(1.0)
        line.set_linewidth(base_width + 0.1)
        line.set_zorder(100)
    elif is_selected:
        line.set_color(original_color)
        line.set_alpha(1.0)
        line.set_linewidth(base_width + 0.1)
        line.set_zorder(10)
    else:
        line.set_color(original_color)
        line.set_alpha(base_alpha)
        line.set_linewidth(base_width)
        line.set_zorder(1)


def set_channel_visibility(r, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
    if fam_visible is not None:
        r._fam_visible = bool(fam_visible)
    if hex_visible is not None:
        r._hex_visible = bool(hex_visible)

    for line in r._fam_lines.values():
        line.set_visible(r._fam_visible)
    for line in r._hex_lines.values():
        line.set_visible(r._hex_visible)

    drawing.refresh_legend(r)
    r.draw_idle()


def set_title(r, title: str) -> None:
    r._title = title
    r.ax.set_title(r._title)
    r.draw_idle()