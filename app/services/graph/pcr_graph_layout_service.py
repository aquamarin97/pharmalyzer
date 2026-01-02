# app\services\graph\pcr_graph_layout_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Sequence, Union

import numpy as np  # <-- ekle

Coord = Tuple[int, float]
CoordArray = np.ndarray  # shape: (N, 2)
CoordsLike = Sequence[Union[Coord, CoordArray]]
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
        fam_coords: CoordsLike,
        hex_coords: CoordsLike,
        min_floor: float = 4500.0,
        y_padding: float = 500.0,
    ) -> Optional[tuple[float, float]]:
        fam_coords = fam_coords or []
        hex_coords = hex_coords or []

        all_y: List[float] = []

        def collect_y(coords: CoordsLike) -> None:
            for item in coords:
                # item bir numpy array ise (N,2) bekleriz
                if isinstance(item, np.ndarray):
                    if item.size == 0:
                        continue
                    # Güvenlik: en az 2 kolon olmalı
                    if item.ndim == 2 and item.shape[1] >= 2:
                        all_y.extend(item[:, 1].astype(float).tolist())
                    continue

                # item tuple/list gibi (x,y) ise
                try:
                    x, y = item  # type: ignore[misc]
                    all_y.append(float(y))
                except Exception:
                    # Beklenmeyen format: sessizce geç (istersen log ekleyebilirsin)
                    continue

        collect_y(fam_coords)
        collect_y(hex_coords)

        if not all_y:
            return None

        ymax = max(all_y)
        top = max(min_floor, ymax + y_padding)
        return (0.0, float(top))