# app/views/plotting/pyqtgraph_regression_renderer.py
from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from app.i18n import t
from app.services.regression_plot_service import RegressionPlotData


class PyqtgraphRegressionRenderer:
    def __init__(self):
        self._proxy = None

        # Hover için tek havuz (daha hızlı / points() yok)
        self._hover_x: np.ndarray = np.array([], dtype=float)
        self._hover_y: np.ndarray = np.array([], dtype=float)
        self._hover_wells: np.ndarray = np.array([], dtype=str)

    def render(
        self,
        plot_item: pg.PlotItem,
        data: RegressionPlotData,
        enable_hover: bool = True,
        hover_text_item: pg.TextItem | None = None,
    ) -> None:
        plot_item.clear()
        plot_item.addLegend(offset=(10, 10))
        plot_item.showGrid(x=True, y=True, alpha=0.25)

        # Hover state sıfırla
        self._hover_x = np.array([], dtype=float)
        self._hover_y = np.array([], dtype=float)
        self._hover_wells = np.array([], dtype=str)

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
            name=t("regression.plot.regression_line"),
        )
        reg_line.setZValue(2)
        plot_item.addItem(reg_line)

        # scatter styles (legacy renkleri)
        styles = {
            "Sağlıklı": dict(brush=(0, 191, 255), pen=(255, 255, 255)),
            "Taşıyıcı": dict(brush=(255, 165, 0), pen=(255, 215, 0)),
            "Belirsiz": dict(brush=(255, 0, 255), pen=(211, 211, 211)),
        }

        # Hover için concat havuzu
        hx: list[np.ndarray] = []
        hy: list[np.ndarray] = []
        hw: list[np.ndarray] = []

        for s in data.series:
            st = styles.get(s.label, dict(brush=(200, 200, 200), pen=(255, 255, 255)))

            # Legend/display label i18n (df değeri sabit kalsın)
            display_name = {
                "Sağlıklı": t("regression.plot.legend.healthy"),
                "Taşıyıcı": t("regression.plot.legend.carrier"),
                "Belirsiz": t("regression.plot.legend.uncertain"),
            }.get(s.label, s.label)

            sc = pg.ScatterPlotItem(
                x=s.x,
                y=s.y,
                size=8,
                brush=pg.mkBrush(*st["brush"]),
                pen=pg.mkPen(*st["pen"], width=1),
                name=display_name,
            )
            sc.setZValue(3)
            plot_item.addItem(sc)

            hx.append(np.asarray(s.x, dtype=float))
            hy.append(np.asarray(s.y, dtype=float))
            hw.append(np.asarray(s.wells, dtype=str))

        if hx:
            self._hover_x = np.concatenate(hx)
            self._hover_y = np.concatenate(hy)
            self._hover_wells = np.concatenate(hw)

        # hover
        self.detach_hover()
        if enable_hover and hover_text_item is not None and self._hover_x.size > 0:
            self._attach_hover(plot_item, hover_text_item)
        elif hover_text_item is not None:
            hover_text_item.hide()

    def _attach_hover(self, plot_item: pg.PlotItem, hover_text_item: pg.TextItem) -> None:
        vb = plot_item.vb

        def on_mouse_moved(evt):
            pos = evt[0]
            if not vb.sceneBoundingRect().contains(pos):
                hover_text_item.hide()
                return

            mouse_point = vb.mapSceneToView(pos)
            mx, my = float(mouse_point.x()), float(mouse_point.y())

            # en yakın nokta (vektörize)
            dx = self._hover_x - mx
            dy = self._hover_y - my
            d2 = dx * dx + dy * dy

            if d2.size == 0:
                hover_text_item.hide()
                return

            i = int(np.argmin(d2))

            # adaptif threshold (view range'e göre)
            xr = plot_item.viewRange()[0]
            yr = plot_item.viewRange()[1]
            thresh = ((xr[1] - xr[0]) * 0.01) ** 2 + ((yr[1] - yr[0]) * 0.01) ** 2
            if float(d2[i]) > float(thresh):
                hover_text_item.hide()
                return

            well = self._hover_wells[i] if i < self._hover_wells.size else ""
            hover_text_item.setText(t("regression.plot.hover.well_no", well=well))
            hover_text_item.setPos(float(self._hover_x[i]), float(self._hover_y[i]))
            hover_text_item.show()

        # Proxy her render'da yenilenebilir ama detach_hover bunu temizler
        self._proxy = pg.SignalProxy(
            plot_item.scene().sigMouseMoved,
            rateLimit=60,
            slot=on_mouse_moved,
        )

    def detach_hover(self) -> None:
        if self._proxy is None:
            return
        try:
            # pyqtgraph SignalProxy bazı sürümlerde disconnect destekler
            if hasattr(self._proxy, "disconnect"):
                self._proxy.disconnect()
        except Exception:
            pass
        self._proxy = None
