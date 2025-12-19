# app\controllers\analysis_controller.py
from PyQt5.QtCore import Qt

from app.willbedeleted.utils.file_utils.output_file import (
    export_table_to_excel_with_path,
)


class AnalysisController:
    """
    Analiz butonu, checkbox, spinbox validasyonu, export, temizle, analysis completed akışı.
    """

    def __init__(
        self, view, model, table_controller, graph_controller, drag_drop_controller
    ):
        self.view = view
        self.model = model
        self.table = table_controller
        self.graph = graph_controller
        self.drag_drop = drag_drop_controller


    # -------- signals ----------
    def setup_signals(self):
        ui = self.view.ui

        ui.pushButton_analiz_et.clicked.connect(self._on_analyze_button_click)
        ui.checkBox_istatistik.stateChanged.connect(self._on_checkbox_state_changed)

        ui.pushButton_disaaktar.clicked.connect(
            lambda: export_table_to_excel_with_path(
                self.table.table_widget, self.model.state.file_name
            )
        )
        ui.pushButton_iceaktar.clicked.connect(self._select_rdml_file)

        ui.doubleSpinBox_tasiyici.valueChanged.connect(
            lambda val: self._validate_and_set_range(val, "carrier")
        )
        ui.doubleSpinBox_belirsiz.valueChanged.connect(
            lambda val: self._validate_and_set_range(val, "uncertain")
        )

        ui.pushButton_temizle.clicked.connect(self.initialize_components)

    # -------- init/reset ----------
    def initialize_components(self):
        # grafik reset + regression reset
        self.graph.initialize_graphics()
        self.graph.reset_regression_graph()

        # state reset
        self.model.state.file_name = ""
        self.model.reset_data()
        self.model.analysis_finished.connect(self._on_async_analysis_finished)
        self.model.analysis_error.connect(lambda msg: self.view.show_warning(msg))
        # drag-drop reset
        self.drag_drop.setup()

        # ui reset
        self.view.set_analyze_enabled(False)
        self.view.reset_box_colors()
        self.view.set_title_label("")
        self.view.set_dragdrop_label("RDML dosyanızı sürükleyip bırakınız")

        # tablo reset
        self.table.setup_table_in_main_window()

        # well reset
        # (WellController kendi içinde zaten lineEdit'leri kuruyor; MainController yaratırken kurulmuş oluyor)
        # Eğer yeniden kurmak istersen: self.well.setup_well_managers() şeklinde bağlayabilirsin.
        # Burada basit bıraktım.

        # drop false simülasyonu: analyze disable kalsın
        self.handle_drop_result(False, "", "")

    # -------- drag-drop result ----------
    def handle_drop_result(self, success: bool, file_path: str, file_name: str):
        """
        Drag-drop sonucunu işler: csv üret, analyze aktif et, dosya adı label güncelle.
        """
        if success:
            self.view.set_analyze_enabled(True)
            df = self.model.process_rdml(file_path)
            # sonra table_controller'a df ver
            self.table.load_dataframe(df)
        else:
            self.view.set_analyze_enabled(False)

        # Dosya adı state + label
        if file_name:
            self.model.set_file_name_from_rdml(file_name)
            self.view.set_title_label(self.model.state.file_name)

    # -------- checkbox ----------
    def _on_checkbox_state_changed(self, state: int):
        is_checked = state == Qt.Checked
        self.model.colored_box_handler.set_check_box_status(is_checked)
        self.model.analyze_button.set_checkbox_status(is_checked)

    # -------- spinbox validation ----------
    def _validate_and_set_range(self, val: float, range_type: str):
        try:
            if range_type == "carrier":
                if val < self.model.analyze_button.uncertain_range:
                    self.model.analyze_button.set_carrier_range(val)
                    self.table.set_carrier_range(val)
                else:
                    raise ValueError(
                        "Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır."
                    )
            elif range_type == "uncertain":
                if val > self.model.analyze_button.carrier_range:
                    self.model.analyze_button.set_uncertain_range(val)
                    self.table.set_uncertain_range(val)
                else:
                    raise ValueError(
                        "Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır."
                    )
        except ValueError as e:
            self.view.show_warning(str(e))

    # -------- analyze ----------
    def _on_analyze_button_click(self):
        success = self.model.run_analysis()
        if success:
            print("Analiz başarıyla tamamlandı.")
            self.model.colored_box_handler.define_box_color()
            self._on_analysis_completed()
        else:
            print("Analiz sırasında bir hata oluştu.")

    def on_analysis_completed(self):
        self._on_analysis_completed()

    def _on_analysis_completed(self):
        # tabloyu güncelle
        self.table.load_csv_to_table()

        # regression graph update
        self.graph.update_regression_graph()

    # -------- file select ----------
    def _select_rdml_file(self):
        file_path, file_name = self.view.select_rdml_file_dialog()
        if not file_path:
            return

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)

        # drag-drop handler içindeki manuel tetik
        self.drag_drop.drop_manual(file_path, file_name)

    def _on_async_analysis_finished(self, success: bool):
        if success:
            self.model.colored_box_handler.define_box_color()
            self._on_analysis_completed()
        else:
            print("Analiz sırasında bir hata oluştu.")