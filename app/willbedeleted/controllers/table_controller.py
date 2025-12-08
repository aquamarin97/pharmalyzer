import pandas as pd
from PyQt5.QtCore import QObject

from app.willbedeleted.config.config import (CSV_FILE_HEADERS, DROPDOWN_COLUMN, DROPDOWN_OPTIONS,
                           ROUND_COLUMNS, TABLE_WIDGET_HEADERS)
from app.willbedeleted.managers.csv_manager import CSVManager
from app.willbedeleted.models.drop_down_delegate import DropDownDelegate
from app.willbedeleted.models.editable_table_model import EditableTableModel


class TableController(QObject):
    """
    Tablonun veri kaynaklarıyla etkileşimini kontrol eden sınıf.
    """

    def __init__(self, table_widget, model=None):
        super().__init__()
        self.table_widget = table_widget
        self.model = model
        self.dropdown_column = DROPDOWN_COLUMN
        self.dropdown_options = DROPDOWN_OPTIONS
        self.round_columns = ROUND_COLUMNS
        self.carrier_range = 0.5999
        self.uncertain_range = 0.6199
        # DropDownDelegate'i bir kez oluştur
        self.dropdown_delegate = DropDownDelegate(
            options=self.dropdown_options,
            parent=self.table_widget,
        )

    def set_carrier_range(self, carrier_range):
        self.carrier_range = carrier_range

    def set_uncertain_range(self, uncertain_range):
        self.uncertain_range = uncertain_range

    def load_csv(self):
        try:
            df = self._get_csv_data()
            df = self._round_columns(df)
            df = self._filter_columns(df)

            self._update_model(df)
        except Exception as e:
            print(f"CSV yüklenirken hata oluştu: {e}")

    def _get_csv_data(self):
        """CSV verisini DataFrame olarak döndürür."""
        return CSVManager.get_csv_df()

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
        # Sütun indeksini bul
        dropdown_column_index = df.columns.get_loc(self.dropdown_column)

        # Modeli oluştur ve tabloya bağla
        self.model = EditableTableModel(
            dropdown_column=dropdown_column_index,  # Sütun indeksi kullanılır
            dropdown_options=self.dropdown_options,
            carrier_range=self.carrier_range,
            uncertain_range=self.uncertain_range,
        )
        self.model._data = df
        self.model.setHorizontalHeaderLabels(list(df.columns))
        self.table_widget.setModel(self.model)

        # Daha önce oluşturulan DropDownDelegate'i sadece bir kez atıyoruz
        self.table_widget.setItemDelegateForColumn(
            dropdown_column_index, self.dropdown_delegate
        )
