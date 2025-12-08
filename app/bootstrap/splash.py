# app/bootstrap/splash.py

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QSplashScreen, QApplication

from app.bootstrap.resources import resource_path
from app.constants.app_styles import FONT_STYLES, COLOR_STYLES
from app.constants.app_text_key import TextKey
from app.constants.asset_paths import IMAGE_PATHS
from app.i18n import t, t_list


def show_splash() -> QSplashScreen:
    # Ana canvas oluştur
    canvas = QPixmap(800, 300)
    canvas.fill(COLOR_STYLES.SPLASH_BG)

    app_name = t(TextKey.APP_NAME)
    brand_name = t(TextKey.BRAND_NAME)
    logo_path = IMAGE_PATHS.APP_LOGO_PNG

    loading_messages = t_list(TextKey.LOADING_MESSAGES)
    if not loading_messages:
        # Fallback (liste boşsa modulo hatası olmaması için)
        loading_messages = [t("loading.progress")]

    step_delay_ms: int = 400
    total_duration_ms: int | None = None

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)

    logo = QPixmap(resource_path(logo_path)).scaled(
        250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )

    # Logo
    x_logo = 60
    y_logo = (canvas.height() - logo.height()) // 2
    painter.drawPixmap(x_logo, y_logo, logo)

    # Metinler
    x_text = x_logo + logo.width() + 50
    y_text_base = y_logo + 120

    painter.setFont(FONT_STYLES.SPLASH_APP_NAME)
    painter.setPen(COLOR_STYLES.PRIMARY_TEXT)
    painter.drawText(x_text, y_text_base, app_name)

    painter.setFont(FONT_STYLES.SPLASH_BRAND_NAME)
    painter.setPen(COLOR_STYLES.BRAND_COLOR)
    painter.drawText(x_text, y_text_base + 60, brand_name)

    painter.end()

    # Splash ekranı
    splash = QSplashScreen(canvas, Qt.WindowStaysOnTopHint)
    splash.setFont(FONT_STYLES.SPLASH_MESSAGE)
    splash.show()
    QApplication.processEvents()

    steps = len(loading_messages)
    total_steps = steps  # istersen ayrı bir toplam adım mantığı kurarsın

    # Toplam süre hesapla (opsiyonel)
    if total_duration_ms is not None and total_steps > 0:
        step_delay_ms = max(1, total_duration_ms // total_steps)

    current_step = 0

    def update_progress():
        nonlocal current_step

        if current_step >= total_steps:
            # Not: close() yerine hide() tercih edilebilir, ama finish(view) zaten var.
            splash.close()
            return

        percent = int((current_step + 1) / total_steps * 100)
        message = loading_messages[current_step % len(loading_messages)]

        splash.showMessage(
            f"{message} %{percent}",
            alignment=Qt.AlignBottom | Qt.AlignHCenter,
            color=COLOR_STYLES.PRIMARY_TEXT,
        )
        QApplication.processEvents()

        current_step += 1
        QTimer.singleShot(step_delay_ms, update_progress)

    update_progress()
    return splash
