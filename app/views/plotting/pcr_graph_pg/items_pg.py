# app/views/plotting/pcr_graph_pg/items_pg.py
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pyqtgraph as pg

from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService
from app.services.pcr_data_service import PCRCoords
from app.utils import well_mapping

from .legend import refresh_legend
from .spatial_index import build_spatial_index


def update_items(renderer, data: Dict[str, PCRCoords]) -> None:
    """
    renderer üzerindeki _fam_items/_hex_items/_well_geoms vb. cache'leri günceller.
    """
    plot_item: pg.PlotItem = renderer._plot_item  # noqa

    # remove missing wells
    for well in list(renderer._fam_items.keys()):
        if well not in data:
            plot_item.removeItem(renderer._fam_items.pop(well))
            renderer._well_geoms.pop(well, None)

    for well in list(renderer._hex_items.keys()):
        if well not in data:
            plot_item.removeItem(renderer._hex_items.pop(well))
            renderer._well_geoms.pop(well, None)

    wells_sorted = sorted(data.keys(), key=lambda w: well_mapping.well_id_to_patient_no(w))
    fam_all: List[np.ndarray] = []
    hex_all: List[np.ndarray] = []
    center_ids: List[str] = []
    center_points: List[Tuple[float, float]] = []
    center_has_fam: List[bool] = []
    center_has_hex: List[bool] = []

    for well in wells_sorted:
        coords = data.get(well)
        if coords is None:
            continue

        fam_coords = coords.fam
        hex_coords = coords.hex
        fam_has_data = fam_coords.size > 0
        hex_has_data = hex_coords.size > 0

        renderer._well_geoms[well] = {
            "fam": fam_coords if fam_has_data else np.empty((0, 2), dtype=float),
            "hex": hex_coords if hex_has_data else np.empty((0, 2), dtype=float),
        }

        if fam_has_data:
            fam_all.append(fam_coords)
            fam_item = renderer._fam_items.get(well)
            if fam_item is None:
                fam_item = pg.PlotDataItem(connect="finite", name="FAM")
                plot_item.addItem(fam_item)
                renderer._fam_items[well] = fam_item
            fam_item.setData(fam_coords[:, 0], fam_coords[:, 1])
            fam_item.setVisible(renderer._fam_visible)
            fam_item.setProperty("has_data", True)
        else:
            if well in renderer._fam_items:
                renderer._fam_items[well].setData([], [])
                renderer._fam_items[well].setProperty("has_data", False)

        if hex_has_data:
            hex_all.append(hex_coords)
            hex_item = renderer._hex_items.get(well)
            if hex_item is None:
                hex_item = pg.PlotDataItem(connect="finite", name="HEX")
                plot_item.addItem(hex_item)
                renderer._hex_items[well] = hex_item
            hex_item.setData(hex_coords[:, 0], hex_coords[:, 1])
            hex_item.setVisible(renderer._hex_visible)
            hex_item.setProperty("has_data", True)
        else:
            if well in renderer._hex_items:
                renderer._hex_items[well].setData([], [])
                renderer._hex_items[well].setProperty("has_data", False)

        center = _compute_well_center(fam_coords if fam_has_data else None, hex_coords if hex_has_data else None)
        if center is not None:
            center_ids.append(well)
            center_points.append(center)
            center_has_fam.append(fam_has_data)
            center_has_hex.append(hex_has_data)

    refresh_axes_limits(renderer, fam_all, hex_all)
    refresh_legend_pg(renderer)
    _update_center_cache(renderer, center_ids, center_points, center_has_fam, center_has_hex)


def refresh_axes_limits(renderer, fam_coords: List[np.ndarray], hex_coords: List[np.ndarray]) -> None:
    ylim = PCRGraphLayoutService.compute_ylim_for_static_draw(
        fam_coords=fam_coords,
        hex_coords=hex_coords,
        min_floor=4500.0,
        y_padding=500.0,
    )
    target_ylim = ylim if ylim else renderer._style.axes.default_ylim  # noqa
    renderer._apply_axis_ranges(xlim=renderer._style.axes.default_xlim, ylim=target_ylim)  # noqa


def refresh_legend_pg(renderer) -> None:
    refresh_legend(renderer, renderer._legend)  # noqa


def rebuild_spatial_index(renderer) -> None:
    renderer._spatial_index = build_spatial_index(  # noqa
        renderer._well_geoms,
        fam_visible=renderer._fam_visible,
        hex_visible=renderer._hex_visible,
    )


def _compute_well_center(fam_coords: Optional[np.ndarray], hex_coords: Optional[np.ndarray]) -> Optional[Tuple[float, float]]:
    coords_list: List[np.ndarray] = []
    if fam_coords is not None and fam_coords.size > 0:
        coords_list.append(fam_coords)
    if hex_coords is not None and hex_coords.size > 0:
        coords_list.append(hex_coords)
    if not coords_list:
        return None

    combined = np.vstack(coords_list)
    xs = combined[:, 0]
    ys = combined[:, 1]
    mask = np.isfinite(xs) & np.isfinite(ys)
    if not np.any(mask):
        return None

    center_x = float(np.mean(xs[mask]))
    center_y = float(np.mean(ys[mask]))
    return center_x, center_y


def _update_center_cache(
    renderer,
    center_ids: List[str],
    center_points: List[Tuple[float, float]],
    center_has_fam: List[bool],
    center_has_hex: List[bool],
) -> None:
    if center_points:
        renderer._well_centers = np.array(center_points, dtype=float)  # noqa
        renderer._well_center_ids = center_ids  # noqa
        renderer._well_center_has_fam = np.array(center_has_fam, dtype=bool)  # noqa
        renderer._well_center_has_hex = np.array(center_has_hex, dtype=bool)  # noqa
        renderer._well_center_index = {well: idx for idx, well in enumerate(center_ids)}  # noqa
        return

    renderer._well_centers = np.empty((0, 2), dtype=float)  # noqa
    renderer._well_center_ids = []  # noqa
    renderer._well_center_has_fam = np.array([], dtype=bool)  # noqa
    renderer._well_center_has_hex = np.array([], dtype=bool)  # noqa
    renderer._well_center_index = {}  # noqa
