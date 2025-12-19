# app\controllers\table_controller.py
from app.willbedeleted.widgets.table_view_widget import TableViewWidget
from app.willbedeleted.config.config import TABLE_WIDGET_HEADERS
from app.willbedeleted.managers.table_manager import TableManager
from app.willbedeleted.controllers.table_controller import TableController as LegacyTableController
from app.willbedeleted.handlers.table_view_handler import TableViewHandler


class AppTableController:
    """
    UI table widget kurulumu + legacy TableController ile csv yükleme + handler bağlama.
    """
    def __init__(self, view, model, graph_controller):
        self.view = view
        self.model = model
        self.graph = graph_controller

        self.table_widget = None
        self.table_manager = None
        self.legacy = None
        self.table_handler = None

        self.setup_table_in_main_window()

    def setup_table_in_main_window(self):
        ui = self.view.ui
        original_widget = ui.table_widget_resulttable
        ui.table_widget_resulttable = TableViewWidget(original_widget)

        ui.verticalLayout_3.replaceWidget(original_widget, ui.table_widget_resulttable)
        original_widget.deleteLater()

        ui.table_widget_resulttable.set_column_expansion_ratios(
            [2, 2, 2, 10, 5, 2, 2, 2, 3, 3, 3, 3]
        )

        headers = TABLE_WIDGET_HEADERS
        manager = TableManager(ui.table_widget_resulttable, headers)
        manager.create_empty_table()

        legacy_controller = LegacyTableController(
            table_widget=ui.table_widget_resulttable,
            model=None
        )

        handler = TableViewHandler(
            table_widget=ui.table_widget_resulttable,
            model=legacy_controller.model,
            data_manager=self.model.data_manager,
            graph_drawer=self.model.graph_drawer,  # GraphDrawer GraphController'da initialize ediliyor
        )

        self.table_widget = ui.table_widget_resulttable
        self.table_manager = manager
        self.legacy = legacy_controller
        self.table_handler = handler

    # range setters (analysis spinbox kullanıyor)
    def set_carrier_range(self, val: float):
        self.legacy.set_carrier_range(val)

    def set_uncertain_range(self, val: float):
        self.legacy.set_uncertain_range(val)

    def load_csv_to_table(self):
        self.legacy.load_csv()
        self.table_widget.setModel(self.legacy.model)

        # Handler'e güncel model ata
        self.table_handler.model = self.legacy.model
        self.table_handler.table_widget.setModel(self.table_handler.model)
