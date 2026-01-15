from __future__ import annotations

import math
from decimal import Decimal
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
    # --- 1. Eksen Kalemleri ve Sabitleme ---
    bottom_axis = plot_widget.getAxis("bottom")
    left_axis = plot_widget.getAxis("left")
    
    # Profesyonel Dokunuş: Y ekseni genişliğini sabitle (Grafiğin zıplamasını önler)
    left_axis.setWidth(55) # 55px sabit genişlik (5 basamaklı sayılar için yeterli)
    
    for axis in [bottom_axis, left_axis]:
        axis.setPen(pg.mkPen(style_axes.tick_color, width=style_axes.tick_width))
        axis.setTextPen(pg.mkPen(style_axes.label_color))
    
    view_box.setBackgroundColor(style_axes.ax_facecolor)
    
    # --- 2. Grid Yönetimi (Daha Az Baskın) ---
    plot_widget.showGrid(x=True, y=True, alpha=0.2) # Alpha çok düşük olmalı
    
    # Kesişim Çizgileri (0 noktaları yerine senin istediğin offsetli kesişim)
    # Not: İstenirse InfiniteLine yerine eksen sınırları kullanılabilir
    
    # --- 3. Etiketler ve Başlık ---
    plot_item.setTitle(title, color=style_axes.title_color, size="12pt")
    
    # --- 4. Padding ve Aralık ---
    # Eksen etiketlerinin grafiğe çok yaklaşmasını önle
    left_axis.setStyle(tickTextOffset=10)
    bottom_axis.setStyle(tickTextOffset=8)

    apply_axis_ranges(plot_item, view_box, xlim=xlim, ylim=ylim)
def set_axis_ticks(plot_item: pg.PlotItem, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> None:
    bottom_axis = plot_item.getAxis("bottom")
    left_axis = plot_item.getAxis("left")

    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]
    
    # Hata önleyici: Aralık aşırı küçükse (float precision hatası) işlem yapma
    if x_range < 1e-10 or y_range < 1e-10:
        return

    # target_ticks değerlerini zoom seviyesine göre dinamik bırakabiliriz
    x_step = _nice_step(x_range, target_ticks=7)
    y_step = _nice_step(y_range, target_ticks=6)

    # build_ticks senin fonksiyonun, aynı kalabilir
    x_ticks = build_ticks(xlim[0], xlim[1], step=x_step, force_end=False) # Zoom'da force_end False daha iyidir
    y_ticks = build_ticks(ylim[0], ylim[1], step=y_step, force_end=False)

    if x_ticks:
        bottom_axis.setTicks([x_ticks])
    if y_ticks:
        left_axis.setTicks([y_ticks])

def build_ticks(start: float, end: float, step: float, force_end: bool = False, align_to: float = 0) -> List[tuple[float, str]]:
    ticks: List[tuple[float, str]] = []

    if step <= 0:
        return ticks

    first_tick = math.floor(start / step) * step
    if first_tick < start:
        first_tick += step

    current = first_tick
    
    while current <= end + (step * 0.001):
        val = _round_to_step(current, step)
        ticks.append((val, format_tick_value(val, step)))
        current += step

    has_zero = any(t[0] == 0 for t in ticks)
    if not has_zero and start <= 0 <= end:
        ticks.append((0.0, "0"))
        ticks.sort()

    if force_end:
        last_val = ticks[-1][0] if ticks else start
        if end - last_val > (step * 0.1):
            ticks.append((end, format_tick_value(end, step)))
        
    return ticks

def format_tick_value(value: float, step: float) -> str:
    if abs(value) < 0.000001:
        return "0"
    if abs(value) >= 1000 and step >= 1:
        return f"{int(round(value))}"
    decimals = _decimal_places(step)
    formatted = f"{value:.{decimals}f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _nice_step(value_range: float, target_ticks: int = 7) -> float:
    if value_range <= 0:
        return 1.0
    raw = value_range / max(target_ticks, 1)
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        step = factor * magnitude
        if step >= raw:
            return step
    return 10 * magnitude


def _decimal_places(step: float) -> int:
    dec = Decimal(str(step)).normalize()
    exp = -dec.as_tuple().exponent
    return max(0, exp)


def _round_to_step(value: float, step: float) -> float:
    if step == 0:
        return value
    return round(value / step) * step

def apply_axis_ranges(
    plot_item: pg.PlotItem,
    view_box: pg.ViewBox,
    *,
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
) -> None:
    custom_ymin = -500.0
    custom_xmin = 0.0
    
    plot_item.enableAutoRange(x=False, y=False)
    
    # Padding: Verinin en üstte eksene yapışmaması için %10 pay
    actual_ymax = ylim[1] * 1.1 

    plot_item.setLimits(
        xMin=custom_xmin, 
        xMax=xlim[1], 
        yMin=custom_ymin, 
        yMax=actual_ymax
    )

    view_box.setRange(
        xRange=(custom_xmin, xlim[1]),
        yRange=(custom_ymin, ylim[1]),
        padding=0.0
    )

    # Ticks fonksiyonuna güncellenmiş sınırları gönderiyoruz
    set_axis_ticks(plot_item, (custom_xmin, xlim[1]), (custom_ymin, ylim[1]))