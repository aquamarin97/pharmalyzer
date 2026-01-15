# app/views/plotting/pcr_graph_pg/interaction_handlers_pg.py
from __future__ import annotations

from typing import Optional, Set


from .hit_test import nearest_well, wells_in_rect, wells_in_rect_centers
from .render_scheduler_pg import schedule_render
from .overlays_pg import update_overlays
from time import perf_counter

def pixel_tol_in_data(renderer) -> tuple[float, float]:
    pixel = renderer._view_box.viewPixelSize()
    if pixel is None:
        return 0.1, 0.1
    # 6 piksel yerine 3 piksel (daha hassas ve profesyonel bir seçim alanı)
    return abs(pixel[0] * 2), abs(pixel[1] * 2)


def collect_preview_wells(renderer) -> Set[str]:
    if renderer._store is not None:  # noqa
        return set(renderer._store.preview_wells)  # noqa
    return set(renderer._rect_preview_wells)  # noqa

def set_rect_preview(renderer, wells: Set[str]) -> None:
    if wells == renderer._rect_preview_wells:  # noqa
        return
    renderer._rect_preview_wells = wells  # noqa
    if renderer._store is not None:  # noqa
        renderer._store.set_preview(wells)  # noqa
    renderer._update_preview_proxy(wells)  # noqa

    change = renderer._apply_interaction_styles(  # noqa
        hovered=renderer._hover_well,  # noqa
        selected=set(renderer._store.selected_wells) if renderer._store else set(),  # noqa
        preview=collect_preview_wells(renderer),
    )
    update_overlays(renderer, change)


def on_store_preview_changed(renderer, wells: Set[str]) -> None:
    renderer._rect_preview_wells = set(wells or set())  # noqa
    renderer._update_preview_proxy(renderer._rect_preview_wells)  # noqa
    change = renderer._apply_interaction_styles(  # noqa
        hovered=renderer._hover_well,  # noqa
        selected=set(renderer._store.selected_wells) if renderer._store else set(),  # noqa
        preview=collect_preview_wells(renderer),
    )
    update_overlays(renderer, change)
    schedule_render(renderer, full=False, overlay=True)


def handle_hover(renderer, pos: Optional[tuple[float, float]]) -> None:
    if pos is None:
        _clear_hover(renderer)
        return

    x, y = pos
    tol_x, tol_y = pixel_tol_in_data(renderer)
    
    well = nearest_well(
        renderer._spatial_index,
        renderer._well_geoms,
        x, y,
        tol_x, tol_y,
        fam_visible=renderer._fam_visible,
        hex_visible=renderer._hex_visible,
    )

    # Eğer well None ise (yani mesafe tol_x/y'den büyükse), hover'ı temizle
    if renderer._store is not None:
        if renderer._store.hover_well != well: # Gereksiz güncellemeyi engelle
            renderer._store.set_hover(well)
    else:
        renderer.set_hover(well)

def _clear_hover(renderer):
    if renderer._store is not None:
        renderer._store.set_hover(None)
    else:
        renderer.set_hover(None)
        
def handle_click(renderer, pos: tuple[float, float], *, ctrl_pressed: bool) -> None:
    if renderer._store is None:  # noqa
        return

    x, y = pos
    tol_x, tol_y = pixel_tol_in_data(renderer)
    well = nearest_well(
        renderer._spatial_index,  # noqa
        renderer._well_geoms,  # noqa
        x,
        y,
        tol_x,
        tol_y,
        fam_visible=renderer._fam_visible,  # noqa
        hex_visible=renderer._hex_visible,  # noqa
    )

    # boş yere tıklandıysa
    if well is None:
        if not ctrl_pressed:
            renderer._store.set_selection(set())  # noqa
        return

    if ctrl_pressed:
        renderer._store.toggle_wells({well})  # noqa
    else:
        current = set(renderer._store.selected_wells)  # noqa
        if len(current) == 1 and well in current:
            renderer._store.set_selection(set())  # noqa
        else:
            renderer._store.set_selection({well})  # noqa

def handle_drag(renderer, start: tuple[float, float], current: tuple[float, float], *, finished: bool) -> None:
    if finished:
        if renderer._drag_throttle_timer.isActive():  # noqa
            renderer._drag_throttle_timer.stop()  # noqa
        renderer._pending_drag = None  # noqa
        renderer._last_drag_ts = perf_counter()  # noqa
        _apply_drag_update(renderer, start, current, finished=True)
        return

    now = perf_counter()
    elapsed_ms = (now - renderer._last_drag_ts) * 1000.0  # noqa
    if elapsed_ms < renderer._drag_throttle_ms:  # noqa
        renderer._pending_drag = (start, current)  # noqa
        if not renderer._drag_throttle_timer.isActive():  # noqa
            wait_ms = max(0, int(renderer._drag_throttle_ms - elapsed_ms))  # noqa
            renderer._drag_throttle_timer.start(wait_ms)  # noqa
        return

    renderer._last_drag_ts = now  # noqa
    _apply_drag_update(renderer, start, current, finished=False)


def flush_pending_drag(renderer) -> None:
    pending = renderer._pending_drag  # noqa
    renderer._pending_drag = None  # noqa
    if pending is None:
        return
    start, current = pending
    renderer._last_drag_ts = perf_counter()  # noqa
    _apply_drag_update(renderer, start, current, finished=False)


def _apply_drag_update(renderer, start: tuple[float, float], current: tuple[float, float], *, finished: bool) -> None:
    x0, y0 = start
    x1, y1 = current
    rect_x, rect_y = min(x0, x1), min(y0, y1)
    w, h = abs(x1 - x0), abs(y1 - y0)

    renderer._rect_roi.setPos((rect_x, rect_y))  # noqa
    renderer._rect_roi.setSize((w, h))  # noqa
    renderer._rect_roi.setVisible(not finished)  # noqa

    if finished:
        set_rect_preview(renderer, set())
        schedule_render(renderer, full=False, overlay=True)
        return

    wells = wells_in_rect_centers(
        renderer._well_center_ids,  # noqa
        renderer._well_centers,  # noqa
        renderer._well_center_has_fam,  # noqa
        renderer._well_center_has_hex,  # noqa
        x0,
        x1,
        y0,
        y1,
        fam_visible=renderer._fam_visible,  # noqa
        hex_visible=renderer._hex_visible,  # noqa
    )
    if not wells:
        wells = wells_in_rect(
            renderer._spatial_index,  # noqa
            renderer._well_geoms,  # noqa
            x0,
            x1,
            y0,
            y1,
            fam_visible=renderer._fam_visible,  # noqa
            hex_visible=renderer._hex_visible,  # noqa
        )
    set_rect_preview(renderer, wells)
    schedule_render(renderer, full=False, overlay=True)