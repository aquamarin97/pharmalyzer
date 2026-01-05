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
    plot_item.setTitle(title, color=style_axes.title_color, size="12pt")
    
    # --- 4. Padding ve Aralık ---
    # Eksen etiketlerinin grafiğe çok yaklaşmasını önle
    left_axis.setStyle(tickTextOffset=10)
    bottom_axis.setStyle(tickTextOffset=8)

    apply_axis_ranges(plot_item, view_box, xlim=xlim, ylim=ylim)
def set_axis_ticks(plot_item: pg.PlotItem, xlim: Tuple[float, float], ylim: Tuple[float, float]) -> None:
    bottom_axis = plot_item.getAxis("bottom")
    left_axis = plot_item.getAxis("left")

    # X adımları (Cycle) - Tam sayılara hizalı
    x_step = 5 if (xlim[1] - xlim[0]) > 20 else 2
    
    # Y adımları (Floresan)
    y_range = ylim[1] - ylim[0]
    if y_range > 15000: y_step = 5000
    elif y_range > 5000: y_step = 2000
    else: y_step = 1000

    # Ticks oluştur: 
    # Y ekseni için özel hizalama: -500'den başlasa bile ilk tick'i 0'a veya 1000'e kurar.
    bottom_axis.setTicks([build_ticks(xlim[0], xlim[1], step=x_step, force_end=True, align_to=0)])
    left_axis.setTicks([build_ticks(ylim[0], ylim[1], step=y_step, force_end=True, align_to=0)])

def build_ticks(start: float, end: float, step: float, force_end: bool = False, align_to: float = 0) -> List[tuple[float, str]]:
    ticks: List[tuple[float, str]] = []
    
    # 1. İlk tick'i "align_to" (örneğin 0) değerine göre hizala
    # Start -500 ise ve align_to 0 ise, ilk tick 0'dan başlar.
    # Eğer start -500 iken -1000, 0, 1000 gibi gitsin istiyorsak:
    first_tick = (start // step) * step
    if first_tick < start:
        first_tick += step
    
    # 0 değerini mutlaka içermesi gerekiyorsa ve start/end arasındaysa listeye dahil et
    current = first_tick
    
    # Eksen başlangıcında (örn: -500) sayı yazmasın, sadece tam sayılarda yazsın istiyoruz
    while current <= end:
        # Küsürat hatalarını önlemek için round kullanıyoruz
        val = round(current / (step / 100)) * (step / 100) 
        ticks.append((val, format_tick_value(val)))
        current += step
    
    # 2. 0 değerini zorla ekle (Eğer aralıktaysa ve yukarıdaki döngü kaçırdıysa)
    has_zero = any(t[0] == 0 for t in ticks)
    if not has_zero and start <= 0 <= end:
        ticks.append((0.0, "0"))
        ticks.sort() # Sıralamayı koru

    # 3. Uç nokta değerini ekle (Maksimum Cycle değeri)
    if force_end:
        last_val = ticks[-1][0] if ticks else start
        if end - last_val > (step * 0.1): # Eğer uç noktaya çok yakın değilsek ekle
            ticks.append((end, format_tick_value(end)))
        
    return ticks

def format_tick_value(value: float) -> str:
    if abs(value) < 0.001: return "0" # Floating point 0.0000004 hatasını önler
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