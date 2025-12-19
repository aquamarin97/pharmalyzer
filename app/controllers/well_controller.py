# app\controllers\well_controller.py
from app.willbedeleted.managers.well_manager import WellEditManager


class WellController:
    """
    Referans / homozigot / heterozigot / ntc kuyu lineEdit yöneticileri.
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.referans_kuyu_manager = None
        self.homozigot_manager = None
        self.heterozigot_manager = None
        self.ntc_manager = None

        self.setup_well_managers()

    def setup_well_managers(self):
        ui = self.view.ui
        self.referans_kuyu_manager = WellEditManager(
            line_edit=ui.lineEdit_standart_kuyu,
            default_value="F12",
            callback=self.model.analyze_button.set_referance_well,
        )
        self.homozigot_manager = WellEditManager(
            line_edit=ui.line_edit_saglikli_kontrol,
            default_value="F12",
            callback=self.model.colored_box_handler.set_homozigot_line_edit,
        )
        self.heterozigot_manager = WellEditManager(
            line_edit=ui.line_edit_tasiyici_kontrol,
            default_value="G12",
            callback=self.model.colored_box_handler.set_heterozigot_line_edit,
        )
        self.ntc_manager = WellEditManager(
            line_edit=ui.line_edit_NTC_kontrol,
            default_value="H12",
            callback=self.model.colored_box_handler.set_NTC_line_edit,
        )
