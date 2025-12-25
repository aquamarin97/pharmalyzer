# app/views/widgets/regression_graph_view.py


from __future__ import annotations

import pandas as pd
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from app.services.regression_plot_service import RegressionPlotService
from app.views.plotting.pyqtgraph_regression_renderer import PyqtgraphRegressionRenderer
from app.constants.regression_plot_style import RegressionPlotStyle


class RegressionGraphView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        pg.setConfigOptions(antialias=True)

        self._style = RegressionPlotStyle()

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.plot_item = self.plot_widget.getPlotItem()

        self._hover_text = pg.TextItem(anchor=(0, 1), color=(255, 255, 255))
        self._hover_text.setZValue(999)
        self._hover_text.hide()
        self.plot_item.addItem(self._hover_text)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)

        self._renderer = PyqtgraphRegressionRenderer(style=self._style)

        self._apply_theme_and_setup()

    def _apply_theme_and_setup(self) -> None:
        self.plot_widget.setBackground(self._style.widget_background_rgb)
        self.plot_item.getViewBox().setBackgroundColor(self._style.background_hex)

        self.plot_item.setDefaultPadding(0.02)

        # Grid açık
        self.plot_item.showGrid(x=True, y=True, alpha=self._style.grid_alpha)

        # Axis styling (text + axis line)
        for name in ("bottom", "left"):
            ax = self.plot_item.getAxis(name)

            # eksen çizgisi
            ax.setPen(pg.mkPen(self._style.grid_color_rgb, width=1))

            # yazılar
            ax.setTextPen(pg.mkPen(self._style.axis_text_rgb))

            # tick'ler (pyqtgraph sürümüne göre varsa)
            if hasattr(ax, "setTickPen"):
                ax.setTickPen(pg.mkPen(self._style.grid_color_rgb, width=1))

            # grid çizgileri tick pen'den türediği için bunu da set etmek uyumu artırır
            if hasattr(ax, "setGrid"):
                ax.setGrid(self._style.grid_alpha)

        self.plot_item.setLabel("bottom", "fam_end_rfu")
        self.plot_item.setLabel("left", "hex_end_rfu")

        if self.plot_item.legend is None:
            self.plot_item.addLegend(offset=(10, 10))

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

        # hover text tekrar eklenmeli çünkü clear() siliyor
        self.plot_item.addItem(self._hover_text)
        self._hover_text.hide()

        self._apply_theme_and_setup()
