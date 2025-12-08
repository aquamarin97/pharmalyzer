import pyqtgraph as pg
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy

from app.willbedeleted.managers.csv_manager import CSVManager
from app.willbedeleted.managers.regression_plot_manager import RegressionPlotManager


class RegressionGraphViewer:
    """
    Regresyon grafiğini PyQtGraph ile gösterir.
    """
    def __init__(self, container_widget):
        self.container_widget = container_widget

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Dark theme benzeri
        pg.setConfigOptions(antialias=True)
        self.plot_widget.setBackground((10, 10, 10))

        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.showGrid(x=True, y=True, alpha=0.25)
        self.plot_item.setLabel("bottom", "fam_end_rfu")
        self.plot_item.setLabel("left", "hex_end_rfu")
        self.plot_item.addLegend(offset=(10, 10))

        self.main_layout = QVBoxLayout()
        self.container_widget.setLayout(self.main_layout)
        self.main_layout.addWidget(self.plot_widget)

        self._hover_proxy = None  # Signal proxy (mouse move)
        self._hover_text = pg.TextItem(anchor=(0, 1), color=(255, 255, 255))
        self._hover_text.setZValue(999)
        self.plot_item.addItem(self._hover_text)
        self._hover_text.hide()

    def update_graph(self):
        try:
            df = CSVManager.get_csv_df()

            plot_manager = RegressionPlotManager(df)
            plot_manager.render_on_plotitem(
                self.plot_item,
                enable_hover=True,
                hover_text_item=self._hover_text,
            )
        except Exception as e:
            print(f"Grafik güncelleme hatası: {e}")

    def reset_regression_graph(self):
        self.plot_item.clear()
        self.plot_item.addLegend(offset=(10, 10))
