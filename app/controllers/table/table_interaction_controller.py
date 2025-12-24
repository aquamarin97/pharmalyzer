# app/controllers/table/table_interaction_controller.py
from __future__ import annotations

import logging
from PyQt5.QtCore import QObject, Qt, QEvent
from PyQt5.QtGui import QKeyEvent

logger = logging.getLogger(__name__)


class TableInteractionController(QObject):
    def __init__(self, table_widget, pcr_data_service, graph_drawer=None):
        super().__init__()
        self.table_widget = table_widget
        self.pcr_data_service = pcr_data_service
        self.graph_drawer = graph_drawer

        # ✅ dedupe artık row değil hasta no üzerinden
        self._last_patient_no: int | None = None

        self.table_widget.clicked.connect(self.on_item_clicked)
        self.table_widget.installEventFilter(self)

    def on_item_clicked(self, index):
        model = self.table_widget.model()
        if model is None or not index.isValid():
            return

        row = index.row()

        if not hasattr(model, "get_patient_no"):
            logger.warning("Table model get_patient_no() sağlamıyor. Model=%s", type(model).__name__)
            return

        raw_patient_no = model.get_patient_no(row)
        if raw_patient_no is None:
            return

        patient_no = self._normalize_patient_no(raw_patient_no)
        if patient_no is None:
            return

        # ✅ aynı hasta tekrar seçilirse çizme
        if self._last_patient_no == patient_no:
            return
        self._last_patient_no = patient_no

        self._draw_patient(patient_no)

    @staticmethod
    def _normalize_patient_no(value) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _draw_patient(self, patient_no: int):
        try:
            coords = self.pcr_data_service.get_coords(patient_no)

            if self.graph_drawer is not None:
                self.graph_drawer.set_title(f"Hasta {patient_no}")
                self.graph_drawer.animate_graph(coords.fam, coords.hex)

        except Exception as e:
            logger.warning("PCR çizimi başarısız (Hasta No=%s): %s", patient_no, e, exc_info=True)

    def eventFilter(self, obj, event):
        if obj == self.table_widget and event.type() == QEvent.KeyPress and isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                index = self.table_widget.currentIndex()
                if index.isValid():
                    self.on_item_clicked(index)
                    return True
        return super().eventFilter(obj, event)
