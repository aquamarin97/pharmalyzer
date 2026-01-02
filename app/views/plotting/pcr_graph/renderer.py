# app\views\plotting\pcr_graph\renderer.py
from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, List, Optional, Set

import numpy as np
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRCoords

from . import drawing, hit_test, interactions, styles
from .axes import setup_axes

logger = logging.getLogger(__name__)


class PCRGraphRenderer(FigureCanvas):
    """
    Matplotlib PCR grafiği: sadece render sorumluluğu taşır.
    InteractionStore veya veri erişimi içermez.
    """

    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        self.fig = Figure(figsize=(6, 4.5))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self._style = style or PCRGraphStyle()
        self._title = "PCR Grafik"

        self._fam_lines: Dict[str, Line2D] = {}
        self._hex_lines: Dict[str, Line2D] = {}
        self._hover_well: Optional[str] = None
        self._fam_visible = True
        self._hex_visible = True
        self._rendered_wells: Set[str] = set()
        self._data_cache_token: int = 0

        self._line_to_well: Dict[Line2D, str] = {}
        self._well_geoms: Dict[str, Dict[str, np.ndarray]] = {}
        self._spatial_index = None
        self._style_state = None
        self._store: InteractionStore | None = None
        self._selecting: bool = False
        self._selection_buffer: Set[str] = set()
        self._rect_selector = None
        self._rect_selecting: bool = False
        self._rect_preview_wells: Set[str] = set()

        hover_width = float(self._style.fam_pen.get("linewidth", 0.05)) + 0.1
        self._hover_artist = LineCollection(
            [], colors=["#D3D3D3"], linewidths=hover_width, zorder=200, visible=False
        )
        self._preview_artist = LineCollection(
            [], colors=["#D3D3D3"], linewidths=hover_width, zorder=150, alpha=0.9, visible=False
        )
        self._hover_artist.set_animated(True)
        self._preview_artist.set_animated(True)

        self._background = None
        self._renderer_cache = None
        self._pending_full_draw = False
        self._pending_overlay = False
        self._frame_interval_ms = 16  # ~60 FPS
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._flush_pending_render)
        self._last_render_ts = perf_counter()
        self._render_counter = 0
        self._fps_anchor = perf_counter()
        self._throttle_hits = 0

        setup_axes(self)
        self.ax.add_collection(self._preview_artist)
        self.ax.add_collection(self._hover_artist)
        interactions.connect_events(self)
        
    # ---- lifecycle ----
    def reset(self) -> None:
        """Grafiği temizle ve varsayılan stile dön."""
        self._fam_lines.clear()
        self._hex_lines.clear()
        self._line_to_well.clear()
        self._well_geoms.clear()
        self._spatial_index = None
        self._rendered_wells.clear()
        self._data_cache_token = 0
        self._style_state = None
        self.ax.clear()
        self._hover_artist.set_segments([])
        self._hover_artist.set_visible(False)
        self._preview_artist.set_segments([])
        self._preview_artist.set_visible(False)
        self._background = None
        self._renderer_cache = None
        if self._render_timer.isActive():
            self._render_timer.stop()
        setup_axes(self)
        self.ax.set_title(self._title)
        self.schedule_render(full=True, overlay=False)

    def closeEvent(self, event) -> None:
        self.reset()
        super().closeEvent(event)

    # ---- rendering ----
    def render_wells(self, data: Dict[str, PCRCoords], *, cache_token: int | None = None) -> None:
        """
        Verilen kuyu koordinatlarını çiz.

        Params:
            data: kuyu_id -> PCRCoords
        """
        incoming_wells = set(data.keys())
        token = cache_token if cache_token is not None else self._data_cache_token
        selected = set(self._store.selected_wells) if self._store else set()
        preview = interactions.collect_preview_wells(self)

        if incoming_wells and incoming_wells == self._rendered_wells and token == self._data_cache_token:
            change = styles.apply_interaction_styles(
                self, hovered=self._hover_well, selected=selected, preview=preview
            )
            self.update_overlays(change.hover_segments, change.preview_segments)
            self.ax.set_title(self._title)
            if change.base_dirty:
                self.invalidate_background()
            self.schedule_render(full=change.base_dirty, overlay=change.overlay_dirty or change.base_dirty)
            return

        self._style_state = None
        drawing.render_wells(self, data)
        hit_test.rebuild_spatial_index(self)
        self._rendered_wells = incoming_wells
        self._data_cache_token = token
        change = styles.apply_interaction_styles(self, hovered=self._hover_well, selected=selected, preview=preview)
        self.update_overlays(change.hover_segments, change.preview_segments)
        self.ax.set_title(self._title)
        self.invalidate_background()
        self.schedule_render(full=True, overlay=True)

    def set_hover(self, well: Optional[str]) -> None:
        interactions.set_hover(self, well)

    def bind_interaction_store(self, store: InteractionStore | None) -> None:
        """Grafik etkileşimlerini InteractionStore ile köprüle."""
        interactions.bind_interaction_store(self, store)

    # ---- visibility ----
    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        visibility_changed = styles.set_channel_visibility(self, fam_visible, hex_visible)
        if not visibility_changed:
            return
        change = styles.apply_interaction_styles(
            self,
            hovered=self._hover_well,
            selected=set(self._store.selected_wells) if self._store else set(),
            preview=interactions.collect_preview_wells(self),
        )
        self.update_overlays(change.hover_segments, change.preview_segments)
        self.invalidate_background()
        self.schedule_render(full=True, overlay=True)

    def set_title(self, title: str) -> None:
        styles.set_title(self, title)
        self.invalidate_background()
        self.schedule_render(full=True, overlay=True)

    # ---- overlays & scheduling ----
    def update_overlays(self, hover_segments: List[np.ndarray], preview_segments: List[np.ndarray]) -> None:
        self._hover_artist.set_segments(hover_segments or [])
        self._hover_artist.set_visible(bool(hover_segments))

        self._preview_artist.set_segments(preview_segments or [])
        self._preview_artist.set_visible(bool(preview_segments))

    def invalidate_background(self) -> None:
        self._background = None
        self._renderer_cache = None

    def schedule_render(self, *, full: bool = False, overlay: bool = False) -> None:
        self._pending_full_draw = self._pending_full_draw or full
        self._pending_overlay = self._pending_overlay or overlay

        elapsed_ms = (perf_counter() - self._last_render_ts) * 1000.0
        delay = max(0, int(self._frame_interval_ms - elapsed_ms))

        if self._render_timer.isActive():
            self._throttle_hits += 1
            return
        if delay > 0:
            self._throttle_hits += 1
        if not self._render_timer.isActive():
            self._render_timer.start(delay)

    def _flush_pending_render(self) -> None:
        full = self._pending_full_draw
        overlay = self._pending_overlay or full
        self._pending_full_draw = False
        self._pending_overlay = False

        if full:
            self._draw_full_frame()
        if overlay:
            self._draw_overlays()
        self._last_render_ts = perf_counter()

    def _draw_full_frame(self) -> None:
        hover_visible = self._hover_artist.get_visible()
        preview_visible = self._preview_artist.get_visible()
        self._hover_artist.set_visible(False)
        self._preview_artist.set_visible(False)

        self.draw()
        try:
            self._background = self.copy_from_bbox(self.fig.bbox)
        except Exception:
            self._background = None
        self._renderer_cache = self.get_renderer()

        self._hover_artist.set_visible(hover_visible)
        self._preview_artist.set_visible(preview_visible)
        self._register_frame("full")

    def _draw_overlays(self) -> None:
        if self._background is None or self._renderer_cache is None:
            self._draw_full_frame()
        if self._background is None or self._renderer_cache is None:
            return

        self.restore_region(self._background)
        if self._preview_artist.get_visible():
            self._preview_artist.draw(self._renderer_cache)
        if self._hover_artist.get_visible():
            self._hover_artist.draw(self._renderer_cache)
        self.blit(self.fig.bbox)
        self.flush_events()
        self._register_frame("overlay")

    def _register_frame(self, kind: str) -> None:
        self._render_counter += 1
        now = perf_counter()
        window = now - self._fps_anchor
        if window >= 1.0:
            fps = self._render_counter / window
            logger.debug("PCRGraphRenderer %s FPS: %.1f (throttled=%d)", kind, fps, self._throttle_hits)
            self._render_counter = 0
            self._fps_anchor = now
            self._throttle_hits = 0

    def resizeEvent(self, event) -> None:
        self.invalidate_background()
        super().resizeEvent(event)