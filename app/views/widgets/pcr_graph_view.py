# app/views/widgets/pcr_graph_view.py
from __future__ import annotations

from typing import Tuple, List, Optional

import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


Coord = Tuple[int, float]


class PCRGraphView(FigureCanvas):
    """
    Matplotlib tabanlı PCR grafik view'i.
    UI bileşenidir (View).
    """

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4.5))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

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
        self.ax.legend()
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
        # Widget kapanırken animasyonu kesin durdur
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

        # split + cache list'lere yaz
        self._static_fam_x.clear(); self._static_fam_y.clear()
        self._static_hex_x.clear(); self._static_hex_y.clear()
        self._anim_fam_x.clear(); self._anim_fam_y.clear()
        self._anim_hex_x.clear(); self._anim_hex_y.clear()

        for x, y in fam_coords:
            if x < start_x:
                self._static_fam_x.append(int(x))
                self._static_fam_y.append(float(y))
            else:
                self._anim_fam_x.append(int(x))
                self._anim_fam_y.append(float(y))

        for x, y in hex_coords:
            if x < start_x:
                self._static_hex_x.append(int(x))
                self._static_hex_y.append(float(y))
            else:
                self._anim_hex_x.append(int(x))
                self._anim_hex_y.append(float(y))

        # axis limits
        all_x = [x for x, _ in (fam_coords + hex_coords)]
        all_y = [y for _, y in (fam_coords + hex_coords)]

        if all_x:
            self.ax.set_xlim(min(all_x) - 1, max(all_x) + 1)
        if all_y:
            ymax = max(all_y)
            self.ax.set_ylim(0, ymax + 500 if ymax > 5000 else 5000)

        # draw static part
        self.fam_line.set_data(self._static_fam_x, self._static_fam_y)
        self.hex_line.set_data(self._static_hex_x, self._static_hex_y)

        def update(frame: int):
            # frame kadar animasyon datasını ekle (slice -> list allocation var ama minimal)
            fam_x = self._static_fam_x + self._anim_fam_x[:frame]
            fam_y = self._static_fam_y + self._anim_fam_y[:frame]
            hex_x = self._static_hex_x + self._anim_hex_x[:frame]
            hex_y = self._static_hex_y + self._anim_hex_y[:frame]

            self.fam_line.set_data(fam_x, fam_y)
            self.hex_line.set_data(hex_x, hex_y)
            return self.fam_line, self.hex_line

        frames = max(len(self._anim_fam_x), len(self._anim_hex_x)) + 1

        self._ani = animation.FuncAnimation(
            self.fig,
            update,
            frames=frames,
            interval=speed,
            blit=False,   # blit=True istersen performans artar ama Qt+Matplotlib bazen sorun çıkarır
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

        all_y = list(fam_y) + list(hex_y)
        if all_y:
            ymax = max(all_y)
            self.ax.set_ylim(0, ymax + 500 if ymax > 4500 else 4500)

        self.ax.relim()
        self.ax.autoscale_view(scalex=True, scaley=False)
        self.draw_idle()

    # ---- visibility ----
    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        """
        Kanal görünürlüğünü günceller ve lejandı senkronize eder.
        """
        if fam_visible is not None:
            self.fam_line.set_visible(bool(fam_visible))
        if hex_visible is not None:
            self.hex_line.set_visible(bool(hex_visible))

        self._refresh_legend()
        self.draw_idle()

    def _refresh_legend(self) -> None:
        """Yalnızca görünür hatları içeren lejantı yeniden oluştur."""
        legend = self.ax.get_legend()
        if legend:
            legend.remove()

        handles_labels = [
            (self.fam_line, self.fam_line.get_label()),
            (self.hex_line, self.hex_line.get_label()),
        ]
        visible_handles = [(h, label) for h, label in handles_labels if h.get_visible()]

        if visible_handles:
            handles, labels = zip(*visible_handles)
            legend = self.ax.legend(handles, labels)
            for text in legend.get_texts():
                text.set_color("white")
            legend.get_frame().set_facecolor("#202020")
            legend.get_frame().set_edgecolor("white")