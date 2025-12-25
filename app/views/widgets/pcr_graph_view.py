# app/views/widgets/pcr_graph_view.py
from __future__ import annotations

from typing import Tuple, List, Optional

import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.graph.pcr_graph_layout_service import PCRGraphLayoutService, Coord, PCRSplitData


class PCRGraphView(FigureCanvas):
    """
    Matplotlib tabanlı PCR grafik view'i.
    UI bileşenidir (View).
    """

    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        self.fig = Figure(figsize=(6, 4.5))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self._style = style or PCRGraphStyle()
        self._title = "PCR Grafik"
        self._ani: Optional[animation.FuncAnimation] = None

        # cache: static + anim koordinatlarını her frame yeniden allocate etmeyelim
        self._static_fam_x: List[int] = []
        self._static_fam_y: List[float] = []
        self._static_hex_x: List[int] = []
        self._static_hex_y: List[float] = []
        self._anim_fam_x: List[int] = []
        self._anim_fam_y: List[float] = []
        self._anim_hex_x: List[int] = []
        self._anim_hex_y: List[float] = []

        self._setup_style()
        self._setup_lines()

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

    def _setup_lines(self) -> None:
        s = self._style
        (self.fam_line,) = self.ax.plot([], [], label="FAM", linestyle="-", linewidth=2, color=s.fam_color)
        (self.hex_line,) = self.ax.plot([], [], label="HEX", linestyle="-", linewidth=2, color=s.hex_color)
        self.ax.set_title(self._title)
        self._refresh_legend()

    def set_title(self, title: str) -> None:
        self._title = title
        self.ax.set_title(self._title)
        self.draw_idle()

    # ---- lifecycle / cleanup ----
    def reset_plot(self) -> None:
        """Grafiği temizle (animasyonu iptal eder, çizgileri sıfırlar)."""
        self._stop_animation()
        self.fam_line.set_data([], [])
        self.hex_line.set_data([], [])
        self.ax.set_title(self._title)
        self.draw_idle()

    def _stop_animation(self) -> None:
        if self._ani is None:
            return
        try:
            if getattr(self._ani, "event_source", None) is not None:
                self._ani.event_source.stop()
        except Exception:
            pass
        finally:
            self._ani = None

    def closeEvent(self, event) -> None:
        self._stop_animation()
        super().closeEvent(event)

    # ---- drawing ----
    def animate_graph(
        self,
        fam_coords: List[Coord],
        hex_coords: List[Coord],
        start_x: int = 21,
        speed: int = 25,
    ) -> None:
        """
        Grafiği animasyonla çizer.
        - start_x öncesi statik
        - start_x sonrası frame frame akar
        """
        self._stop_animation()

        fam_coords = fam_coords or []
        hex_coords = hex_coords or []
        if not fam_coords and not hex_coords:
            self.reset_plot()
            return

        split: PCRSplitData = PCRGraphLayoutService.split_static_anim(
            fam_coords=fam_coords,
            hex_coords=hex_coords,
            start_x=start_x,
            min_y_floor=float(self._style.default_ylim[1]),
            y_padding=500.0,
        )

        # cache'leri güncelle
        self._static_fam_x[:] = split.static_fam_x
        self._static_fam_y[:] = split.static_fam_y
        self._static_hex_x[:] = split.static_hex_x
        self._static_hex_y[:] = split.static_hex_y
        self._anim_fam_x[:] = split.anim_fam_x
        self._anim_fam_y[:] = split.anim_fam_y
        self._anim_hex_x[:] = split.anim_hex_x
        self._anim_hex_y[:] = split.anim_hex_y

        if split.xlim:
            self.ax.set_xlim(*split.xlim)
        if split.ylim:
            self.ax.set_ylim(*split.ylim)

        # static part
        self.fam_line.set_data(self._static_fam_x, self._static_fam_y)
        self.hex_line.set_data(self._static_hex_x, self._static_hex_y)

        def update(frame: int):
            fam_x = self._static_fam_x + self._anim_fam_x[:frame]
            fam_y = self._static_fam_y + self._anim_fam_y[:frame]
            hex_x = self._static_hex_x + self._anim_hex_x[:frame]
            hex_y = self._static_hex_y + self._anim_hex_y[:frame]

            self.fam_line.set_data(fam_x, fam_y)
            self.hex_line.set_data(hex_x, hex_y)
            return self.fam_line, self.hex_line

        self._ani = animation.FuncAnimation(
            self.fig,
            update,
            frames=split.frames,
            interval=speed,
            blit=False,
            repeat=False,
        )
        self.draw_idle()

    def draw_graph(self, fam_coords: List[Coord], hex_coords: List[Coord]) -> None:
        """Animasyonsuz çizim."""
        self._stop_animation()

        fam_coords = fam_coords or []
        hex_coords = hex_coords or []
        if not fam_coords and not hex_coords:
            self.reset_plot()
            return

        if fam_coords:
            fam_x, fam_y = zip(*fam_coords)
        else:
            fam_x, fam_y = [], []

        if hex_coords:
            hex_x, hex_y = zip(*hex_coords)
        else:
            hex_x, hex_y = [], []

        self.fam_line.set_data(fam_x, fam_y)
        self.hex_line.set_data(hex_x, hex_y)

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
        self.draw_idle()

    # ---- visibility ----
    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        if fam_visible is not None:
            self.fam_line.set_visible(bool(fam_visible))
        if hex_visible is not None:
            self.hex_line.set_visible(bool(hex_visible))

        self._refresh_legend()
        self.draw_idle()

    def _refresh_legend(self) -> None:
        legend = self.ax.get_legend()
        if legend:
            legend.remove()

        handles_labels = [
            (self.fam_line, self.fam_line.get_label()),
            (self.hex_line, self.hex_line.get_label()),
        ]
        visible_handles = [(h, label) for h, label in handles_labels if h.get_visible()]

        if not visible_handles:
            return

        handles, labels = zip(*visible_handles)
        legend = self.ax.legend(handles, labels)

        s = self._style
        for text in legend.get_texts():
            text.set_color(s.legend_text_color)
        legend.get_frame().set_facecolor(s.legend_frame_facecolor)
        legend.get_frame().set_edgecolor(s.legend_frame_edgecolor)
