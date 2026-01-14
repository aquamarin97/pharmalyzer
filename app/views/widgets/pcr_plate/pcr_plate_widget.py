# app/views/widgets/pcr_plate/pcr_plate_widget.py
from __future__ import annotations

from typing import Set

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemView, QWidget, QVBoxLayout

from app.services.interaction_store import InteractionStore
from app.views.widgets.pcr_plate.pcr_plate_table import PlateTable

from ._ui_setup import configure_headers, setup_grid, resize_columns_to_fit_safe
from ._store_binding import bind_store
from ._mouse_handlers import (
    handle_mouse_move,
    handle_mouse_press,
    handle_mouse_release,
)
from ._render_apply import (
    on_selection_changed,
    on_hover_changed,
    on_preview_changed,
)


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

        # state
        self._store: InteractionStore | None = None
        self._hover_row: int | None = None
        self._hover_col: int | None = None
        self._preview_cells: Set[tuple[int, int]] = set()
        self._anchor_cell: tuple[int, int] | None = None

        # drag selection (interaction obj)
        from app.views.widgets.pcr_plate.interaction.drag_select import DragSelection
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

        configure_headers(self.table, min_col_width=self.MIN_COLUMN_WIDTH, row_height=self.ROW_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

        setup_grid(
            widget=self,
            table=self.table,
        )
        self._resize_columns_to_fit()

    # ---- interaction store ----
    def set_interaction_store(self, store: InteractionStore) -> None:
        bind_store(
            widget=self,
            store=store,
            on_selection_changed=self._on_selection_changed,
            on_hover_changed=self._on_hover_changed,
            on_preview_changed=self._on_preview_changed,
        )

    # ---- mouse events (delegate) ----
    def _handle_mouse_move(self, event):
        return handle_mouse_move(self, event)

    def _handle_mouse_press(self, event):
        return handle_mouse_press(self, event)

    def _handle_mouse_release(self, event) -> None:
        return handle_mouse_release(self, event)

    # ---- interaction callbacks (delegate) ----
    def _on_selection_changed(self, selected_wells: Set[str]) -> None:
        return on_selection_changed(self, selected_wells)

    def _on_hover_changed(self, well: str | None) -> None:
        return on_hover_changed(self, well)

    def _on_preview_changed(self, wells: Set[str]) -> None:
        return on_preview_changed(self, wells)

    # ---- styling helpers ----
    def _get_hover_index(self):
        return self._hover_row, self._hover_col

    def _table_index_to_patient_no(self, row: int, column: int) -> int:
        from app.utils import well_mapping
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
        resize_columns_to_fit_safe(self.table, self.MIN_COLUMN_WIDTH)
