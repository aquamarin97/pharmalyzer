# app\views\table\drop_down_delegate.py
# app\views\delegates\drop_down_delegate.py
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate


class DropDownDelegate(QStyledItemDelegate):
    """
    Belirli bir sütuna QComboBox (drop-down) ekleyen delegate.
    View katmanına aittir.
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
        return """
        QComboBox {
            background-color: #F0F0F0;
            border: 1px solid #AAAAAA;
            border-radius: 5px;
            color: #333333;
            font-size: 11pt;
            font-family: "Arial";
        }
        QComboBox:hover {
            border: 1px solid #888888;
        }
        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #AAAAAA;
        }
        QComboBox QAbstractItemView::item {
            background-color: transparent;
            color: white;
            selection-background-color: transparent;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: rgba(255, 255, 255, 0.5);
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: rgba(255, 255, 255, 0.5);
        }
        """

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.options)
        combo.setStyleSheet(self.combo_style)

        # Her seçenek için farklı arkaplan rengi uygula
        for i, opt in enumerate(self.options):
            if opt in self.item_styles:
                combo.setItemData(i, self.item_styles[opt], Qt.BackgroundRole)

        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value if value else "")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
