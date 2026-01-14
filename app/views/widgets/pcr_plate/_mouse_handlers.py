# app/views/widgets/pcr_plate/_mouse_handlers.py
from __future__ import annotations

from PyQt5.QtCore import Qt

from app.utils import well_mapping
from app.views.widgets.pcr_plate.interaction.header_select import toggle_header_selection
from app.views.widgets.pcr_plate.interaction.range_select import apply_range_selection


def handle_mouse_move(widget, event):
    # --- mouse left / invalid area ---
    if event is None:
        return _clear_hover(widget)

    idx = widget.table.indexAt(event.pos())
    if not idx.isValid():
        return _clear_hover(widget)

    row, col = idx.row(), idx.column()

    if widget._drag_selection.dragging and event.buttons() & Qt.LeftButton and row > 0 and col > 0:
        _continue_drag(widget, row, col)

    if row == widget._hover_row and col == widget._hover_col:
        return

    widget._hover_row, widget._hover_col = row, col

    if widget._store is not None:
        well = well_mapping.table_index_to_well_id(row, col) if (row > 0 and col > 0) else None
        if well != widget._last_hover_well_sent:
            widget._store.set_hover(well)
            widget._last_hover_well_sent = well

    widget.table.viewport().update()


def handle_mouse_press(widget, event):
    if widget._store is None or event.button() != Qt.LeftButton:
        return

    idx = widget.table.indexAt(event.pos())
    if not idx.isValid():
        return

    row, col = idx.row(), idx.column()
    wells = well_mapping.wells_for_header(row, col)

    if not wells:
        widget._store.clear_selection()
        widget._anchor_cell = None
        return

    if event.modifiers() & Qt.ShiftModifier and row > 0 and col > 0:
        widget._anchor_cell = apply_range_selection(widget._store, widget._anchor_cell, row, col, event.modifiers())
        return

    if row == 0 or col == 0:
        toggle_header_selection(widget._store, wells)
        widget._anchor_cell = None
        return

    force_mode = None
    if event.modifiers() == Qt.NoModifier and row > 0 and col > 0:
        widget._store.set_selection(wells)
        force_mode = "add"

    _start_drag(widget, row, col, wells, force_mode)


def handle_mouse_release(widget, event) -> None:
    if event.button() != Qt.LeftButton:
        return

    if widget._drag_selection.dragging and widget._store is not None:
        widget._store.set_preview(set())

    widget._drag_selection.reset()


def _start_drag(widget, row: int, col: int, wells, force_mode: str | None = None) -> None:
    if widget._store is None:
        return

    selection = widget._drag_selection.start(row, col, wells, set(widget._store.selected_wells), force_mode)
    widget._anchor_cell = widget._drag_selection.anchor_cell
    if selection is not None:
        widget._store.set_selection(selection)


def _continue_drag(widget, row: int, col: int) -> None:
    if widget._store is None or not widget._drag_selection.dragging:
        return

    if not widget._drag_selection.continue_drag(row, col):
        return

    updated_selection = widget._drag_selection.apply_from_position(row, col)
    if updated_selection is not None:
        widget._store.set_selection(updated_selection)


def _clear_hover(widget):
    if widget._hover_row is None and widget._hover_col is None:
        return

    widget._hover_row = None
    widget._hover_col = None

    if widget._store is not None and widget._last_hover_well_sent is not None:
        widget._store.set_hover(None)
        widget._last_hover_well_sent = None

    widget.table.viewport().update()
