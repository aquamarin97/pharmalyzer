# app\constants\pcr_graph_style.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from app.constants.app_styles import COLOR_STYLES


@dataclass(frozen=True)
class AxesStyle:
    fig_facecolor: str = COLOR_STYLES.PLOT_BG_HEX
    ax_facecolor: str = COLOR_STYLES.PLOT_BG_HEX

    grid_color: str = COLOR_STYLES.PLOT_GRID_HEX
    grid_linestyle: str = "-"
    grid_linewidth: float = 0.7

    tick_color: str = COLOR_STYLES.PLOT_TEXT_HEX
    tick_width: float = 0.8
    label_color: str = COLOR_STYLES.PLOT_TEXT_HEX
    title_color: str = COLOR_STYLES.PLOT_TITLE_HEX

    default_xlim: Tuple[int, int] = (0, 40)
    default_ylim: Tuple[int, int] = (0, 4500)


@dataclass(frozen=True)
class PCRGraphStyle:
    # 1. Basit varsayılan değerleri en başa al
    fam_color: str = "#22C7A8"
    hex_color: str = "#F4A261"
    
    legend_frame_facecolor: str = COLOR_STYLES.PLOT_LEGEND_BG_HEX
    legend_frame_edgecolor: str = COLOR_STYLES.PLOT_GRID_HEX
    legend_text_color: str = COLOR_STYLES.PLOT_TEXT_HEX

    # 2. AxesStyle gibi karmaşık objeler
    axes: AxesStyle = field(default_factory=AxesStyle)

    # 3. Default Factory (Mutable) alanları en sona al
    fam_pen: Dict[str, float | str] = field(
        default_factory=lambda: {"linewidth": 2.1, "alpha": 0.95}
    )
    hex_pen: Dict[str, float | str] = field(
        default_factory=lambda: {"linewidth": 2.0, "alpha": 0.7, "linestyle": "-"}
    )