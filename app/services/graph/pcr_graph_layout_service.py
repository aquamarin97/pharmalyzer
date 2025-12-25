# app/services/graph/pcr_graph_layout_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional


Coord = Tuple[int, float]


@dataclass
class PCRSplitData:
    static_fam_x: List[int]
    static_fam_y: List[float]
    static_hex_x: List[int]
    static_hex_y: List[float]
    anim_fam_x: List[int]
    anim_fam_y: List[float]
    anim_hex_x: List[int]
    anim_hex_y: List[float]

    xlim: Optional[tuple[float, float]]
    ylim: Optional[tuple[float, float]]

    @property
    def frames(self) -> int:
        return max(len(self.anim_fam_x), len(self.anim_hex_x)) + 1


class PCRGraphLayoutService:
    """View'e hazır olacak şekilde PCR grafik datasını hazırlar."""

    @staticmethod
    def split_static_anim(
        fam_coords: List[Coord],
        hex_coords: List[Coord],
        start_x: int,
        min_y_floor: float = 5000.0,
        y_padding: float = 500.0,
    ) -> PCRSplitData:
        fam_coords = fam_coords or []
        hex_coords = hex_coords or []

        static_fam_x: List[int] = []
        static_fam_y: List[float] = []
        static_hex_x: List[int] = []
        static_hex_y: List[float] = []
        anim_fam_x: List[int] = []
        anim_fam_y: List[float] = []
        anim_hex_x: List[int] = []
        anim_hex_y: List[float] = []

        for x, y in fam_coords:
            if x < start_x:
                static_fam_x.append(int(x)); static_fam_y.append(float(y))
            else:
                anim_fam_x.append(int(x)); anim_fam_y.append(float(y))

        for x, y in hex_coords:
            if x < start_x:
                static_hex_x.append(int(x)); static_hex_y.append(float(y))
            else:
                anim_hex_x.append(int(x)); anim_hex_y.append(float(y))

        all_coords = fam_coords + hex_coords
        xlim: Optional[tuple[float, float]] = None
        ylim: Optional[tuple[float, float]] = None

        if all_coords:
            all_x = [x for x, _ in all_coords]
            all_y = [y for _, y in all_coords]

            if all_x:
                xlim = (min(all_x) - 1, max(all_x) + 1)

            if all_y:
                ymax = max(all_y)
                target_top = max(min_y_floor, ymax + y_padding)
                ylim = (0.0, float(target_top))

        return PCRSplitData(
            static_fam_x=static_fam_x,
            static_fam_y=static_fam_y,
            static_hex_x=static_hex_x,
            static_hex_y=static_hex_y,
            anim_fam_x=anim_fam_x,
            anim_fam_y=anim_fam_y,
            anim_hex_x=anim_hex_x,
            anim_hex_y=anim_hex_y,
            xlim=xlim,
            ylim=ylim,
        )

    @staticmethod
    def compute_ylim_for_static_draw(
        fam_coords: List[Coord],
        hex_coords: List[Coord],
        min_floor: float = 4500.0,
        y_padding: float = 500.0,
    ) -> Optional[tuple[float, float]]:
        fam_coords = fam_coords or []
        hex_coords = hex_coords or []
        all_y = [y for _, y in fam_coords] + [y for _, y in hex_coords]
        if not all_y:
            return None
        ymax = max(all_y)
        top = max(min_floor, ymax + y_padding)
        return (0.0, float(top))
