# app\views\plotting\pcr_graph_pg\geometry_pg.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

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


def wells_in_rect(
    index: Optional[WellSpatialIndex],
    well_geoms: Dict[str, Dict[str, np.ndarray]],
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    *,
    fam_visible: bool,
    hex_visible: bool,
) -> Set[str]:
    if index is None:
        return set()

    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])
    candidates = index.rect_candidates(x0, x1, y0, y1)
    if not candidates:
        return set()

    wells_in_rect: Set[str] = set()
    for well in candidates:
        coords = well_geoms.get(well)
        if coords is None:
            continue
        if fam_visible:
            fam = coords.get("fam")
            if fam is not None and fam.size > 0 and _any_point_in_rect(fam, x0, x1, y0, y1):
                wells_in_rect.add(well)
                continue
        if hex_visible:
            hex_c = coords.get("hex")
            if hex_c is not None and hex_c.size > 0 and _any_point_in_rect(hex_c, x0, x1, y0, y1):
                wells_in_rect.add(well)
                continue
    return wells_in_rect


def nearest_well(
    index: Optional[WellSpatialIndex],
    well_geoms: Dict[str, Dict[str, np.ndarray]],
    x: float,
    y: float,
    tol_x: float,
    tol_y: float,
    *,
    fam_visible: bool,
    hex_visible: bool,
) -> Optional[str]:
    if index is None:
        return None

    candidates = [
        w for w in index.point_candidates(x, y, tol_x, tol_y) if _well_has_visible_channel(well_geoms, w, fam_visible, hex_visible)
    ]
    if not candidates:
        return None

    best = None
    best_dist = float("inf")
    max_dist = tol_x * tol_x + tol_y * tol_y
    for well in candidates:
        dist = _distance_sq_to_well(well_geoms, well, x, y, fam_visible, hex_visible)
        if dist < best_dist:
            best = well
            best_dist = dist
    if best is None or best_dist > max_dist:
        return None
    return best


def _any_point_in_rect(coords: np.ndarray, x0: float, x1: float, y0: float, y1: float) -> bool:
    if coords.ndim != 2 or coords.shape[1] != 2:
        if coords.ndim == 2 and coords.shape[0] == 2:
            coords = coords.T
        else:
            return False

    xs = coords[:, 0]
    ys = coords[:, 1]
    mask = np.isfinite(xs) & np.isfinite(ys)
    if not np.any(mask):
        return False

    xs = xs[mask]
    ys = ys[mask]
    inside = (x0 <= xs) & (xs <= x1) & (y0 <= ys) & (ys <= y1)
    return bool(np.any(inside))


def _distance_sq_to_well(
    well_geoms: Dict[str, Dict[str, np.ndarray]],
    well: str,
    x: float,
    y: float,
    fam_visible: bool,
    hex_visible: bool,
) -> float:
    coords = well_geoms.get(well)
    if not coords:
        return float("inf")

    distances: List[float] = []
    if fam_visible:
        fam = coords.get("fam")
        if fam is not None and fam.size > 0:
            distances.append(_min_distance_sq(x, y, fam))
    if hex_visible:
        hex_c = coords.get("hex")
        if hex_c is not None and hex_c.size > 0:
            distances.append(_min_distance_sq(x, y, hex_c))

    return min(distances) if distances else float("inf")


def _well_has_visible_channel(well_geoms: Dict[str, Dict[str, np.ndarray]], well: str, fam_visible: bool, hex_visible: bool) -> bool:
    coords = well_geoms.get(well)
    if not coords:
        return False
    fam_ok = fam_visible and coords.get("fam") is not None and coords["fam"].size > 0
    hex_ok = hex_visible and coords.get("hex") is not None and coords["hex"].size > 0
    return fam_ok or hex_ok


def _min_distance_sq(x: float, y: float, coords: np.ndarray) -> float:
    if coords.shape[0] == 0:
        return float("inf")
    if coords.shape[0] == 1:
        dx = coords[0, 0] - x
        dy = coords[0, 1] - y
        return float(dx * dx + dy * dy)

    xs = coords[:, 0]
    ys = coords[:, 1]
    dx = xs[1:] - xs[:-1]
    dy = ys[1:] - ys[:-1]
    px = x - xs[:-1]
    py = y - ys[:-1]
    denom = dx * dx + dy * dy + 1e-12
    t = np.clip((px * dx + py * dy) / denom, 0.0, 1.0)
    proj_x = xs[:-1] + t * dx
    proj_y = ys[:-1] + t * dy
    dist_sq = (x - proj_x) ** 2 + (y - proj_y) ** 2
    return float(np.min(dist_sq))