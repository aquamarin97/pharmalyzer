# main.py
from __future__ import annotations

import os
import sys
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from app.bootstrap.splash import show_splash
from app.bootstrap.resources import resource_path
from app.licensing.ui import ensure_license_or_exit
from app.constants.asset_paths import IMAGE_PATHS

from app.controllers.main_controller import MainController
from app.models.main_model import MainModel
from app.views.main_view import MainView

from app.logging.setup import setup_logging
from app.exceptions.base import install_global_exception_hook
from app.exceptions.handler import handle_exception

logger = logging.getLogger(__name__)


def _warmup_during_splash(splash) -> None:
    """
    Heavy imports + first-call overhead warm-up.
    Runs on MAIN thread while splash is visible.
    """
    def show(msg: str, p: int) -> None:
        try:
            splash.showMessage(
                f"{msg} %{p}",
                alignment=Qt.AlignBottom | Qt.AlignHCenter,
            )
            QApplication.processEvents()  # splash redraw
        except Exception:
            # splash yoksa bile warmup sürsün
            pass

        logger.info("[Warmup] %s", msg)

    # 1) numpy + BLAS first touch
    show("NumPy hazırlanıyor...", 10)
    import numpy as _np
    a = _np.random.rand(200, 200)
    _ = a @ a

    # 2) sklearn + KMeans first fit
    show("scikit-learn hazırlanıyor...", 35)
    from sklearn.linear_model import LinearRegression as _LR
    from sklearn.cluster import KMeans as _KMeans

    X = _np.array([[0.0], [1.0]])
    y = _np.array([0.0, 1.0])
    _LR().fit(X, y)

    X2 = _np.random.rand(200, 1)
    _KMeans(n_clusters=5, random_state=42).fit(X2)

    # 3) scipy minimize first call (L-BFGS-B)
    show("SciPy hazırlanıyor...", 55)
    from scipy.optimize import minimize as _minimize

    def _obj(x):
        # x is ndarray
        return float((x[0] - 0.1234) ** 2)

    _minimize(
        _obj,
        x0=_np.array([0.0]),
        bounds=[(-4, 4)],
        method="L-BFGS-B",
        options={"maxiter": 20},
    )

    # 4) matplotlib minimal init
    show("Matplotlib hazırlanıyor...", 75)
    import matplotlib.pyplot as _plt
    fig = _plt.figure()
    _plt.close(fig)

    # 5) pyqtgraph (Qt ile ilişkili -> main thread)
    show("PyQtGraph hazırlanıyor...", 90)
    import pyqtgraph as _pg
    _pg.setConfigOptions(antialias=True)

    show("Hazır!", 100)


def main() -> int:
    setup_logging("pharmalizer")
    install_global_exception_hook()

    app = QApplication(sys.argv)

    if os.getenv("ENVIRONMENT") == "production":
        ensure_license_or_exit(app)

    app.setWindowIcon(QIcon(resource_path(IMAGE_PATHS.APP_LOGO_PNG)))

    # ---- Splash ----
    splash = show_splash()

    # Model uzun ömürlü
    model = MainModel()
    app.aboutToQuit.connect(model.shutdown)

    # ---- Warmup: splash açıkken, UI açılmadan önce ----
    try:
        _warmup_during_splash(splash)
    except Exception as exc:
        # Warmup patlasa bile uygulama açılmalı
        logger.exception("Warmup failed: %s", exc)

    # ---- UI bootstrap ----
    view = MainView()
    controller = MainController(view, model)

    # GC guard (bazı ortamlarda faydalı)
    view.controller = controller

    splash.finish(view)
    view.show()

    return app.exec_()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.exit(handle_exception(exc))
