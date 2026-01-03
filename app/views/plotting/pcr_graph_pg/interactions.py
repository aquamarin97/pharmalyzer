# app\views\plotting\pcr_graph_pg\interactions.py
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
import pyqtgraph as pg

if TYPE_CHECKING:
    from .renderer import PCRGraphRendererPG


class PCRGraphViewBox(pg.ViewBox):
    """
    Custom ViewBox to own mouse interactions without triggering default panning/zooming.
    """

    def __init__(self, renderer: "PCRGraphRendererPG"):
        super().__init__(enableMenu=False)
        self._renderer = renderer
        self.setMouseEnabled(x=False, y=False)
        self.setAcceptHoverEvents(True)
        self._drag_active = False

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