from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QKeyEvent

from app.willbedeleted.controllers.table_controller import DropDownDelegate
from app.willbedeleted.models.editable_table_model import EditableTableModel


class TableViewHandler(QObject):
    """
    Kullanıcı etkileşimlerini yöneten sınıf.
    """

    def __init__(self, table_widget, model, data_manager, graph_drawer):
        super().__init__()
        self.table_widget = table_widget
        self.model = model
        self._last_clicked_row = None
        self.data_manager = data_manager
        self.graph_drawer = graph_drawer

        # Tıklama olayını bağla
        self.table_widget.clicked.connect(self.on_item_clicked)

        # Klavye olaylarını dinle
        self.table_widget.installEventFilter(self)
        
        self._setup_dropdown_delegate()
        print(f"TableView Handler {self.model}")

    def _setup_dropdown_delegate(self):
        if isinstance(self.model, EditableTableModel):
            dropdown_delegate = DropDownDelegate(self.model.dropdown_options, self.table_widget)
            self.table_widget.setItemDelegateForColumn(self.model.dropdown_column, dropdown_delegate)
            print(f"DropDownDelegate atandı: Sütun {self.model.dropdown_column}")

    def on_item_clicked(self, index):
        if not isinstance(self.model, EditableTableModel):
            print("Model EditableTableModel değil veya henüz atanmadı!")
            return

        row = index.row()
        if self._last_clicked_row != row:
            self._last_clicked_row = row

            if self.model and hasattr(self.model, "_data"):
                patient_no = self.model._data.iloc[row]["Hasta No"]
                print(f"Tıklanan Hasta No: {patient_no}")
                self.on_table_click(row, patient_no)

    def on_table_click(self, row, patient_no):
        try:
            print(f"Tıklanan Hasta No: {patient_no}")
            data = self.data_manager.get_row_by_patient_no(patient_no)
            fam_coords = data["FAM"]
            hex_coords = data["HEX"]

            self.graph_drawer.set_title(f"Hasta {patient_no}")
            self.graph_drawer.animate_graph(fam_coords, hex_coords)

        except Exception as e:
            print(f"Tablo tıklama işlenirken hata: {e}")

    def get_patient_no(self, row):
        patient_no_index = self.model.index(row, 0)
        return self.model.data(patient_no_index)

    def eventFilter(self, obj, event):
        if obj == self.table_widget and isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                index = self.table_widget.currentIndex()
                if index.isValid():
                    self.on_item_clicked(index)
                    return True
        return super().eventFilter(obj, event)
