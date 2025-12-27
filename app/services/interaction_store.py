# app\services\interaction_store.py
from __future__ import annotations

from typing import Iterable, Optional, Set

from PyQt5.QtCore import QObject, pyqtSignal

from app.utils import well_mapping


class InteractionStore(QObject):
    """
    Tek doğrulayıcı etkileşim durumu.
    Tüm widget'lar seçim/hover bilgisini buraya yazar ve buradan okur.
    """

    selectedChanged = pyqtSignal(set)
    hoverChanged = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.selected_wells: Set[str] = set()
        self.hover_well: Optional[str] = None

    # ---- selection ----
    def set_selection(self, wells: Iterable[str]) -> None:
        normalized = self._normalize_wells(wells)
        if normalized == self.selected_wells:
            return
        self.selected_wells = normalized
        self.selectedChanged.emit(set(self.selected_wells))

    def toggle_wells(self, wells: Iterable[str]) -> None:
        normalized = self._normalize_wells(wells)
        if not normalized:
            return

        updated = set(self.selected_wells)
        for w in normalized:
            if w in updated:
                updated.remove(w)
            else:
                updated.add(w)

        if updated == self.selected_wells:
            return

        self.selected_wells = updated
        self.selectedChanged.emit(set(self.selected_wells))

    def clear_selection(self) -> None:
        if not self.selected_wells:
            return
        self.selected_wells.clear()
        self.selectedChanged.emit(set())

    # ---- hover ----
    def set_hover(self, well: Optional[str]) -> None:
        normalized = self._normalize_hover(well)
        if normalized == self.hover_well:
            return
        self.hover_well = normalized
        self.hoverChanged.emit(self.hover_well)

    # ---- helpers ----
    @staticmethod
    def _normalize_wells(wells: Iterable[str]) -> Set[str]:
        normalized: Set[str] = set()
        for w in wells or []:
            if well_mapping.is_valid_well_id(w):
                normalized.add(w.strip().upper())
        return normalized

    @staticmethod
    def _normalize_hover(well: Optional[str]) -> Optional[str]:
        if well is None:
            return None
        return well.strip().upper() if well_mapping.is_valid_well_id(well) else None