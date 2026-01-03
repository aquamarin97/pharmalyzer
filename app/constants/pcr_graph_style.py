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
# Profesyonel Medikal Palet (Daha az 'neon', daha çok 'vurgu')
    fam_color: str = "#00F2C3"       # Canlı Turkuaz/Yeşil (Gözün en hassas olduğu renk)
    hex_color: str = "#FFB03B"       # Amber/Altın (FAM ile kontrastı yüksek)
    
    # Etkileşim Renkleri
    overlay_color: str = "#FFFFFF"   # Hover/Seçim çerçevesi saf beyaz veya parlak olmalı
    inactive_alpha: float = 0.15      # Seçili olmayanlar arkada 'hayalet' gibi kalmalı
    
    # Kalınlık Standartları (Retina/High-DPI uyumlu)
    base_width: float = 1.2          # Normal durum
    selected_width: float = 2.5      # Seçili durum (Belirgin fark)
    overlay_hover_width: float = 3.0 # Hover etkisi en üstte ve en kalın
    overlay_preview_width: float = 2.0
    overlay_roi_width: float = 1.0
    
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