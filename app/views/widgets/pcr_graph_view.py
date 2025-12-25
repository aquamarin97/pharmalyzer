# app/views/widgets/pcr_graph_view.py
from __future__ import annotations

from typing import Tuple, List, Optional

import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib import cm
import logging
from typing import Dict, List, Optional, Set
from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService, Coord
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRDataService, PCRCoords
from app.utils import well_mapping
logger = logging.getLogger(__name__)

class PCRGraphView(FigureCanvas):
    """
InteractionStore seçimlerini dinleyip çoklu kuyu çizimi yapan, sadece render
    sorumluluğuna sahip Matplotlib PCR grafiği.
    """

    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        self.fig = Figure(figsize=(6, 4.5))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self._style = style or PCRGraphStyle()
        self._title = "PCR Grafik"
        
        self._store: InteractionStore | None = None
        self._data_service: PCRDataService | None = None

        self._fam_lines: Dict[str, Line2D] = {}
        self._hex_lines: Dict[str, Line2D] = {}
        self._selected_wells: Set[str] = set()
        self._hover_well: Optional[str] = None

    def _setup_style(self) -> None:
        self._fam_visible = True
        self._hex_visible = True
        
        self._setup_style()

    # ---- interaction wiring ----
    def set_interaction_store(self, store: InteractionStore, data_service: PCRDataService) -> None:
        if self._store is not None:
            try:
                self._store.selectedChanged.disconnect(self._on_selection_changed)
                self._store.hoverChanged.disconnect(self._on_hover_changed)
            except Exception:
                pass

        self._store = store
        self._data_service = data_service
        self._store.selectedChanged.connect(self._on_selection_changed)
        self._store.hoverChanged.connect(self._on_hover_changed)

        # mevcut state'i uygula
        self._on_selection_changed(self._store.selected_wells)
        self._on_hover_changed(self._store.hover_well)

    # ---- lifecycle / cleanup ----
    def reset_plot(self) -> None:
        """Grafiği temizle."""
        self._fam_lines.clear()
        self._hex_lines.clear()
        self.ax.clear()
        self._setup_style()
        self.ax.set_title(self._title)
        self.draw_idle()



    def closeEvent(self, event) -> None:
        self.reset_plot()
        super().closeEvent(event)

    # ---- rendering ----
    def _on_selection_changed(self, wells: Set[str]) -> None:
        self._selected_wells = wells or set()
        if self._data_service is None:
            return

        if not self._selected_wells:
            self.reset_plot()
            return
        
        try:
            data = self._data_service.get_coords_for_wells(self._selected_wells)
        except Exception as exc:
            logger.warning("PCR koordinatları alınamadı: %s", exc, exc_info=True)
            self.reset_plot()
            return

        self._render_wells(data)

    def _render_wells(self, data: Dict[str, PCRCoords]) -> None:
        self._fam_lines.clear()
        self._hex_lines.clear()

        self.ax.clear()
        self._setup_style()

        if not data:
            self.ax.set_title(self._title)
            self.draw_idle()
            return

        wells_sorted = sorted(data.keys(), key=lambda w: well_mapping.well_id_to_patient_no(w))
        color_map = cm.get_cmap("tab20", max(1, len(wells_sorted)))

        fam_all: List[Coord] = []
        hex_all: List[Coord] = []

        for idx, well in enumerate(wells_sorted):
            coords = data.get(well)
            if coords is None:
                continue

            fam_coords = coords.fam or []
            hex_coords = coords.hex or []

            if fam_coords:
                fam_all.extend(fam_coords)
                fam_x, fam_y = zip(*fam_coords)
            else:
                fam_x, fam_y = [], []

            if hex_coords:
                hex_all.extend(hex_coords)
                hex_x, hex_y = zip(*hex_coords)
            else:
                hex_x, hex_y = [], []

            color = color_map(idx)
            fam_line, = self.ax.plot(
                fam_x,
                fam_y,
                label=f"{well} FAM",
                color=color,
                linewidth=2.0,
                alpha=0.9,
            )
            hex_line, = self.ax.plot(
                hex_x,
                hex_y,
                label=f"{well} HEX",
                color=color,
                linewidth=2.0,
                alpha=0.6,
                linestyle="--",
            )

            fam_line.set_visible(self._fam_visible)
            hex_line.set_visible(self._hex_visible)

            self._fam_lines[well] = fam_line
            self._hex_lines[well] = hex_line

        self._apply_ylim(fam_all, hex_all)
        self._apply_hover_highlight()
        self._refresh_legend()
        self.draw_idle()


    def _apply_ylim(self, fam_coords: List[Coord], hex_coords: List[Coord]) -> None:
        ylim = PCRGraphLayoutService.compute_ylim_for_static_draw(
            fam_coords=fam_coords,
            hex_coords=hex_coords,
            min_floor=4500.0,
            y_padding=500.0,
        )
        if ylim:
            self.ax.set_ylim(*ylim)
        self.ax.relim()
        self.ax.autoscale_view(scalex=True, scaley=False)

    def _on_hover_changed(self, well: Optional[str]) -> None:
        self._hover_well = well if well_mapping.is_valid_well_id(well) else None
        self._apply_hover_highlight()
        self.draw_idle()
    def _apply_hover_highlight(self) -> None:
        if not self._fam_lines and not self._hex_lines:
            return

        hovered = self._hover_well
        for well, line in self._fam_lines.items():
            self._style_line(line, hovered, well, channel="fam")
        for well, line in self._hex_lines.items():
            self._style_line(line, hovered, well, channel="hex")

    def _style_line(self, line: Line2D, hovered: Optional[str], well: str, channel: str) -> None:
        base_alpha = 0.9 if channel == "fam" else 0.6
        base_width = 2.0
        if hovered is None:
            line.set_alpha(base_alpha)
            line.set_linewidth(base_width)
            return

        if well == hovered:
            line.set_alpha(1.0)
            line.set_linewidth(base_width + 1.2)
        else:
            line.set_alpha(base_alpha * 0.25)
            line.set_linewidth(base_width)

    # ---- visibility ----
    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        if fam_visible is not None:
            self._fam_visible = bool(fam_visible)

        if hex_visible is not None:
            self._hex_visible = bool(hex_visible)

        for line in self._fam_lines.values():
            line.set_visible(self._fam_visible)
        for line in self._hex_lines.values():
            line.set_visible(self._hex_visible)

        self._refresh_legend()
        self.draw_idle()

    def set_title(self, title: str) -> None:
        self._title = title
        self.ax.set_title(self._title)
        self.draw_idle()

    # ---- styling ----
    def _setup_style(self) -> None:
        s = self._style
        self.fig.patch.set_facecolor(s.fig_facecolor)
        self.ax.set_facecolor(s.ax_facecolor)
        self.ax.grid(color=s.grid_color, linestyle=s.grid_linestyle, linewidth=s.grid_linewidth)

        self.ax.tick_params(colors=s.tick_color)
        self.ax.xaxis.label.set_color(s.label_color)
        self.ax.yaxis.label.set_color(s.label_color)
        self.ax.title.set_color(s.title_color)

        self.ax.set_xlim(*s.default_xlim)
        self.ax.set_ylim(*s.default_ylim)

        self.ax.axhline(y=0, color=s.grid_color, linestyle="-", linewidth=1)
        self.ax.axvline(x=0, color=s.grid_color, linestyle="-", linewidth=1)

    def _refresh_legend(self) -> None:
        legend = self.ax.get_legend()
        if legend:
            legend.remove()

        handles_labels = []
        for well, line in self._fam_lines.items():
            if line.get_visible():
                handles_labels.append((line, line.get_label()))
        for well, line in self._hex_lines.items():
            if line.get_visible():
                handles_labels.append((line, line.get_label()))

        visible_handles = [(h, label) for h, label in handles_labels if h.get_visible()]
        
        if not visible_handles:
            return

        handles, labels = zip(*visible_handles)
        legend = self.ax.legend(handles, labels, fontsize=8)

        s = self._style
        for text in legend.get_texts():
            text.set_color(s.legend_text_color)
        legend.get_frame().set_facecolor(s.legend_frame_facecolor)
        legend.get_frame().set_edgecolor(s.legend_frame_edgecolor)
