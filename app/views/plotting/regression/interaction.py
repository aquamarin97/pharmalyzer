from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt

from app.i18n import t
from app.services.interaction_store import InteractionStore
from app.views.plotting.regression.adapters import HoverPoints


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
            hover_text_item.setText(t("regression.plot.hover.well_no", well=well))
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

        def on_mouse_clicked(evt):
            if evt.button() != Qt.LeftButton:
                return
            pos = evt.scenePos()
            if not view_box.sceneBoundingRect().contains(pos):
                return

            mouse_point = view_box.mapSceneToView(pos)
            mx, my = float(mouse_point.x()), float(mouse_point.y())
            well_idx = self._nearest_well_index(mx, my, plot_item)

            if well_idx is not None:
                well = self._hover_points.wells[well_idx] if well_idx < self._hover_points.wells.size else ""
                if self._store is not None:
                    if evt.modifiers() & Qt.ControlModifier:
                        self._store.toggle_wells({well})
                    else:
                        self._store.set_selection({well})
                    self._store.set_hover(well)
                hover_text_item.setText(t("regression.plot.hover.well_no", well=well))
                hover_text_item.setPos(float(self._hover_points.x[well_idx]), float(self._hover_points.y[well_idx]))
                hover_text_item.show()
                evt.accept()
                return

            if self._store is not None:
                self._store.clear_selection()
                self._store.set_hover(None)
            hover_text_item.hide()

        self._click_proxy = pg.SignalProxy(
            plot_item.scene().sigMouseClicked,
            rateLimit=60,
            slot=on_mouse_clicked,
        )

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