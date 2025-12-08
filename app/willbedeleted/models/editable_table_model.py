from typing import Any, List

import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QBrush, QColor

from app.willbedeleted.config.config import DROPDOWN_OPTIONS
from app.willbedeleted.managers.csv_manager import CSVManager


class EditableTableModel(QAbstractTableModel):

    
    INSUFFICIENT_DNA = "Yetersiz DNA"
    EMPTY_WELL = "Boş Kuyu"
    OUTLIER = "Riskli Alan"
    SAFE_ZONE = "Güvenli Bölge"

    def __init__(
        self,
        dropdown_column: int,
        dropdown_options: List[str],
        carrier_range: float,
        uncertain_range: float,
    ):
        """
        QTableView için düzenlenebilir bir model.
        """
        super().__init__()
        self._data = CSVManager.get_csv_df()
        self.headers = list(self._data.columns)  # Varsayılan başlıklar
        self.dropdown_column = dropdown_column
        self.dropdown_options = dropdown_options
        self.orange_brush = QBrush(QColor(230, 135, 0))  # Daha mat turuncu
        self.warning_orange_brush = QBrush(QColor(230, 90, 50))  # Daha az parlak kırmızımsı turuncu

        self.carrier_range = carrier_range
        self.uncertain_range = uncertain_range

    def setHorizontalHeaderLabels(self, headers: List[str]):
        """
        Tablonun yatay başlıklarını ayarlar.
        Args:
            headers (List[str]): Başlık listesi.
        """
        self.headers = headers

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """
        Başlık verisini döndürür.
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self.headers):
                return self.headers[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        Veriyi döndürür veya arka plan rengini belirler.
        """
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.get_display_data(index)

        if role == Qt.BackgroundRole:
            return self.get_background_brush(index)

        return None

    def get_display_data(self, index: QModelIndex) -> str:
        """
        Hücrede gösterilecek değeri belirler.
        """
        value = self._data.iloc[index.row(), index.column()]
        if pd.isna(value):
            column_name = self._data.columns[index.column()]
            if column_name in ["İstatistik Oranı", "Standart Oranı"]:
                return "-"
            return ""
        return str(value)

    def get_background_brush(self, index: QModelIndex) -> QBrush:
        """
        Hücrenin arka plan rengini belirler.
        """
        column = index.column()
        value = self._data.iloc[index.row(), column]

        if column == self.dropdown_column:
            return self.get_dropdown_brush(value)

        if column == self._data.columns.get_loc("İstatistik Oranı"):
            return self.get_threshold_brush(value)

        if column == self._data.columns.get_loc("Standart Oranı"):
            return self.get_threshold_brush(value)

        # if column == self._data.columns.get_loc("Uyarı"):
        #     return self.get_warning_brush(value)

        if column == self._data.columns.get_loc("Regresyon"):
            return self.get_regression_brush(value)

        return None

    def get_dropdown_brush(self, value: str) -> QBrush:
        """
        Drop-down sütununun renk mantığı.
        """
        if value == DROPDOWN_OPTIONS[0]:
            return QBrush(QColor("#A9D08E"))  # Pastel yeşil
        elif value == DROPDOWN_OPTIONS[1]:
            return QBrush(QColor("#FFE599"))  # Daha yoğun pastel sarı
        elif value == DROPDOWN_OPTIONS[2]:
            return QBrush(QColor("#E87E2C"))  # Daha sıcak
        elif value == DROPDOWN_OPTIONS[3]:
            return QBrush(QColor("#B4A7D6"))  # Pastel mor (Test Tekrarı için)
        elif value == DROPDOWN_OPTIONS[4]:
            return QBrush(QColor("#FF6B6B"))  # Canlı kırmızı (Yeni Numune için)


    def get_threshold_brush(self, value: float) -> QBrush:
        """
        Yazılım ve Referans Sonucu renk mantığı.
        """
        if value >= self.uncertain_range:
            return QBrush(QColor("#A9D08E"))  # Pastel yeşil
        elif self.carrier_range < value <= self.uncertain_range:
            return QBrush(QColor("#E87E2C"))  # Daha sıcak turuncu

        elif value <= self.carrier_range:
            return QBrush(QColor("#FFE599"))  # Daha yoğun pastel sarı
        return None

    # def get_warning_brush(self, value: str) -> QBrush:
    #     """
    #     Uyarı sütununun renk mantığı.
    #     """
    #     if value == self.INSUFFICIENT_DNA:
    #         return self.warning_orange_brush
    #     elif value == self.EMPTY_WELL:
    #         return QBrush(Qt.cyan)

    def get_regression_brush(self, value: str) -> QBrush:
        """
        Regresyon Sonucu sütununun renk mantığı.
        """
        if value == self.OUTLIER:
            return self.warning_orange_brush
        elif value == self.SAFE_ZONE:
            return QBrush(QColor("#A9D08E"))  # Pastel yeşil
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """
        Modelin verisini günceller.

        Args:
            index (QModelIndex): Güncellenen hücrenin indeksi.
            value (Any): Yeni değer.
            role (int): Edit rolü.

        Returns:
            bool: True, eğer değer başarılı şekilde atanmışsa.
        """
        if role == Qt.EditRole:
            # Sütun kontrolü yaparak sadece ilgili sütunu düzenlenebilir yap
            if index.column() == self.dropdown_column:
                # Yeni değeri DataFrame'e yaz
                self._data.iloc[index.row(), index.column()] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Hücrelerin özelliklerini belirler.
        """
        if not index.isValid():
            return Qt.ItemIsEnabled

        flags = super().flags(index)
        if index.column() == self.dropdown_column:
            flags |= Qt.ItemIsEditable  # Yalnızca dropdown sütunu düzenlenebilir
        return flags
