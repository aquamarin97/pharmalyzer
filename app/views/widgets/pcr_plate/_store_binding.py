# app/views/widgets/pcr_plate/_store_binding.py
from __future__ import annotations

from app.services.interaction_store import InteractionStore


def bind_store(widget, store: InteractionStore, on_selection_changed, on_hover_changed, on_preview_changed) -> None:
    if widget._store is not None:
        try:
            widget._store.selectedChanged.disconnect(on_selection_changed)
            widget._store.hoverChanged.disconnect(on_hover_changed)
            widget._store.previewChanged.disconnect(on_preview_changed)
        except Exception:
            pass

    widget._store = store
    widget._store.selectedChanged.connect(on_selection_changed)
    widget._store.hoverChanged.connect(on_hover_changed)
    widget._store.previewChanged.connect(on_preview_changed)

    # mevcut state'i uygula
    on_selection_changed(widget._store.selected_wells)
    on_hover_changed(widget._store.hover_well)
    on_preview_changed(widget._store.preview_wells)
