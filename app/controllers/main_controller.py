# app\controllers\main_controller.py
from PyQt5.QtCore import Qt
from app.controllers.app.export_controller import ExportController
from app.controllers.well.well_edit_controller import WellEditController
from app.services.export.export_options import ExportOptions
from app.views.main_view import MainView
from app.models.main_model import MainModel
from app.controllers.table.table_controller import AppTableController
from app.controllers.app.drag_drop_controller import DragDropController
from app.views.widgets.regression_graph_view import RegressionGraphView
from app.services.data_store import DataStore
from app.views.widgets.pcr_graph_view import PCRGraphView


class MainController:
    def __init__(self, view: MainView, model: MainModel):
        self.view = view
        self.model = model

        # RegressionGraphViewer view container istediği için burada bağla
        self.regression_graph_view = RegressionGraphView(self.view.ui.regration_container)

        self.graph_drawer = None
        # GraphDrawer init
        self._initialize_graphics()

        # Signals from model components
        self.model.colored_box_controller.calculationCompleted.connect(
            self.view.update_colored_box_widgets
        )
        self.model.analysis_finished.connect(self._on_async_analysis_finished)
        self.model.analysis_error.connect(self.view.show_warning)
        self.export_controller = ExportController()

        # Init components + signals
        self.initialize_components()
        self._setup_signals()

    # ---- Public init ----
    def initialize_components(self):
        self._initialize_components()

    # ---- Signals ----
    def _setup_signals(self):
        ui = self.view.ui

        ui.pushButton_analiz_et.clicked.connect(self._on_analyze_button_click)
        ui.checkBox_istatistik.stateChanged.connect(self._on_checkbox_state_changed)
        ui.pushButton_disaaktar.clicked.connect(
            lambda: self.export_controller.export_table_view(
                self.table_controller.table_widget,
                file_name=self.model.state.file_name,
                options=ExportOptions(fmt="xlsx", preset="full", include_headers=True),
            )
        )
        ui.pushButton_iceaktar.clicked.connect(self._select_rdml_file)

        ui.doubleSpinBox_tasiyici.valueChanged.connect(
            lambda val: self._validate_and_set_range(val, "carrier")
        )
        ui.doubleSpinBox_belirsiz.valueChanged.connect(
            lambda val: self._validate_and_set_range(val, "uncertain")
        )

        ui.pushButton_temizle.clicked.connect(self._initialize_components)

    # ---- Core handlers ----
    def handle_drop_result(self, success: bool, rdml_path: str, file_name: str, message: str):
        # CMV: UI update burada (View katmanı)
        self.view.set_dragdrop_label(message)

        self._handle_drop_result(success, rdml_path)

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)

    def _handle_drop_result(self, success: bool, rdml_path: str):
        if success:
            self.view.set_analyze_enabled(True)
            # Artık rdml_path gönderiyoruz (xml extracted path değil)
            self.model.import_rdml(rdml_path)
        else:
            self.view.set_analyze_enabled(False)

    def _on_checkbox_state_changed(self, state: int):
        is_checked = state == Qt.Checked
        self.model.colored_box_controller.set_check_box_status(is_checked)
        self.model.set_checkbox_status(is_checked)  # <-- analyze_button yerine


    def _on_async_analysis_finished(self, success: bool):
        if success:
            self.model.colored_box_controller.define_box_color()  # <-- EKLE
            self._on_analysis_completed()
        else:
            self.view.show_warning("Analiz başarısız oldu.")

    def _validate_and_set_range(self, val: float, range_type: str):
        try:
            if range_type == "carrier":
                # artık config'i model üzerinden oku
                if val < self.model.get_uncertain_range():
                    self.model.set_carrier_range(val)
                    self.table_controller.set_carrier_range(val)
                else:
                    raise ValueError("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")

            elif range_type == "uncertain":
                if val > self.model.get_carrier_range():
                    self.model.set_uncertain_range(val)
                    self.table_controller.set_uncertain_range(val)
                else:
                    raise ValueError("Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır.")

        except ValueError as e:
            self.view.show_warning(str(e))


    def _on_analyze_button_click(self):
        """
        This function runs an analysis process and handles success or failure accordingly.
        """
        self.model.run_analysis()


    def on_analysis_completed(self):
        self._on_analysis_completed()

    def _on_analysis_completed(self):
        # AppTableController zaten table model + handler güncellemeyi kendi içinde yapıyor
        self.table_controller.load_csv_to_table()

        df = DataStore.get_df_copy()
        self.regression_graph_view.update(df)


    # ---- Table / well managers ----
    def setup_well_managers(self):
        ui = self.view.ui
        self.referans_kuyu_manager = WellEditController(
            line_edit=ui.lineEdit_standart_kuyu,
            default_value="F12",
            on_change=self.model.set_referance_well,
        )
        self.homozigot_manager = WellEditController(
            line_edit=ui.line_edit_saglikli_kontrol,
            default_value="F12",
            on_change=self.model.colored_box_controller.set_homozigot_line_edit,
        )
        self.heterozigot_manager = WellEditController(
            line_edit=ui.line_edit_tasiyici_kontrol,
            default_value="G12",
            on_change=self.model.colored_box_controller.set_heterozigot_line_edit,
        )
        self.ntc_manager = WellEditController(
            line_edit=ui.line_edit_NTC_kontrol,
            default_value="H12",
            on_change=self.model.colored_box_controller.set_NTC_line_edit,
        )

    # ---- Drag & drop / init / reset ----
    def _setup_drag_and_drop(self):
        self.drag_drop_controller = DragDropController(self.view.ui.label_drag_drop_area)
        self.drag_drop_controller.drop_completed.connect(self.handle_drop_result)

    def _initialize_components(self):
        self._initialize_graphics()
        self.model.state.file_name = ""
        self._setup_drag_and_drop()
        self.view.set_analyze_enabled(False)

        self.table_controller = AppTableController(
            view=self.view,
            model=self.model,
            graph_drawer=self.graph_drawer,  # <-- kritik kısım
        )
        self.setup_well_managers()

        self.view.reset_box_colors()
        self.handle_drop_result(False, "", self.model.state.file_name, "RDML dosyanızı sürükleyip bırakınız")

        self.reset_regression_graph()

    # ---- Graphics ----
    def _initialize_graphics(self):
        # Eski GraphDrawer'ı kaldır
        if self.graph_drawer is not None:
            self.graph_drawer.deleteLater()
            self.graph_drawer = None

        layout = self.view.ensure_graph_drawer()
        self.graph_drawer = PCRGraphView(parent=self.view.ui.PCR_graph_container)
        layout.addWidget(self.graph_drawer)

    def reset_regression_graph(self):
        self.regression_graph_view.reset()


    # ---- File select ----
    def _select_rdml_file(self):
        file_path, file_name = self.view.select_rdml_file_dialog()
        if not file_path:
            return

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)

        self.drag_drop_controller.manual_drop(file_path, file_name)