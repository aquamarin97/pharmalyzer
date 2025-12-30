# app\views\plotting\pcr_graph\interactions.py
from __future__ import annotations

from typing import Optional, Set

from matplotlib.widgets import RectangleSelector

from app.utils import well_mapping

from . import hit_test, selection, styles


def connect_events(r) -> None:
    r.mpl_connect("motion_notify_event", lambda event: on_motion(r, event))
    r.mpl_connect("button_press_event", lambda event: on_button_press(r, event))
    r.mpl_connect("button_release_event", lambda event: on_button_release(r, event))

    r._rect_selector = RectangleSelector(
        r.ax,
        lambda eclick, erelease: on_rectangle_select(r, eclick, erelease),
        useblit=True,
        button=[1],
        interactive=False,
        props={"edgecolor": "red", "facecolor": "none", "linewidth": 1},
    )
    r._rect_selector.connect_event("button_press_event", lambda event: on_rect_press(r, event))
    r._rect_selector.connect_event("button_release_event", lambda event: on_rect_release(r, event))
    r._rect_selector.connect_event("motion_notify_event", lambda event: on_rect_motion(r, event))


def bind_interaction_store(r, store) -> None:
    if r._store is not None:
        try:
            r._store.previewChanged.disconnect(r._preview_slot)  # type: ignore[attr-defined]
        except Exception:
            pass
    r._store = store
    if r._store is not None:
        r._preview_slot = lambda wells: on_store_preview_changed(r, wells)  # type: ignore[attr-defined]
        r._store.previewChanged.connect(r._preview_slot)


def set_hover(r, well: Optional[str]) -> None:
    r._hover_well = well if well_mapping.is_valid_well_id(well) else None
    _apply_styles(r)
    r.draw_idle()


def apply_hover_from_graph(r, well: Optional[str]) -> None:
    if r._store is not None:
        r._store.set_hover(well)
    else:
        set_hover(r, well)


def collect_preview_wells(r) -> Set[str]:
    if r._store is not None:
        return set(r._store.preview_wells)
    return set(r._rect_preview_wells)


def set_rect_preview(r, wells: Set[str]) -> None:
    if wells == r._rect_preview_wells:
        return
    r._rect_preview_wells = wells
    if r._store is not None:
        r._store.set_preview(wells)
    _apply_styles(r)
    r.draw_idle()


def on_store_preview_changed(r, wells: Set[str]) -> None:
    r._rect_preview_wells = set(wells or set())
    _apply_styles(r)
    r.draw_idle()


def on_motion(r, event) -> None:
    if r._rect_selecting:
        return

    if event.inaxes != r.ax:
        apply_hover_from_graph(r, None)
        return

    well = hit_test.find_well_at_event(r, event)
    apply_hover_from_graph(r, well)


def on_button_press(r, event) -> None:
    if event.button != 1:
        return
    if r._rect_selecting:
        return
    r._selecting = True
    r._selection_buffer.clear()


# app/views/plotting/pcr_graph/interactions.py içindeki kritik düzeltme

def on_button_release(r, event) -> None:
    if event.button != 1:
        return

    # EĞER dikdörtgen seçimi aktifse veya o an bittiyse (rect_selecting),
    # bu standart canvas olayının Store'u bozmasına izin verme.
    if r._rect_selecting:
        r._selecting = False # Güvenlik için normal modu da kapat
        return

    # Temizlik
    r._selecting = False
    r._selection_buffer.clear()


def on_rect_press(r, event) -> None:
    if event.button != 1:
        return
    r._rect_selecting = True
    r._selecting = False
    r._selection_buffer.clear()
    set_rect_preview(r, set())


def on_rect_release(r, event) -> None:
    if event.button != 1:
        return
    r._rect_selecting = False
    r._selecting = False
    set_rect_preview(r, set())


def on_rect_motion(r, event) -> None:
    if not r._rect_selecting:
        return
    if r._rect_selector is None:
        return

    x0, x1, y0, y1 = r._rect_selector.extents
    if any(v is None for v in (x0, x1, y0, y1)):
        set_rect_preview(r, set())
        return

    wells_in_rect = hit_test.find_wells_in_rect(r, x0, x1, y0, y1)
    set_rect_preview(r, wells_in_rect)


def on_rectangle_select(r, eclick, erelease) -> None:
    wells = selection.handle_rectangle_select(r, eclick, erelease)
    if not wells:
        return
    set_rect_preview(r, wells)
    _apply_styles(r)


def _apply_styles(r) -> None:
    hovered = r._hover_well
    selected = selection.collect_selected_wells(r)
    preview = collect_preview_wells(r)
    styles.apply_interaction_styles(r, hovered=hovered, selected=selected, preview=preview)