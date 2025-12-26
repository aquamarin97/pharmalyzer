from __future__ import annotations

from typing import Optional, Set

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygon
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout

from app.services.interaction_store import InteractionStore
from app.utils import well_mapping


class _PlateTable(QTableWidget):
    def __init__(self, parent, hover_index_getter, on_hover_move, on_mouse_press):
        super().__init__(parent)
        self._hover_index_getter = hover_index_getter
        self._on_hover_move = on_hover_move
        self._on_mouse_press = on_mouse_press

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)

        self._draw_corner_indicator(painter)
        self._draw_hover_highlight(painter)

        painter.end()

    def _draw_corner_indicator(self, painter: QPainter) -> None:
        corner_index = self.model().index(0, 0)
        rect = self.visualRect(corner_index)
        if not rect.isValid():
            return

        size = min(rect.width(), rect.height())
        if size <= 0:
            return

        triangle_size = max(6, size // 3)
        triangle = QPolygon(
            [
                rect.topLeft(),
                rect.topLeft() + QPoint(triangle_size, 0),
                rect.topLeft() + QPoint(0, triangle_size),
            ]
        )

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#999"))
        painter.drawPolygon(triangle)
        painter.restore()

    def _draw_hover_highlight(self, painter: QPainter) -> None:
        row, col = self._hover_index_getter()
        if row is None or col is None:
            return
        model_index = self.model().index(row, col)
        rect = self.visualRect(model_index)
        if not rect.isValid():
            return

        painter.save()
        pen = QPen(Qt.red, 2)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        painter.restore()

    def mouseMoveEvent(self, event):
        self._on_hover_move(event)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._on_hover_move(None)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._on_mouse_press(event)
        super().mousePressEvent(event)


class PCRPlateWidget(QWidget):
    """
    9x13 (header + 96 kuyu) ızgarayı çizen ve InteractionStore ile
    çift yönlü senkron çalışan plaka widget'ı.
    """

    HEADER_ROWS = 1
    HEADER_COLS = 1

    COLOR_SELECTED = QColor("#3A7AFE")  # mavi
    COLOR_BASE = QColor("#f2f2f2")
    COLOR_HEADER = QColor("#d9d9d9")
    MIN_COLUMN_WIDTH = 40
    ROW_HEIGHT = 32

    def __init__(self, original_widget: QWidget, parent: QWidget | None = None):
        super().__init__(parent or original_widget.parent())

        self.setObjectName(original_widget.objectName())
        self.setSizePolicy(original_widget.sizePolicy())
        self.setMinimumSize(original_widget.minimumSize())
        self.setMaximumSize(original_widget.maximumSize())
        self.setStyleSheet(original_widget.styleSheet())

        self._store: InteractionStore | None = None
        self._hover_row: int | None = None
        self._hover_col: int | None = None

        self.table = _PlateTable(
            self,
            hover_index_getter=self._get_hover_index,
            on_hover_move=self._handle_mouse_move,
            on_mouse_press=self._handle_mouse_press,
        )
        self.table.setMouseTracking(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

        self._setup_grid()

    # ---- interaction store ----
    def set_interaction_store(self, store: InteractionStore) -> None:
        if self._store is not None:
            try:
                self._store.selectedChanged.disconnect(self._on_selection_changed)
                self._store.hoverChanged.disconnect(self._on_hover_changed)
            except Exception:
                pass

        self._store = store
        self._store.selectedChanged.connect(self._on_selection_changed)
        self._store.hoverChanged.connect(self._on_hover_changed)
        # mevcut state'i uygula
        self._on_selection_changed(self._store.selected_wells)
        self._on_hover_changed(self._store.hover_well)

    # ---- setup ----
    def _setup_grid(self) -> None:
        self.table.setFrameShape(self.table.NoFrame)
        self.table.setLineWidth(0)
        self.table.setMidLineWidth(0)

        # viewport'un ve table'ın iç padding'ini sıfırla (style kaynaklı boşlukları temizler)
        self.table.setStyleSheet("""
        QTableWidget { border: 0px; padding: 0px; }
        QTableWidget::item { padding: 0px; margin: 0px; }
        QTableWidget QAbstractScrollArea::viewport { border: 0px; padding: 0px; }
        """)

        self.table.setRowCount(len(well_mapping.ROWS) + self.HEADER_ROWS)
        self.table.setColumnCount(len(well_mapping.COLUMNS) + self.HEADER_COLS)

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        self._populate_headers()
        self._populate_cells()
        self._apply_base_colors()
        self._resize_columns_to_fit()

    def _populate_headers(self) -> None:
        # (0,0)
        corner = self.table.item(0, 0)
        if corner:
            corner.setText("")

        # kolon header'ları (1-12)
        for idx, col in enumerate(well_mapping.COLUMNS, start=1):
            item = self.table.item(0, idx)
            if item:
                item.setText(f"{col:02d}")

        # row header'ları (A-H)
        for idx, row_label in enumerate(well_mapping.ROWS, start=1):
            item = self.table.item(idx, 0)
            if item:
                item.setText(row_label)

    def _populate_cells(self) -> None:
        for row_idx, row_label in enumerate(well_mapping.ROWS, start=1):
            for col_idx, col in enumerate(well_mapping.COLUMNS, start=1):
                item = self.table.item(row_idx, col_idx)
                if item:
                    patient_no = self._table_index_to_patient_no(row_idx, col_idx)
                    item.setText(str(patient_no))

        self._set_row_heights()

    # ---- mouse events ----
    def _handle_mouse_move(self, event):
        if self._store is None:
            return
        if event is None:
            self._store.set_hover(None)
            return
        idx = self.table.indexAt(event.pos())
        well = well_mapping.table_index_to_well_id(idx.row(), idx.column())
        self._store.set_hover(well)

    def _handle_mouse_press(self, event):
        if self._store is None or event.button() != Qt.LeftButton:
            return

        idx = self.table.indexAt(event.pos())
        wells = well_mapping.wells_for_header(idx.row(), idx.column())
        if not wells:
            self._store.clear_selection()
            return

        if event.modifiers() & Qt.ControlModifier:
            self._store.toggle_wells(wells)
        else:
            self._store.set_selection(wells)

    def _on_selection_changed(self, selected_wells: Set[str]) -> None:
        for row in range(self.HEADER_ROWS, self.table.rowCount()):
            for col in range(self.HEADER_COLS, self.table.columnCount()):
                well = well_mapping.table_index_to_well_id(row, col)
                item = self.table.item(row, col)
                if item and well:
                    if well in selected_wells:
                        item.setBackground(self.COLOR_SELECTED)
                        item.setForeground(Qt.white)
                    else:
                        item.setBackground(self.COLOR_BASE)
                        item.setForeground(Qt.black)

    def _on_hover_changed(self, well: str | None) -> None:
        if well is None:
            self._hover_row = None
            self._hover_col = None
        else:
            try:
                self._hover_row, self._hover_col = well_mapping.well_id_to_table_index(well)
            except ValueError:
                self._hover_row = None
                self._hover_col = None
        self.table.viewport().update()
        self.update()

    # ---- styling helpers ----
    def _apply_base_colors(self) -> None:
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is None:
                    continue
                if row == 0 or col == 0:
                    item.setBackground(self.COLOR_HEADER)
                else:
                    item.setBackground(self.COLOR_BASE)

    def _get_hover_index(self):
        return self._hover_row, self._hover_col

    def _table_index_to_patient_no(self, row: int, column: int) -> int:
        well_id = well_mapping.table_index_to_well_id(row, column)
        if well_id is None:
            raise ValueError(f"Invalid table index for patient number: ({row}, {column})")
        return well_mapping.well_id_to_patient_no(well_id)

    def _set_row_heights(self) -> None:
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, self.ROW_HEIGHT)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_columns_to_fit()

    def _resize_columns_to_fit(self) -> None:
        n = self.table.columnCount()
        if n == 0:
            return

        vp = self.table.viewport()
        avail = vp.width()
        if avail <= 0:
            return

        # İlk n-1 kolonu eşit dağıt
        base = max(1, avail // n)
        for c in range(n - 1):
            self.table.setColumnWidth(c, base)

        used = sum(self.table.columnWidth(c) for c in range(n - 1))

        # Son kolon kalan neyse o
        last = max(1, avail - used)
        self.table.setColumnWidth(n - 1, last)
