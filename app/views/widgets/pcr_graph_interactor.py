from __future__ import annotations

import logging
from typing import Optional, Set

from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRDataService
from app.utils import well_mapping
from app.views.widgets.pcr_graph_renderer import PCRGraphRenderer

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

    def set_interaction_store(self, store: InteractionStore, data_service: PCRDataService | None = None) -> None:
        self._disconnect_store()
        self.store = store
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

        if not wells:
            self.renderer.reset()
            return

        try:
            data = self.data_service.get_coords_for_wells(wells)
        except Exception as exc:
            logger.warning("PCR koordinatları alınamadı: %s", exc, exc_info=True)
            self.renderer.reset()
            return

        self.renderer.render_wells(data)

    def _on_hover_changed(self, well: Optional[str]) -> None:
        normalized = well if well_mapping.is_valid_well_id(well) else None
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
        except Exception:
            # Qt disconnect'i sessizce geçebilir; exception'a gerek yok
            pass