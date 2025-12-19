# app\willbedeleted\managers\well_manager.py
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QLineEdit

from app.willbedeleted.utils.validators.well_validators import WellValidator


class WellEditManager(QObject):
    """
    QLineEdit'ler için yeniden kullanılabilir bir sınıf.
    """

    valueChanged = pyqtSignal(str)  # Değer değiştiğinde tetiklenecek sinyal

    def __init__(self, line_edit: QLineEdit, default_value="", callback=None):
        super().__init__()
        self.validator = WellValidator()
        self.line_edit = line_edit
        self.default_value = default_value
        self.callback = callback

        # Varsayılan değer atama
        self.line_edit.setText(self.format_text(self.default_value))

        # Validator atama
        self.line_edit.setValidator(self.validator)

        # Sinyal bağlantısı
        self.line_edit.textChanged.connect(self.on_text_changed)

    def on_text_changed(self, text):
        """
        Metin değiştiğinde çalışır.
        """
        formatted_text = self.format_text(text)

        if self.line_edit.hasAcceptableInput():  # Geçerli metni kontrol et
            self.valueChanged.emit(formatted_text)  # Sinyal yayımı
            if self.callback:
                self.callback(formatted_text)

    @staticmethod
    def format_text(text):
        """
        Text formatlama işlemi.
        """
        text = text.upper()  # Girilen metni büyük harfe çevir
        if len(text) <= 1:
            return ""
        elif len(text) == 2:
            return (text[0] + "0" + text[1]).upper()
        elif len(text) == 3:
            return text.upper()
        return text.upper()
