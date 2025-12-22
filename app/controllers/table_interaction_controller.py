# app\controllers\table_interaction_controller.py
from PyQt5.QtCore import QObject, Qt, QEvent
from PyQt5.QtGui import QKeyEvent

class TableInteractionController(QObject):
    def __init__(self, table_widget, pcr_data_service, graph_drawer=None):
        super().__init__()
        self.table_widget = table_widget
        self.pcr_data_service = pcr_data_service
        self.graph_drawer = graph_drawer
        self._last_row = None

        self.table_widget.clicked.connect(self.on_item_clicked)
        self.table_widget.installEventFilter(self)

    def on_item_clicked(self, index):
        model = self.table_widget.model()
        if model is None or not index.isValid():
            return

        row = index.row()
        if self._last_row == row:
            return
        self._last_row = row

        patient_no = self._read_patient_no(model, row)
        if patient_no in (None, "", "-"):
            return

        self._draw_patient(patient_no)

    def _read_patient_no(self, model, row: int):
        # Eğer modelde yardımcı method eklediysen:
        if hasattr(model, "get_patient_no"):
            return model.get_patient_no(row)

        # fallback: "Hasta No" kolonunu bulmaya çalış
        if hasattr(model, "_data") and "Hasta No" in model._data.columns:
            col = model._data.columns.get_loc("Hasta No")
            idx = model.index(row, col)
            return model.data(idx, Qt.DisplayRole)

        return None

    def _draw_patient(self, patient_no):
        try:
            coords = self.pcr_data_service.get_coords(patient_no)
            fam_coords = coords.fam
            hex_coords = coords.hex

            if self.graph_drawer is not None:
                self.graph_drawer.set_title(f"Hasta {patient_no}")
                self.graph_drawer.animate_graph(fam_coords, hex_coords)
        except Exception as e:
            print(f"[TableInteractionController] çizim hatası: {e}")


    def eventFilter(self, obj, event):
        if obj == self.table_widget and isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                index = self.table_widget.currentIndex()
                if index.isValid():
                    self.on_item_clicked(index)
                    return True
        return super().eventFilter(obj, event)
