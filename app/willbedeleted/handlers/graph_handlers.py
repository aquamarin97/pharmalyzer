# app\willbedeleted\handlers\graph_handlers.py
from test_pcrgraph.GraphDrawer import GraphDrawer

from scripts.regration_graph.regression_graph_manager import \
    RegressionGraphManager


def initialize_graphics(window):
    window.graph_drawer = GraphDrawer(parent=window.ui.pcr_graph)
    layout = QtWidgets.QVBoxLayout(window.ui.pcr_graph)
    layout.addWidget(window.graph_drawer)
    layout.setContentsMargins(0, 0, 0, 0)

    window.regression_graph_manager = RegressionGraphManager(window.ui.regration_graph)

def update_regression_graph(window):
    try:
        window.regression_graph_manager.update_graph("result.csv")
    except Exception as e:
        print(f"Regresyon grafiği güncelleme hatası: {e}")
