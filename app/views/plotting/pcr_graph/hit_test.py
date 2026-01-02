# app\views\plotting\pcr_graph\hit_test.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WellSpatialIndex:
    wells: List[str]
    boxes: np.ndarray  # shape (N, 4) = xmin, xmax, ymin, ymax

    def rect_candidates(self, x0: float, x1: float, y0: float, y1: float, *, tol_x: float = 0.0, tol_y: float = 0.0) -> List[str]:
        if self.boxes.size == 0:
            return []
        xmin, xmax, ymin, ymax = (
            self.boxes[:, 0] - tol_x,
            self.boxes[:, 1] + tol_x,
            self.boxes[:, 2] - tol_y,
            self.boxes[:, 3] + tol_y,
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


def rebuild_spatial_index(r) -> None:
    """
    Well AABB cache'i oluştur.
    - Her kuyu için FAM ve HEX kanallarının birleşik bounding box'ı hesaplanır.
    - Sonuç r._spatial_index içine yazılır.
    """
    boxes: List[list[float]] = []
    wells: List[str] = []

    for well, coords in r._well_geoms.items():
        fam = coords.get("fam")
        hex_c = coords.get("hex")
        channel_arrays = [_normalize_coords(c) for c in (fam, hex_c) if c is not None and c.size > 0]
        if not channel_arrays:
            continue

        stacked = np.vstack(channel_arrays)
        xmin = float(np.nanmin(stacked[:, 0]))
        xmax = float(np.nanmax(stacked[:, 0]))
        ymin = float(np.nanmin(stacked[:, 1]))
        ymax = float(np.nanmax(stacked[:, 1]))
        boxes.append([xmin, xmax, ymin, ymax])
        wells.append(well)

    if not wells:
        r._spatial_index = None
        return

    r._spatial_index = WellSpatialIndex(wells=wells, boxes=np.asarray(boxes, dtype=float))


def _ensure_spatial_index(r) -> Optional[WellSpatialIndex]:
    if getattr(r, "_spatial_index", None) is None:
        rebuild_spatial_index(r)
    return r._spatial_index


def find_well_at_event(r, event) -> Optional[str]:
    if event.xdata is None or event.ydata is None:
        return None

    start = perf_counter()
    index = _ensure_spatial_index(r)
    if index is None:
        return None

    tol_x, tol_y = _pixel_tolerance_in_data(r, px=6)
    candidate_wells = [
        w for w in index.point_candidates(event.xdata, event.ydata, tol_x, tol_y) if _well_has_visible_channel(r, w)
    ]
    if not candidate_wells:
        return None

    best_well = _pick_nearest_well(r, candidate_wells, event.xdata, event.ydata, tol_x, tol_y)
    elapsed = (perf_counter() - start) * 1000.0
    logger.debug("hover hit-test: %d candidates -> %s (%.3f ms)", len(candidate_wells), best_well, elapsed)
    return best_well


def find_wells_in_rect(r, x0: float, x1: float, y0: float, y1: float) -> Set[str]:
    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])
    start = perf_counter()

    index = _ensure_spatial_index(r)
    if index is None:
        return set()

    tol_x, tol_y = _pixel_tolerance_in_data(r, px=4)
    rx0, rx1, ry0, ry1 = x0 - tol_x, x1 + tol_x, y0 - tol_y, y1 + tol_y
    candidates = index.rect_candidates(rx0, rx1, ry0, ry1)
    wells_in_rect: Set[str] = set()
    for w in candidates:
        if not _well_has_visible_channel(r, w):
            continue
        if _rect_touches_well(r, w, rx0, rx1, ry0, ry1):
            wells_in_rect.add(w)

    elapsed = (perf_counter() - start) * 1000.0
    logger.debug("rect hit-test: %d/%d wells (%.3f ms)", len(wells_in_rect), len(candidates), elapsed)
    return wells_in_rect


def _well_has_visible_channel(r, well: str) -> bool:
    coords = r._well_geoms.get(well)
    if not coords:
        return False
    fam_ok = r._fam_visible and coords.get("fam") is not None and coords["fam"].size > 0
    hex_ok = r._hex_visible and coords.get("hex") is not None and coords["hex"].size > 0
    return fam_ok or hex_ok


def _pick_nearest_well(r, wells: Iterable[str], x: float, y: float, tol_x: float, tol_y: float) -> Optional[str]:
    best = None
    best_dist = float("inf")
    max_dist_sq = tol_x * tol_x + tol_y * tol_y

    for well in wells:
        dist_sq = _distance_sq_to_well(r, well, x, y)
        if dist_sq < best_dist:
            best = well
            best_dist = dist_sq

    if best is None or best_dist > max_dist_sq:
        return None
    return best


def _distance_sq_to_well(r, well: str, x: float, y: float) -> float:
    coords = r._well_geoms.get(well)
    if not coords:
        return float("inf")

    distances = []
    fam = _normalize_coords(coords.get("fam"))
    hex_c = _normalize_coords(coords.get("hex"))

    if r._fam_visible and fam.size > 0:
        distances.append(_min_distance_sq(x, y, fam))
    if r._hex_visible and hex_c.size > 0:
        distances.append(_min_distance_sq(x, y, hex_c))

    return min(distances) if distances else float("inf")


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


def _pixel_tolerance_in_data(r, px: int = 6) -> tuple[float, float]:
    inv = r.ax.transData.inverted()
    x0, y0 = inv.transform((0, 0))
    x1, y1 = inv.transform((px, px))
    return abs(x1 - x0), abs(y1 - y0)


def pixel_tolerance(r, px: int = 6) -> tuple[float, float]:
    """Public helper to convert pixel tolerance to data-space tolerance."""
    return _pixel_tolerance_in_data(r, px=px)


def _normalize_coords(coords: Optional[np.ndarray]) -> np.ndarray:
    if coords is None:
        return np.empty((0, 2), dtype=float)
    arr = np.asarray(coords, dtype=float)
    if arr.size == 0:
        return np.empty((0, 2), dtype=float)
    if arr.ndim != 2:
        arr = np.atleast_2d(arr)
    if arr.shape[1] != 2 and arr.shape[0] == 2:
        arr = arr.T
    if arr.shape[1] != 2:
        arr = arr.reshape(-1, 2)
    return arr


def _rect_touches_well(r, well: str, x0: float, x1: float, y0: float, y1: float) -> bool:
    coords = r._well_geoms.get(well)
    if not coords:
        return False

    fam = _normalize_coords(coords.get("fam"))
    hex_c = _normalize_coords(coords.get("hex"))
    if r._fam_visible and fam.size > 0 and _curve_intersects_rect(fam, x0, x1, y0, y1):
        return True
    if r._hex_visible and hex_c.size > 0 and _curve_intersects_rect(hex_c, x0, x1, y0, y1):
        return True
    return False


def _curve_intersects_rect(coords: np.ndarray, x0: float, x1: float, y0: float, y1: float) -> bool:
    if coords.size == 0:
        return False
    # Any point inside expanded rect
    inside_mask = (coords[:, 0] >= x0) & (coords[:, 0] <= x1) & (coords[:, 1] >= y0) & (coords[:, 1] <= y1)
    if bool(np.any(inside_mask)):
        return True

    rx0, rx1 = min(x0, x1), max(x0, x1)
    ry0, ry1 = min(y0, y1), max(y0, y1)
    rect_edges = [
        ((rx0, ry0), (rx1, ry0)),
        ((rx1, ry0), (rx1, ry1)),
        ((rx1, ry1), (rx0, ry1)),
        ((rx0, ry1), (rx0, ry0)),
    ]

    xs, ys = coords[:, 0], coords[:, 1]
    for i in range(len(xs) - 1):
        p1 = (xs[i], ys[i])
        p2 = (xs[i + 1], ys[i + 1])
        seg_min_x, seg_max_x = sorted((p1[0], p2[0]))
        seg_min_y, seg_max_y = sorted((p1[1], p2[1]))

        # quick reject with bounding boxes
        if seg_max_x < rx0 or seg_min_x > rx1 or seg_max_y < ry0 or seg_min_y > ry1:
            continue

        # segment endpoints inside rect already handled above; check edge intersections
        for e1, e2 in rect_edges:
            if _segments_intersect(p1, p2, e1, e2):
                return True
    return False


def _segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float], q1: Tuple[float, float], q2: Tuple[float, float]) -> bool:
    def orient(a, b, c) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)
    eps = 1e-12

    if (abs(o1) < eps and _on_segment(p1, q1, p2)) or (abs(o2) < eps and _on_segment(p1, q2, p2)):
        return True
    if (abs(o3) < eps and _on_segment(q1, p1, q2)) or (abs(o4) < eps and _on_segment(q1, p2, q2)):
        return True

    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _on_segment(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> bool:
    return min(a[0], c[0]) - 1e-12 <= b[0] <= max(a[0], c[0]) + 1e-12 and min(a[1], c[1]) - 1e-12 <= b[1] <= max(
        a[1], c[1]
    ) + 1e-12