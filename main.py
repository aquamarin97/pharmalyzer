# pharmalizer_v2/main.py
import sys
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

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
from app.exceptions.types import StartupError, LicenseError  # ekle


def main() -> int:
    setup_logging("pharmalizer")
    install_global_exception_hook()

    app = QApplication(sys.argv)

    if os.getenv("ENVIRONMENT") == "production":
        ensure_license_or_exit(app)

    app_icon_path = resource_path(IMAGE_PATHS.APP_LOGO_PNG)
    app.setWindowIcon(QIcon(app_icon_path))

    splash = show_splash()
    model = MainModel()
    view = MainView()
    controller = MainController(view, model)
    view.controller = controller

    splash.finish(view)
    view.show()

    return app.exec_()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.exit(handle_exception(exc))
