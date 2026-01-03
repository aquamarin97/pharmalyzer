from __future__ import annotations
from typing import List, Tuple
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

def refresh_legend(renderer, legend_item: pg.LegendItem) -> None:
    """
    Lejantı temizler ve profesyonel stillerle yeniden yapılandırır.
    """
    # 1. Temel Temizlik
    legend_item.clear()
    
    # 2. Profesyonel Stil Ayarları
    # Arka planı hafif şeffaf yaparak grafiğin arkadan görünmesini sağlıyoruz
    bg_color = QtGui.QColor(renderer._style.legend_frame_facecolor)
    bg_color.setAlpha(180)  # 255 üzerinden 180 (hafif şeffaf)
    
    legend_item.setBrush(pg.mkBrush(bg_color))
    legend_item.setPen(pg.mkPen(renderer._style.legend_frame_edgecolor, width=0.8))
    
    # Yazı tipi ve boşluk ayarları
    label_style = {
        'color': renderer._style.legend_text_color,
        'size': '10pt',
        'bold': True,
        'font-family': 'Segoe UI, Roboto, Helvetica, Arial'
    }

    # 3. Kanalları Ekle (FAM/HEX)
    # renderer._fam_visible gibi flag'leri doğrudan kontrol etmek daha hızlıdır
    if renderer._fam_visible and renderer._fam_items:
        _add_legend_row(legend_item, "FAM", renderer._style.fam_color, label_style)
        
    if renderer._hex_visible and renderer._hex_items:
        _add_legend_row(legend_item, "HEX", renderer._style.hex_color, label_style)

def _add_legend_row(legend, name: str, color: str, label_style: dict):
    """Lejant satırı için stilize edilmiş bir ikon ve metin ekler."""
    # Lejanttaki çizgi örneği (sample) ana grafikteki 'parlak' hali temsil etmeli
    sample_pen = pg.mkPen(color=color, width=3)
    sample_item = pg.PlotDataItem(pen=sample_pen)
    
    # Satırı ekle
    legend.addItem(sample_item, name)
    
    # Eklenen metnin stilini güncelle (pg.LegendItem metinleri LabelItem olarak tutar)
    for item in legend.items:
        if item[1].text == name:
            item[1].setText(name, **label_style)