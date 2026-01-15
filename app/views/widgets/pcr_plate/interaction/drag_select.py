# app\views\widgets\pcr_plate\interaction\drag_select.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from app.utils import well_mapping


@dataclass
class DragSelection:
    dragging: bool = False
    mode: str | None = None
    visited: Set[str] = field(default_factory=set)
    base_selection: Set[str] = field(default_factory=set)
    current_selection: Set[str] = field(default_factory=set)
    last_cell: tuple[int, int] | None = None
    anchor_cell: tuple[int, int] | None = None

    def start(
        self,
        row: int,
        col: int,
        wells: Set[str],
        selected_wells: Set[str],
        force_mode: str | None = None,
    ) -> Set[str] | None:
        self.dragging = True
        self.last_cell = (row, col)
        first_well = next(iter(wells))
        self.mode = force_mode or ("remove" if first_well in selected_wells else "add")
        self.visited = set()
        self.base_selection = set(selected_wells)
        self.current_selection = set(self.base_selection)
        self.anchor_cell = (row, col)
        return self._apply_wells(wells)

    def continue_drag(self, row: int, col: int) -> bool:
        if not self.dragging or (row, col) == self.last_cell:
            return False
        self.last_cell = (row, col)
        return True

    def apply_from_position(self, row: int, col: int) -> Set[str] | None:
        if not self.dragging or self.anchor_cell is None:
            return None
        
        # 1. Başlangıç ve bitiş koordinatlarını belirle
        r_start, c_start = self.anchor_cell
        r_end, c_end = row, col
        
        # 2. Dikdörtgenin sınırlarını hesapla (min/max kullanarak ters sürüklemeyi destekle)
        row_range = range(min(r_start, r_end), max(r_start, r_end) + 1)
        col_range = range(min(c_start, c_end), max(c_start, c_end) + 1)
        
        # 3. Bu alan içindeki tüm kuyucukları topla
        rect_wells = set()
        for r in row_range:
            for c in col_range:
                wells = well_mapping.wells_for_header(r, c)
                if wells:
                    rect_wells |= wells

        # 4. Moduna göre seçimi uygula
        if self.mode == "add":
            # Temel seçim + yeni dikdörtgen
            self.current_selection = self.base_selection | rect_wells
        else:
            # Temel seçim - yeni dikdörtgen
            self.current_selection = self.base_selection - rect_wells

        return set(self.current_selection)

    def _apply_wells(self, wells: Set[str]) -> Set[str] | None:
        if not self.dragging or not self.mode:
            return None

        new_wells = {w for w in wells if w not in self.visited}
        if not new_wells:
            return None

        self.visited |= new_wells
        if self.mode == "add":
            self.current_selection |= new_wells
        else:
            self.current_selection -= new_wells

        return set(self.current_selection)

    def reset(self) -> None:
        self.dragging = False
        self.mode = None
        self.visited.clear()
        self.base_selection.clear()
        self.current_selection.clear()
        self.last_cell = None
        self.anchor_cell = None