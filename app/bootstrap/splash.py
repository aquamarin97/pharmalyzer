from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QSplashScreen, QApplication

from app.bootstrap.resources import resource_path
from app.constants.app_styles import FONT_STYLES, COLOR_STYLES
from app.constants.app_text_key import TextKey
from app.constants.asset_paths import IMAGE_PATHS
from app.i18n import t, t_list


def show_splash() -> QSplashScreen:
    canvas = QPixmap(800, 300)
    canvas.fill(COLOR_STYLES.SPLASH_BG)

    app_name = t(TextKey.APP_NAME)
    brand_name = t(TextKey.BRAND_NAME)

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)

    logo = QPixmap(resource_path(IMAGE_PATHS.APP_LOGO_PNG)).scaled(
        250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )

    x_logo = 60
    y_logo = (canvas.height() - logo.height()) // 2
    painter.drawPixmap(x_logo, y_logo, logo)

    x_text = x_logo + logo.width() + 50
    y_text_base = y_logo + 120

    painter.setFont(FONT_STYLES.SPLASH_APP_NAME)
    painter.setPen(COLOR_STYLES.PRIMARY_TEXT)
    painter.drawText(x_text, y_text_base, app_name)

    painter.setFont(FONT_STYLES.SPLASH_BRAND_NAME)
    painter.setPen(COLOR_STYLES.BRAND_COLOR)
    painter.drawText(x_text, y_text_base + 60, brand_name)

    painter.end()

    splash = QSplashScreen(canvas, Qt.WindowStaysOnTopHint)
    splash.setFont(FONT_STYLES.SPLASH_MESSAGE)
    splash.show()

    messages = t_list(TextKey.LOADING_MESSAGES) or [t("loading.progress")]
    splash.showMessage(
        f"{messages[0]} 1%",
        alignment=Qt.AlignBottom | Qt.AlignHCenter,
        color=COLOR_STYLES.PRIMARY_TEXT,
    )

    QApplication.processEvents()
    return splash
