# app\views\plotting\pcr_graph_pg\spatial_index.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

BBox = Tuple[float, float, float, float]


@dataclass
class WellSpatialIndex:
    wells: List[str]
    boxes: np.ndarray  # shape (N, 4) => xmin, xmax, ymin, ymax

    def rect_candidates(self, x0: float, x1: float, y0: float, y1: float) -> List[str]:
        if self.boxes.size == 0:
            return []
        xmin, xmax, ymin, ymax = (
            self.boxes[:, 0],
            self.boxes[:, 1],
            self.boxes[:, 2],
            self.boxes[:, 3],
        )
        mask = (xmax >= x0) & (xmin <= x1) & (ymax >= y0) & (ymin <= y1)
        if not np.any(mask):
            return []
        idxs = np.nonzero(mask)[0]
        return [self.wells[i] for i in idxs]

    def point_candidates(self, x: float, y: float, tol_x: float, tol_y: float) -> List[str]:
        if self.boxes.size == 0:
            return []
        xmin, xmax, ymin, ymax = (
            self.boxes[:, 0] - tol_x,
            self.boxes[:, 1] + tol_x,
            self.boxes[:, 2] - tol_y,
            self.boxes[:, 3] + tol_y,
        )
        mask = (xmin <= x) & (xmax >= x) & (ymin <= y) & (ymax >= y)
        if not np.any(mask):
            return []
        idxs = np.nonzero(mask)[0]
        return [self.wells[i] for i in idxs]


def bounding_box(arrays: Sequence[np.ndarray]) -> Optional[BBox]:
    """Compute axis-aligned bounding box for visible channel arrays."""
    valid_arrays = [a for a in arrays if a is not None and a.size > 0]
    if not valid_arrays:
        return None

    stacked = np.vstack(valid_arrays)
    xmin = float(np.nanmin(stacked[:, 0]))
    xmax = float(np.nanmax(stacked[:, 0]))
    ymin = float(np.nanmin(stacked[:, 1]))
    ymax = float(np.nanmax(stacked[:, 1]))
    return xmin, xmax, ymin, ymax


def build_spatial_index(
    well_geoms: Dict[str, Dict[str, np.ndarray]],
    *,
    fam_visible: bool,
    hex_visible: bool,
) -> Optional[WellSpatialIndex]:
    wells: List[str] = []
    boxes: List[BBox] = []

    for well, coords in well_geoms.items():
        arrays: List[np.ndarray] = []
        if fam_visible:
            fam = coords.get("fam")
            if fam is not None and fam.size > 0:
                arrays.append(fam)
        if hex_visible:
            hex_c = coords.get("hex")
            if hex_c is not None and hex_c.size > 0:
                arrays.append(hex_c)

        box = bounding_box(arrays)
        if box is None:
            continue

        wells.append(well)
        boxes.append(box)

    if not wells:
        return None

    return WellSpatialIndex(wells=wells, boxes=np.asarray(boxes, dtype=float))