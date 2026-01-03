from __future__ import annotations
from typing import List, Tuple
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
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
    # Grid rengini arka plana yaklaştırıp alpha'yı düşürüyoruz
    grid_pen = pg.mkPen(color=style_axes.grid_color, width=0.5)
    plot_widget.showGrid(x=True, y=True, alpha=0.2) # Alpha çok düşük olmalı
    
    # Kesişim Çizgileri (0 noktaları yerine senin istediğin offsetli kesişim)
    # Not: İstenirse InfiniteLine yerine eksen sınırları kullanılabilir
    
    # --- 3. Etiketler ve Başlık ---
    plot_item.setLabel("bottom", "Cycle", units="", color=style_axes.label_color)
    plot_item.setLabel("left", "Fluorescence", units="", color=style_axes.label_color)
    plot_item.setTitle(title, color=style_axes.title_color, size="12pt")
    
    # --- 4. Padding ve Aralık ---
    # Eksen etiketlerinin grafiğe çok yaklaşmasını önle
    left_axis.setStyle(tickTextOffset=10)
    bottom_axis.setStyle(tickTextOffset=8)

    apply_axis_ranges(plot_item, view_box, xlim=xlim, ylim=ylim)

def set_axis_ticks(plot_item: pg.PlotItem, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> None:
    bottom_axis = plot_item.getAxis("bottom")
    left_axis = plot_item.getAxis("left")

    # X adımları (Cycle genelde 1-40 arasıdır)
    x_step = 5 if (xlim[1] - xlim[0]) > 20 else 2
    
    # Y adımları (Daha yuvarlak sayılar)
    y_range = ylim[1] - ylim[0]
    if y_range > 15000: y_step = 5000
    elif y_range > 5000: y_step = 2000
    else: y_step = 1000

    # Ticks oluştur ve uygula
    bottom_axis.setTicks([build_ticks(xlim, step=x_step, force_end=True)])
    left_axis.setTicks([build_ticks(ylim, step=y_step, force_end=True)])

def build_ticks(axis_range: Tuple[float, float], step: float, force_end: bool = False) -> List[tuple[float, str]]:
    start, end = axis_range
    ticks: List[tuple[float, str]] = []
    
    # Belirlediğin adıma göre tickleri oluştur
    current = start
    while current <= end:
        ticks.append((current, format_tick_value(current)))
        current += step
    
    # Uç nokta değeri listede yoksa zorla ekle (İsteğin 2)
    if force_end and (not ticks or ticks[-1][0] < end):
        ticks.append((end, format_tick_value(end)))
        
    return ticks

def format_tick_value(value: float) -> str:
    # 10.000 üzerini "10k" olarak veya bilimsel formatta yazabiliriz 
    # Ama netlik için tam sayı döndürmek PCR'da daha iyidir
    if abs(value) >= 1000:
        return f"{int(value)}"
    return f"{value:.0f}"

def apply_axis_ranges(
    plot_item: pg.PlotItem,
    view_box: pg.ViewBox,
    *,
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
) -> None:
    # İsteğin 3: Y ekseni -500'den başlasın
    custom_ymin = -500.0
    custom_xmin = 0.0 # Cycle genelde 0'dan başlar
    
    plot_item.enableAutoRange(x=False, y=False)
    
    # Limitleri belirle (Gereksiz kaydırmayı önlemek için)
    plot_item.setLimits(
        xMin=custom_xmin, 
        xMax=xlim[1] * 1.05, 
        yMin=custom_ymin, 
        yMax=ylim[1] * 1.2
    )

    # Range uygula
    view_box.setRange(
        xRange=(custom_xmin, xlim[1]),
        yRange=(custom_ymin, ylim[1]),
        padding=0.0
    )

    set_axis_ticks(plot_item, (custom_xmin, xlim[1]), (custom_ymin, ylim[1]))