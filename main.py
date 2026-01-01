from __future__ import annotations

import sys
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from app.config.settings import AppSettings
from app.i18n import init_i18n

from app.bootstrap.splash import show_splash
from app.bootstrap.resources import resource_path
from app.bootstrap.warmup import run_warmup
from app.licensing.ui import ensure_license_or_exit
from app.constants.asset_paths import IMAGE_PATHS

from app.controllers.main_controller import MainController
from app.models.main_model import MainModel
from app.views.main_view import MainView

from app.logging.setup import setup_logging, LoggingConfig
from app.exceptions.base import install_global_exception_hook
from app.exceptions.handler import handle_exception

logger = logging.getLogger(__name__)


def configure_app() -> AppSettings:
    settings = AppSettings.from_env()

    # i18n init (explicit, no side-effects)
    init_i18n()

    # Logging (settings'ten)
    level = getattr(logging, settings.log_level, logging.INFO)
    setup_logging(
        LoggingConfig(
            app_name=settings.app_name,
            level=level,
            log_dir=settings.log_dir,
            to_console=settings.log_to_console,
        )
    )

    # Global exception hook
    install_global_exception_hook()

    return settings


def main() -> int:
    settings = configure_app()

    app = QApplication(sys.argv)

    if settings.license_required:
        ensure_license_or_exit(app)

    app.setWindowIcon(QIcon(resource_path(IMAGE_PATHS.APP_LOGO_PNG)))

    splash = show_splash()

    def splash_progress(msg: str, p: int) -> None:
        try:
            splash.showMessage(
                msg,  # yüzde zaten msg içinde
                alignment=Qt.AlignBottom | Qt.AlignHCenter,
            )
            QApplication.processEvents()
        except Exception:
            pass

    model = MainModel()
    app.aboutToQuit.connect(model.shutdown)

    if settings.warmup_enabled:
        try:
            run_warmup(splash_progress)
        except Exception as exc:
            logger.exception("Warmup failed (continuing): %s", exc)

    view = MainView()
    controller = MainController(view, model)
    view.controller = controller  # GC guard

    splash.finish(view)
    view.show()

    return app.exec_()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.exit(handle_exception(exc))
