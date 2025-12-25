from __future__ import annotations

from typing import Dict, List, Optional

from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService, Coord
from app.services.pcr_data_service import PCRCoords
from app.utils import well_mapping


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

        self._setup_axes()

    # ---- lifecycle ----
    def reset(self) -> None:
        """Grafiği temizle ve varsayılan stile dön."""
        self._fam_lines.clear()
        self._hex_lines.clear()
        self.ax.clear()
        self._setup_axes()
        self.ax.set_title(self._title)
        self.draw_idle()

    def closeEvent(self, event) -> None:
        self.reset()
        super().closeEvent(event)

    # ---- rendering ----
    def render_wells(self, data: Dict[str, PCRCoords]) -> None:
        """
        Verilen kuyu koordinatlarını çiz.

        Params:
            data: kuyu_id -> PCRCoords
        """
        self._fam_lines.clear()
        self._hex_lines.clear()

        self.ax.clear()
        self._setup_axes()

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
                **self._style.fam_pen,
            )
            hex_line, = self.ax.plot(
                hex_x,
                hex_y,
                label=f"{well} HEX",
                color=color,
                **self._style.hex_pen,
            )

            fam_line.set_visible(self._fam_visible)
            hex_line.set_visible(self._hex_visible)

            self._fam_lines[well] = fam_line
            self._hex_lines[well] = hex_line

        self._apply_ylim(fam_all, hex_all)
        self._apply_hover_highlight()
        self._refresh_legend()
        self.ax.set_title(self._title)
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
        else:
            self.ax.set_ylim(*self._style.axes.default_ylim)
        self.ax.relim()
        self.ax.autoscale_view(scalex=True, scaley=False)

    def set_hover(self, well: Optional[str]) -> None:
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
        base_alpha = self._style.fam_pen.get("alpha", 1.0) if channel == "fam" else self._style.hex_pen.get("alpha", 1.0)
        base_width = float(self._style.fam_pen.get("linewidth", 2.0)) if channel == "fam" else float(self._style.hex_pen.get("linewidth", 2.0))
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
    def _setup_axes(self) -> None:
        s = self._style.axes
        self.fig.patch.set_facecolor(s.fig_facecolor)
        self.ax.set_facecolor(s.ax_facecolor)
        self.ax.set_axisbelow(True)
        self.fig.set_facecolor(s.fig_facecolor)
        self.ax.grid(color=s.grid_color, linestyle=s.grid_linestyle, linewidth=s.grid_linewidth)

        self.ax.tick_params(colors=s.tick_color, width=s.tick_width)
        self.ax.xaxis.label.set_color(s.label_color)
        self.ax.yaxis.label.set_color(s.label_color)
        self.ax.title.set_color(s.title_color)

        self.ax.set_xlim(*s.default_xlim)
        self.ax.set_ylim(*s.default_ylim)

        self.ax.axhline(y=0, color=s.grid_color, linestyle="-", linewidth=1)
        self.ax.axvline(x=0, color=s.grid_color, linestyle="-", linewidth=1)
        for spine in self.ax.spines.values():
            spine.set_color(s.grid_color)
    def _refresh_legend(self) -> None:
        legend = self.ax.get_legend()
        if legend:
            legend.remove()

        handles_labels = []
        for _, line in self._fam_lines.items():
            if line.get_visible():
                handles_labels.append((line, line.get_label()))
        for _, line in self._hex_lines.items():
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