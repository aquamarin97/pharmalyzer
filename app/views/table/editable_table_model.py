from __future__ import annotations

from typing import Any, List

import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QBrush, QColor


class EditableTableModel(QAbstractTableModel):
    INSUFFICIENT_DNA = "Yetersiz DNA"
    EMPTY_WELL = "Boş Kuyu"
    OUTLIER = "Riskli Alan"
    SAFE_ZONE = "Güvenli Bölge"

    def __init__(
        self,
        data: pd.DataFrame,
        dropdown_column: int,
        dropdown_options: List[str],
        carrier_range: float,
        uncertain_range: float,
    ):
        super().__init__()
        self._data = data.copy(deep=False)  # UI tarafı için yeterli
        self.headers = list(self._data.columns)

        self.dropdown_column = dropdown_column
        self.dropdown_options = dropdown_options

        self.warning_orange_brush = QBrush(QColor(230, 90, 50))  # kırmızımsı turuncu

        self.carrier_range = carrier_range
        self.uncertain_range = uncertain_range

    def setHorizontalHeaderLabels(self, headers: List[str]):
        self.headers = headers

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self.headers):
                return self.headers[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._get_display_data(index)

        if role == Qt.BackgroundRole:
            return self._get_background_brush(index)

        return None

    def _get_display_data(self, index: QModelIndex) -> str:
        value = self._data.iloc[index.row(), index.column()]
        if pd.isna(value):
            column_name = self._data.columns[index.column()]
            if column_name in ("İstatistik Oranı", "Standart Oranı"):
                return "-"
            return ""
        return str(value)

    def _get_background_brush(self, index: QModelIndex) -> QBrush | None:
        col = index.column()
        value = self._data.iloc[index.row(), col]

        # dropdown
        if col == self.dropdown_column:
            return self._get_dropdown_brush(str(value))

        # threshold columns
        for cname in ("İstatistik Oranı", "Standart Oranı"):
            if cname in self._data.columns and col == self._data.columns.get_loc(cname):
                return self._get_threshold_brush(value)

        # regression column
        if "Regresyon" in self._data.columns and col == self._data.columns.get_loc("Regresyon"):
            return self._get_regression_brush(str(value))

        return None

    def _get_dropdown_brush(self, value: str) -> QBrush | None:
        opts = self.dropdown_options
        if not opts:
            return None

        if value == opts[0]:
            return QBrush(QColor("#A9D08E"))  # yeşil
        if len(opts) > 1 and value == opts[1]:
            return QBrush(QColor("#FFE599"))  # sarı
        if len(opts) > 2 and value == opts[2]:
            return QBrush(QColor("#E87E2C"))  # turuncu
        if len(opts) > 3 and value == opts[3]:
            return QBrush(QColor("#B4A7D6"))  # mor
        if len(opts) > 4 and value == opts[4]:
            return QBrush(QColor("#FF6B6B"))  # kırmızı
        return None

    def _get_threshold_brush(self, value: Any) -> QBrush | None:
        try:
            v = float(value)
            carrier = float(self.carrier_range)
            uncertain = float(self.uncertain_range)
        except (TypeError, ValueError):
            return None

        if v >= uncertain:
            return QBrush(QColor("#A9D08E"))  # yeşil
        if carrier < v <= uncertain:
            return QBrush(QColor("#E87E2C"))  # turuncu
        if v <= carrier:
            return QBrush(QColor("#FFE599"))  # sarı
        return None

    def _get_regression_brush(self, value: str) -> QBrush | None:
        if value == self.OUTLIER:
            return self.warning_orange_brush
        if value == self.SAFE_ZONE:
            return QBrush(QColor("#A9D08E"))
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.EditRole and index.isValid():
            if index.column() == self.dropdown_column:
                self._data.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        flags = super().flags(index)
        if index.column() == self.dropdown_column:
            flags |= Qt.ItemIsEditable
        return flags

    # (opsiyonel) Controller'ın df güncellemesini kolaylaştırır
    def set_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._data = df.copy(deep=False)
        self.headers = list(self._data.columns)
        self.endResetModel()
