# app\views\plotting\pcr_graph_pg\hit_test.py
from __future__ import annotations

from typing import Dict, List, Optional, Set

import numpy as np

from .spatial_index import WellSpatialIndex


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

    wells: Set[str] = set()
    for well in candidates:
        coords = well_geoms.get(well)
        if coords is None:
            continue
        if fam_visible:
            fam = coords.get("fam")
            if fam is not None and fam.size > 0 and _any_point_in_rect(fam, x0, x1, y0, y1):
                wells.add(well)
                continue
        if hex_visible:
            hex_c = coords.get("hex")
            if hex_c is not None and hex_c.size > 0 and _any_point_in_rect(hex_c, x0, x1, y0, y1):
                wells.add(well)
                continue
    return wells


def nearest_well(
    index: Optional[WellSpatialIndex],
    well_geoms: Dict[str, Dict[str, np.ndarray]],
    x: float,
    y: float,
    tol_x: float,  # Bu genellikle sahne birimidir
    tol_y: float,
    *,
    fam_visible: bool,
    hex_visible: bool,
) -> Optional[str]:
    if index is None:
        return None

    # 1. Adayları dar bir toleransla belirle
    candidates = [
        w for w in index.point_candidates(x, y, tol_x, tol_y) 
        if _well_has_visible_channel(well_geoms, w, fam_visible, hex_visible)
    ]
    
    if not candidates:
        return None

    best = None
    best_dist_sq = float("inf")
    
    # Toleransın karesini alarak mesafe sınırı koyuyoruz
    max_dist_sq = (tol_x ** 2) + (tol_y ** 2)

    for well in candidates:
        dist_sq = _distance_sq_to_well(well_geoms, well, x, y, fam_visible, hex_visible)
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best = well

    # Mesafe kontrolü: En yakın olan bile tolerans dışındaysa seçim yok demektir.
    if best is None or best_dist_sq > max_dist_sq:
        return None
        
    return best


def wells_in_rect_centers(
    well_ids: List[str],
    centers: np.ndarray,
    has_fam: np.ndarray,
    has_hex: np.ndarray,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    *,
    fam_visible: bool,
    hex_visible: bool,
) -> Set[str]:
    if centers is None or centers.size == 0 or not well_ids:
        return set()
    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])
    xs = centers[:, 0]
    ys = centers[:, 1]

    visible = np.zeros(len(centers), dtype=bool)
    if fam_visible and has_fam.size == len(centers):
        visible |= has_fam

    if hex_visible and has_hex.size == len(centers):
        visible |= has_hex
    if not np.any(visible):
        return set()

    inside = (x0 <= xs) & (xs <= x1) & (y0 <= ys) & (ys <= y1) & visible
    if not np.any(inside):
        return set()
    indices = np.nonzero(inside)[0]
    return {well_ids[i] for i in indices}
def _any_point_in_rect(coords: np.ndarray, x0: float, x1: float, y0: float, y1: float) -> bool:
    if coords.ndim != 2 or coords.shape[1] != 2:
        if coords.ndim == 2 and coords.shape[0] == 2:
            coords = coords.T
        else:
            return False

    xs = coords[:, 0]
    ys = coords[:, 1]
    mask = np.isfinite(xs) & np.isfinite(ys)
    if np.count_nonzero(mask) < 2:
        return False

    xs = xs[mask]
    ys = ys[mask]
    if xs.size == 1:
        return bool((x0 <= xs[0] <= x1) and (y0 <= ys[0] <= y1))
    if xs.size < 2:
        return False
    x_start = xs[:-1]
    y_start = ys[:-1]
    x_end = xs[1:]
    y_end = ys[1:]

    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])

    inside_start = (x0 <= x_start) & (x_start <= x1) & (y0 <= y_start) & (y_start <= y1)
    inside_end = (x0 <= x_end) & (x_end <= x1) & (y0 <= y_end) & (y_end <= y1)
    if np.any(inside_start | inside_end):
        return True

    dx = x_end - x_start
    dy = y_end - y_start
    u1 = np.zeros_like(dx, dtype=float)
    u2 = np.ones_like(dx, dtype=float)
    valid = np.ones_like(dx, dtype=bool)

    def _clip(p: np.ndarray, q: np.ndarray) -> None:
        nonlocal u1, u2, valid
        parallel = p == 0
        valid &= ~(parallel & (q < 0))
        if not np.any(valid):
            return
        ratio = np.empty_like(p, dtype=float)
        ratio[~parallel] = q[~parallel] / p[~parallel]
        ratio[parallel] = 0.0
        neg = (p < 0) & ~parallel
        pos = (p > 0) & ~parallel
        u1 = np.where(neg, np.maximum(u1, ratio), u1)
        u2 = np.where(pos, np.minimum(u2, ratio), u2)
        valid &= u1 <= u2

    _clip(-dx, x_start - x0)
    _clip(dx, x1 - x_start)
    _clip(-dy, y_start - y0)
    _clip(dy, y1 - y_start)

    return bool(np.any(valid))


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