from PyQt5.QtCore import QObject, pyqtSignal

from app.services.data_store import DataStore
from app.services.colored_box_service import ColoredBoxService, ColoredBoxConfig


class ColoredBoxController(QObject):
    calculationCompleted = pyqtSignal(list)

    def __init__(self, service: ColoredBoxService | None = None, parent=None):
        super().__init__(parent)
        self.service = service or ColoredBoxService()
        self.cfg = ColoredBoxConfig()
        self.last_result = [False, False, False]

    # UI setters
    def set_check_box_status(self, status: bool):
        self.cfg.use_statistic_column = bool(status)

    def set_homozigot_line_edit(self, v: str):
        self.cfg.homozigot_well = v

    def set_heterozigot_line_edit(self, v: str):
        self.cfg.heterozigot_well = v

    def set_NTC_line_edit(self, v: str):
        self.cfg.ntc_well = v

    def set_carrier_threshold(self, v: float):
        self.cfg.carrier_threshold = float(v)

    def define_box_color(self):
        df = DataStore.get_df_copy()
        self.last_result = self.service.compute(df, self.cfg)
        self.calculationCompleted.emit(self.last_result)
