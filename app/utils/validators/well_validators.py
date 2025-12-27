# app\utils\validators\well_validators.py
from PyQt5.QtGui import QValidator

class WellValidator(QValidator):
    ROWS = "ABCDEFGH"

    def validate(self, text: str, pos: int):
        t = text.upper()

        # 1. Boş giriş veya silme işlemi: Ara durum olarak kabul et
        if not t:
            return QValidator.Intermediate, t, pos

        # 2. İlk karakter kontrolü (A-H)
        if t[0] not in self.ROWS:
            return QValidator.Invalid, text, pos

        # Sadece harf varsa (örn: "A")
        if len(t) == 1:
            return QValidator.Intermediate, t, pos

        # 3. İkinci karakter kontrolü
        char2 = t[1]
        
        if not char2.isdigit():
            return QValidator.Invalid, text, pos

        # KURAL: İkinci karakter "2-9" arasındaysa doğrudan "X0X" yap
        if char2 in "23456789":
            formatted = f"{t[0]}0{char2}"
            return QValidator.Acceptable, formatted, 3

        # KURAL: İkinci karakter "0" ise (örn: "A0")
        if char2 == "0":
            if len(t) == 2:
                return QValidator.Intermediate, t, pos
            if len(t) == 3:
                # Üçüncü karakter "1-9" olmalı (A01-A09)
                if t[2] in "123456789":
                    return QValidator.Acceptable, t, pos
                return QValidator.Invalid, text, pos

        # KURAL: İkinci karakter "1" ise (örn: "A1")
        if char2 == "1":
            if len(t) == 2:
                return QValidator.Intermediate, t, pos
            if len(t) == 3:
                # Üçüncü karakter sadece "0, 1, 2" olabilir (A10, A11, A12)
                if t[2] in "012":
                    return QValidator.Acceptable, t, pos
                return QValidator.Invalid, text, pos

        # 3 karakterden fazlasına izin verme
        if len(t) > 3:
            return QValidator.Invalid, text, pos

        return QValidator.Invalid, text, pos

    def fixup(self, text: str) -> str:
        """Kullanıcı input'tan ayrıldığında (focus out) veriyi düzeltir."""
        if not text:
            return ""
        
        t = text.upper()
        row = t[0] if t[0] in self.ROWS else "A"
        
        # Eğer giriş eksikse (örn: sadece "A" veya "A0" veya "A1" kalmışsa)
        # Kurallar gereği bunu varsayılan olarak "X01" formatına tamamlıyoruz.
        if len(t) < 3:
            return f"{row}01"
        
        return t