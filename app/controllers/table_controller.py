# app\controllers\table_controller.py
import pandas as pd

from app.controllers.table_interaction_controller import TableInteractionController
from app.services.data_store import DataStore
from app.services.pcr_data_service import PCRDataService
from app.willbedeleted.widgets.table_view_widget import TableViewWidget
from app.willbedeleted.config.config import (
    CSV_FILE_HEADERS,
    DROPDOWN_COLUMN,
    DROPDOWN_OPTIONS,
    ROUND_COLUMNS,
    TABLE_WIDGET_HEADERS,
)
from app.willbedeleted.managers.table_manager import TableManager
from app.willbedeleted.models.drop_down_delegate import DropDownDelegate
from app.willbedeleted.models.editable_table_model import EditableTableModel


class AppTableController:
    """
    UI table widget kurulumu + legacy TableController ile csv yükleme + handler bağlama.
    Uygulama içi tablo kurulumunu, veri yüklemeyi ve handler bağlantısını yönetir.
    """
    def __init__(self, view, model, graph_controller):
        self.view = view
        self.model = model
        self.graph = graph_controller

        self.dropdown_column = DROPDOWN_COLUMN
        self.dropdown_options = DROPDOWN_OPTIONS
        self.round_columns = ROUND_COLUMNS
        self.carrier_range = 0.5999
        self.uncertain_range = 0.6199

        self.table_widget = None
        self.table_manager = None
        self.table_model = None
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
        self.table_widget = ui.table_widget_resulttable
        self.table_manager = manager

        self.table_interaction = TableInteractionController(
            table_widget=self.table_widget,
            pcr_data_service=PCRDataService,
            graph_drawer=self.model.graph_drawer
        )


    # range setters (analysis spinbox kullanıyor)
    def set_carrier_range(self, val: float):
        self.carrier_range = val
        if isinstance(self.table_model, EditableTableModel):
            self.table_model.carrier_range = val

    def set_uncertain_range(self, val: float):
        self.uncertain_range = val
        if isinstance(self.table_model, EditableTableModel):
            self.table_model.uncertain_range = val

    def load_csv_to_table(self):
        df = DataStore.get_df_copy()
        if df is None or df.empty:
            raise ValueError("No data loaded. DataStore is empty.")

        df = self._round_columns(df)
        df = self._filter_columns(df)
        self._update_model(df)

        # Handler'e güncel model ata
        #self.table_handler.table_widget.setModel(self.table_handler.model)

    def _round_columns(self, df):
        """Belirli sütunları yuvarlar."""
        for col, digits in self.round_columns.items():
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: round(x, digits) if pd.notna(x) else x
                )
        return df

    def _filter_columns(self, df):
        """Başlıkları filtreler."""
        csv_headers = CSV_FILE_HEADERS
        table_headers = TABLE_WIDGET_HEADERS
        filtered_columns = [col for col in table_headers if col in csv_headers]
        return df[filtered_columns]

    def _update_model(self, df):
        """Tablo modelini günceller."""
        dropdown_column_index = df.columns.get_loc(self.dropdown_column)

        self.table_model = EditableTableModel(
            dropdown_column=dropdown_column_index,
            dropdown_options=self.dropdown_options,
            carrier_range=self.carrier_range,
            uncertain_range=self.uncertain_range,
        )
        self.table_model._data = df
        self.table_model.setHorizontalHeaderLabels(list(df.columns))
        self.table_widget.setModel(self.table_model)

        dropdown_delegate = DropDownDelegate(
            options=self.dropdown_options,
            parent=self.table_widget,
        )
        self.table_widget.setItemDelegateForColumn(
            dropdown_column_index, dropdown_delegate
        )