# app\views\widgets\pcr_graph_interactor.py
from __future__ import annotations

import logging
from typing import Optional, Set

from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRDataService
from app.utils import well_mapping
from app.views.plotting.pcr_graph.renderer import PCRGraphRenderer

logger = logging.getLogger(__name__)


class PCRGraphInteractor:
    """
    InteractionStore sinyallerini dinler ve sonucu renderera iletir.
    Veri erişimi bu sınıfta tutulur.
    """

    def __init__(self, renderer: PCRGraphRenderer, data_service: PCRDataService | None = None):
        self.renderer = renderer
        self.data_service = data_service
        self.store: InteractionStore | None = None
        self._last_selection: Set[str] = set()
        self._last_cache_token: int | None = None

    def set_interaction_store(self, store: InteractionStore, data_service: PCRDataService | None = None) -> None:
        self._disconnect_store()
        self.store = store
        self.renderer.bind_interaction_store(store)
        if data_service is not None:
            self.data_service = data_service

        if self.store is None:
            return

        self.store.selectedChanged.connect(self._on_selection_changed)
        self.store.hoverChanged.connect(self._on_hover_changed)
        self._apply_current_state()

    def dispose(self) -> None:
        self._disconnect_store()
        self.store = None

    # ---- signal handlers ----
    def _on_selection_changed(self, wells: Set[str]) -> None:
        if self.data_service is None:
            logger.warning("PCRGraphInteractor: data_service ayarlanmadı, render yapılamıyor.")
            self.renderer.reset()
            return

        normalized_wells = {w for w in wells if well_mapping.is_valid_well_id(w)}
        if not normalized_wells:
            self._last_selection = set()
            self._last_cache_token = None
            self.renderer.reset()
            return

        try:
            data = self.data_service.get_coords_for_wells(normalized_wells)
            cache_token = self.data_service.get_cache_token()
        except Exception as exc:
            logger.warning("PCR koordinatları alınamadı: %s", exc, exc_info=True)
            self.renderer.reset()
            return

        if normalized_wells == self._last_selection and cache_token == self._last_cache_token:
            return

        self._last_selection = normalized_wells
        self._last_cache_token = cache_token
        self.renderer.render_wells(data, cache_token=cache_token)

    def _on_hover_changed(self, well: Optional[str]) -> None:
        normalized = well if well_mapping.is_valid_well_id(well) else None
        if normalized == self.renderer._hover_well:
            return
        self.renderer.set_hover(normalized)

    # ---- helpers ----
    def _apply_current_state(self) -> None:
        if self.store is None:
            return

        self._on_selection_changed(self.store.selected_wells)
        self._on_hover_changed(self.store.hover_well)

    def _disconnect_store(self) -> None:
        if self.store is None:
            return
        try:
            self.store.selectedChanged.disconnect(self._on_selection_changed)
            self.store.hoverChanged.disconnect(self._on_hover_changed)
            self.renderer.bind_interaction_store(None)
        except Exception:
            # Qt disconnect'i sessizce geçebilir; exception'a gerek yok
            pass
        self._last_selection = set()
        self._last_cache_token = None