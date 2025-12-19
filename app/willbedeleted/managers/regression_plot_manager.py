# app\willbedeleted\managers\regression_plot_manager.py
import numpy as np
import pyqtgraph as pg

from app.willbedeleted.models.regration_model import RegressionModel
from app.willbedeleted.utils.validators.data_Validor import DataValidator


class RegressionPlotManager:
    def __init__(self, df):
        self.df = df
        self.required_columns = [
            "hex_end_rfu",
            "fam_end_rfu",
            "Kuyu No",
            "Nihai Sonuç",
        ]

        # Hover için saklayacağız:
        self._scatter_items = []   # [(scatterItem, wells_array), ...]
        self._proxy = None         # SignalProxy reference

    def render_on_plotitem(self, plot_item: pg.PlotItem, enable_hover=False, hover_text_item=None):
        """
        Var olan PlotItem üstüne çizer (clear + yeniden çizim).
        """
        DataValidator.validate_columns(self.df, self.required_columns)

        df_copy = self.df.copy()
        df_copy.dropna(subset=self.required_columns, inplace=True)

        # Senin mantığın: sadece bu sınıflar regression + scatter'da
        mask = df_copy["Nihai Sonuç"].isin(["Sağlıklı", "Taşıyıcı", "Belirsiz"])

        model = RegressionModel("hex_end_rfu", "fam_end_rfu")
        model.fit(df_copy, mask)

        # veriler
        fam_rfu = df_copy.loc[mask, "fam_end_rfu"].astype(float).to_numpy()
        hex_rfu = df_copy.loc[mask, "hex_end_rfu"].astype(float).to_numpy()
        wells = df_copy.loc[mask, "Kuyu No"].astype(str).to_numpy()
        sonuc = df_copy.loc[mask, "Nihai Sonuç"].astype(str).to_numpy()

        # prediction + safe zone
        x_vals = fam_rfu.reshape(-1, 1)
        hex_rfu_pred = model.predict(x_vals)

        residuals_filtered = model.calculate_residuals(df_copy, mask)
        sigma = float(np.std(residuals_filtered)) if len(residuals_filtered) else 0.0

        safe_upper = hex_rfu_pred + 2.2 * sigma
        safe_lower = hex_rfu_pred - 2.2 * sigma

        # Plot temizle
        plot_item.clear()
        plot_item.addLegend(offset=(10, 10))
        plot_item.showGrid(x=True, y=True, alpha=0.25)

        # Güvenli alanı çizmek için x'e göre sırala
        sort_idx = np.argsort(fam_rfu)
        xf = fam_rfu[sort_idx]
        yu = safe_upper[sort_idx]
        yl = safe_lower[sort_idx]

        # Üst/alt sınır curve
        upper_curve = pg.PlotDataItem(xf, yu, pen=pg.mkPen((255, 255, 255, 0)))  # çizgi görünmesin
        lower_curve = pg.PlotDataItem(xf, yl, pen=pg.mkPen((255, 255, 255, 0)))
        plot_item.addItem(upper_curve)
        plot_item.addItem(lower_curve)

        fill = pg.FillBetweenItem(upper_curve, lower_curve, brush=pg.mkBrush(255, 255, 255, 40))
        fill.setZValue(0)
        plot_item.addItem(fill)

        # Regresyon çizgisi
        reg_line = pg.PlotDataItem(
            xf,
            hex_rfu_pred[sort_idx],
            pen=pg.mkPen((255, 60, 60), width=2),
            name="Regresyon Doğrusu",
        )
        reg_line.setZValue(2)
        plot_item.addItem(reg_line)

        # Kategorilere göre scatter
        self._scatter_items.clear()

        # Plotly’deki renk mantığın
        styles = {
            "Sağlıklı": dict(brush=(0, 191, 255), pen=(255, 255, 255)),   # deepskyblue + white border
            "Taşıyıcı": dict(brush=(255, 165, 0),  pen=(255, 215, 0)),     # orange + gold border
            "Belirsiz": dict(brush=(255, 0, 255),  pen=(211, 211, 211)),   # magenta + lightgray border
        }

        for label in ["Sağlıklı", "Taşıyıcı", "Belirsiz"]:
            idx = (sonuc == label)
            if not np.any(idx):
                continue

            sc = pg.ScatterPlotItem(
                x=fam_rfu[idx],
                y=hex_rfu[idx],
                size=8,
                brush=pg.mkBrush(*styles[label]["brush"]),
                pen=pg.mkPen(*styles[label]["pen"], width=1),
                name=label,
            )
            sc.setZValue(3)
            plot_item.addItem(sc)

            self._scatter_items.append((sc, wells[idx]))

        # Hover (mouse move) ile en yakın noktayı bulup kuyu no göster
        if enable_hover and hover_text_item is not None:
            vb = plot_item.vb

            # Eski proxy varsa çakışmasın
            if self._proxy is not None:
                try:
                    self._proxy.disconnect()
                except Exception:
                    pass
                self._proxy = None
        def on_mouse_moved(evt):
            pos = evt[0]
            if not vb.sceneBoundingRect().contains(pos):
                hover_text_item.hide()
                return

            mouse_point = vb.mapSceneToView(pos)
            mx, my = mouse_point.x(), mouse_point.y()

            best = None  # (dist2, x, y, well)

            for sc, wells_arr in self._scatter_items:
                pts = sc.points()   # en güvenlisi bu
                if not pts:
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

            # yakınlık eşiği (view-range’e göre)
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


            self._proxy = pg.SignalProxy(plot_item.scene().sigMouseMoved, rateLimit=60, slot=on_mouse_moved)

    def detach_hover(self):
        if getattr(self, "_proxy", None) is not None:
            try:
                self._proxy.disconnect()
            except Exception:
                pass
            self._proxy = None