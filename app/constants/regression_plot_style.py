from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
from app.constants.app_styles import COLOR_STYLES

RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]


@dataclass(frozen=True)
class SeriesStyle:
    brush: RGB
    pen: RGB
def hex_to_rgb(h: str) -> RGB:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

@dataclass(frozen=True)
class RegressionPlotStyle:
    background_hex: str = COLOR_STYLES.PLOT_BG_HEX
    widget_background_rgb: RGB = hex_to_rgb(COLOR_STYLES.PLOT_BG_HEX)

    grid_color_rgb: RGB = hex_to_rgb(COLOR_STYLES.PLOT_GRID_HEX)
    grid_alpha: float = 0.25

    axis_text_rgb: RGB = hex_to_rgb(COLOR_STYLES.PLOT_TEXT_HEX)

    reg_line_pen: RGB = (255, 60, 60)
    reg_line_width: int = 2

    safe_band_brush_rgba: RGBA = (255, 255, 255, 40)

    scatter_size: int = 8
    scatter_pen_width: int = 1

    series: Dict[str, SeriesStyle] = None  # set in __post_init__ gibi de yapılabilir

    def __post_init__(self):
        if self.series is None:
            object.__setattr__(
                self,
                "series",
                {
                    "Sağlıklı": SeriesStyle(brush=(0, 191, 255), pen=(255, 255, 255)),
                    "Taşıyıcı": SeriesStyle(brush=(255, 165, 0), pen=(255, 215, 0)),
                    "Belirsiz": SeriesStyle(brush=(255, 0, 255), pen=(211, 211, 211)),
                },
            )
