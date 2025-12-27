# app\views\widgets\pcr_plate_widget.py
from __future__ import annotations

from typing import Set

from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygon
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout
from PyQt5.QtGui import QLinearGradient

from app.services.interaction_store import InteractionStore
from app.utils import well_mapping


class _PlateTable(QTableWidget):
    def __init__(self, parent, hover_index_getter, on_hover_move, on_mouse_press):
        super().__init__(parent)
        self._hover_index_getter = hover_index_getter
        self._on_hover_move = on_hover_move
        self._on_mouse_press = on_mouse_press
        self._selected_header_rows = set()
        self._selected_header_cols = set()
        self._preview_cells: Set[tuple[int, int]] = set() 
        
        
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)

        self._draw_corner_indicator(painter)
        self._draw_header_selection(painter)
        self._draw_hover_highlight(painter)
        painter.end()
    def _draw_header_selection(self, painter: QPainter) -> None:
        if not self._selected_header_rows and not self._selected_header_cols:
            return

        painter.save()

        accent = QColor("#3A7AFE")               # ana vurgu
        tint = QColor(58, 122, 254, 50)           # soft arkaplan
        inner_glow = QColor(255, 255, 255, 90)    # cam hissi

        # Row header (col=0)
        for r in self._selected_header_rows:
            idx = self.model().index(r, 0)
            rect = self.visualRect(idx)
            if not rect.isValid():
                continue

            rr = rect.adjusted(1, 1, -1, -1)

            # background tint
            painter.setPen(Qt.NoPen)
            painter.setBrush(tint)
            painter.drawRect(rr)

            # accent underline
            painter.setPen(QPen(accent, 2))
            painter.drawLine(rr.bottomLeft(), rr.bottomRight())

            # inner highlight
            painter.setPen(QPen(inner_glow, 1))
            painter.drawRect(rr.adjusted(1, 1, -1, -1))

        # Column header (row=0)
        for c in self._selected_header_cols:
            idx = self.model().index(0, c)
            rect = self.visualRect(idx)
            if not rect.isValid():
                continue

            rr = rect.adjusted(1, 1, -1, -1)

            painter.setPen(Qt.NoPen)
            painter.setBrush(tint)
            painter.drawRect(rr)

            painter.setPen(QPen(accent, 2))
            painter.drawLine(rr.bottomLeft(), rr.bottomRight())

            painter.setPen(QPen(inner_glow, 1))
            painter.drawRect(rr.adjusted(1, 1, -1, -1))

        painter.restore()



    def _draw_corner_indicator(self, painter: QPainter) -> None:
        corner_index = self.model().index(0, 0)
        rect = self.visualRect(corner_index)
        if not rect.isValid():
            return

        size = min(rect.width(), rect.height())
        if size <= 0:
            return

        triangle_size = max(8, int(size * 0.6))
        triangle = QPolygon(
            [
                rect.topLeft(),
                rect.topLeft() + QPoint(triangle_size, 0),
                rect.topLeft() + QPoint(0, triangle_size),
            ]
        )

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#4ca1af"))
        painter.drawPolygon(triangle)
        painter.restore()

    def _draw_hover_highlight(self, painter: QPainter) -> None:
        painter.save()

        if self._preview_cells:
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            for row_idx, col_idx in self._preview_cells:
                model_index = self.model().index(row_idx, col_idx)
                rect = self.visualRect(model_index)
                if rect.isValid():
                    painter.drawRect(rect.adjusted(1, 1, -1, -1))
                    
        row, col = self._hover_index_getter()
        if row is None or col is None:
            painter.restore()
            return

        model_index = self.model().index(row, col)
        rect = self.visualRect(model_index)
        if not rect.isValid():
            painter.restore()
            return


        is_header = (row == 0 or col == 0)
        if is_header:
            r = rect.adjusted(1, 1, -1, -1)

            accent = QColor("#3A7AFE")

            # ✅ Koyu (press) hissi: üst biraz daha az koyu, alt biraz daha koyu
            grad = QLinearGradient(r.topLeft(), r.bottomLeft())
            grad.setColorAt(0.0, QColor(0, 0, 0, 18))
            grad.setColorAt(1.0, QColor(0, 0, 0, 38))

            painter.setPen(Qt.NoPen)
            painter.setBrush(grad)
            painter.drawRect(r)

            # ✅ İnce accent border (premium vurgu)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(accent, 1))
            painter.drawRect(r)

            # ✅ Çok ince inner highlight (cam hissini tamamen kaybetmeyelim)
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
            painter.drawRect(r.adjusted(1, 1, -1, -1))

        else:
            # ✅ Body hücreleri: mevcut kırmızı çerçeve devam
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
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
        
    def set_preview_cells(self, cells: Set[tuple[int, int]]) -> None:
        if cells == self._preview_cells:
            return
        self._preview_cells = cells
        self.viewport().update()

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

        self._store: InteractionStore | None = None
        self._hover_row: int | None = None
        self._hover_col: int | None = None
        self._preview_cells: Set[tuple[int, int]] = set()
        
        
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
        self._configure_headers()

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
                self._store.previewChanged.disconnect(self._on_preview_changed)
            except Exception:
                pass

        self._store = store
        self._store.selectedChanged.connect(self._on_selection_changed)
        self._store.hoverChanged.connect(self._on_hover_changed) 
        self._store.previewChanged.connect(self._on_preview_changed)
        # mevcut state'i uygula
        self._on_selection_changed(self._store.selected_wells)
        self._on_hover_changed(self._store.hover_well)
        self._on_preview_changed(self._store.preview_wells)
    # ---- setup ----
    def _setup_grid(self) -> None:
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
        if event is None:
            self._hover_row = None
            self._hover_col = None
            if self._store is not None:
                self._store.set_hover(None)
            self.table.viewport().update()
            return

        idx = self.table.indexAt(event.pos())
        if not idx.isValid():
            return

        # ✅ header dahil her hücrede hover index’i güncelle
        self._hover_row, self._hover_col = idx.row(), idx.column()

        # ✅ sadece body hücreleri için store hover (well) güncelle
        if self._store is not None:
            well = well_mapping.table_index_to_well_id(idx.row(), idx.column())
            self._store.set_hover(well)  # well None ise None olur, sorun değil

        self.table.viewport().update()

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
        selected_rows = set()
        selected_cols = set()

        for well in selected_wells:
            r, c = well_mapping.well_id_to_table_index(well)
            selected_rows.add(r)
            selected_cols.add(c)

        self.table._selected_header_rows = selected_rows
        self.table._selected_header_cols = selected_cols
        self.table.viewport().update()


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

    def _on_preview_changed(self, wells: Set[str]) -> None:
        preview_cells: Set[tuple[int, int]] = set()
        for well in wells or set():
            try:
                preview_cells.add(well_mapping.well_id_to_table_index(well))
            except ValueError:
                continue
        self._preview_cells = preview_cells
        self.table.set_preview_cells(self._preview_cells)

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

    def _configure_headers(self) -> None:
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Fixed)
        h_header.setMinimumSectionSize(1)
        h_header.setDefaultSectionSize(self.MIN_COLUMN_WIDTH)

        v_header = self.table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        v_header.setMinimumSectionSize(self.ROW_HEIGHT)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_columns_to_fit()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._resize_columns_to_fit)

    def _resize_columns_to_fit(self) -> None:
        column_count = self.table.columnCount()
        if column_count == 0:
            return

        available_width = self.table.viewport().width()
        if available_width <= 0:
            available_width = self.table.width()

        if available_width <= 0:
            return

        # prefer readable width but prioritize fitting without scrollbars
        target_width = max(self.MIN_COLUMN_WIDTH, available_width // column_count)
        if target_width * column_count > available_width:
            target_width = max(1, available_width // column_count)

        remainder = available_width - target_width * column_count
        for col in range(column_count):
            width = target_width + (1 if col < remainder else 0)
            self.table.setColumnWidth(col, width)