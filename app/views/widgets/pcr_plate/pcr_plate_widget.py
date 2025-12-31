# app\views\widgets\pcr_plate\pcr_plate_widget.py
# app\views\widgets\pcr_plate_widget.py
from __future__ import annotations

from typing import Set

from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygon, QLinearGradient
from PyQt5.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout

from app.services.interaction_store import InteractionStore
from app.utils import well_mapping


class _PlateTable(QTableWidget):
    def __init__(self, parent, hover_index_getter, on_hover_move, on_mouse_press, on_mouse_move=None, on_mouse_release=None):
        super().__init__(parent)
        self._hover_index_getter = hover_index_getter
        self._on_hover_move = on_hover_move
        self._on_mouse_press = on_mouse_press
        self._on_mouse_move = on_mouse_move
        self._on_mouse_release = on_mouse_release
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
        if self._on_mouse_move:
            self._on_mouse_move(event)
        else:
            self._on_hover_move(event)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._on_hover_move(None)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._on_mouse_press(event)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._on_mouse_release:
            self._on_mouse_release(event)
        super().mouseReleaseEvent(event)

    def set_preview_cells(self, cells: Set[tuple[int, int]]) -> None:
        if cells == self._preview_cells:
            return
        self._preview_cells = cells
        self.viewport().update()

    def set_selected_headers(self, rows: set[int], cols: set[int]) -> None:
        """Header seçim state'ini kapsülle; gereksiz repaint'i azalt."""
        if rows == self._selected_header_rows and cols == self._selected_header_cols:
            return
        self._selected_header_rows = rows
        self._selected_header_cols = cols
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
        self._anchor_cell: tuple[int, int] | None = None
        self._dragging: bool = False
        self._drag_mode: str | None = None
        self._drag_visited: Set[str] = set()
        self._drag_base_selection: Set[str] = set()
        self._drag_current_selection: Set[str] = set()
        self._drag_last_cell: tuple[int, int] | None = None

        # UI diff/cache
        self._last_selected_wells: Set[str] = set()
        self._last_hover_well_sent: str | None = None

        self.table = _PlateTable(
            self,
            hover_index_getter=self._get_hover_index,
            on_hover_move=self._handle_mouse_move,
            on_mouse_press=self._handle_mouse_press,
            on_mouse_move=self._handle_mouse_move,
            on_mouse_release=self._handle_mouse_release,
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
        # --- mouse left / invalid area ---
        if event is None:
            if self._hover_row is None and self._hover_col is None:
                return
            self._hover_row = None
            self._hover_col = None
            if self._store is not None and self._last_hover_well_sent is not None:
                self._store.set_hover(None)
                self._last_hover_well_sent = None
            self.table.viewport().update()
            return

        idx = self.table.indexAt(event.pos())
        if not idx.isValid():
            if self._hover_row is None and self._hover_col is None:
                return
            self._hover_row = None
            self._hover_col = None
            if self._store is not None and self._last_hover_well_sent is not None:
                self._store.set_hover(None)
                self._last_hover_well_sent = None
            self.table.viewport().update()
            return

        row, col = idx.row(), idx.column()

        # drag sadece body'de devam etsin
        if self._dragging and event.buttons() & Qt.LeftButton and row > 0 and col > 0:
            self._continue_drag(row, col)

        # hover değişmediyse repaint/store spam yapma
        if row == self._hover_row and col == self._hover_col:
            return

        self._hover_row, self._hover_col = row, col

        # sadece body hücreleri için store hover (well) güncelle
        if self._store is not None:
            well = well_mapping.table_index_to_well_id(row, col) if (row > 0 and col > 0) else None
            if well != self._last_hover_well_sent:
                self._store.set_hover(well)
                self._last_hover_well_sent = well

        self.table.viewport().update()

    def _handle_mouse_press(self, event):
        if self._store is None or event.button() != Qt.LeftButton:
            return

        idx = self.table.indexAt(event.pos())
        if not idx.isValid():
            return

        row, col = idx.row(), idx.column()
        wells = well_mapping.wells_for_header(row, col)
        if not wells:
            self._store.clear_selection()
            self._anchor_cell = None
            return

        if event.modifiers() & Qt.ShiftModifier and row > 0 and col > 0:
            self._apply_range_selection(row, col, event.modifiers())
            return

        if row == 0 or col == 0:
            self._apply_header_toggle(wells)
            self._anchor_cell = None
            return

        self._start_drag(row, col, wells)

    def _on_selection_changed(self, selected_wells: Set[str]) -> None:
        # --- body cell renklerini sadece diff ile güncelle ---
        prev = self._last_selected_wells
        new = set(selected_wells or set())

        added = new - prev
        removed = prev - new

        def apply_well(well_id: str, is_selected: bool) -> None:
            try:
                r, c = well_mapping.well_id_to_table_index(well_id)
            except ValueError:
                return
            item = self.table.item(r, c)
            if not item:
                return
            if is_selected:
                item.setBackground(self.COLOR_SELECTED)
                item.setForeground(Qt.white)
            else:
                item.setBackground(self.COLOR_BASE)
                item.setForeground(Qt.black)

        for w in added:
            apply_well(w, True)
        for w in removed:
            apply_well(w, False)

        self._last_selected_wells = new

        # --- header seçili mi? (tüm satır/sütun seçili ise) ---
        selected_rows: set[int] = set()
        selected_cols: set[int] = set()

        for r_idx in range(1, len(well_mapping.ROWS) + 1):
            row_wells = well_mapping.wells_for_header(r_idx, 0)
            if row_wells and row_wells.issubset(new):
                selected_rows.add(r_idx)

        for c_idx in range(1, len(well_mapping.COLUMNS) + 1):
            col_wells = well_mapping.wells_for_header(0, c_idx)
            if col_wells and col_wells.issubset(new):
                selected_cols.add(c_idx)

        self.table.set_selected_headers(selected_rows, selected_cols)


    def _on_hover_changed(self, well: str | None) -> None:
        # Store'dan gelen hover'ı UI'a yansıt (grafik -> plate gibi)
        if well is None:
            if self._hover_row is None and self._hover_col is None:
                return
            self._hover_row = None
            self._hover_col = None
        else:
            try:
                r, c = well_mapping.well_id_to_table_index(well)
            except ValueError:
                r, c = None, None
            if r == self._hover_row and c == self._hover_col:
                return
            self._hover_row, self._hover_col = r, c

        self.table.viewport().update()

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

    # ---- selection helpers ----
    def _apply_header_toggle(self, wells: Set[str]) -> None:
        if self._store is None or not wells:
            return

        selected = set(self._store.selected_wells)
        selected_count = len(selected & wells)
        total = len(wells)

        if selected_count == total or selected_count > total / 2:
            selected -= wells
        else:
            selected |= wells

        self._store.set_selection(selected)

    def _apply_range_selection(self, row: int, col: int, modifiers: Qt.KeyboardModifiers) -> None:
        if self._store is None:
            return

        anchor = self._anchor_cell or (row, col)
        min_row, max_row = sorted((anchor[0], row))
        min_col, max_col = sorted((anchor[1], col))

        wells: Set[str] = set()
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                well = well_mapping.table_index_to_well_id(r, c)
                if well:
                    wells.add(well)

        if modifiers & Qt.ControlModifier:
            updated = set(self._store.selected_wells)
            for w in wells:
                if w in updated:
                    updated.remove(w)
                else:
                    updated.add(w)
            self._store.set_selection(updated)
        else:
            self._store.set_selection(wells)

        self._anchor_cell = (row, col)

    def _start_drag(self, row: int, col: int, wells: Set[str]) -> None:
        if self._store is None:
            return

        self._dragging = True
        self._drag_last_cell = (row, col)
        first_well = next(iter(wells))
        self._drag_mode = "remove" if first_well in self._store.selected_wells else "add"
        self._drag_visited = set()
        self._drag_base_selection = set(self._store.selected_wells)
        self._drag_current_selection = set(self._drag_base_selection)
        self._anchor_cell = (row, col)
        self._apply_drag_wells(wells)

    def _continue_drag(self, row: int, col: int) -> None:
        if self._store is None or not self._dragging:
            return

        if (row, col) == self._drag_last_cell:
            return

        wells = well_mapping.wells_for_header(row, col)
        if not wells:
            return

        self._drag_last_cell = (row, col)
        self._apply_drag_wells(wells)

    def _apply_drag_wells(self, wells: Set[str]) -> None:
        if self._store is None or not self._dragging or not self._drag_mode:
            return

        new_wells = {w for w in wells if w not in self._drag_visited}
        if not new_wells:
            return

        self._drag_visited |= new_wells
        if self._drag_mode == "add":
            self._drag_current_selection |= new_wells
        else:
            self._drag_current_selection -= new_wells

        self._store.set_selection(self._drag_current_selection)

    def _handle_mouse_release(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return

        if self._dragging and self._store is not None:
            self._store.set_preview(set())

        self._dragging = False
        self._drag_mode = None
        self._drag_visited.clear()
        self._drag_base_selection.clear()
        self._drag_current_selection.clear()
        self._drag_last_cell = None
