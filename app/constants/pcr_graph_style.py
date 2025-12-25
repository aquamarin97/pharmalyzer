# app/constants/pcr_graph_style.py
from __future__ import annotations

from dataclasses import dataclass
from app.constants.app_styles import COLOR_STYLES


@dataclass(frozen=True)
class PCRGraphStyle:
    fig_facecolor: str = COLOR_STYLES.PLOT_BG_HEX
    ax_facecolor: str = COLOR_STYLES.PLOT_BG_HEX

    grid_color: str = COLOR_STYLES.PLOT_GRID_HEX
    grid_linestyle: str = "--"
    grid_linewidth: float = 0.6

    tick_color: str = COLOR_STYLES.PLOT_TEXT_HEX
    label_color: str = COLOR_STYLES.PLOT_TEXT_HEX
    title_color: str = COLOR_STYLES.PLOT_TITLE_HEX

    fam_color: str = "#22C7A8"
    hex_color: str = "#F4A261"

    legend_frame_facecolor: str = COLOR_STYLES.PLOT_LEGEND_BG_HEX
    legend_frame_edgecolor: str = COLOR_STYLES.PLOT_GRID_HEX
    legend_text_color: str = COLOR_STYLES.PLOT_TEXT_HEX

    default_xlim: tuple[int, int] = (0, 40)
    default_ylim: tuple[int, int] = (0, 5000)
