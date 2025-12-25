from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from dataclasses import dataclass

from app.i18n import t
from app.services.regression_plot_service import RegressionPlotData
from app.constants.regression_plot_style import RegressionPlotStyle

@dataclass
class _ScatterHandle:
    item: pg.ScatterPlotItem
    x: np.ndarray
    y: np.ndarray
    wells: np.ndarray
    base_brush: tuple
    base_pen: tuple


class PyqtgraphRegressionRenderer:
    def __init__(self, style: RegressionPlotStyle):
        self._style = style

        self._hover_proxy = None
        self._click_proxy = None
        self._store: InteractionStore | None = None

        self._hover_x: np.ndarray = np.array([], dtype=float)
        self._hover_y: np.ndarray = np.array([], dtype=float)
        self._hover_wells: np.ndarray = np.array([], dtype=str)

        self._scatter_handles: list[_ScatterHandle] = []


    def render(
        self,
        plot_item: pg.PlotItem,
        data: RegressionPlotData,
        enable_hover: bool = True,
        hover_text_item: pg.TextItem | None = None,
        interaction_store: InteractionStore | None = None,
    ) -> None:
        plot_item.clear()

        self._scatter_handles.clear()
        self._store = interaction_store

        # Hover state sıfırla
        self._hover_x = np.array([], dtype=float)
        self._hover_y = np.array([], dtype=float)
        self._hover_wells = np.array([], dtype=str)

        if data.reg_line.x_sorted.size == 0:
            if hover_text_item is not None:
                hover_text_item.hide()
            self.detach_hover()
            return

        # safe band fill
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
            brush=pg.mkBrush(*self._style.safe_band_brush_rgba),
        )
        fill.setZValue(0)
        plot_item.addItem(fill)

        # regression line
        reg_line = pg.PlotDataItem(
            data.reg_line.x_sorted,
            data.reg_line.y_pred_sorted,
            pen=pg.mkPen(self._style.reg_line_pen, width=self._style.reg_line_width),
            name=t("regression.plot.regression_line"),
        )
        reg_line.setZValue(2)
        plot_item.addItem(reg_line)

        # Hover için concat havuzu
        hx: list[np.ndarray] = []
        hy: list[np.ndarray] = []
        hw: list[np.ndarray] = []

        for s in data.series:
            st = self._style.series.get(s.label)

            if st is None:
                brush = (200, 200, 200)
                pen = (255, 255, 255)
            else:
                brush = st.brush
                pen = st.pen

            display_name = {
                "Sağlıklı": t("regression.plot.legend.healthy"),
                "Taşıyıcı": t("regression.plot.legend.carrier"),
                "Belirsiz": t("regression.plot.legend.uncertain"),
            }.get(s.label, s.label)

            sc = pg.ScatterPlotItem(
                x=s.x,
                y=s.y,
                size=self._style.scatter_size,
                brush=pg.mkBrush(*brush),
                pen=pg.mkPen(*pen, width=self._style.scatter_pen_width),
                name=display_name,
            )
            sc.setZValue(3)
            plot_item.addItem(sc)

            hx.append(np.asarray(s.x, dtype=float))
            hy.append(np.asarray(s.y, dtype=float))
            hw.append(np.asarray(s.wells, dtype=str))

            handle = _ScatterHandle(
                item=sc,
                x=np.asarray(s.x, dtype=float),
                y=np.asarray(s.y, dtype=float),
                wells=np.asarray(s.wells, dtype=str),
                base_brush=brush,
                base_pen=pen,
            )
            self._scatter_handles.append(handle)

        if hx:
            self._hover_x = np.concatenate(hx)
            self._hover_y = np.concatenate(hy)
            self._hover_wells = np.concatenate(hw)

        # hover + click
        self.detach_hover()
        if enable_hover and hover_text_item is not None and self._hover_x.size > 0:
            self._attach_hover(plot_item, hover_text_item)
            self._attach_click(plot_item, hover_text_item)

        elif hover_text_item is not None:
            hover_text_item.hide()
    def update_styles(self, selected_wells: set[str] | None, hover_well: str | None) -> None:
        selected_wells = selected_wells or set()
        for handle in self._scatter_handles:
            brushes = []
            pens = []
            sizes = []
            for idx, well in enumerate(handle.wells):
                is_selected = well in selected_wells
                is_hovered = hover_well == well

                size = self._style.scatter_size
                if is_hovered:
                    size += 3
                elif is_selected:
                    size += 1.5

                if is_hovered:
                    pen = pg.mkPen(255, 59, 48, width=max(2, self._style.scatter_pen_width + 1))
                elif is_selected:
                    pen = pg.mkPen(58, 122, 254, width=max(2, self._style.scatter_pen_width + 1))
                else:
                    pen = pg.mkPen(*handle.base_pen, width=self._style.scatter_pen_width)

                brush = pg.mkBrush(*handle.base_brush)

                brushes.append(brush)
                pens.append(pen)
                sizes.append(size)

            handle.item.setData(
                x=handle.x,
                y=handle.y,
                brush=brushes,
                pen=pens,
                size=sizes,
            )

    # ---- hover / click ----
    def _attach_hover(self, plot_item: pg.PlotItem, hover_text_item: pg.TextItem) -> None:
        vb = plot_item.vb

        def on_mouse_moved(evt):
            pos = evt[0]
            if not vb.sceneBoundingRect().contains(pos):
                hover_text_item.hide()
                if self._store is not None:
                    self._store.set_hover(None)
                return

            mouse_point = vb.mapSceneToView(pos)
            mx, my = float(mouse_point.x()), float(mouse_point.y())
            well_idx = self._nearest_well_index(mx, my, plot_item)
            if well_idx is None:
                hover_text_item.hide()
                if self._store is not None:
                    self._store.set_hover(None)
                return
            
            well = self._hover_wells[well_idx] if well_idx < self._hover_wells.size else ""
            hover_text_item.setText(t("regression.plot.hover.well_no", well=well))
            hover_text_item.setPos(float(self._hover_x[well_idx]), float(self._hover_y[well_idx]))
            hover_text_item.show()

            if self._store is not None:
                self._store.set_hover(well)

        self._hover_proxy = pg.SignalProxy(
            plot_item.scene().sigMouseMoved,
            rateLimit=60,
            slot=on_mouse_moved,
        )
    def _attach_click(self, plot_item: pg.PlotItem, hover_text_item: pg.TextItem) -> None:
        vb = plot_item.vb

        def on_mouse_clicked(evt):
            if evt.button() != Qt.LeftButton:
                return
            pos = evt.scenePos()
            if not vb.sceneBoundingRect().contains(pos):
                return

            mouse_point = vb.mapSceneToView(pos)
            mx, my = float(mouse_point.x()), float(mouse_point.y())
            well_idx = self._nearest_well_index(mx, my, plot_item)

            if well_idx is not None:
                well = self._hover_wells[well_idx] if well_idx < self._hover_wells.size else ""
                if self._store is not None:
                    if evt.modifiers() & Qt.ControlModifier:
                        self._store.toggle_wells({well})
                    else:
                        self._store.set_selection({well})
                    self._store.set_hover(well)
                hover_text_item.setText(t("regression.plot.hover.well_no", well=well))
                hover_text_item.setPos(float(self._hover_x[well_idx]), float(self._hover_y[well_idx]))
                hover_text_item.show()
                evt.accept()
                return

            # boş alana tıklandı -> temizle
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
        dx = self._hover_x - mx
        dy = self._hover_y - my
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

    def detach_hover(self) -> None:
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
