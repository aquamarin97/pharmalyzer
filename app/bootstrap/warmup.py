from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from app.i18n import t_list

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WarmupConfig:
    numpy_size: int = 200
    kmeans_clusters: int = 5
    random_state: int = 42


ProgressCb = Callable[[str, int], None]


def _safe_messages() -> list[str]:
    msgs = t_list("loading.messages")
    return msgs if msgs else ["Yükleniyor..."]


def _compose_ui_text(step_index: int, p: int) -> str:
    msgs = _safe_messages()
    base = msgs[min(step_index, len(msgs) - 1)]
    return f"{base}  {p}%"


def run_warmup(progress: Optional[ProgressCb], cfg: WarmupConfig = WarmupConfig()) -> None:
    """
    Heavy imports + first-call overhead warm-up.
    UI: only loading.messages + percent (non-technical).
    Logs: keep technical detail for debugging.
    """

    def show(step_index: int, p: int, *, log_detail: str) -> None:
        if progress is not None:
            try:
                progress(_compose_ui_text(step_index, p), p)
            except Exception:
                pass
        logger.info("[Warmup] %s (%s%%)", log_detail, p)

    # ---- Smooth progress plan ----
    show(0, 5,  log_detail="warmup start")
    show(0, 10, log_detail="numpy import / first touch")
    import numpy as np
    a = np.random.rand(cfg.numpy_size, cfg.numpy_size)
    _ = a @ a

    show(1, 15, log_detail="qt-related init boundary (still main thread)")

    show(2, 25, log_detail="sklearn import")
    from sklearn.linear_model import LinearRegression
    from sklearn.cluster import KMeans

    show(2, 35, log_detail="sklearn first fit (LR + KMeans)")
    X = np.array([[0.0], [1.0]])
    y = np.array([0.0, 1.0])
    LinearRegression().fit(X, y)

    X2 = np.random.rand(cfg.numpy_size, 1)
    KMeans(n_clusters=cfg.kmeans_clusters, random_state=cfg.random_state).fit(X2)

    show(3, 45, log_detail="scipy import")
    from scipy.optimize import minimize

    show(3, 55, log_detail="scipy.optimize.minimize first call")
    def obj(x):
        return float((x[0] - 0.1234) ** 2)

    minimize(
        obj,
        x0=np.array([0.0]),
        bounds=[(-4, 4)],
        method="L-BFGS-B",
        options={"maxiter": 20},
    )

    show(4, 70, log_detail="matplotlib import")
    import matplotlib.pyplot as plt

    show(4, 80, log_detail="matplotlib first figure")
    fig = plt.figure()
    plt.close(fig)

    show(5, 90, log_detail="pyqtgraph import/config")
    import pyqtgraph as pg
    pg.setConfigOptions(antialias=True)

    show(6, 95, log_detail="finalizing warmup")
    show(7, 100, log_detail="warmup done")
