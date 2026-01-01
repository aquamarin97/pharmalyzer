from __future__ import annotations

import logging
from typing import Set, Optional

from PyQt5.QtCore import QEvent, QObject, Qt, QItemSelection, QItemSelectionModel
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QAbstractItemView

from app.services.data_management import well_mapping
from app.services.data_management.interaction_store import InteractionStore
from app.services.data_management.data_store import DataStore

logger = logging.getLogger(__name__)


class TableInteractionController(QObject):
    def __init__(self, table_widget, pcr_data_service, graph_drawer=None, interaction_store: Optional[InteractionStore] = None):
        super().__init__()
        self.table_widget = table_widget
        self.pcr_data_service = pcr_data_service
        self.graph_drawer = graph_drawer
        self.interaction_store: Optional[InteractionStore] = interaction_store

        self.table_widget.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.CurrentChanged)

        self._syncing_from_store = False
        self._selection_model = None
        self._store_connected = False

        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.table_widget.clicked.connect(self.on_item_clicked)
        self.table_widget.installEventFilter(self)
        self.attach_selection_model()

        if self.interaction_store is not None:
            self._connect_store_once()

    def _connect_store_once(self) -> None:
        if self.interaction_store is None or self._store_connected:
            return
        self._store_connected = True
        self.interaction_store.selectedChanged.connect(self._apply_store_selection)
        # mevcut state'i uygula
        self._apply_store_selection(set(self.interaction_store.selected_wells))

    def set_interaction_store(self, store: InteractionStore) -> None:
        self.interaction_store = store
        self._store_connected = False
        self._connect_store_once()

    def on_item_clicked(self, index):
        model = self.table_widget.model()
        if model is None or not index.isValid():
            return

        if not hasattr(model, "get_patient_no"):
            logger.warning("Table model get_patient_no() sağlamıyor. Model=%s", type(model).__name__)
            return

        row = index.row()
        raw_patient_no = model.get_patient_no(row)
        if raw_patient_no is None:
            return

        patient_no = self._normalize_patient_no(raw_patient_no)
        if patient_no is None:
            return

        try:
            wells = {well_mapping.patient_no_to_well_id(patient_no)}
        except ValueError as exc:
            logger.warning("Geçersiz hasta numarası: %s", exc)
            return

        if self.interaction_store is None:
            return

        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            self.interaction_store.toggle_wells(wells)
        else:
            self.interaction_store.set_selection(wells)

    @staticmethod
    def _normalize_patient_no(value) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def eventFilter(self, obj, event):
        if obj == self.table_widget and event.type() == QEvent.KeyPress and isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                index = self.table_widget.currentIndex()
                if index.isValid():
                    self.on_item_clicked(index)
                    return True
        return super().eventFilter(obj, event)

    def attach_selection_model(self):
        sel_model = self.table_widget.selectionModel()
        if sel_model is None or sel_model is self._selection_model:
            return

        if self._selection_model is not None:
            try:
                self._selection_model.selectionChanged.disconnect(self._on_view_selection_changed)
            except Exception:
                pass

        self._selection_model = sel_model
        self._selection_model.selectionChanged.connect(self._on_view_selection_changed)

    def _on_view_selection_changed(self, selected, deselected):
        if self.interaction_store is None or self._syncing_from_store:
            return

        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            return

        wells = self._gather_selected_wells()
        if wells:
            self.interaction_store.set_selection(wells)
        else:
            self.interaction_store.clear_selection()

    def _gather_selected_wells(self) -> Set[str]:
        model = self.table_widget.model()
        sel_model = self.table_widget.selectionModel()
        if model is None or sel_model is None or not hasattr(model, "get_patient_no"):
            return set()

        wells: Set[str] = set()
        for idx in sel_model.selectedRows():
            pn = self._normalize_patient_no(model.get_patient_no(idx.row()))
            if pn is None:
                continue
            try:
                wells.add(well_mapping.patient_no_to_well_id(pn))
            except ValueError:
                continue
        return wells

    def _apply_store_selection(self, wells: Set[str]) -> None:
        """
        Release-grade:
        - O(N) satır tarama YOK
        - DataStore index cache ile patient->row O(k)
        - Batch selection (QItemSelection) + updates disabled
        """
        model = self.table_widget.model()
        sel_model = self.table_widget.selectionModel()
        if model is None or sel_model is None:
            return

        # wells -> patient_nos
        target_patients: list[int] = []
        for w in wells or set():
            if not well_mapping.is_valid_well_id(w):
                continue
            try:
                target_patients.append(well_mapping.well_id_to_patient_no(w))
            except ValueError:
                continue

        self._syncing_from_store = True
        self.table_widget.setUpdatesEnabled(False)
        try:
            sel_model.clearSelection()
            if not target_patients:
                return

            rows = DataStore.find_rows_by_patient_nos(target_patients)

            if not rows:
                # index cache yoksa fall-back: minimum iş (satır tarama yapmıyoruz)
                return

            selection = QItemSelection()
            for r in rows:
                # row seçimi için 0..last_col aralığı seç
                top_left = model.index(r, 0)
                bottom_right = model.index(r, max(0, model.columnCount() - 1))
                selection.select(top_left, bottom_right)

            sel_model.select(selection, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        finally:
            self.table_widget.setUpdatesEnabled(True)
            self._syncing_from_store = False
