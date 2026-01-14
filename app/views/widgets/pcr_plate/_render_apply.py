# app/views/widgets/pcr_plate/_render_apply.py
from __future__ import annotations

from typing import Set

from PyQt5.QtCore import Qt
from app.utils import well_mapping


def on_selection_changed(widget, selected_wells: Set[str]) -> None:
    prev = widget._last_selected_wells
    new = set(selected_wells or set())

    added = new - prev
    removed = prev - new

    def apply_well(well_id: str, is_selected: bool) -> None:
        try:
            r, c = well_mapping.well_id_to_table_index(well_id)
        except ValueError:
            return
        item = widget.table.item(r, c)
        if not item:
            return
        if is_selected:
            item.setBackground(widget.COLOR_SELECTED)
            item.setForeground(Qt.white)
        else:
            item.setBackground(widget.COLOR_BASE)
            item.setForeground(Qt.black)

    for w in added:
        apply_well(w, True)
    for w in removed:
        apply_well(w, False)

    widget._last_selected_wells = new

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

    widget.table.set_selected_headers(selected_rows, selected_cols)


def on_hover_changed(widget, well: str | None) -> None:
    if well is None:
        if widget._hover_row is None and widget._hover_col is None:
            return
        widget._hover_row = None
        widget._hover_col = None
    else:
        try:
            r, c = well_mapping.well_id_to_table_index(well)
        except ValueError:
            r, c = None, None
        if r == widget._hover_row and c == widget._hover_col:
            return
        widget._hover_row, widget._hover_col = r, c

    widget.table.viewport().update()


def on_preview_changed(widget, wells: Set[str]) -> None:
    preview_cells: Set[tuple[int, int]] = set()
    for well in wells or set():
        try:
            preview_cells.add(well_mapping.well_id_to_table_index(well))
        except ValueError:
            continue
    widget._preview_cells = preview_cells
    widget.table.set_preview_cells(widget._preview_cells)
