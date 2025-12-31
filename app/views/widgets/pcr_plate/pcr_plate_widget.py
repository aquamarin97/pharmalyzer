# app\views\widgets\pcr_plate\pcr_plate_widget.py
# app\views\widgets\pcr_plate_widget.py
from __future__ import annotations

from typing import Set

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QWidget, QVBoxLayout

from app.services.interaction_store import InteractionStore
from app.utils import well_mapping
from app.views.widgets.pcr_plate.interaction.drag_select import DragSelection
from app.views.widgets.pcr_plate.interaction.header_select import toggle_header_selection
from app.views.widgets.pcr_plate.interaction.range_select import apply_range_selection
from app.views.widgets.pcr_plate.pcr_plate_table import PlateTable
from app.views.widgets.pcr_plate.setup.grid_setup import initialize_grid
from app.views.widgets.pcr_plate.setup.resizing import resize_columns_to_fit


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
        self._drag_selection = DragSelection()

        # UI diff/cache
        self._last_selected_wells: Set[str] = set()
        self._last_hover_well_sent: str | None = None

        self.table = PlateTable(
            self,
            hover_index_getter=self._get_hover_index,
            on_hover_move=self._handle_mouse_move,
            on_mouse_press=self._handle_mouse_press,
            on_mouse_move=self._handle_mouse_move,
            on_mouse_release=self._handle_mouse_release,
        )
        self.table.setMouseTracking(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
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
        initialize_grid(
            self.table,
            header_rows=self.HEADER_ROWS,
            header_cols=self.HEADER_COLS,
            row_height=self.ROW_HEIGHT,
            header_color=self.COLOR_HEADER,
            base_color=self.COLOR_BASE,
            table_index_to_patient_no=self._table_index_to_patient_no,
        )
        self._resize_columns_to_fit()

    def _configure_headers(self) -> None:
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Fixed)
        h_header.setMinimumSectionSize(1)
        h_header.setDefaultSectionSize(self.MIN_COLUMN_WIDTH)

        v_header = self.table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        v_header.setMinimumSectionSize(self.ROW_HEIGHT)

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

        if self._drag_selection.dragging and event.buttons() & Qt.LeftButton and row > 0 and col > 0:
            self._continue_drag(row, col)

        if row == self._hover_row and col == self._hover_col:
            return

        self._hover_row, self._hover_col = row, col

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
            self._anchor_cell = apply_range_selection(self._store, self._anchor_cell, row, col, event.modifiers())
            return

        if row == 0 or col == 0:
            toggle_header_selection(self._store, wells)
            self._anchor_cell = None
            return

        self._start_drag(row, col, wells)

    def _handle_mouse_release(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return

        if self._drag_selection.dragging and self._store is not None:
            self._store.set_preview(set())

        self._drag_selection.reset()

    # ---- interaction helpers ----
    def _start_drag(self, row: int, col: int, wells: Set[str]) -> None:
        if self._store is None:
            return

        selection = self._drag_selection.start(row, col, wells, set(self._store.selected_wells))
        self._anchor_cell = self._drag_selection.anchor_cell
        if selection is not None:
            self._store.set_selection(selection)

    def _continue_drag(self, row: int, col: int) -> None:
        if self._store is None or not self._drag_selection.dragging:
            return

        if not self._drag_selection.continue_drag(row, col):
            return

        updated_selection = self._drag_selection.apply_from_position(row, col)
        if updated_selection is not None:
            self._store.set_selection(updated_selection)

    # ---- interaction callbacks ----
    def _on_selection_changed(self, selected_wells: Set[str]) -> None:
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
    def _get_hover_index(self):
        return self._hover_row, self._hover_col

    def _table_index_to_patient_no(self, row: int, column: int) -> int:
        well_id = well_mapping.table_index_to_well_id(row, column)
        if well_id is None:
            raise ValueError(f"Invalid table index for patient number: ({row}, {column})")
        return well_mapping.well_id_to_patient_no(well_id)

    # ---- resize ----
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_columns_to_fit()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._resize_columns_to_fit)

    def _resize_columns_to_fit(self) -> None:
        resize_columns_to_fit(self.table, self.MIN_COLUMN_WIDTH)
