# app\views\plotting\pcr_graph_pg\view.py
from __future__ import annotations

from PyQt5 import QtWidgets

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRCoords

from .renderer import PCRGraphRendererPG


class PCRGraphView(QtWidgets.QWidget):
    """
    Thin QWidget wrapper owning PCRGraphRendererPG.
    Exposes a limited API for UI integration without leaking renderer internals.
    """

    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        super().__init__(parent)
        self.renderer = PCRGraphRendererPG(parent=self, style=style)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.renderer)

    def set_title(self, title: str) -> None:
        self.renderer.set_title(title)

    def bind_interaction_store(self, store: InteractionStore | None) -> None:
        self.renderer.bind_interaction_store(store)

    def set_channel_visibility(self, fam_visible: bool | None = None, hex_visible: bool | None = None) -> None:
        self.renderer.set_channel_visibility(fam_visible=fam_visible, hex_visible=hex_visible)

    def render_wells(self, data: dict[str, PCRCoords], *, cache_token: int | None = None) -> None:
        self.renderer.render_wells(data, cache_token=cache_token)