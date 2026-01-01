# app\views\widgets\pcr_graph_view.py
from __future__ import annotations

from app.constants.pcr_graph_style import PCRGraphStyle
from app.services.pcr_data_service import PCRDataService
from app.views.widgets.pcr_graph_interactor import PCRGraphInteractor
from app.views.plotting.pcr_graph.renderer import PCRGraphRenderer
from app.services.data_management.interaction_store import InteractionStore


class PCRGraphView(PCRGraphRenderer):
    """
    Renderer + interactor kombinasyonu.
    FigureCanvas olarak kullanılmaya devam eder, InteractionStore kablolaması
    PCRGraphInteractor üzerinden yapılır.
    """

    def __init__(self, parent=None, style: PCRGraphStyle | None = None):
        super().__init__(parent=parent, style=style)
        self._interactor = PCRGraphInteractor(renderer=self)

    def set_interaction_store(self, store: InteractionStore, data_service: PCRDataService) -> None:
        """
        InteractionStore sinyallerini bağla.

        Params:
            store: Seçim/hover state'lerini taşıyan store
            data_service: Veri erişimi için servis
        """
        self._interactor.set_interaction_store(store=store, data_service=data_service)

    def reset_plot(self) -> None:
        """Geriye dönük uyumluluk için reset alias'ı."""
        self.reset()

    def closeEvent(self, event) -> None:
        self._interactor.dispose()
        super().closeEvent(event)