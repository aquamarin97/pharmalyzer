# main_controller.py
from PyQt5.QtCore import Qt
from app.views.main_view import MainView
from app.models.main_model import MainModel
from app.willbedeleted.controllers.regression_controller import RegressionGraphViewer
from app.willbedeleted.utils.file_utils.output_file import export_table_to_excel_with_path
from app.willbedeleted.managers.well_manager import WellEditManager
from app.willbedeleted.widgets.table_view_widget import TableViewWidget
from app.willbedeleted.config.config import TABLE_WIDGET_HEADERS
from app.willbedeleted.managers.table_manager import TableManager
from app.willbedeleted.controllers.table_controller import TableController
from app.willbedeleted.handlers.table_view_handler import TableViewHandler
from app.willbedeleted.handlers.drag_handler import DragDropHandler
from app.willbedeleted.scripts.pcr_graph_drawer import GraphDrawer




class MainController:
    def __init__(self, view: MainView, model: MainModel):
        self.view = view
        self.model = model

        # RegressionGraphViewer view container istediği için burada bağla
        self.model.regression_graph_manager = RegressionGraphViewer(
            self.view.ui.regration_container
        )

        # GraphDrawer init
        self._initialize_graphics()

        # Signals from model components
        self.model.colored_box_handler.calculationCompleted.connect(
            self.view.update_colored_box_widgets
        )
        self.model.analyze_button.analysisCompleted.connect(
            self.on_analysis_completed
        )

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
            lambda: export_table_to_excel_with_path(self.table_widget, self.model.state.file_name)
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
    def handle_drop_result(self, success: bool, file_path: str, file_name: str):
        self._handle_drop_result(success, file_path)

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)

    def _handle_drop_result(self, success: bool, file_path: str):
        if success:
            self.view.set_analyze_enabled(True)
            self.model.process_rdml_to_csv(file_path)
        else:
            self.view.set_analyze_enabled(False)

    def _on_checkbox_state_changed(self, state: int):
        is_checked = state == Qt.Checked
        self.model.colored_box_handler.set_check_box_status(is_checked)
        self.model.analyze_button.set_checkbox_status(is_checked)

    def _validate_and_set_range(self, val: float, range_type: str):
        try:
            if range_type == "carrier":
                if val < self.model.analyze_button.uncertain_range:
                    self.model.analyze_button.set_carrier_range(val)
                    self.table_controller.set_carrier_range(val)
                else:
                    raise ValueError("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")
            elif range_type == "uncertain":
                if val > self.model.analyze_button.carrier_range:
                    self.model.analyze_button.set_uncertain_range(val)
                    self.table_controller.set_uncertain_range(val)
                else:
                    raise ValueError("Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır.")
        except ValueError as e:
            self.view.show_warning(str(e))

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
        self.table_controller.load_csv()
        self.table_widget.setModel(self.table_controller.model)

        self.table_handler.model = self.table_controller.model
        self.table_handler.table_widget.setModel(self.table_handler.model)

        self.model.regression_graph_manager.update_graph()

    # ---- Table / well managers ----
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

    def setup_table_in_main_window(self):
        ui = self.view.ui
        original_widget = ui.table_widget_resulttable
        ui.table_widget_resulttable = TableViewWidget(original_widget)

        ui.verticalLayout_3.replaceWidget(original_widget, ui.table_widget_resulttable)
        original_widget.deleteLater()

        ui.table_widget_resulttable.set_column_expansion_ratios(
            [2, 2, 2, 10, 5, 2, 2, 2, 3, 3, 3, 3]
        )

        headers = TABLE_WIDGET_HEADERS
        manager = TableManager(ui.table_widget_resulttable, headers)
        manager.create_empty_table()

        controller = TableController(table_widget=ui.table_widget_resulttable, model=None)

        handler = TableViewHandler(
            table_widget=ui.table_widget_resulttable,
            model=controller.model,
            data_manager=self.model.data_manager,
            graph_drawer=self.model.graph_drawer,
        )

        self.table_widget = ui.table_widget_resulttable
        self.table_manager = manager
        self.table_controller = controller
        self.table_handler = handler

    # ---- Drag & drop / init / reset ----
    def _setup_drag_and_drop(self):
        self.drag_drop_handler = DragDropHandler(self.view.ui.label_drag_drop_area)
        self.drag_drop_handler.setup()
        self.drag_drop_handler.dropCompleted.connect(self.handle_drop_result)

    def _initialize_components(self):
        self._initialize_graphics()
        self.model.state.file_name = ""
        self._setup_drag_and_drop()
        self.view.set_analyze_enabled(False)

        self.setup_table_in_main_window()
        self.setup_well_managers()

        self.view.reset_box_colors()
        self.handle_drop_result(False, "", self.model.state.file_name)
        self.view.set_dragdrop_label("RDML dosyanızı sürükleyip bırakınız")

        self.reset_regression_graph()

    # ---- Graphics ----
    def _initialize_graphics(self):
        # Eski GraphDrawer'ı kaldır
        if self.model.graph_drawer is not None:
            self.model.graph_drawer.deleteLater()
            self.model.graph_drawer = None

        layout = self.view.ensure_graph_drawer()
        self.model.graph_drawer = GraphDrawer(parent=self.view.ui.PCR_graph_container)
        layout.addWidget(self.model.graph_drawer)

    def reset_regression_graph(self):
        mgr = getattr(self.model, "regression_graph_manager", None)
        if mgr:
            mgr.reset_regression_graph()

    # ---- File select ----
    def _select_rdml_file(self):
        file_path, file_name = self.view.select_rdml_file_dialog()
        if not file_path:
            return

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)

        # drag-drop handler içindeki manuel tetik (sende var)
        self.drag_drop_handler._drop_event_manual(file_path, file_name)
