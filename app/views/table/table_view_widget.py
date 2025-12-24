# app\views\table\table_view_widget.py
# app\views\widgets\table_view_widget.py
# app/views/widgets/table_view_widget.py
from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QTableView


class TableViewWidget(QTableView):
    """
    QTableView'i genişleten ve özelleştiren widget.
    Model/headers controller tarafından set edilir.
    """

    def __init__(self, original_table: QTableView):
        super().__init__(original_table.parent())

        # Qt Designer'daki widget'ı "replaceWidget" ile değiştiriyorsun:
        self.setObjectName(original_table.objectName())
        self.setSizePolicy(original_table.sizePolicy())
        self.setMinimumSize(original_table.minimumSize())
        self.setFont(original_table.font())
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)

        self.verticalHeader().setVisible(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self._apply_styles_to_table()

        self.column_expansion_ratios = []
        self.viewport().installEventFilter(self)

    def set_column_expansion_ratios(self, ratios: list[int]):
        if self.model() is None:
            # model daha sonra set edilecekse oranları şimdilik sakla
            self.column_expansion_ratios = ratios
            return

        if len(ratios) != self.model().columnCount():
            raise ValueError("Genişleme katsayıları sütun sayısıyla eşleşmiyor.")
        self.column_expansion_ratios = ratios
        QTimer.singleShot(0, self.adjust_column_widths)

    def eventFilter(self, obj, event):
        if obj == self.viewport() and event.type() == QEvent.Resize:
            self.adjust_column_widths()
        return super().eventFilter(obj, event)

    def _apply_styles_to_table(self):
        self.setStyleSheet(
            "QTableView {"
            "background-color: #d9d9d9;"
            "border: 1px solid #d6d6d6;"
            "gridline-color: purple;"
            "color: #333333;"
            "}"
        )

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

    def adjust_column_widths(self):
        if self.model() is None:
            return

        col_count = self.model().columnCount()
        if col_count == 0:
            return

        if not self.column_expansion_ratios:
            self.column_expansion_ratios = [1] * col_count

        if len(self.column_expansion_ratios) != col_count:
            # model değiştiyse ratio da güncellenmemiş olabilir
            self.column_expansion_ratios = [1] * col_count

        total_width = self.viewport().width()
        ratio_sum = sum(self.column_expansion_ratios) or 1

        for i in range(col_count):
            w = int(total_width * (self.column_expansion_ratios[i] / ratio_sum))
            self.setColumnWidth(i, w)
