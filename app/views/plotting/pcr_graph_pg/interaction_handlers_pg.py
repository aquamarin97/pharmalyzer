# app/views/plotting/pcr_graph_pg/interaction_handlers_pg.py
from __future__ import annotations

from typing import Optional, Set

from app.utils import well_mapping

from .hit_test import nearest_well, wells_in_rect
from .render_scheduler_pg import schedule_render
from .overlays_pg import update_overlays


def pixel_tol_in_data(renderer) -> tuple[float, float]:
    pixel = renderer._view_box.viewPixelSize()  # noqa
    if pixel is None:
        return 0.1, 0.1
    return abs(pixel[0] * 6), abs(pixel[1] * 6)


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

    change = renderer._apply_interaction_styles(  # noqa
        hovered=renderer._hover_well,  # noqa
        selected=set(renderer._store.selected_wells) if renderer._store else set(),  # noqa
        preview=collect_preview_wells(renderer),
    )
    update_overlays(renderer, change)


def on_store_preview_changed(renderer, wells: Set[str]) -> None:
    renderer._rect_preview_wells = set(wells or set())  # noqa
    change = renderer._apply_interaction_styles(  # noqa
        hovered=renderer._hover_well,  # noqa
        selected=set(renderer._store.selected_wells) if renderer._store else set(),  # noqa
        preview=collect_preview_wells(renderer),
    )
    update_overlays(renderer, change)
    schedule_render(renderer, full=False, overlay=True)


def handle_hover(renderer, pos: Optional[tuple[float, float]]) -> None:
    if pos is None:
        if renderer._store is not None:  # noqa
            renderer._store.set_hover(None)  # noqa
        else:
            renderer.set_hover(None)
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

    if renderer._store is not None:  # noqa
        renderer._store.set_hover(well)  # noqa
    else:
        renderer.set_hover(well)


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
