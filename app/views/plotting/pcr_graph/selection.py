from __future__ import annotations

from typing import Set

from . import hit_test


def collect_selected_wells(r) -> Set[str]:
    if r._store is None:
        return set()
    return set(r._store.selected_wells)


def add_to_selection(r, well: str) -> None:
    if well in r._selection_buffer:
        return
    r._selection_buffer.add(well)
    if r._store is None:
        return

    updated = set(r._store.selected_wells)
    updated.add(well)
    r._store.set_selection(updated)


def handle_rectangle_select(r, eclick, erelease) -> Set[str]:
    """
    Dikdörtgen içindeki kuyuları döndür.

    Bu fonksiyon InteractionStore'daki seçim durumunu değiştirmez; yalnızca
    görsel vurgulama için kullanılacak kuyu kümesini hesaplar.
    """
    if (
        eclick.xdata is None
        or erelease.xdata is None
        or eclick.ydata is None
        or erelease.ydata is None
    ):
        return set()

    x0, x1 = sorted([eclick.xdata, erelease.xdata])
    y0, y1 = sorted([eclick.ydata, erelease.ydata])
    wells_in_rect = hit_test.find_wells_in_rect(r, x0, x1, y0, y1)

    return wells_in_rect
