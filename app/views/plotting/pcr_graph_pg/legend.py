from __future__ import annotations
from typing import List, Tuple
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

# app\views\plotting\pcr_graph_pg\legend.py

def refresh_legend(renderer, legend_item: pg.LegendItem) -> None:
    legend_item.clear()
    
    # 1. Stil Ayarları (Daha dar ve zarif bir görünüm için)
    # Legend'ın maksimum genişliğini sınırlayarak grafik alanını işgal etmesini önlüyoruz
    legend_item.layout.setContentsMargins(1, 1, 1, 1)
    legend_item.layout.setSpacing(4)

    # 2. İçerik Ekleme
    label_style = {'color': renderer._style.legend_text_color, 'size': '9pt', 'bold': False}
    
    if renderer._fam_visible and renderer._fam_items:
        _add_legend_row(legend_item, "FAM", renderer._style.fam_color, label_style)
    if renderer._hex_visible and renderer._hex_items:
        _add_legend_row(legend_item, "HEX", renderer._style.hex_color, label_style)

    # 3. Konumlandırma (Kritik Nokta)
    # Legend'ı sağ üst köşeye, eksenlerden 10px içeride olacak şekilde sabitler.
    # offset=(x, y) -> x negatif olursa sağdan, pozitif olursa soldan hizalar.
    legend_item.setOffset((57, 38))

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