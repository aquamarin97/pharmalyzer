# app/controllers/main_controller.py
from __future__ import annotations
import time
import logging 
logger = logging.getLogger(__name__)

from PyQt5.QtCore import Qt

from app.controllers.app.export_controller import ExportController
from app.controllers.well.well_edit_controller import WellEditController
from app.controllers.table.table_controller import AppTableController
from app.controllers.app.drag_drop_controller import DragDropController

from app.services.export.export_options import ExportOptions
from app.services.data_store import DataStore

from app.views.main_view import MainView
from app.models.main_model import MainModel

from app.views.widgets.regression_graph_view import RegressionGraphView
from app.views.widgets.pcr_graph_view import PCRGraphView


class MainController:
    def __init__(self, view: MainView, model: MainModel):
        self.view = view
        self.model = model

        self.export_controller = ExportController()
        self.drag_drop_controller: DragDropController | None = None
        self.table_controller: AppTableController | None = None

        self.graph_drawer: PCRGraphView | None = None
        self.regression_graph_view: RegressionGraphView | None = None

        self._wire_model_signals()
        self._wire_view_signals()

        self._initialize_components()
        self._t_analyze_clicked = None
        self._t_worker_finished = None

    # -------------------- Wiring --------------------
    def _wire_view_signals(self) -> None:
        v = self.view
        v.analyze_requested.connect(self._on_analyze_requested)
        v.import_requested.connect(self._on_import_requested)
        v.export_requested.connect(self._on_export_requested)
        v.clear_requested.connect(self._initialize_components)

        v.stats_toggled.connect(self._on_stats_toggled)
        v.carrier_range_changed.connect(lambda val: self._validate_and_set_range(val, "carrier"))
        v.uncertain_range_changed.connect(lambda val: self._validate_and_set_range(val, "uncertain"))
        v.close_requested.connect(self._on_close_requested)
    def _wire_model_signals(self) -> None:
        m = self.model

        # colored box updates
        m.colored_box_controller.calculationCompleted.connect(self.view.update_colored_box_widgets)

        # analysis lifecycle
        m.analysis_busy.connect(self.view.set_busy)
        m.analysis_progress.connect(self._on_analysis_progress)
        m.analysis_finished.connect(self._on_async_analysis_finished)
        m.analysis_error.connect(self.view.show_warning)

    # -------------------- Init / Reset --------------------
    def _initialize_components(self) -> None:
        # grafikler (view container üzerinden)
        self._initialize_graphics()

        self.model.state.file_name = ""
        self.model.reset_data()

        self._setup_drag_and_drop()
        self._setup_table_controller()
        self._setup_well_managers()

        self.view.reset_box_colors()
        self.view.set_analyze_enabled(False)
        self.view.set_dragdrop_label("RDML dosyanızı sürükleyip bırakınız")
        self._reset_regression_graph()

    def _setup_drag_and_drop(self) -> None:
        self.drag_drop_controller = DragDropController(self.view.ui.label_drag_drop_area)
        self.drag_drop_controller.drop_completed.connect(self.handle_drop_result)

    def _setup_table_controller(self) -> None:
        self.table_controller = AppTableController(
            view=self.view,
            model=self.model,
            graph_drawer=self.graph_drawer,  # PCRGraphView
        )

    def _setup_well_managers(self) -> None:
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

    # -------------------- Graphics --------------------
    def _initialize_graphics(self) -> None:
        # PCR graph
        if self.graph_drawer is not None:
            self.graph_drawer.deleteLater()
            self.graph_drawer = None

        layout = self.view.ensure_graph_drawer_layout()
        self.graph_drawer = PCRGraphView(parent=self.view.ui.PCR_graph_container)
        layout.addWidget(self.graph_drawer)

        # Regression graph container (UI name typo: regration_container)
        # Profesyonellik: mümkünse UI'da ismi "regression_container" yap.
        layout = self.view.ensure_regression_graph_container()
        self.regression_graph_view = RegressionGraphView(parent=self.view.ui.regration_container)
        layout.addWidget(self.regression_graph_view)

    def _on_close_requested(self) -> None:
        # Release-grade: thread’i güvenli kapat
        try:
            self.model.shutdown()
        except Exception:
            # UI kapanışında exception fırlatmak istemeyiz
            pass

    def _reset_regression_graph(self) -> None:
        if self.regression_graph_view is not None:
            self.regression_graph_view.reset()


    # -------------------- Handlers --------------------
    def handle_drop_result(self, success: bool, rdml_path: str, file_name: str, message: str) -> None:
        self.view.set_dragdrop_label(message)

        if success:
            self.view.set_analyze_enabled(True)
            self.model.import_rdml(rdml_path)
            self.model.set_file_name_from_rdml(file_name)
            self.view.set_title_label(self.model.state.file_name)
        else:
            self.view.set_analyze_enabled(False)

    def _on_import_requested(self) -> None:
        file_path, file_name = self.view.select_rdml_file_dialog()
        if not file_path or self.drag_drop_controller is None:
            return

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)
        self.drag_drop_controller.manual_drop(file_path, file_name)

    def _on_export_requested(self) -> None:
        if self.table_controller is None:
            return
        self.export_controller.export_table_view(
            self.table_controller.table_widget,
            file_name=self.model.state.file_name,
            options=ExportOptions(fmt="xlsx", preset="full", include_headers=True),
        )

    def _on_analyze_requested(self) -> None:
        self._t_analyze_clicked = time.perf_counter()
        logger.info("[PERF] Analyze clicked")

        self.model.run_analysis()

    def _on_stats_toggled(self, checked: bool) -> None:
        self.model.colored_box_controller.set_check_box_status(bool(checked))
        self.model.set_checkbox_status(bool(checked))

    def _validate_and_set_range(self, val: float, range_type: str) -> None:
        try:
            if self.table_controller is None:
                return

            if range_type == "carrier":
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

    def _on_analysis_progress(self, percent: int, message: str) -> None:
        # İstersen burada status bar / label güncelleyebilirsin.
        # Örn: self.view.ui.statusbar.showMessage(f"{message} ({percent}%)")
        pass

    def _on_async_analysis_finished(self, success: bool) -> None:
        self._t_worker_finished = time.perf_counter()
        if self._t_analyze_clicked is not None:
            logger.info("[PERF] Worker finished in %.0f ms", (self._t_worker_finished - self._t_analyze_clicked) * 1000)

        if not success:
            self.view.show_warning("Analiz başarısız oldu.")
            return

        # ---- UI update ölçümü ----
        t0 = time.perf_counter()

        # Color calc
        self.model.colored_box_controller.define_box_color()

        # Table + graph
        if self.table_controller is not None:
            self.table_controller.load_csv_to_table()

        df = DataStore.get_df_copy()
        if self.regression_graph_view is not None:
            self.regression_graph_view.update(df)

        t1 = time.perf_counter()
        logger.info("[PERF] UI update after analysis took %.0f ms", (t1 - t0) * 1000)
