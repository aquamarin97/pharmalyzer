# app\willbedeleted\managers\table_manager.py
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class TableManager(QObject):
    """
    Genel tablo yönetimiyle ilgilenen sınıf.
    """

    def __init__(self, table_widget, headers):
        super().__init__()
        self.table_widget = table_widget
        self.headers = headers
        self.model = None
        print(self.model)

    def create_empty_table(self):
        """Sadece başlıklarla boş bir tablo oluşturur."""
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.headers)
        self.table_widget.setModel(self.model)
        
    def clear_table(self):
        """Tabloyu temizler."""
        self.create_empty_table()
