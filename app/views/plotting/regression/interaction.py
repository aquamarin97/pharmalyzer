# app\views\plotting\regression\interaction.py
from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5 import QtGui

from app.i18n import t
from app.views.plotting.regression.adapters import HoverPoints
from app.services.data_management.interaction_store import InteractionStore


class RegressionInteraction:
    def __init__(self):
        self._hover_proxy = None
        self._click_proxy = None
        self._store: InteractionStore | None = None
        self._hover_points: HoverPoints = HoverPoints.empty()

    def attach(
        self,
        plot_item: pg.PlotItem,
        hover_text_item: pg.TextItem,
        hover_points: HoverPoints,
        interaction_store: InteractionStore | None,
    ) -> None:
        self.detach()
        self._store = interaction_store
        self._hover_points = hover_points

        if hover_points.is_empty:
            hover_text_item.hide()
            return

        self._attach_hover(plot_item, hover_text_item)
        self._attach_click(plot_item, hover_text_item)

    def detach(self) -> None:
        for proxy in (self._hover_proxy, self._click_proxy):
            if proxy is None:
                continue
            try:
                if hasattr(proxy, "disconnect"):
                    proxy.disconnect()
                elif isinstance(proxy, tuple) and len(proxy) == 2:
                    signal, slot = proxy
                    signal.disconnect(slot)
            except Exception:
                pass
        self._hover_proxy = None
        self._click_proxy = None
        self._store = None
        self._hover_points = HoverPoints.empty()

    # ---- hover / click ----
    def _attach_hover(self, plot_item: pg.PlotItem, hover_text_item: pg.TextItem) -> None:
        view_box = plot_item.vb

        def on_mouse_moved(evt):
            pos = evt[0]
            if not view_box.sceneBoundingRect().contains(pos):
                hover_text_item.hide()
                if self._store is not None:
                    self._store.set_hover(None)
                return

            mouse_point = view_box.mapSceneToView(pos)
            mx, my = float(mouse_point.x()), float(mouse_point.y())
            well_idx = self._nearest_well_index(mx, my, plot_item)
            if well_idx is None:
                hover_text_item.hide()
                if self._store is not None:
                    self._store.set_hover(None)
                return

            well = self._hover_points.wells[well_idx] if well_idx < self._hover_points.wells.size else ""
            text_color = "#FFFFFF"  # Beyaz yazı
            bg_color = "rgba(40, 44, 52, 200)"  # Yarı saydam koyu arka plan
            border_color = "#FFD700"  # Altın sarısı çerçeve (Ampul rengi)

            well_text = t("regression.plot.hover.well_no", well=well)
            html_text = (
                f'<div style="background-color: {bg_color}; '
                f'border: 1px solid {border_color}; '
                f'border-radius: 4px; '
                f'padding: 3px 6px;">'
                f'<span style="color: {text_color}; font-weight: bold; font-family: Arial;">'
                f'{well_text}'
                f'</span></div>'
            )
            hover_text_item.setHtml(html_text)
            hover_text_item.setPos(float(self._hover_points.x[well_idx]), float(self._hover_points.y[well_idx]))
            hover_text_item.show()

            if self._store is not None:
                self._store.set_hover(well)

        self._hover_proxy = pg.SignalProxy(
            plot_item.scene().sigMouseMoved,
            rateLimit=60,
            slot=on_mouse_moved,
        )

    def _attach_click(self, plot_item: pg.PlotItem, hover_text_item: pg.TextItem) -> None:
        view_box = plot_item.vb

        def on_mouse_clicked(mouse_evt: QtGui.QGraphicsSceneMouseEvent):
            if mouse_evt.button() != Qt.LeftButton:
                return
            pos = mouse_evt.scenePos()
            if not view_box.sceneBoundingRect().contains(pos):
                return

            mouse_point = view_box.mapSceneToView(pos)
            mx, my = float(mouse_point.x()), float(mouse_point.y())
            well_idx = self._nearest_well_index(mx, my, plot_item)

            if well_idx is not None:
                well = self._hover_points.wells[well_idx] if well_idx < self._hover_points.wells.size else ""
                if self._store is not None:
                    if mouse_evt.modifiers() & Qt.ControlModifier:
                        self._store.toggle_wells({well})
                    else:
                        self._store.set_selection({well})
                    self._store.set_hover(well)
                text_color = "#FFFFFF"  # Beyaz yazı
                bg_color = "rgba(40, 44, 52, 200)"  # Yarı saydam koyu arka plan
                border_color = "#FFD700"  # Altın sarısı çerçeve (Ampul rengi)

                well_text = t("regression.plot.hover.well_no", well=well)
                html_text = (
                    f'<div style="background-color: {bg_color}; '
                    f'border: 1px solid {border_color}; '
                    f'border-radius: 4px; '
                    f'padding: 3px 6px;">'
                    f'<span style="color: {text_color}; font-weight: bold; font-family: Arial;">'
                    f'{well_text}'
                    f'</span></div>'
                )
                hover_text_item.setHtml(html_text)
                hover_text_item.setPos(float(self._hover_points.x[well_idx]), float(self._hover_points.y[well_idx]))
                hover_text_item.show()
                mouse_evt.accept()
                return

            if self._store is not None:
                self._store.clear_selection()
                self._store.set_hover(None)
            hover_text_item.hide()

        plot_item.scene().sigMouseClicked.connect(on_mouse_clicked)
        self._click_proxy = (plot_item.scene().sigMouseClicked, on_mouse_clicked)

    def _nearest_well_index(self, mx: float, my: float, plot_item: pg.PlotItem) -> int | None:
        dx = self._hover_points.x - mx
        dy = self._hover_points.y - my
        d2 = dx * dx + dy * dy

        if d2.size == 0:
            return None

        i = int(np.argmin(d2))

        xr = plot_item.viewRange()[0]
        yr = plot_item.viewRange()[1]
        thresh = ((xr[1] - xr[0]) * 0.01) ** 2 + ((yr[1] - yr[0]) * 0.01) ** 2
        if float(d2[i]) > float(thresh):
            return None
        return i