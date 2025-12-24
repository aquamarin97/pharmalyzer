# app\views\widgets\pcr_graph_view.py
# app/views/widgets/pcr_graph_view.py
from __future__ import annotations

from typing import Iterable, Tuple, List, Optional

import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


Coord = Tuple[int, float]


class PCRGraphView(FigureCanvas):
    """
    Matplotlib tabanlı PCR grafik view'i.
    UI bileşenidir (CMV: View).
    """

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4.5))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self._title = "PCR Grafik"
        self._ani: Optional[animation.FuncAnimation] = None

        self._setup_style()
        self._setup_lines()

    def _setup_style(self) -> None:
        self.fig.patch.set_facecolor("black")
        self.ax.set_facecolor("black")
        self.ax.grid(color="grey", linestyle="--", linewidth=0.5)

        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")

        self.ax.set_xlim(0, 40)
        self.ax.set_ylim(0, 5000)

        self.ax.axhline(y=0, color="grey", linestyle="-", linewidth=1)
        self.ax.axvline(x=0, color="grey", linestyle="-", linewidth=1)

    def _setup_lines(self) -> None:
        (self.fam_line,) = self.ax.plot(
            [], [],
            label="FAM",
            linestyle="-",
            linewidth=2,
            color="#39FF14",
        )
        (self.hex_line,) = self.ax.plot(
            [], [],
            label="HEX",
            linestyle="-",
            linewidth=2,
            color="#FF7F00",
        )

        # legend sabit kalsın
        self.ax.legend()

        self.ax.set_title(self._title)

    def set_title(self, title: str) -> None:
        self._title = title
        self.ax.set_title(self._title)
        self.draw_idle()

    def clear(self) -> None:
        """Grafiği temizle (animasyonu iptal eder, çizgileri sıfırlar)."""
        self._stop_animation()
        self.fam_line.set_data([], [])
        self.hex_line.set_data([], [])
        self.ax.set_title(self._title)
        self.draw_idle()

    def _stop_animation(self) -> None:
        # Önceki animasyonun event-source'unu durdur (üst üste binmeyi engeller)
        if self._ani is not None:
            try:
                if self._ani.event_source is not None:
                    self._ani.event_source.stop()
            except Exception:
                pass
            self._ani = None

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
            self.clear()
            return

        # split
        static_fam = [(x, y) for x, y in fam_coords if x < start_x]
        static_hex = [(x, y) for x, y in hex_coords if x < start_x]
        anim_fam = [(x, y) for x, y in fam_coords if x >= start_x]
        anim_hex = [(x, y) for x, y in hex_coords if x >= start_x]

        static_fam_x, static_fam_y = zip(*static_fam) if static_fam else ([], [])
        static_hex_x, static_hex_y = zip(*static_hex) if static_hex else ([], [])
        anim_fam_x, anim_fam_y = zip(*anim_fam) if anim_fam else ([], [])
        anim_hex_x, anim_hex_y = zip(*anim_hex) if anim_hex else ([], [])

        # axis limits
        all_x = [x for x, _ in (fam_coords + hex_coords)]
        all_y = [y for _, y in (fam_coords + hex_coords)]

        if all_x:
            self.ax.set_xlim(min(all_x) - 1, max(all_x) + 1)
        if all_y:
            ymax = max(all_y)
            self.ax.set_ylim(0, ymax + 500 if ymax > 5000 else 5000)

        # draw static part
        self.fam_line.set_data(static_fam_x, static_fam_y)
        self.hex_line.set_data(static_hex_x, static_hex_y)

        def update(frame: int):
            self.fam_line.set_data(
                list(static_fam_x) + list(anim_fam_x[:frame]),
                list(static_fam_y) + list(anim_fam_y[:frame]),
            )
            self.hex_line.set_data(
                list(static_hex_x) + list(anim_hex_x[:frame]),
                list(static_hex_y) + list(anim_hex_y[:frame]),
            )
            return self.fam_line, self.hex_line

        frames = max(len(anim_fam_x), len(anim_hex_x)) + 1

        self._ani = animation.FuncAnimation(
            self.fig,
            update,
            frames=frames,
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
            self.clear()
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

        all_y = list(fam_y) + list(hex_y)
        if all_y:
            ymax = max(all_y)
            self.ax.set_ylim(0, ymax + 500 if ymax > 4500 else 4500)

        self.ax.relim()
        self.ax.autoscale_view(scalex=True, scaley=False)
        self.draw_idle()
