from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QTableView


class TableViewWidget(QTableView):
    """
    QTableView'i genişleten ve özelleştiren bir widget sınıfı.
    """

    def __init__(self, table_widget):
        super().__init__(table_widget.parent())
        self.setObjectName(table_widget.objectName())
        self.setParent(table_widget.parent())
        self.verticalHeader().setVisible(False)

        # ScrollBar Ayarları
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setSizePolicy(table_widget.sizePolicy())
        self.setMinimumSize(table_widget.minimumSize())
        self.setFont(table_widget.font())
        self.setAlternatingRowColors(True)
        self.setMouseTracking(True)

        # Model oluştur
        self.table_model = QStandardItemModel(10, 12)  # 10 satır, 12 sütun
        self.setModel(self.table_model)

        # Stil uygulaması
        self._apply_styles_to_table()

        # Genişleme katsayıları tanımlama
        self.column_expansion_ratios = [1] * self.model().columnCount()

        # Resize olayını bağla
        self.viewport().installEventFilter(self)

    def set_column_expansion_ratios(self, ratios):
        """
        Sütun genişleme katsayılarını ayarlar.
        """
        if len(ratios) == self.model().columnCount():
            self.column_expansion_ratios = ratios
        else:
            raise ValueError("Genişleme katsayıları sütun sayısıyla eşleşmiyor.")

    def eventFilter(self, obj, event):
        if obj == self.viewport() and event.type() == QEvent.Resize:
            self.adjust_column_widths()
        return super().eventFilter(obj, event)

    def _apply_styles_to_table(self):
        """
        QTableView widget'ına stil uygular.
        """
        # QTableView arka planı ve grid rengi
        self.setStyleSheet(
            "QTableView {"
            "background-color: #d9d9d9;"
            "border: 1px solid #d6d6d6;"
            "gridline-color: purple;"
            "color: #333333;"
            "}"
        )
            # "QTableView {"
            # "background-color: yellow;"
            # "border: 1px solid blue;"
            # "gridline-color: purple;"
            # "color: cyan;"
            # "}"
        # Başlık stil ayarı
        header = self.horizontalHeader()
        header.setFixedHeight(50)
        header.setStyleSheet(
            "QHeaderView::section {"
            "background-color: #4ca1af;"
            "font-family: 'Arial';"
            "color: white;"
            "font-size: 17px;"
            "font-weight: bold;"
            "border: 1px solid #d6d6d6;"
            "padding: 3px 0;"
            "text-align: center;"
            "}"
        )

        QTimer.singleShot(80, self.adjust_column_widths)

    def adjust_column_widths(self):
        total_width = self.viewport().width()
        current_width = sum(
            self.columnWidth(i) for i in range(self.model().columnCount())
        )
        if current_width < total_width:
            extra_space = total_width - current_width
            ratio_sum = sum(self.column_expansion_ratios)
            for i in range(self.model().columnCount()):
                additional_width = int(
                    extra_space * (self.column_expansion_ratios[i] / ratio_sum)
                )
                self.setColumnWidth(i, self.columnWidth(i) + additional_width)
        else:
            for i in range(self.model().columnCount()):
                self.setColumnWidth(
                    i,
                    int(
                        total_width
                        * (
                            self.column_expansion_ratios[i]
                            / sum(self.column_expansion_ratios)
                        )
                    ),
                )
