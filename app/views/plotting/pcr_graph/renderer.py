# app\views\plotting\pcr_graph\renderer.py
from __future__ import annotations

from typing import Dict, Optional, Set

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRCoords

from . import drawing, interactions, styles
from .axes import setup_axes


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
        self._rect_selector = None
        self._rect_selecting: bool = False
        self._rect_preview_wells: Set[str] = set()
       
        setup_axes(self)
        interactions.connect_events(self)
        
    # ---- lifecycle ----
    def reset(self) -> None:
        """Grafiği temizle ve varsayılan stile dön."""
        self._fam_lines.clear()
        self._hex_lines.clear()
        self._line_to_well.clear()
        self.ax.clear()
        setup_axes(self)
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
        drawing.render_wells(self, data)
        styles.apply_interaction_styles(
            self,
            hovered=self._hover_well,
            selected=set(self._store.selected_wells) if self._store else set(),
            preview=interactions.collect_preview_wells(self),
        )
        self.ax.set_title(self._title)
        self.draw_idle()

    def set_hover(self, well: Optional[str]) -> None:
        interactions.set_hover(self, well)

    def bind_interaction_store(self, store: InteractionStore | None) -> None:
        """Grafik etkileşimlerini InteractionStore ile köprüle."""
        interactions.bind_interaction_store(self, store)

    # ---- visibility ----
    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        styles.set_channel_visibility(self, fam_visible, hex_visible)

    def set_title(self, title: str) -> None:
        styles.set_title(self, title)
