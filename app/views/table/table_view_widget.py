# app\views\table\table_view_widget.py
from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QHeaderView, QTableView


class TableViewWidget(QTableView):
    def __init__(self, original_table: QTableView):
        super().__init__(original_table.parent())

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

        header = self.horizontalHeader()
        header.setFixedHeight(50)
        header.setDefaultAlignment(Qt.AlignCenter)  # <-- text-align yerine

        # İstersen: header resize mode sabit kalsın (manuel width veriyoruz)
        header.setSectionResizeMode(QHeaderView.Fixed)

        self._resize_pending = False
        self.column_expansion_ratios = []
        self.viewport().installEventFilter(self)

    def setModel(self, model):
        super().setModel(model)
        QTimer.singleShot(0, self.adjust_column_widths)  # model set edilince uygula

    def set_column_expansion_ratios(self, ratios: list[int]):
        self.column_expansion_ratios = ratios
        QTimer.singleShot(0, self.adjust_column_widths)

    def eventFilter(self, obj, event):
        if obj == self.viewport() and event.type() == QEvent.Resize:
            if not self._resize_pending:
                self._resize_pending = True
                QTimer.singleShot(0, self._apply_resize)
        return super().eventFilter(obj, event)

    def _apply_styles_to_table(self):
        self.setStyleSheet(
            "QTableView {"
            "background-color: #d9d9d9;"
            "border: 1px solid #d6d6d6;"
            "gridline-color: purple;"
            "color: #333333;"
            "}"
            "QTableView::item:selected {"
            "background-color: #2b78da;"
            "color: white;"
            "}"
            "QTableView::item:selected:!active {"
            "background-color: #2b78da;"
            "color: white;"
            "}"
        )
        self.horizontalHeader().setStyleSheet(
            "QHeaderView::section {"
            "background-color: #4ca1af;"
            "font-family: 'Arial';"
            "color: white;"
            "font-size: 15px;"
            "font-weight: bold;"
            "border: 1px solid #d6d6d6;"
            "padding: 3px 0;"
            "}"
        )

    def adjust_column_widths(self):
        model = self.model()
        if model is None:
            return

        col_count = model.columnCount()
        if col_count <= 0:
            return

        ratios = self.column_expansion_ratios or [1] * col_count
        if len(ratios) != col_count:
            ratios = [1] * col_count
            self.column_expansion_ratios = ratios

        total_width = self.viewport().width()
        ratio_sum = sum(ratios) or 1

        used = 0
        for i in range(col_count):
            if i == col_count - 1:
                w = max(0, total_width - used)  # kalan
            else:
                w = int(total_width * (ratios[i] / ratio_sum))
                used += w
            self.setColumnWidth(i, w)

    def _apply_resize(self):
        self._resize_pending = False
        self.adjust_column_widths()
