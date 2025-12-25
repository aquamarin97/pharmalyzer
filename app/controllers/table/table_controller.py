# app/controllers/table/table_controller.py
import pandas as pd

from PyQt5.QtGui import QStandardItemModel

from app.constants.table_config import (
    CSV_FILE_HEADERS,
    DROPDOWN_COLUMN,
    DROPDOWN_OPTIONS,
    ITEM_STYLES,
    ROUND_COLUMNS,
    TABLE_WIDGET_HEADERS,
)
from app.controllers.table.table_interaction_controller import TableInteractionController
from app.services.data_store import DataStore
from app.services.pcr_data_service import PCRDataService
from app.views.table.editable_table_model import EditableTableModel
from app.views.table.drop_down_delegate import DropDownDelegate
from app.views.table.table_view_widget import TableViewWidget


class AppTableController:
    """
    - UI table widget kurulumu
    - DataStore'dan DF alıp EditableTableModel'e basma
    - TableInteractionController ile tıklama/enter etkileşimlerini bağlama
    """

    def __init__(self, view, model, graph_drawer=None, interaction_store=None):
        self.view = view
        self.model = model
        self.graph_drawer = graph_drawer
        self.interaction_store = interaction_store

        self.dropdown_column = DROPDOWN_COLUMN
        self.dropdown_options = DROPDOWN_OPTIONS
        self.round_columns = ROUND_COLUMNS

        self.carrier_range = 0.5999
        self.uncertain_range = 0.6199

        self.table_widget = None
        self.table_model = None
        self.table_interaction = None

        # ✅ Tek kaynak: kolon oranları burada saklanır
        self._column_ratios = [2, 2, 2, 10, 5, 2, 2, 2, 3, 3, 3, 3]

        self.setup_table_in_main_window()

    def setup_table_in_main_window(self):
        ui = self.view.ui

        original_widget = ui.table_widget_resulttable
        ui.table_widget_resulttable = TableViewWidget(original_widget)
        ui.verticalLayout_3.replaceWidget(original_widget, ui.table_widget_resulttable)
        original_widget.deleteLater()

        self.table_widget = ui.table_widget_resulttable

        empty_model = QStandardItemModel()
        empty_model.setHorizontalHeaderLabels(TABLE_WIDGET_HEADERS)
        self.table_widget.setModel(empty_model)

        # ✅ İlk kurulum
        self.table_widget.set_column_expansion_ratios(self._column_ratios)

        self.table_interaction = TableInteractionController(
            table_widget=self.table_widget,
            pcr_data_service=PCRDataService(),
            graph_drawer=self.graph_drawer,
            interaction_store=self.interaction_store,
        )

    def set_carrier_range(self, val: float):
        self.carrier_range = float(val)
        if isinstance(self.table_model, EditableTableModel):
            self.table_model.carrier_range = self.carrier_range

    def set_uncertain_range(self, val: float):
        self.uncertain_range = float(val)
        if isinstance(self.table_model, EditableTableModel):
            self.table_model.uncertain_range = self.uncertain_range

    def load_csv_to_table(self):
        df = DataStore.get_df_copy()
        if df is None or df.empty:
            raise ValueError("No data loaded. DataStore is empty.")

        df = self._round_columns(df)
        df = self._filter_columns(df)
        self._update_model(df)

    def _round_columns(self, df):
        for col, digits in self.round_columns.items():
            if col in df.columns:
                df[col] = df[col].apply(lambda x: round(x, digits) if pd.notna(x) else x)
        return df

    def _filter_columns(self, df):
        csv_headers = CSV_FILE_HEADERS
        table_headers = TABLE_WIDGET_HEADERS
        filtered_columns = [col for col in table_headers if col in csv_headers]
        return df[filtered_columns]

    def _update_model(self, df):
        if self.dropdown_column not in df.columns:
            raise ValueError(f"Dropdown kolonu bulunamadı: {self.dropdown_column}")

        dropdown_column_index = df.columns.get_loc(self.dropdown_column)

        if isinstance(self.table_model, EditableTableModel):
            self.table_model.set_dataframe(
                df,
                dropdown_column=dropdown_column_index,
                dropdown_options=self.dropdown_options,
                carrier_range=self.carrier_range,
                uncertain_range=self.uncertain_range,
            )
        else:
            self.table_model = EditableTableModel(
                data=df,
                dropdown_column=dropdown_column_index,
                dropdown_options=self.dropdown_options,
                carrier_range=self.carrier_range,
                uncertain_range=self.uncertain_range,
            )
            self.table_widget.setModel(self.table_model)
            if self.table_interaction is not None:
                self.table_interaction.attach_selection_model()

        dropdown_delegate = DropDownDelegate(
            options=self.dropdown_options,
            parent=self.table_widget,
            item_styles=ITEM_STYLES,
        )
        self.table_widget.setItemDelegateForColumn(dropdown_column_index, dropdown_delegate)

        # ✅ Model güncellendikten sonra kolon oranlarını tekrar uygula
        # Model columnCount değişmiş olabilir; TableViewWidget kendi içinde kontrol ediyor.
        self.table_widget.set_column_expansion_ratios(self._column_ratios)
