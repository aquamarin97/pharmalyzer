from __future__ import annotations

from typing import Iterable, Optional, Set

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from app.services.data_management import well_mapping


class InteractionStore(QObject):
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

        self._pending_selected = False
        self._pending_hover = False
        self._pending_preview = False

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)

    # ---- batching ----
    def begin_batch(self) -> None:
        self._batch_depth += 1

    def end_batch(self) -> None:
        if self._batch_depth > 0:
            self._batch_depth -= 1
        if self._batch_depth == 0:
            self._schedule()

    # ---- selection ----
    def set_selection(self, wells: Iterable[str]) -> None:
        normalized = self._normalize_wells(wells)
        if normalized == self.selected_wells:
            return
        self.selected_wells = normalized
        self._pending_selected = True
        self._schedule()

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
        self._pending_selected = True
        self._schedule()

    def clear_selection(self) -> None:
        if not self.selected_wells:
            return
        self.selected_wells.clear()
        self._pending_selected = True
        self._schedule()

    # ---- hover ----
    def set_hover(self, well: Optional[str]) -> None:
        normalized = self._normalize_hover(well)
        if normalized == self.hover_well:
            return
        self.hover_well = normalized
        self._pending_hover = True
        self._schedule()

    # ---- preview ----
    def set_preview(self, wells: Iterable[str]) -> None:
        normalized = self._normalize_wells(wells)
        if normalized == self.preview_wells:
            return
        self.preview_wells = normalized
        self._pending_preview = True
        self._schedule()

    # ---- internal ----
    def _schedule(self) -> None:
        if self._batch_depth > 0:
            return
        if not self._coalesce:
            self._flush()
            return
        if not self._timer.isActive():
            self._timer.start(0)

    def _flush(self) -> None:
        if self._pending_selected:
            self._pending_selected = False
            self.selectedChanged.emit(set(self.selected_wells))
        if self._pending_preview:
            self._pending_preview = False
            self.previewChanged.emit(set(self.preview_wells))
        if self._pending_hover:
            self._pending_hover = False
            self.hoverChanged.emit(self.hover_well)

    # ---- helpers ----
    @staticmethod
    def _normalize_wells(wells: Iterable[str]) -> Set[str]:
        out: Set[str] = set()
        for w in wells or []:
            if well_mapping.is_valid_well_id(w):
                out.add(w.strip().upper())
        return out

    @staticmethod
    def _normalize_hover(well: Optional[str]) -> Optional[str]:
        if well is None:
            return None
        return well.strip().upper() if well_mapping.is_valid_well_id(well) else None
