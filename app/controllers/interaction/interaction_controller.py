# app\controllers\interaction\interaction_controller.py
from __future__ import annotations

from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRDataService
from app.views.widgets.pcr_graph_view import PCRGraphView
from app.views.widgets.pcr_plate.pcr_plate_widget import PCRPlateWidget
from app.views.widgets.regression_graph_view import RegressionGraphView
from app.controllers.table.table_interaction_controller import TableInteractionController


class InteractionController:
    """
    Widget'ları InteractionStore etrafında kablolamak için hafif yardımcı.
    State/iş mantığı içermez.
    """

    def __init__(
        self,
        store: InteractionStore,
        *,
        plate_widget: PCRPlateWidget,
        table_interaction: TableInteractionController,
        regression_graph_view: RegressionGraphView,
        pcr_graph_view: PCRGraphView,
        pcr_data_service: PCRDataService,
    ):
        self.store = store
        self.plate_widget = plate_widget
        self.table_interaction = table_interaction
        self.regression_graph_view = regression_graph_view
        self.pcr_graph_view = pcr_graph_view
        self.pcr_data_service = pcr_data_service

        self._wire()

    def _wire(self) -> None:
        self.plate_widget.set_interaction_store(self.store)
        self.table_interaction.set_interaction_store(self.store)
        self.regression_graph_view.set_interaction_store(self.store)
        self.pcr_graph_view.set_interaction_store(self.store, self.pcr_data_service)