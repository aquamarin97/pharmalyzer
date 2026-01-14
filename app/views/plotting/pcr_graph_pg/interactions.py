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
        self._pan_active = False
        self._pan_speed = 0.0015  # daha yumuşak
        self._pan_speed = 0.003   # daha hızlı



    def hoverEvent(self, ev):
        if ev.isExit() or self._drag_active or self._pan_active:
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
        # --- Middle mouse => SMOOTH PAN ---
        if ev.button() == QtCore.Qt.MiddleButton:
            if ev.isStart():
                self._pan_active = True
                self._last_pan_pos = ev.scenePos()
                ev.accept()
                return

            if not self._pan_active or self._last_pan_pos is None:
                return

            delta_px = ev.scenePos() - self._last_pan_pos
            self._last_pan_pos = ev.scenePos()

            # view range al
            (x0, x1), (y0, y1) = self.viewRange()
            w = x1 - x0
            h = y1 - y0

            # pixel -> view space dönüşüm
            dx = -delta_px.x() * w * self._pan_speed
            dy =  delta_px.y() * h * self._pan_speed

            self.setRange(
                xRange=(x0 + dx, x1 + dx),
                yRange=(y0 + dy, y1 + dy),
                padding=0,
            )

            ev.accept()
            if ev.isFinish():
                self._pan_active = False
                self._last_pan_pos = None
            return

        # --- Left mouse => mevcut davranış ---
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


            
            
    def wheelEvent(self, ev):
        # pyqtgraph ViewBox wheel zoom'u normalde mouseEnabled ile ilişkilidir;
        # biz custom zoom yapıyoruz.
        try:
            delta = ev.delta()  # bazı sürümlerde var
        except Exception:
            delta = ev.angleDelta().y()  # Qt5 wheel event

        if delta == 0:
            ev.ignore()
            return

        # wheel up -> zoom in, wheel down -> zoom out
        steps = delta / 120.0
        zoom_factor = 0.9 ** steps  # 0.9: hassasiyet; istersen 0.95 yaparız

        mouse_point = self.mapSceneToView(ev.scenePos())
        self.scaleBy((zoom_factor, zoom_factor), center=mouse_point)

        ev.accept()
