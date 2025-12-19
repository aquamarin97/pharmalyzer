# app\willbedeleted\utils\validators\well_validators.py
from PyQt5.QtGui import QValidator


class WellValidator(QValidator):
    def validate(self, input_text, pos):
        # Boş metin geçerli
        if input_text == "":
            return QValidator.Acceptable, input_text, pos

        # Maksimum 3 karakter kontrolü
        if len(input_text) > 3:
            return QValidator.Invalid, input_text, pos

        # İlk karakter kontrolü
        if len(input_text) >= 1:
            if input_text[0].upper() not in "ABCDEFGH":
                return QValidator.Invalid, input_text, pos

        # İkinci ve üçüncü karakter kontrolü (birlikte)
        if len(input_text) >= 2:
            # İkinci ve üçüncü karakteri birleştirip sayı olarak değerlendirme
            number_part = input_text[1:]
            if not number_part.isdigit():
                return QValidator.Invalid, input_text, pos
            if int(number_part) > 12:
                return QValidator.Invalid, input_text, pos

        # Tüm kontrollerden geçerse
        return QValidator.Acceptable, input_text, pos

    def fixup(self, input_text):
        """Geçersiz metinlerle ilgili düzeltme yapılabilir."""
        return ""
