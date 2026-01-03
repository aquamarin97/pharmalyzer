# app\views\plotting\pcr_graph_pg\renderer_pg.py
from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, List, Optional, Set

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRCoords
from app.utils import well_mapping

from .geometry_pg import build_spatial_index, nearest_well, wells_in_rect
from .styles_pg import InteractionStyleChange, StyleState, apply_interaction_styles, legend_entries, set_channel_visibility

logger = logging.getLogger(__name__)


class _PCRGraphViewBox(pg.ViewBox):
    """
    Custom ViewBox to own mouse interactions without triggering default panning/zooming.
    """

    def __init__(self, renderer: "PCRGraphRendererPG"):
        super().__init__(enableMenu=False)
        self._renderer = renderer
        self.setMouseEnabled(x=False, y=False)
        self.setAcceptHoverEvents(True)
        self._drag_active = False

    # Hover -> cross-highlighting
    def hoverEvent(self, ev):
        if self._drag_active or ev.isExit():
            self._renderer.handle_hover(None)
            return
        pos = ev.pos()
        if pos is None:
            self._renderer.handle_hover(None)
            return
        view_pos = self.mapToView(pos)
        self._renderer.handle_hover((view_pos.x(), view_pos.y()))

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            view = self.mapSceneToView(ev.scenePos())
            self._renderer.handle_click(
                (view.x(), view.y()),
                ctrl_pressed=bool(ev.modifiers() & QtCore.Qt.ControlModifier),
            )
            ev.accept()
            return
        super().mouseClickEvent(ev)

    def mouseDragEvent(self, ev, axis=None):
        if ev.button() != QtCore.Qt.LeftButton:
            super().mouseDragEvent(ev, axis=axis)
            return

        self._drag_active = True
        start = self.mapSceneToView(ev.buttonDownScenePos())
        current = self.mapSceneToView(ev.scenePos())
        self._renderer.handle_drag(
            (start.x(), start.y()),
            (current.x(), current.y()),
            finished=ev.isFinish(),
        )
        ev.accept()
        if ev.isFinish():
            self._drag_active = False


class PCRGraphRendererPG(pg.PlotWidget):
    """
    PyQtGraph-based PCR grafiği: yüksek FPS için optimize edildi.
    """

    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        self._style = style or PCRGraphStyle()
        self._title = "PCR Grafik"

        self._view_box = _PCRGraphViewBox(self)
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
        self._hover_overlay = self._build_overlay(pen=pg.mkPen("#D9534F", width=2.5))
        self._preview_overlay = self._build_overlay(pen=pg.mkPen("#D9534F", width=2.0, style=QtCore.Qt.DashLine))

        self._fam_visible = True
        self._hex_visible = True
        self._rendered_wells: Set[str] = set()
        self._data_cache_token: int = 0
        self._well_geoms: Dict[str, Dict[str, np.ndarray]] = {}
        self._spatial_index = None
        self._rect_preview_wells: Set[str] = set()
        self._legend = pg.LegendItem(offset=(10, 10))
        self._legend.setParentItem(self._plot_item.graphicsItem())
        self._rect_roi = pg.RectROI([0, 0], [0, 0], pen=pg.mkPen("#D9534F", width=1.0), movable=False)
        self._rect_roi.setZValue(50)
        self._rect_roi.setVisible(False)
        self._plot_item.addItem(self._rect_roi, ignoreBounds=True)

        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._flush_pending_render)
        self._frame_interval_ms = 16
        self._pending_full_draw = False
        self._pending_overlay = False
        self._last_render_ts = perf_counter()

        self._setup_axes()
        self._plot_item.addItem(self._hover_overlay)
        self._plot_item.addItem(self._preview_overlay)

    # ---- lifecycle ----
    def reset(self) -> None:
        self._fam_items.clear()
        self._hex_items.clear()
        self._rendered_wells.clear()
        self._well_geoms.clear()
        self._spatial_index = None
        self._data_cache_token = 0
        self._style_state = None
        self._hover_well = None
        self._rect_preview_wells.clear()
        self._plot_item.clear()
        self._legend.clear()
        self._hover_overlay.clear()
        self._hover_overlay.setVisible(False)
        self._preview_overlay.clear()
        self._preview_overlay.setVisible(False)
        self._plot_item.addItem(self._rect_roi, ignoreBounds=True)
        self._plot_item.addItem(self._hover_overlay)
        self._plot_item.addItem(self._preview_overlay)
        self._setup_axes()
        if self._render_timer.isActive():
            self._render_timer.stop()

    def closeEvent(self, event) -> None:
        if self._render_timer.isActive():
            self._render_timer.stop()
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

        self._style_state = None
        self._rendered_wells = incoming_wells
        self._data_cache_token = token
        self._update_items(data)
        self._rebuild_spatial_index()
        change = self._apply_interaction_styles(hovered=self._hover_well, selected=selected, preview=preview)
        self._update_overlays(change)
        self._schedule_render(full=True, overlay=True)

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
        if self._store is not None:
            try:
                self._store.previewChanged.disconnect(self._preview_slot)  # type: ignore[attr-defined]
            except Exception:
                pass
        self._store = store
        if self._store is not None:
            self._preview_slot = lambda wells: self._on_store_preview_changed(wells)  # type: ignore[attr-defined]
            self._store.previewChanged.connect(self._preview_slot)

    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        visibility_changed = set_channel_visibility(self, fam_visible, hex_visible)
        if not visibility_changed:
            return
        self._refresh_legend()
        self._rebuild_spatial_index()
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
        if pos is None:
            if self._store is not None:
                self._store.set_hover(None)
            else:
                self.set_hover(None)
            return

        x, y = pos
        tol_x, tol_y = self._pixel_tol_in_data()
        well = nearest_well(
            self._spatial_index,
            self._well_geoms,
            x,
            y,
            tol_x,
            tol_y,
            fam_visible=self._fam_visible,
            hex_visible=self._hex_visible,
        )
        if self._store is not None:
            self._store.set_hover(well)
        else:
            self.set_hover(well)

    def handle_click(self, pos: tuple[float, float], *, ctrl_pressed: bool) -> None:
        x, y = pos
        tol_x, tol_y = self._pixel_tol_in_data()
        well = nearest_well(
            self._spatial_index,
            self._well_geoms,
            x,
            y,
            tol_x,
            tol_y,
            fam_visible=self._fam_visible,
            hex_visible=self._hex_visible,
        )
        if well is None or self._store is None:
            return
        if ctrl_pressed:
            self._store.toggle_wells({well})
        else:
            self._store.set_selection({well})

    def handle_drag(self, start: tuple[float, float], current: tuple[float, float], *, finished: bool) -> None:
        x0, y0 = start
        x1, y1 = current
        rect_x, rect_y = min(x0, x1), min(y0, y1)
        w, h = abs(x1 - x0), abs(y1 - y0)
        self._rect_roi.setPos((rect_x, rect_y))
        self._rect_roi.setSize((w, h))
        self._rect_roi.setVisible(not finished)

        if finished:
            self._set_rect_preview(set())
            self._schedule_render(full=False, overlay=True)
            return

        wells = wells_in_rect(
            self._spatial_index,
            self._well_geoms,
            x0,
            x1,
            y0,
            y1,
            fam_visible=self._fam_visible,
            hex_visible=self._hex_visible,
        )
        self._set_rect_preview(wells)
        self._schedule_render(full=False, overlay=True)

    # ---- internal render helpers ----
    def _setup_axes(self) -> None:
        s = self._style.axes
        self.getAxis("bottom").setPen(pg.mkPen(s.tick_color, width=s.tick_width))
        self.getAxis("left").setPen(pg.mkPen(s.tick_color, width=s.tick_width))
        self.getAxis("bottom").setTextPen(pg.mkPen(s.label_color))
        self.getAxis("left").setTextPen(pg.mkPen(s.label_color))
        self._view_box.setBackgroundColor(s.ax_facecolor)
        self.showGrid(x=True, y=True, alpha=0.55)
        self._plot_item.addItem(pg.InfiniteLine(angle=0, pen=pg.mkPen(s.grid_color, width=1)))
        self._plot_item.addItem(pg.InfiniteLine(angle=90, pen=pg.mkPen(s.grid_color, width=1)))
        self._plot_item.getAxis("left").setStyle(tickTextOffset=3)
        self._plot_item.getAxis("bottom").setStyle(tickTextOffset=3)
        self._plot_item.setLabel("bottom", "Cycle", color=s.label_color)
        self._plot_item.setLabel("left", "Fluorescence", color=s.label_color)
        self._plot_item.setTitle(self._title, color=s.title_color)
        self._apply_axis_ranges(xlim=s.default_xlim, ylim=s.default_ylim)

    def _build_overlay(self, pen: QtGui.QPen) -> pg.PlotDataItem:
        item = pg.PlotDataItem(pen=pen, connect="finite")
        item.setZValue(30)
        item.setVisible(False)
        return item

    def _update_items(self, data: Dict[str, PCRCoords]) -> None:
        # remove missing wells
        for well in list(self._fam_items.keys()):
            if well not in data:
                self._plot_item.removeItem(self._fam_items.pop(well))
                self._well_geoms.pop(well, None)
        for well in list(self._hex_items.keys()):
            if well not in data:
                self._plot_item.removeItem(self._hex_items.pop(well))
                self._well_geoms.pop(well, None)

        wells_sorted = sorted(data.keys(), key=lambda w: well_mapping.well_id_to_patient_no(w))
        fam_all: List[np.ndarray] = []
        hex_all: List[np.ndarray] = []

        for well in wells_sorted:
            coords = data.get(well)
            if coords is None:
                continue

            fam_coords = coords.fam
            hex_coords = coords.hex
            fam_has_data = fam_coords.size > 0
            hex_has_data = hex_coords.size > 0
            self._well_geoms[well] = {
                "fam": fam_coords if fam_has_data else np.empty((0, 2), dtype=float),
                "hex": hex_coords if hex_has_data else np.empty((0, 2), dtype=float),
            }

            if fam_has_data:
                fam_all.append(fam_coords)
                fam_item = self._fam_items.get(well)
                if fam_item is None:
                    fam_item = pg.PlotDataItem(connect="finite", name="FAM")
                    self._plot_item.addItem(fam_item)
                    self._fam_items[well] = fam_item
                fam_item.setData(fam_coords[:, 0], fam_coords[:, 1])
                fam_item.setVisible(self._fam_visible)
                fam_item.setProperty("has_data", True)
            else:
                if well in self._fam_items:
                    self._fam_items[well].setData([], [])
                    self._fam_items[well].setProperty("has_data", False)

            if hex_has_data:
                hex_all.append(hex_coords)
                hex_item = self._hex_items.get(well)
                if hex_item is None:
                    hex_item = pg.PlotDataItem(connect="finite", name="HEX")
                    self._plot_item.addItem(hex_item)
                    self._hex_items[well] = hex_item
                hex_item.setData(hex_coords[:, 0], hex_coords[:, 1])
                hex_item.setVisible(self._hex_visible)
                hex_item.setProperty("has_data", True)
            else:
                if well in self._hex_items:
                    self._hex_items[well].setData([], [])
                    self._hex_items[well].setProperty("has_data", False)

        self._refresh_axes_limits(fam_all, hex_all)
        self._refresh_legend()

    def _refresh_axes_limits(self, fam_coords: List[np.ndarray], hex_coords: List[np.ndarray]) -> None:
            # 1. Dinamik Y limitini hesapla
            ylim = PCRGraphLayoutService.compute_ylim_for_static_draw(
                fam_coords=fam_coords,
                hex_coords=hex_coords,
                min_floor=4500.0,
                y_padding=500.0,
            )
            target_ylim = ylim if ylim else self._style.axes.default_ylim
            
            # 2. Limitleri uygula
            self._apply_axis_ranges(xlim=self._style.axes.default_xlim, ylim=target_ylim)
            
            # BUG FIX: İlk çizimde ViewBox'ın eski limitlerde asılı kalmasını engellemek için
            # ViewBox'a koordinatların güncellendiğini ve "auto-range" istemediğimizi açıkça bildiriyoruz.
            self._view_box.sigStateChanged.emit(self._view_box)
            
    def _set_axis_ticks(self, *, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
            bottom_axis = self._plot_item.getAxis("bottom")
            left_axis = self._plot_item.getAxis("left")

            # X ekseni (Cycle): Genellikle 40 döngü olduğu için 4'erli veya 5'erli tamsayı adımlar
            x_range = xlim[1] - xlim[0]
            x_step = max(1, round(x_range / 10)) 
            
            # Y ekseni (Fluorescence): 10'a böl ve en yakın 1000'in katına yuvarla
            y_range = ylim[1] - ylim[0]
            y_raw_step = y_range / 10
            
            if y_range > 5000:
                # 5000'den büyükse 1000'in katlarına yuvarla (Örn: 1200 -> 1000, 1600 -> 2000)
                y_step = max(1000, round(y_raw_step / 1000) * 1000)
            elif y_range > 1000:
                # Daha küçük aralıklarda 500'ün katları daha iyi sonuç verir
                y_step = max(500, round(y_raw_step / 500) * 500)
            else:
                # Çok düşük sinyallerde 100'ün katları
                y_step = max(100, round(y_raw_step / 100) * 100)

            bottom_axis.setTicks([self._build_ticks(xlim, step=x_step)])
            left_axis.setTicks([self._build_ticks(ylim, step=y_step)])
            
    def _build_ticks(self, axis_range: tuple[float, float], step: float) -> list[tuple[float, str]]:
            start, end = axis_range
            ticks: list[tuple[float, str]] = []
            
            current = float(start)
            # Yüksek hassasiyetli karşılaştırma için küçük bir tolerans
            eps = step * 0.01

            while current < end - eps:
                ticks.append((current, self._format_tick_value(current)))
                current += step
            
            # Son değeri (Max) her zaman ekle
            ticks.append((float(end), self._format_tick_value(end)))
            
            return ticks

    @staticmethod
    def _format_tick_value(value: float) -> str:
        # 10'a bölünce küsurat çıkabilir, eğer sayı tamsa (örn: 40.0) tam sayı bas
        # Değilse virgülden sonra 1 basamak bas (örn: 450.5)
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.1f}"    
    def _refresh_legend(self) -> None:
        self._legend.clear()
        for name, pen in legend_entries(self):
            sample = pg.PlotDataItem(pen=pen)
            self._legend.addItem(sample, name)

    def _rebuild_spatial_index(self) -> None:
        self._spatial_index = build_spatial_index(
            self._well_geoms,
            fam_visible=self._fam_visible,
            hex_visible=self._hex_visible,
        )

    def _apply_interaction_styles(self, hovered: Optional[str], selected: Set[str], preview: Set[str]) -> InteractionStyleChange:
        change = apply_interaction_styles(self, hovered=hovered, selected=selected, preview=preview)
        return change

    def _segments_to_xy_with_nans(self, segments: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        if not segments:
            return np.array([]), np.array([])

        xs_list = []
        ys_list = []
        for seg in segments:
            if seg is None or seg.size == 0:
                continue
            # seg shape (N,2) varsayımı
            xs_list.append(seg[:, 0])
            ys_list.append(seg[:, 1])
            # segment kırıcı
            xs_list.append(np.array([np.nan]))
            ys_list.append(np.array([np.nan]))

        if not xs_list:
            return np.array([]), np.array([])
        return np.concatenate(xs_list), np.concatenate(ys_list)

    def _update_overlays(self, change):
        if change.hover_segments:
            xs, ys = self._segments_to_xy_with_nans(change.hover_segments)
            self._hover_overlay.setData(xs, ys)
            self._hover_overlay.setVisible(True)
        else:
            self._hover_overlay.setData([], [])
            self._hover_overlay.setVisible(False)

        if change.preview_segments:
            xs, ys = self._segments_to_xy_with_nans(change.preview_segments)
            self._preview_overlay.setData(xs, ys)
            self._preview_overlay.setVisible(True)
        else:
            self._preview_overlay.setData([], [])
            self._preview_overlay.setVisible(False)

    def _collect_preview_wells(self) -> Set[str]:
        if self._store is not None:
            return set(self._store.preview_wells)
        return set(self._rect_preview_wells)

    def _set_rect_preview(self, wells: Set[str]) -> None:
        if wells == self._rect_preview_wells:
            return
        self._rect_preview_wells = wells
        if self._store is not None:
            self._store.set_preview(wells)
        change = self._apply_interaction_styles(
            hovered=self._hover_well,
            selected=set(self._store.selected_wells) if self._store else set(),
            preview=self._collect_preview_wells(),
        )
        self._update_overlays(change)

    def _on_store_preview_changed(self, wells: Set[str]) -> None:
        self._rect_preview_wells = set(wells or set())
        change = self._apply_interaction_styles(
            hovered=self._hover_well,
            selected=set(self._store.selected_wells) if self._store else set(),
            preview=self._collect_preview_wells(),
        )
        self._update_overlays(change)
        self._schedule_render(full=False, overlay=True)

    def _pixel_tol_in_data(self) -> tuple[float, float]:
        pixel = self._view_box.viewPixelSize()
        if pixel is None:
            return 0.1, 0.1
        return abs(pixel[0] * 6), abs(pixel[1] * 6)

    # ---- render scheduling ----
    def _schedule_render(self, *, full: bool = False, overlay: bool = False) -> None:
        self._pending_full_draw = self._pending_full_draw or full
        self._pending_overlay = self._pending_overlay or overlay
        elapsed_ms = (perf_counter() - self._last_render_ts) * 1000.0
        delay = max(0, int(self._frame_interval_ms - elapsed_ms))
        if self._render_timer.isActive():
            return
        self._render_timer.start(delay)

    def _flush_pending_render(self) -> None:
            full = self._pending_full_draw
            overlay = self._pending_overlay or full
            self._pending_full_draw = False
            self._pending_overlay = False
            
            if full or overlay:
                self.update() # Veya self._plot_item.update()
                
            self._last_render_ts = perf_counter() 
            
    def _apply_axis_ranges(self, *, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
            # Otomatik ölçeklendirmeyi tamamen kapat
            self._plot_item.enableAutoRange(x=False, y=False)
            
            # X Eksen: Kesinlikle padding yok (0,0 noktası için)
            self._plot_item.setXRange(xlim[0], xlim[1], padding=0, update=True)
            
            # Y Eksen: Üstten ve alttan hafif boşluk, update=True zorunlu
            self._plot_item.setYRange(ylim[0], ylim[1], padding=0.03, update=True)
            
            # Kullanıcının sınırların dışına çıkmasını engelle
            # yMin'i biraz daha esnek bırakalım ki 0 etiketi rahat görünsün
            self._plot_item.setLimits(
                xMin=xlim[0], 
                xMax=xlim[1], 
                yMin=ylim[0] - (ylim[1]-ylim[0]) * 0.05, 
                yMax=ylim[1] * 1.1
            )
            
            # Tick'leri hesapla
            self._set_axis_ticks(xlim=xlim, ylim=ylim)