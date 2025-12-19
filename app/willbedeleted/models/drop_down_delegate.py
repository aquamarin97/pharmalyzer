# app\willbedeleted\models\drop_down_delegate.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate

from app.willbedeleted.config.config import ITEM_STYLES


class DropDownDelegate(QStyledItemDelegate):
    """
    Belirli bir sütuna QComboBox (drop-down) ekleyen delegate sınıfı.
    """

    def __init__(
        self,
        options: list,
        parent=None,
        combo_style: str = None,
        item_styles: dict = None,
    ):
        """
        Delegate başlatılırken seçenekleri ve opsiyonel olarak stil ayarlarını alır.

        Args:
            options (list): Drop-down menüde gösterilecek seçenekler.
            parent: Üst widget.
            combo_style (str): QComboBox için stil ayarları (opsiyonel).
            item_styles (dict): Her seçenek için ayrı arkaplan rengi (opsiyonel).
        """
        super().__init__(parent)
        self.options = options
        self.combo_style = combo_style or self.default_style()
        self.item_styles = (
            item_styles or ITEM_STYLES
        )  # Varsayılan olarak ITEM_STYLES kullanılır.

    def default_style(self):
        """
        Varsayılan QComboBox stilini döner.
        """
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
            color: white;  /* Yazı rengi beyaz */
            selection-background-color: transparent;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: rgba(255, 255, 255, 0.5);  /* Hafif opak beyaz */
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: rgba(255, 255, 255, 0.5);  /* Seçim sırasında opak beyaz */
        }
        """

    def createEditor(self, parent, option, index):
        """
        Editor (QComboBox) oluşturur ve stilini ayarlar.
        """
        combo = QComboBox(parent)
        combo.addItems(self.options)  # Drop-down menüye seçenekleri ekle
        combo.setStyleSheet(self.combo_style)  # Dinamik stil ayarı

        # Her seçenek için farklı arkaplan rengi uygula
        for i, option in enumerate(self.options):
            if option in self.item_styles:
                combo.setItemData(i, self.item_styles[option], Qt.BackgroundRole)

        return combo

    def setEditorData(self, editor, index):
        """
        Mevcut değeri editor'a (QComboBox) ayarlar.
        """
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value if value else "")

    def setModelData(self, editor, model, index):
        """
        Editor'daki değeri modele kaydeder.
        """
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)
