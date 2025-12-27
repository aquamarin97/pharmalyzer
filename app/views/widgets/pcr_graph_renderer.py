# app\views\widgets\pcr_graph_renderer.py
from __future__ import annotations

from typing import Dict, List, Optional, Set
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from app.services.interaction_store import InteractionStore
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

        self._line_to_well: Dict[Line2D, str] = {}
        self._store: InteractionStore | None = None
        self._selecting: bool = False
        self._selection_buffer: Set[str] = set()
        self._rect_selector: RectangleSelector | None = None
        self._rect_selecting: bool = False

       
        self._setup_axes()
        self._connect_events()
        
    # ---- lifecycle ----
    def reset(self) -> None:
        """Grafiği temizle ve varsayılan stile dön."""
        self._fam_lines.clear()
        self._hex_lines.clear()
        self._line_to_well.clear()
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
        self._line_to_well.clear()
        
        self.ax.clear()
        self._setup_axes()

        if not data:
            self.ax.set_title(self._title)
            self.draw_idle()
            return

        wells_sorted = sorted(data.keys(), key=lambda w: well_mapping.well_id_to_patient_no(w))

        fam_all: List[Coord] = []
        hex_all: List[Coord] = []
        for well in wells_sorted:

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

            fam_line, = self.ax.plot(
                fam_x,
                fam_y,
                label="FAM",
                color=self._style.fam_color,
                **self._style.fam_pen,
            )
            hex_line, = self.ax.plot(
                hex_x,
                hex_y,
                label="HEX",
                color=self._style.hex_color,
                **self._style.hex_pen,
            )

            fam_line.set_visible(self._fam_visible)
            hex_line.set_visible(self._hex_visible)
            fam_line.set_picker(5)
            hex_line.set_picker(5)


            self._fam_lines[well] = fam_line
            self._hex_lines[well] = hex_line

            self._line_to_well[fam_line] = well
            self._line_to_well[hex_line] = well

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
            line.set_alpha(base_alpha * 1)
            line.set_linewidth(base_width)

    def bind_interaction_store(self, store: InteractionStore | None) -> None:
        """Grafik etkileşimlerini InteractionStore ile köprüle."""
        self._store = store

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
            
    # ---- events ----
    def _connect_events(self) -> None:
        self.mpl_connect("motion_notify_event", self._on_motion)
        self.mpl_connect("button_press_event", self._on_button_press)
        self.mpl_connect("button_release_event", self._on_button_release)
        self._rect_selector = RectangleSelector(
            self.ax,
            self._on_rectangle_select,
            useblit=True,
            button=[1],
            interactive=False,
            props={"edgecolor": "red", "facecolor": "none", "linewidth": 1},
        )
        self._rect_selector.connect_event("button_press_event", self._on_rect_press)
        self._rect_selector.connect_event("button_release_event", self._on_rect_release)

    def _on_motion(self, event) -> None:
        if self._rect_selecting:
            return

        if event.inaxes != self.ax:
            self._apply_hover_from_graph(None)
            return

        well = self._find_well_at_event(event)
        self._apply_hover_from_graph(well)

        if self._selecting and well:
            self._add_to_selection(well)

    def _on_button_press(self, event) -> None:
        if event.button != 1:
            return
        if self._rect_selecting:
            return
        self._selecting = True
        self._selection_buffer.clear()

        well = self._find_well_at_event(event)
        if well:
            self._add_to_selection(well)
        elif self._store is not None:
            self._store.clear_selection()

    def _on_button_release(self, event) -> None:
        if event.button != 1:
            return
        if self._rect_selecting:
            return
        self._selecting = False
        if not self._selection_buffer and self._store is not None:
            self._store.clear_selection()
        self._selection_buffer.clear()

    def _on_rect_press(self, event) -> None:
        if event.button != 1:
            return
        self._rect_selecting = True
        self._selection_buffer.clear()

    def _on_rect_release(self, event) -> None:
        if event.button != 1:
            return
        self._rect_selecting = False

    def _on_rectangle_select(self, eclick, erelease) -> None:
        if self._store is None:
            return

        if eclick.xdata is None or erelease.xdata is None or eclick.ydata is None or erelease.ydata is None:
            return

        x0, x1 = sorted([eclick.xdata, erelease.xdata])
        y0, y1 = sorted([eclick.ydata, erelease.ydata])

        wells_in_rect: Set[str] = set()
        for line, well in self._line_to_well.items():
            if not line.get_visible():
                continue
            x_data = line.get_xdata(orig=False)
            y_data = line.get_ydata(orig=False)
            for x, y in zip(x_data, y_data):
                if x is None or y is None:
                    continue
                if x0 <= x <= x1 and y0 <= y <= y1:
                    wells_in_rect.add(well)
                    break

        ctrl_pressed = bool(
            (eclick.key and "control" in str(eclick.key).lower())
            or (erelease.key and "control" in str(erelease.key).lower())
        )

        if not wells_in_rect and not ctrl_pressed:
            self._store.clear_selection()
            return

        if ctrl_pressed:
            updated = set(self._store.selected_wells)
            updated.update(wells_in_rect)
            self._store.set_selection(updated)
        else:
            self._store.set_selection(wells_in_rect)

    def _apply_hover_from_graph(self, well: Optional[str]) -> None:
        if self._store is not None:
            self._store.set_hover(well)
        else:
            self.set_hover(well)

    def _add_to_selection(self, well: str) -> None:
        if well in self._selection_buffer:
            return
        self._selection_buffer.add(well)
        if self._store is None:
            return

        updated = set(self._store.selected_wells)
        updated.add(well)
        self._store.set_selection(updated)

    def _find_well_at_event(self, event) -> Optional[str]:
        for line, well in self._line_to_well.items():
            if not line.get_visible():
                continue
            contains, _ = line.contains(event)
            if contains:
                return well
        return None

            
    def _refresh_legend(self) -> None:
        legend = self.ax.get_legend()
        if legend:
            legend.remove()

        fam_visible = any(line.get_visible() for line in self._fam_lines.values())
        hex_visible = any(line.get_visible() for line in self._hex_lines.values())

        if not fam_visible and not hex_visible:
            return

        handles: List[Line2D] = []
        labels: List[str] = []
        if fam_visible:
            handles.append(Line2D([0], [0], color=self._style.fam_color, label="FAM", **self._style.fam_pen))
            labels.append("FAM")
        if hex_visible:
            handles.append(Line2D([0], [0], color=self._style.hex_color, label="HEX", **self._style.hex_pen))
            labels.append("HEX")
        if not handles:
            return

        legend = self.ax.legend(handles, labels, fontsize=8, loc="upper left")

        s = self._style
        for text in legend.get_texts():
            text.set_color(s.legend_text_color)
        legend.get_frame().set_facecolor(s.legend_frame_facecolor)
        legend.get_frame().set_edgecolor(s.legend_frame_edgecolor)