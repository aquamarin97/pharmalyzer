# app\views\plotting\pyqtgraph_regression_renderer.py
from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from app.services.regression_plot_service import RegressionPlotData


class PyqtgraphRegressionRenderer:
    def __init__(self):
        self._scatter_items = []  # [(ScatterPlotItem, wells_array)]
        self._proxy = None

    def render(
        self,
        plot_item: pg.PlotItem,
        data: RegressionPlotData,
        enable_hover: bool = True,
        hover_text_item: pg.TextItem | None = None,
    ):
        plot_item.clear()
        plot_item.addLegend(offset=(10, 10))
        plot_item.showGrid(x=True, y=True, alpha=0.25)

        self._scatter_items.clear()

        # boş data
        if data.reg_line.x_sorted.size == 0:
            if hover_text_item is not None:
                hover_text_item.hide()
            self.detach_hover()
            return

        # safe band fill (legacy ile aynı)
        upper_curve = pg.PlotDataItem(
            data.safe_band.x_sorted,
            data.safe_band.upper,
            pen=pg.mkPen((255, 255, 255, 0)),
        )
        lower_curve = pg.PlotDataItem(
            data.safe_band.x_sorted,
            data.safe_band.lower,
            pen=pg.mkPen((255, 255, 255, 0)),
        )
        plot_item.addItem(upper_curve)
        plot_item.addItem(lower_curve)

        fill = pg.FillBetweenItem(
            upper_curve,
            lower_curve,
            brush=pg.mkBrush(255, 255, 255, 40),
        )
        fill.setZValue(0)
        plot_item.addItem(fill)

        # regression line
        reg_line = pg.PlotDataItem(
            data.reg_line.x_sorted,
            data.reg_line.y_pred_sorted,
            pen=pg.mkPen((255, 60, 60), width=2),
            name="Regresyon Doğrusu",
        )
        reg_line.setZValue(2)
        plot_item.addItem(reg_line)

        # scatter styles (legacy renkleri)
        styles = {
            "Sağlıklı": dict(brush=(0, 191, 255), pen=(255, 255, 255)),
            "Taşıyıcı": dict(brush=(255, 165, 0), pen=(255, 215, 0)),
            "Belirsiz": dict(brush=(255, 0, 255), pen=(211, 211, 211)),
        }

        for s in data.series:
            st = styles.get(s.label, dict(brush=(200, 200, 200), pen=(255, 255, 255)))
            sc = pg.ScatterPlotItem(
                x=s.x,
                y=s.y,
                size=8,
                brush=pg.mkBrush(*st["brush"]),
                pen=pg.mkPen(*st["pen"], width=1),
                name=s.label,
            )
            sc.setZValue(3)
            plot_item.addItem(sc)
            self._scatter_items.append((sc, s.wells))

        # hover
        self.detach_hover()
        if enable_hover and hover_text_item is not None:
            self._attach_hover(plot_item, hover_text_item)

    def _attach_hover(self, plot_item: pg.PlotItem, hover_text_item: pg.TextItem):
        vb = plot_item.vb

        def on_mouse_moved(evt):
            pos = evt[0]
            if not vb.sceneBoundingRect().contains(pos):
                hover_text_item.hide()
                return

            mouse_point = vb.mapSceneToView(pos)
            mx, my = mouse_point.x(), mouse_point.y()

            best = None  # (dist2, x, y, well)
            for sc, wells_arr in self._scatter_items:
                pts = list(sc.points())  # ✅ truthiness bug fix
                if len(pts) == 0:
                    continue

                for i, p in enumerate(pts):
                    pt = p.pos()
                    px, py = pt.x(), pt.y()
                    d2 = (px - mx) ** 2 + (py - my) ** 2
                    if best is None or d2 < best[0]:
                        well = wells_arr[i] if i < len(wells_arr) else ""
                        best = (d2, px, py, well)
                        if best is None:
                            hover_text_item.hide()
                            return

            xr = plot_item.viewRange()[0]
            yr = plot_item.viewRange()[1]
            thresh = ((xr[1] - xr[0]) * 0.01) ** 2 + ((yr[1] - yr[0]) * 0.01) ** 2
            if best[0] > thresh:
                hover_text_item.hide()
                return

            _, px, py, well = best
            hover_text_item.setText(f"Kuyu No: {well}")
            hover_text_item.setPos(px, py)
            hover_text_item.show()

        # ✅ PROXY BİR KERE KURULUR (BUG FIX)
        self._proxy = pg.SignalProxy(plot_item.scene().sigMouseMoved, rateLimit=60, slot=on_mouse_moved)

    def detach_hover(self):
        if self._proxy is not None:
            try:
                self._proxy.disconnect()
            except Exception:
                pass
            self._proxy = None
