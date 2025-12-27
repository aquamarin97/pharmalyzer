# app/views/table/drop_down_delegate.py
from __future__ import annotations

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate, QStyle, QStyleOptionViewItem


def _best_contrast_foreground(bg: QColor) -> QColor:
    r, g, b = bg.red(), bg.green(), bg.blue()
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return QColor(Qt.black) if luminance >= 160 else QColor(Qt.white)


class _ComboPopupItemDelegate(QStyledItemDelegate):
    """
    QComboBox popup (QAbstractItemView) item'larını custom çizer:
    - BackgroundRole rengi = asıl anlam rengi (HER ZAMAN korunur)
    - Hover/Selected = arka plan bozulmaz; sadece hafif koyulaştırma + border + font-weight
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Base rect
        r = option.rect.adjusted(4, 2, -4, -2)

        # Background rengi (model/itemData'dan)
        bg = index.data(Qt.BackgroundRole)
        if isinstance(bg, QColor):
            base = bg
        else:
            # fallback: koyu panel üstünde nötr bir renk
            base = QColor("#4ca1af")

        # Hover/selected: rengi KORU, sadece hafif koyulaştır (istersen kapatabilirsin)
        is_hover = bool(option.state & QStyle.State_MouseOver)
        is_selected = bool(option.state & QStyle.State_Selected)

        fill = QColor(base)
        if is_selected:
            fill = fill.darker(112)   # %12 koyu
        elif is_hover:
            fill = fill.darker(106)   # %6 koyu

        # Draw background rounded rect
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(r, 6, 6)

        # Border (hover/selected vurgusu)
        if is_selected:
            pen = QPen(QColor(255, 255, 255, 220), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r, 6, 6)
        elif is_hover:
            pen = QPen(QColor(255, 255, 255, 140), 1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r, 6, 6)

        # Text
        text = str(index.data(Qt.DisplayRole) or "")
        painter.setPen(QColor(Qt.white))

        font = option.font
        if is_selected:
            font.setWeight(600)
        painter.setFont(font)

        painter.drawText(
            r.adjusted(10, 0, -10, 0),
            Qt.AlignVCenter | Qt.AlignLeft,
            text,
        )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        s = super().sizeHint(option, index)
        return QSize(max(s.width(), 180), max(s.height(), 28))


class DropDownDelegate(QStyledItemDelegate):
    """
    Tablodaki belirli bir sütuna QComboBox editor ekleyen delegate.

    Kritik fark:
    - QComboBox popup item'larını stylesheet yerine custom delegate ile çiziyoruz.
      Böylece hover/selected asla anlam rengini yok etmiyor.
    """

    def __init__(
        self,
        options: list[str],
        parent=None,
        combo_style: str | None = None,
        item_styles: dict[str, object] | None = None,
    ):
        super().__init__(parent)
        self.options = options
        self.combo_style = combo_style or self.default_style()
        self.item_styles = item_styles or {}

    def default_style(self) -> str:
        # Combo'nun "kapalı" hali
        return """
        QComboBox {
            background-color: #4ca1af;
            border: 1px solid #3b8793;
            border-radius: 6px;
            color: white;
            padding: 4px 10px;
            font-size: 11pt;
            font-family: "Arial";
        }
        QComboBox:hover { border: 1px solid #2f6f79; }
        QComboBox:focus { border: 2px solid #2b78da; }

        /* popup panel arka planı (item'lar zaten renkli çizilecek) */
        QComboBox QAbstractItemView {
            background-color: #2f3337;
            border: 1px solid #1f2327;
            outline: 0;
            padding: 4px;
        }
        """

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.options)
        combo.setStyleSheet(self.combo_style)

        # Popup view ayarları
        view = combo.view()
        view.setMouseTracking(True)  # hover state gelsin
        view.setItemDelegate(_ComboPopupItemDelegate(view))

        # Her option için arkaplan + otomatik kontrast text rengi
        for i, opt in enumerate(self.options):
            if opt in self.item_styles:
                bg = self.item_styles[opt]
                if isinstance(bg, QColor):
                    combo.setItemData(i, bg, Qt.BackgroundRole)
                    combo.setItemData(i, QColor(Qt.black), Qt.ForegroundRole)


        # Genişlik stabil dursun
        view.setMinimumWidth(max(220, combo.sizeHint().width()))
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value if value else "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
