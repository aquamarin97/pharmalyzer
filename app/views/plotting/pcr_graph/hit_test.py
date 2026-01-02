# app\views\plotting\pcr_graph\hit_test.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Iterable, List, Optional, Set

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WellSpatialIndex:
    wells: List[str]
    boxes: np.ndarray  # shape (N, 4) = xmin, xmax, ymin, ymax

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
        channel_arrays = [c for c in (fam, hex_c) if c is not None and c.size > 0]
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

    # 1) Hızlı AABB adayları
    candidates = index.rect_candidates(x0, x1, y0, y1)
    if not candidates:
        return set()

    # 2) Refine: V1 semantiği (rect içinde en az 1 nokta var mı?)
    wells_in_rect: Set[str] = set()
    for w in candidates:
        if not _well_has_visible_channel(r, w):
            continue

        coords = r._well_geoms.get(w)
        if not coords:
            continue

        # visible kanalları kontrol et
        if r._fam_visible:
            fam = coords.get("fam")
            if fam is not None and fam.size > 0 and _any_point_in_rect(fam, x0, x1, y0, y1):
                wells_in_rect.add(w)
                continue

        if r._hex_visible:
            hex_c = coords.get("hex")
            if hex_c is not None and hex_c.size > 0 and _any_point_in_rect(hex_c, x0, x1, y0, y1):
                wells_in_rect.add(w)
                continue

    elapsed = (perf_counter() - start) * 1000.0
    logger.debug("rect hit-test: %d refined / %d candidates (%.3f ms)", len(wells_in_rect), len(candidates), elapsed)
    return wells_in_rect


def _any_point_in_rect(coords: np.ndarray, x0: float, x1: float, y0: float, y1: float) -> bool:
    """
    coords shape beklenen: (N, 2) => [:,0]=x, [:,1]=y
    NaN/inf içeriyorsa otomatik elenir.
    """
    if coords.ndim != 2 or coords.shape[1] != 2:
        # Eğer bazı yerde (2,N) gibi geliyorsa güvenli fallback:
        if coords.ndim == 2 and coords.shape[0] == 2:
            coords = coords.T
        else:
            return False

    xs = coords[:, 0]
    ys = coords[:, 1]
    # NaN filtre
    m = np.isfinite(xs) & np.isfinite(ys)
    if not np.any(m):
        return False

    xs = xs[m]
    ys = ys[m]
    inside = (x0 <= xs) & (xs <= x1) & (y0 <= ys) & (ys <= y1)
    return bool(np.any(inside))



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
    fam = coords.get("fam")
    hex_c = coords.get("hex")

    if r._fam_visible and fam is not None and fam.size > 0:
        distances.append(_min_distance_sq(x, y, fam))
    if r._hex_visible and hex_c is not None and hex_c.size > 0:
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