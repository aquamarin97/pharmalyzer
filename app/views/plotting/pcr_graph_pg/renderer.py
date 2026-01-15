# app/views/plotting/pcr_graph_pg/renderer.py
from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRCoords
from app.utils import well_mapping

from .axes import apply_axis_ranges, apply_axes_style, set_axis_ticks
from .interactions import PCRGraphViewBox
from .styles import InteractionStyleChange, StyleState, apply_interaction_styles, set_channel_visibility

from .items_pg import update_items, refresh_legend_pg, rebuild_spatial_index
from .overlays_pg import build_overlay, make_hover_pen, make_preview_pen, update_overlays
from .interaction_handlers_pg import (
    handle_hover as handle_hover_impl,
    handle_click as handle_click_impl,
    handle_drag as handle_drag_impl,
    on_store_preview_changed as on_store_preview_changed_impl,
    collect_preview_wells as collect_preview_wells_impl,
    flush_pending_drag as flush_pending_drag_impl,
)
from .render_scheduler_pg import schedule_render as schedule_render_impl, flush_pending_render as flush_pending_render_impl


logger = logging.getLogger(__name__)


class PCRGraphRendererPG(pg.PlotWidget):
    """
    PyQtGraph-based PCR grafiği: yüksek FPS için optimize edildi.
    """
    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        self._style = style or PCRGraphStyle()
        self._title = "PCR Grafik"

        self._view_box = PCRGraphViewBox(self)
        self._view_box.setDefaultPadding(0.0)
        plot_item = pg.PlotItem(viewBox=self._view_box)
        plot_item.setMenuEnabled(False)
        plot_item.hideButtons()
        super().__init__(parent=parent, plotItem=plot_item, background=self._style.axes.fig_facecolor)

        self._plot_item: pg.PlotItem = plot_item
        self._store: InteractionStore | None = None
        self._style_state: Optional[StyleState] = None

        self._fam_items: Dict[str, pg.PlotDataItem] = {}
        self._hex_items: Dict[str, pg.PlotDataItem] = {}
        self._hover_well: Optional[str] = None

        # overlays
        self._hover_overlay = build_overlay(pen=make_hover_pen(self))
        self._preview_overlay = build_overlay(pen=make_preview_pen(self))

        self._fam_visible = True
        self._hex_visible = True
        self._rendered_wells: Set[str] = set()
        self._data_cache_token: int = 0
        self._well_geoms: Dict[str, Dict[str, np.ndarray]] = {}
        self._spatial_index = None
        self._rect_preview_wells: Set[str] = set()
        self._well_centers = np.empty((0, 2), dtype=float)
        self._well_center_ids: List[str] = []
        self._well_center_has_fam = np.array([], dtype=bool)
        self._well_center_has_hex = np.array([], dtype=bool)
        self._well_center_index: Dict[str, int] = {}

        # legend + ROI
        self._legend = pg.LegendItem(offset=(10, 10))
        self._legend.setParentItem(self._plot_item.graphicsItem())
        self._rect_roi = pg.RectROI(
            [0, 0],
            [0, 0],
            pen=pg.mkPen(self._style.overlay_color, width=self._style.overlay_roi_width),
            movable=False,
        )
        self._rect_roi.setZValue(50)
        self._rect_roi.setVisible(False)
        self._plot_item.addItem(self._rect_roi, ignoreBounds=True)

        # render scheduling
        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._flush_pending_render)
        self._frame_interval_ms = 16
        self._pending_full_draw = False
        self._pending_overlay = False
        self._last_render_ts = perf_counter()
        self._drag_throttle_ms = 30
        self._last_drag_ts = 0.0
        self._pending_drag: Optional[Tuple[tuple[float, float], tuple[float, float]]] = None
        self._drag_throttle_timer = QtCore.QTimer(self)
        self._drag_throttle_timer.setSingleShot(True)
        self._drag_throttle_timer.timeout.connect(self._flush_pending_drag)
        self._use_preview_proxy = False
        self._tick_update_timer = QtCore.QTimer(self)
        self._tick_update_timer.setSingleShot(True)
        self._tick_update_timer.timeout.connect(self._flush_pending_ticks)
        self._pending_tick_range: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None
        self._last_tick_range: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None
        self._large_dataset = False


        self._setup_axes()
        self._plot_item.addItem(self._hover_overlay)
        self._plot_item.addItem(self._preview_overlay)
        self._preview_proxy = pg.ScatterPlotItem(
            pen=None,
            brush=pg.mkBrush(QtGui.QColor(self._style.overlay_color)),
            size=6,
        )
        self._preview_proxy.setZValue(40)
        self._preview_proxy.setVisible(False)
        self._plot_item.addItem(self._preview_proxy, ignoreBounds=True)
        self._view_box.sigRangeChanged.connect(self._on_view_range_changed)

    # ---- lifecycle ----
    def reset(self) -> None:
        # state
        self._fam_items.clear()
        self._hex_items.clear()
        self._rendered_wells.clear()
        self._well_geoms.clear()
        self._spatial_index = None
        self._data_cache_token = 0
        self._style_state = None
        self._hover_well = None
        self._rect_preview_wells.clear()
        self._well_centers = np.empty((0, 2), dtype=float)
        self._well_center_ids = []
        self._well_center_has_fam = np.array([], dtype=bool)
        self._well_center_has_hex = np.array([], dtype=bool)
        self._well_center_index = {}
        self._pending_drag = None

        # scene cleanup
        try:
            self._plot_item.clear()
        except Exception:
            pass

        # legend & overlays
        try:
            self._legend.clear()
        except Exception:
            pass

        self._hover_overlay.clear()
        self._hover_overlay.setVisible(False)
        self._preview_overlay.clear()
        self._preview_overlay.setVisible(False)
        self._preview_proxy.setData([], [])
        self._preview_proxy.setVisible(False)

        # re-add fixed items
        self._plot_item.addItem(self._rect_roi, ignoreBounds=True)
        self._plot_item.addItem(self._hover_overlay)
        self._plot_item.addItem(self._preview_overlay)
        self._plot_item.addItem(self._preview_proxy, ignoreBounds=True)

        # axes
        self._setup_axes()

        if self._render_timer.isActive():
            self._render_timer.stop()
        if self._drag_throttle_timer.isActive():
            self._drag_throttle_timer.stop()
        if self._tick_update_timer.isActive():
            self._tick_update_timer.stop() 
            
    def closeEvent(self, event) -> None:
        if self._render_timer.isActive():
            self._render_timer.stop()
        if self._drag_throttle_timer.isActive():
            self._drag_throttle_timer.stop()
        if self._tick_update_timer.isActive():
            self._tick_update_timer.stop()
        try:
            self._legend.clear()
        except Exception:
            pass
        super().closeEvent(event)

    # ---- public api ----
    def render_wells(self, data: Dict[str, PCRCoords], *, cache_token: int | None = None) -> None:
        incoming_wells = set(data.keys())
        token = cache_token if cache_token is not None else self._data_cache_token
        selected = set(self._store.selected_wells) if self._store else set()
        preview = self._collect_preview_wells()

        if incoming_wells and incoming_wells == self._rendered_wells and token == self._data_cache_token:
            change = self._apply_interaction_styles(hovered=self._hover_well, selected=selected, preview=preview)
            self._update_overlays(change)
            self._schedule_render(full=change.base_dirty, overlay=change.overlay_dirty or change.base_dirty)
            return

        plot_was_empty = not self._fam_items and not self._hex_items

        self._style_state = None
        self._rendered_wells = incoming_wells
        self._data_cache_token = token

        update_items(self, data)
        rebuild_spatial_index(self)

        change = self._apply_interaction_styles(hovered=self._hover_well, selected=selected, preview=preview)
        self._update_overlays(change)
        self._schedule_render(full=True, overlay=True, force_flush=plot_was_empty)

    def set_hover(self, well: Optional[str]) -> None:
        normalized = well if well_mapping.is_valid_well_id(well) else None
        if normalized == self._hover_well:
            return
        self._hover_well = normalized

        change = self._apply_interaction_styles(
            hovered=self._hover_well,
            selected=set(self._store.selected_wells) if self._store else set(),
            preview=self._collect_preview_wells(),
        )
        self._update_overlays(change)
        self._schedule_render(full=change.base_dirty, overlay=True)

    def bind_interaction_store(self, store: InteractionStore | None) -> None:
        # Eski store varsa disconnect et
        if self._store is not None:
            try:
                self._store.previewChanged.disconnect(self._on_store_preview_changed)
            except TypeError:
                # Zaten bağlı değilse PyQt TypeError fırlatır
                pass

        self._store = store

        # Yeni store varsa connect et
        if self._store is not None:
            self._store.previewChanged.connect(
    self._on_store_preview_changed,
    QtCore.Qt.QueuedConnection,
)

    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        visibility_changed = set_channel_visibility(self, fam_visible, hex_visible)
        if not visibility_changed:
            return

        refresh_legend_pg(self)
        rebuild_spatial_index(self)
        self._update_preview_proxy(self._collect_preview_wells())

        change = self._apply_interaction_styles(
            hovered=self._hover_well,
            selected=set(self._store.selected_wells) if self._store else set(),
            preview=self._collect_preview_wells(),
        )
        self._update_overlays(change)
        self._schedule_render(full=True, overlay=True)

    def set_title(self, title: str) -> None:
        self._title = title
        self._plot_item.setTitle(self._title, color=self._style.axes.title_color)

    # ---- interaction helpers invoked by ViewBox ----
    def handle_hover(self, pos: Optional[tuple[float, float]]) -> None:
        return handle_hover_impl(self, pos)

    def handle_click(self, pos: tuple[float, float], *, ctrl_pressed: bool) -> None:
        return handle_click_impl(self, pos, ctrl_pressed=ctrl_pressed)

    def handle_drag(self, start: tuple[float, float], current: tuple[float, float], *, finished: bool) -> None:
        return handle_drag_impl(self, start, current, finished=finished)

    # ---- internal render helpers ----
    def _setup_axes(self) -> None:
        apply_axes_style(
            self,
            self._plot_item,
            self._view_box,
            self._style.axes,
            self._title,
            self._style.axes.default_xlim,
            self._style.axes.default_ylim,
        )

    def _update_overlays(self, change):
        update_overlays(self, change)

    def _collect_preview_wells(self) -> Set[str]:
        return collect_preview_wells_impl(self)

    def _on_store_preview_changed(self, wells: Set[str]) -> None:
        return on_store_preview_changed_impl(self, wells)

    def _apply_interaction_styles(self, hovered: Optional[str], selected: Set[str], preview: Set[str]) -> InteractionStyleChange:
        return apply_interaction_styles(self, hovered=hovered, selected=selected, preview=preview)

    def _update_preview_proxy(self, wells: Set[str]) -> None:
        if not self._use_preview_proxy:
            self._preview_proxy.setData([], [])
            self._preview_proxy.setVisible(False)
            return
        if not wells or not self._well_center_index:
            self._preview_proxy.setData([], [])
            self._preview_proxy.setVisible(False)
            return
        indices: List[int] = []
        for well in wells:
            idx = self._well_center_index.get(well)
            if idx is None:
                continue
            fam_ok = self._fam_visible and self._well_center_has_fam[idx]
            hex_ok = self._hex_visible and self._well_center_has_hex[idx]
            if fam_ok or hex_ok:
                indices.append(idx)
        if not indices:
            self._preview_proxy.setData([], [])
            self._preview_proxy.setVisible(False)
            return
        coords = self._well_centers[indices]
        self._preview_proxy.setData(coords[:, 0], coords[:, 1])
        self._preview_proxy.setVisible(True)

    # ---- render scheduling ----
    def _schedule_render(self, *, full: bool = False, overlay: bool = False, force_flush: bool = False) -> None:
        return schedule_render_impl(self, full=full, overlay=overlay, force_flush=force_flush)

    def _flush_pending_render(self) -> None:
        return flush_pending_render_impl(self)

    def _flush_pending_drag(self) -> None:
        return flush_pending_drag_impl(self)

    def _apply_axis_ranges(self, *, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
        apply_axis_ranges(self._plot_item, self._view_box, xlim=xlim, ylim=ylim)

    def _on_view_range_changed(self, view_box, range_) -> None:
        if not range_ or len(range_) < 2:
            return
        x_range = (float(range_[0][0]), float(range_[0][1]))
        y_range = (float(range_[1][0]), float(range_[1][1]))
        if self._last_tick_range == (x_range, y_range):
            return
        self._pending_tick_range = (x_range, y_range)
        if not self._tick_update_timer.isActive():
            self._tick_update_timer.start(30)
    def update_axes_dynamically(self):
            """ViewBox değiştikçe eksen etiketlerini yeniden hesaplar."""
            try:
                # Mevcut görünür aralığı al
                (x0, x1), (y0, y1) = self._view_box.viewRange()            
                set_axis_ticks(self._plot_item, (x0, x1), (y0, y1))
            except Exception as e:
                print(f"Dynamic axis update error: {e}")
    def _flush_pending_ticks(self) -> None:
        if self._pending_tick_range is None:
            return
        x_range, y_range = self._pending_tick_range
        self._pending_tick_range = None
        self._last_tick_range = (x_range, y_range)
        set_axis_ticks(self._plot_item, x_range, y_range)