# pharmalizer_v2/app/licensing/ui.py
import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from app.licensing.manager import read_saved_license_path, save_license_path
from app.licensing.validator import validate_license_file

from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from app.i18n import t
from app.constants.app_text_key import TextKey
def ensure_license_or_exit(app: QApplication | None = None) -> None:
    """
    Lisans doğrulanamazsa kullanıcıya UI ile sorar, geçerli lisans alamazsa uygulamayı kapatır.
    """

    # 1) Kayıtlı lisans yolunu dene
    saved_path = read_saved_license_path()
    if saved_path and os.path.exists(saved_path) and validate_license_file(saved_path):
        return  # Lisans geçerli → devam et

    # Kayıtlı lisans vardı ama geçersizse uyarı ver
    if saved_path:
        QMessageBox.warning(
            None,
            t(TextKey.TITLE_LICENSE_ERROR),
            t(TextKey.MSG_INVALID_SAVED)
        )

    # 2) Kullanıcıdan yeni lisans dosyası seçtir
    license_file, _ = QFileDialog.getOpenFileName(
        None,
        caption=t(TextKey.TITLE_SELECT_FILE),           # "Lisans Dosyasını Seç"
        directory="",
        filter=t(TextKey.FILTER_LICENSE_FILES)          # "Lisans Dosyaları (*.key)"
    )

    # Kullanıcı bir dosya seçti mi ve geçerli mi?
    if license_file and validate_license_file(license_file):
        try:
            save_license_path(license_file)
            return  # Başarılı → uygulamaya devam
        except Exception as e:
            QMessageBox.critical(
                None,
                t(TextKey.TITLE_ERROR),
                f"{t(TextKey.MSG_PATH_SAVE_FAILED)} {e}"
            )
            raise SystemExit(1)

    # Hiçbir şekilde geçerli lisans elde edilemedi
    QMessageBox.critical(
        None,
        t(TextKey.TITLE_LICENSE_ERROR),
        t(TextKey.MSG_INVALID_SELECTED)
    )
    raise SystemExit(1)
