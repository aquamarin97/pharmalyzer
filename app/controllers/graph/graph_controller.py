# app/controllers/graph/graph_controller.py
from __future__ import annotations

from PyQt5.QtCore import QObject

from app.views.ui.ui import Ui_MainWindow
from app.views.widgets.pcr_graph_view import PCRGraphView


class GraphController(QObject):
    """
    PCR grafik görünürlüğünü checkbox'lar ile kontrol eden controller.
    UI (checkbox) -> View (PCRGraphView) iletişimini üstlenir.
    """

    def __init__(self, ui: Ui_MainWindow, graph_view: PCRGraphView | None = None):
        super().__init__()
        self.ui = ui
        self.graph_view = graph_view

        self._connect_signals()
        self.reset_checkboxes()

    def _connect_signals(self) -> None:
        self.ui.checkBox_FAM.toggled.connect(self._on_fam_toggled)
        self.ui.checkBox_HEX.toggled.connect(self._on_hex_toggled)

    def set_graph_view(self, graph_view: PCRGraphView) -> None:
        """
        Grafiğin yeniden oluşturulması durumunda controller'a yeni view'i tanıtır.
        """
        self.graph_view = graph_view
        self._sync_visibility()

    def reset_checkboxes(self) -> None:
        """
        Başlangıç varsayılanını uygula: her iki kanal da açık.
        """
        self.ui.checkBox_FAM.setChecked(True)
        self.ui.checkBox_HEX.setChecked(True)
        self._sync_visibility()

    def _on_fam_toggled(self, checked: bool) -> None:
        self._sync_visibility(fam_visible=bool(checked))

    def _on_hex_toggled(self, checked: bool) -> None:
        self._sync_visibility(hex_visible=bool(checked))

    def _sync_visibility(
        self,
        fam_visible: bool | None = None,
        hex_visible: bool | None = None,
    ) -> None:
        """
        Checkbox durumlarını grafik görünürlüğü ile senkronize eder.
        """
        if self.graph_view is None:
            return

        fam_state = self.ui.checkBox_FAM.isChecked() if fam_visible is None else fam_visible
        hex_state = self.ui.checkBox_HEX.isChecked() if hex_visible is None else hex_visible

        self.graph_view.set_channel_visibility(
            fam_visible=fam_state,
            hex_visible=hex_state,
        )