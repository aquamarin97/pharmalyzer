# app/services/data_management/interaction_store.py
from __future__ import annotations

from typing import Iterable, Optional, Set

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from app.services.data_management import well_mapping  # yeni konum


class InteractionStore(QObject):
    """
    Release-grade InteractionStore:
    - selection/hover/preview state tek kaynak
    - sinyal "coalescing": hızlı ardışık değişikliklerde tek emit
    - batch mode: begin_batch/end_batch ile birden çok update tek emite iner
    """

    selectedChanged = pyqtSignal(set)
    hoverChanged = pyqtSignal(object)
    previewChanged = pyqtSignal(set)

    def __init__(self, *, coalesce: bool = True):
        super().__init__()
        self.selected_wells: Set[str] = set()
        self.hover_well: Optional[str] = None
        self.preview_wells: Set[str] = set()

        self._coalesce = bool(coalesce)
        self._batch_depth = 0

        self._pending_selected_emit = False
        self._pending_preview_emit = False
        self._pending_hover_emit = False

        self._emit_timer = QTimer(self)
        self._emit_timer.setSingleShot(True)
        self._emit_timer.timeout.connect(self._flush_emits)

    # -------------------- batching --------------------
    def begin_batch(self) -> None:
        self._batch_depth += 1

    def end_batch(self) -> None:
        if self._batch_depth > 0:
            self._batch_depth -= 1
        if self._batch_depth == 0:
            self._schedule_flush()

    # -------------------- selection --------------------
    def set_selection(self, wells: Iterable[str]) -> None:
        normalized = self._normalize_wells(wells)
        if normalized == self.selected_wells:
            return
        self.selected_wells = normalized
        self._mark_selected_dirty()

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
        self._mark_selected_dirty()

    def clear_selection(self) -> None:
        if not self.selected_wells:
            return
        self.selected_wells.clear()
        self._mark_selected_dirty()

    # -------------------- hover --------------------
    def set_hover(self, well: Optional[str]) -> None:
        normalized = self._normalize_hover(well)
        if normalized == self.hover_well:
            return
        self.hover_well = normalized
        self._mark_hover_dirty()

    # -------------------- preview --------------------
    def set_preview(self, wells: Iterable[str]) -> None:
        normalized = self._normalize_wells(wells)
        if normalized == self.preview_wells:
            return
        self.preview_wells = normalized
        self._mark_preview_dirty()

    # -------------------- internal: emit control --------------------
    def _mark_selected_dirty(self) -> None:
        self._pending_selected_emit = True
        self._schedule_flush()

    def _mark_preview_dirty(self) -> None:
        self._pending_preview_emit = True
        self._schedule_flush()

    def _mark_hover_dirty(self) -> None:
        self._pending_hover_emit = True
        self._schedule_flush()

    def _schedule_flush(self) -> None:
        if self._batch_depth > 0:
            return
        if not self._coalesce:
            self._flush_emits()
            return
        if not self._emit_timer.isActive():
            # 0ms: aynı event loop tick'inde biriken değişiklikleri tek emite indirir
            self._emit_timer.start(0)

    def _flush_emits(self) -> None:
        # Emit snapshot al (mutation riskini azaltmak için)
        if self._pending_selected_emit:
            self._pending_selected_emit = False
            self.selectedChanged.emit(set(self.selected_wells))
        if self._pending_preview_emit:
            self._pending_preview_emit = False
            self.previewChanged.emit(set(self.preview_wells))
        if self._pending_hover_emit:
            self._pending_hover_emit = False
            self.hoverChanged.emit(self.hover_well)

    # -------------------- helpers --------------------
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
