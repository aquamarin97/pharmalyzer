# app/views/plotting/pcr_graph_pg/render_scheduler_pg.py
from __future__ import annotations

from time import perf_counter


def schedule_render(renderer, *, full: bool = False, overlay: bool = False, force_flush: bool = False) -> None:
    renderer._pending_full_draw = renderer._pending_full_draw or full  # noqa
    renderer._pending_overlay = renderer._pending_overlay or overlay  # noqa

    if force_flush:
        if renderer._render_timer.isActive():  # noqa
            renderer._render_timer.stop()  # noqa
        flush_pending_render(renderer)
        return

    elapsed_ms = (perf_counter() - renderer._last_render_ts) * 1000.0  # noqa
    delay = max(0, int(renderer._frame_interval_ms - elapsed_ms))  # noqa
    if renderer._render_timer.isActive():  # noqa
        return
    renderer._render_timer.start(delay)  # noqa


def flush_pending_render(renderer) -> None:
    full = renderer._pending_full_draw  # noqa
    overlay = renderer._pending_overlay or full  # noqa
    renderer._pending_full_draw = False  # noqa
    renderer._pending_overlay = False  # noqa

    if full or overlay:
        renderer.update()

    renderer._last_render_ts = perf_counter()  # noqa
