# app\views\widgets\regression_graph_view.py
from __future__ import annotations

import pandas as pd
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from app.services.regression_plot_service import RegressionPlotService
from app.views.plotting.pyqtgraph_regression_renderer import PyqtgraphRegressionRenderer


class RegressionGraphView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        pg.setConfigOptions(antialias=True)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_widget.setBackground((10, 10, 10))

        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.setLabel("bottom", "fam_end_rfu")
        self.plot_item.setLabel("left", "hex_end_rfu")
        self.plot_item.addLegend(offset=(10, 10))

        self._hover_text = pg.TextItem(anchor=(0, 1), color=(255, 255, 255))
        self._hover_text.setZValue(999)
        self._hover_text.hide()
        self.plot_item.addItem(self._hover_text)

        # ✅ Layout artık bu widget'ın kendi layout'u
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)

        self._renderer = PyqtgraphRegressionRenderer()

    def update(self, df: pd.DataFrame):
        data = RegressionPlotService.build(df)
        self._renderer.render(
            self.plot_item,
            data,
            enable_hover=True,
            hover_text_item=self._hover_text,
        )

    def reset(self):
        self._renderer.detach_hover()
        self.plot_item.clear()
        self.plot_item.addLegend(offset=(10, 10))
        self._hover_text.hide()
