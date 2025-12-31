# app\views\widgets\pcr_plate\interaction\header_select.py
from __future__ import annotations

from typing import Set

from app.services.interaction_store import InteractionStore


def toggle_header_selection(store: InteractionStore, wells: Set[str]) -> None:
    if store is None or not wells:
        return

    selected = set(store.selected_wells)
    selected_count = len(selected & wells)
    total = len(wells)

    if selected_count == total or selected_count > total / 2:
        selected -= wells
    else:
        selected |= wells

    store.set_selection(selected)