# app\controllers\drag_drop_controller.py
from app.willbedeleted.handlers.drag_handler import DragDropHandler


class DragDropController:
    """
    DragDropHandler'ı kurar ve dropCompleted sinyalini dışarı aktarır.
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.handler = None

        # dışarıdan set edilecek callback: (success, file_path, file_name) -> None
        self.on_drop_result = None

        self.setup()

    def setup(self):
        self.handler = DragDropHandler(self.view.ui.label_drag_drop_area)
        self.handler.setup()

        # sinyali buradan yakala, callback'e ilet
        self.handler.dropCompleted.connect(self._handle_drop_completed)

    def _handle_drop_completed(self, success: bool, file_path: str, file_name: str):
        if callable(self.on_drop_result):
            self.on_drop_result(success, file_path, file_name)

    def drop_manual(self, file_path: str, file_name: str):
        # sende var olan manuel tetik
        self.handler._drop_event_manual(file_path, file_name)
