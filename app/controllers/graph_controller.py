# # app\controllers\graph_controller.py
# from app.willbedeleted.controllers.regression_controller import RegressionGraphViewer
# from app.willbedeleted.scripts.pcr_graph_drawer import GraphDrawer


# class GraphController:
#     """
#     GraphDrawer ve regression graph yönetimi.
#     """
#     def __init__(self, view, model):
#         self.view = view
#         self.model = model

#         # RegressionGraphViewer view container ister
#         self.model.regression_graph_manager = RegressionGraphViewer(
#             self.view.ui.regration_container
#         )

#         self.initialize_graphics()

#     def initialize_graphics(self):
#         # Eski GraphDrawer'ı kaldır
#         if getattr(self.model, "graph_drawer", None) is not None:
#             self.model.graph_drawer.deleteLater()
#             self.model.graph_drawer = None

#         layout = self.view.ensure_graph_drawer()
#         self.model.graph_drawer = GraphDrawer(parent=self.view.ui.PCR_graph_container)
#         layout.addWidget(self.model.graph_drawer)

#     def reset_regression_graph(self):
#         self.plot_item.clear()
#         if hasattr(self, "_hover_text") and self._hover_text is not None:
#             self._hover_text.hide()
#         self.plot_item.addLegend(offset=(10, 10))

#         # Eğer manager proxy tutuyorsa, onu da kopar:
#         if hasattr(self, "plot_manager") and self.plot_manager is not None:
#             self.plot_manager.detach_hover()

#     def update_regression_graph(self):
#         mgr = self.model.regression_graph_manager
#         if mgr:
#             mgr.update_graph()
