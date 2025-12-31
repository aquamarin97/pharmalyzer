# app\views\widgets\pcr_plate\interaction\range_select.py
from __future__ import annotations

from typing import Set, Tuple

from PyQt5.QtCore import Qt

from app.services.interaction_store import InteractionStore
from app.utils import well_mapping


def apply_range_selection(
    store: InteractionStore,
    anchor_cell: tuple[int, int] | None,
    row: int,
    col: int,
    modifiers: Qt.KeyboardModifiers,
) -> tuple[int, int] | None:
    if store is None:
        return anchor_cell

    anchor = anchor_cell or (row, col)
    min_row, max_row = sorted((anchor[0], row))
    min_col, max_col = sorted((anchor[1], col))

    wells: Set[str] = set()
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            well = well_mapping.table_index_to_well_id(r, c)
            if well:
                wells.add(well)

    if modifiers & Qt.ControlModifier:
        updated = set(store.selected_wells)
        for w in wells:
            if w in updated:
                updated.remove(w)
            else:
                updated.add(w)
        store.set_selection(updated)
    else:
        store.set_selection(wells)

    return (row, col)