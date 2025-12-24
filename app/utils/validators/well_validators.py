# app\utils\validators\well_validators.py
# app/utils/validators/well_validator.py
from PyQt5.QtGui import QValidator


class WellValidator(QValidator):
    ROWS = "ABCDEFGH"

    def validate(self, text: str, pos: int):
        if text is None:
            text = ""

        t = text.upper()

        # silmeye izin ver
        if t == "":
            return QValidator.Intermediate, text, pos

        # max len
        if len(t) > 3:
            return QValidator.Invalid, text, pos

        # 1) ilk char harf olmalı
        if t[0] not in self.ROWS:
            return QValidator.Invalid, text, pos

        # sadece harf -> typing aşaması
        if len(t) == 1:
            return QValidator.Intermediate, text, pos

        # 2) kalan kısım rakam olmalı
        num_part = t[1:]
        if not num_part.isdigit():
            return QValidator.Invalid, text, pos

        # "0" veya "00" gibi şeyleri engelle
        try:
            n = int(num_part)
        except ValueError:
            return QValidator.Invalid, text, pos

        if n < 1 or n > 12:
            return QValidator.Invalid, text, pos

        # burada "F1" ve "F12" geçerli yolda:
        # - F1: intermediate (çünkü kullanıcı 2 basamağa tamamlayabilir)
        # - F12: acceptable
        if len(num_part) == 1:
            return QValidator.Intermediate, text, pos

        return QValidator.Acceptable, text, pos

    def fixup(self, text: str) -> str:
        return (text or "").upper()
