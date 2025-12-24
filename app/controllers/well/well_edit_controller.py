# app\controllers\well\well_edit_controller.py
# app\controllers\well_edit_controller.py
# app/controllers/well_edit_controller.py  (veya app/utils/qt/well_edit_manager.py)
from PyQt5.QtCore import QObject, pyqtSignal, QSignalBlocker
from PyQt5.QtWidgets import QLineEdit

from app.utils.validators.well_validators import WellValidator



class WellEditController(QObject):
    valueChanged = pyqtSignal(str)  # sadece stabilize edilmiş değeri yay

    def __init__(self, line_edit: QLineEdit, default_value: str = "F12", on_change=None):
        super().__init__()
        self.line_edit = line_edit
        self.on_change = on_change

        self.validator = WellValidator()
        self.line_edit.setValidator(self.validator)

        # default set (stabilize edilmiş halde)
        self.line_edit.setText(self._stabilize(default_value))

        # typing event: uppercase (padding YOK)
        self.line_edit.textEdited.connect(self._on_text_edited)

        # finalize event: padding burada
        self.line_edit.editingFinished.connect(self._on_editing_finished)

    def _on_text_edited(self, text: str):
        # kullanıcı yazarken sadece uppercase yap, başka şeye dokunma
        upper = (text or "").upper()
        if upper != text:
            cursor = self.line_edit.cursorPosition()
            with QSignalBlocker(self.line_edit):
                self.line_edit.setText(upper)
            # cursor’u koru (backspace / typing bozulmasın)
            self.line_edit.setCursorPosition(min(cursor, len(upper)))

        # burada on_change çağırma: çünkü değer henüz “tam” değil olabilir

    def _on_editing_finished(self):
        # fokus kaybı / enter → stabilize et (F1 -> F01 gibi)
        text = (self.line_edit.text() or "").upper()
        stabilized = self._stabilize(text)

        if stabilized != text:
            with QSignalBlocker(self.line_edit):
                self.line_edit.setText(stabilized)

        # sadece stabilize edilmiş değeri dışarı yay
        if stabilized:
            self.valueChanged.emit(stabilized)
            if self.on_change:
                self.on_change(stabilized)

    @staticmethod
    def _stabilize(text: str) -> str:
        """
        "F1" -> "F01"
        "F12" -> "F12"
        "" -> ""
        """
        t = (text or "").upper().strip()
        if len(t) == 2 and t[0].isalpha() and t[1].isdigit():
            return f"{t[0]}0{t[1]}"
        return t
