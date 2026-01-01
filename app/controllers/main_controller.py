# app/controllers/main_controller.py
from __future__ import annotations

import logging
from typing import Optional

from app.controllers.app.export_controller import ExportController
from app.controllers.well.well_edit_controller import WellEditController
from app.controllers.table.table_controller import AppTableController
from app.controllers.app.drag_drop_controller import DragDropController
from app.services.interaction_store import InteractionStore
from app.services.pcr_data_service import PCRDataService
from app.services.export.export_options import ExportOptions
from app.services.data_store import DataStore
from app.controllers.interaction.interaction_controller import InteractionController
from app.views.main_view import MainView
from app.models.main_model import MainModel
from app.views.widgets.pcr_plate.pcr_plate_widget import PCRPlateWidget
from app.views.widgets.regression_graph_view import RegressionGraphView
from app.views.widgets.pcr_graph_view import PCRGraphView
from app.controllers.graph.graph_controller import GraphController

logger = logging.getLogger(__name__)


class MainController:
    """
    Release-grade goals:
    - Avoid re-creating QObject widgets/controllers repeatedly (prevents signal duplication, leaks, UI jank)
    - Wire signals exactly once
    - Provide safe close/shutdown behavior (no UI updates after closing)
    - Keep reset cheap: clear state + reset views, do not rebuild tree unless mandatory
    """

    def __init__(self, view: MainView, model: MainModel):
        self.view = view
        self.model = model

        self.export_controller = ExportController()

        # Controllers / services
        self.drag_drop_controller: Optional[DragDropController] = None
        self.table_controller: Optional[AppTableController] = None
        self.graph_controller: Optional[GraphController] = None
        self.interaction_controller: Optional[InteractionController] = None

        self.interaction_store = InteractionStore()
        self.pcr_data_service = PCRDataService()

        # Views (widgets)
        self.graph_drawer: Optional[PCRGraphView] = None
        self.regression_graph_view: Optional[RegressionGraphView] = None
        self.plate_widget: Optional[PCRPlateWidget] = None

        # Well managers
        self.referans_kuyu_manager: Optional[WellEditController] = None
        self.homozigot_manager: Optional[WellEditController] = None
        self.heterozigot_manager: Optional[WellEditController] = None
        self.ntc_manager: Optional[WellEditController] = None

        # Lifecycle / safety
        self._closing: bool = False
        self._view_wired: bool = False
        self._model_wired: bool = False
        self._components_built: bool = False

        # Wire once
        self._wire_model_signals_once()
        self._wire_view_signals_once()

        # Build once (widgets/controllers), then reset state
        self._build_components_once()
        self.reset_state()

    # -------------------- Wiring (ONCE) --------------------
    def _wire_view_signals_once(self) -> None:
        if self._view_wired:
            return
        self._view_wired = True

        v = self.view
        v.analyze_requested.connect(self._on_analyze_requested)
        v.import_requested.connect(self._on_import_requested)
        v.export_requested.connect(self._on_export_requested)
        v.clear_requested.connect(self.reset_state)  # IMPORTANT: reset without re-creating objects
        v.stats_toggled.connect(self._on_stats_toggled)
        v.carrier_range_changed.connect(lambda val: self._validate_and_set_range(val, "carrier"))
        v.uncertain_range_changed.connect(lambda val: self._validate_and_set_range(val, "uncertain"))
        v.close_requested.connect(self._on_close_requested)

    def _wire_model_signals_once(self) -> None:
        if self._model_wired:
            return
        self._model_wired = True

        m = self.model

        # colored box updates
        m.colored_box_controller.calculationCompleted.connect(self.view.update_colored_box_widgets)

        # analysis lifecycle
        m.analysis_busy.connect(self.view.set_busy)
        m.analysis_progress.connect(self._on_analysis_progress)
        m.analysis_finished.connect(self._on_async_analysis_finished)
        m.analysis_error.connect(self.view.show_warning)
        m.analysis_summary_ready.connect(self._on_analysis_summary_ready)

    def _disconnect_model_signals_safely(self) -> None:
        """
        Qt disconnect can throw if not connected; wrap safely.
        """
        if not self._model_wired:
            return
        m = self.model
        v = self.view
        try:
            m.colored_box_controller.calculationCompleted.disconnect(v.update_colored_box_widgets)
        except Exception:
            pass
        try:
            m.analysis_busy.disconnect(v.set_busy)
        except Exception:
            pass
        try:
            m.analysis_progress.disconnect(self._on_analysis_progress)
        except Exception:
            pass
        try:
            m.analysis_finished.disconnect(self._on_async_analysis_finished)
        except Exception:
            pass
        try:
            m.analysis_error.disconnect(v.show_warning)
        except Exception:
            pass
        try:
            m.analysis_summary_ready.disconnect(self._on_analysis_summary_ready)
        except Exception:
            pass

        self._model_wired = False

    # -------------------- Build once (widgets/controllers) --------------------
    def _build_components_once(self) -> None:
        if self._components_built:
            return
        self._components_built = True

        self._build_graphics_once()
        self._build_drag_and_drop_once()
        self._build_table_controller_once()
        self._build_well_managers_once()
        self._build_interaction_controller_once()

    def _build_graphics_once(self) -> None:
        """
        Create heavy widgets ONCE. Reset later by clearing data.
        """
        # PCR graph
        layout_graph = self.view.ensure_graph_drawer_layout()
        self.graph_drawer = PCRGraphView(parent=self.view.ui.PCR_graph_container)
        layout_graph.addWidget(self.graph_drawer)

        # Graph controller once; can swap graph view if needed, but we keep a single graph view.
        self.graph_controller = GraphController(ui=self.view.ui, graph_view=self.graph_drawer)

        # Regression graph
        layout_reg = self.view.ensure_regression_graph_container()
        self.regression_graph_view = RegressionGraphView(parent=self.view.ui.regration_container)
        layout_reg.addWidget(self.regression_graph_view)

        # PCR plate: create once; avoid replaceWidget each reset.
        # If your UI already has a placeholder widget, we replace it ONCE here.
        original_plate = getattr(self.view.ui, "PCR_plate_container", None)
        if original_plate is not None and not isinstance(original_plate, PCRPlateWidget):
            new_plate = PCRPlateWidget(original_plate)
            self.view.ui.PCR_plate_container = new_plate
            try:
                self.view.ui.verticalLayout_2.replaceWidget(original_plate, new_plate)
            except Exception:
                # In case layout name differs or replaceWidget is unavailable
                pass
            try:
                original_plate.deleteLater()
            except Exception:
                pass

        self.plate_widget = self.view.ui.PCR_plate_container

    def _build_drag_and_drop_once(self) -> None:
        self.drag_drop_controller = DragDropController(self.view.ui.label_drag_drop_area)
        self.drag_drop_controller.drop_completed.connect(self.handle_drop_result)

    def _build_table_controller_once(self) -> None:
        self.table_controller = AppTableController(
            view=self.view,
            model=self.model,
            graph_drawer=self.graph_drawer,  # PCRGraphView
            interaction_store=self.interaction_store,
        )

    def _build_well_managers_once(self) -> None:
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

    def _build_interaction_controller_once(self) -> None:
        if (
            self.table_controller is None
            or getattr(self.table_controller, "table_interaction", None) is None
            or self.graph_drawer is None
            or self.regression_graph_view is None
            or self.plate_widget is None
        ):
            logger.warning("InteractionController prerequisites are missing; skipping build.")
            return

        self.interaction_controller = InteractionController(
            store=self.interaction_store,
            plate_widget=self.plate_widget,
            table_interaction=self.table_controller.table_interaction,
            regression_graph_view=self.regression_graph_view,
            pcr_graph_view=self.graph_drawer,
            pcr_data_service=self.pcr_data_service,
        )

    # -------------------- Reset (cheap, no rebuild) --------------------
    def reset_state(self) -> None:
        """
        Release-grade: do NOT recreate widgets/controllers. Just clear state/data and reset views.
        """
        if self._closing:
            return

        # interaction store
        self.interaction_store.clear_selection()
        self.interaction_store.set_hover(None)

        # model data
        self.model.state.file_name = ""
        self.model.reset_data()

        # reset view widgets / labels
        self.view.reset_box_colors()
        self.view.reset_summary_labels()
        self.view.set_analyze_enabled(False)
        self.view.set_dragdrop_label("RDML dosyanızı sürükleyip bırakınız")
        self._reset_graphs()

        # reset controllers/views if they expose reset API
        self._safe_reset(self.drag_drop_controller)
        self._safe_reset(self.table_controller)
        self._safe_reset(self.referans_kuyu_manager)
        self._safe_reset(self.homozigot_manager)
        self._safe_reset(self.heterozigot_manager)
        self._safe_reset(self.ntc_manager)
        self._safe_reset(self.interaction_controller)

        # graph controller checkboxes reset
        if self.graph_controller is not None:
            try:
                self.graph_controller.reset_checkboxes()
            except Exception:
                logger.exception("GraphController.reset_checkboxes failed")

    def _safe_reset(self, obj) -> None:
        """
        If obj has reset()/clear() call it. Non-fatal if not present.
        """
        if obj is None:
            return
        for method_name in ("reset", "clear", "reset_state"):
            if hasattr(obj, method_name):
                try:
                    getattr(obj, method_name)()
                except Exception:
                    logger.exception("%s.%s() failed", type(obj).__name__, method_name)
                break

    def _reset_graphs(self) -> None:
        # Reset regression graph
        if self.regression_graph_view is not None:
            try:
                self.regression_graph_view.reset()
            except Exception:
                logger.exception("RegressionGraphView.reset failed")

        # Reset PCR graph view if it has a reset/clear method
        if self.graph_drawer is not None:
            for method_name in ("reset", "clear", "clear_plot"):
                if hasattr(self.graph_drawer, method_name):
                    try:
                        getattr(self.graph_drawer, method_name)()
                    except Exception:
                        logger.exception("PCRGraphView.%s failed", method_name)
                    break

        # Plate widget reset if available
        if self.plate_widget is not None:
            for method_name in ("reset", "clear", "reset_state"):
                if hasattr(self.plate_widget, method_name):
                    try:
                        getattr(self.plate_widget, method_name)()
                    except Exception:
                        logger.exception("PCRPlateWidget.%s failed", method_name)
                    break

    # -------------------- Close / Shutdown --------------------
    def _on_close_requested(self) -> None:
        """
        Release-grade: prevent any post-close UI updates and shut down model threads safely.
        """
        if self._closing:
            return
        self._closing = True

        # Best effort disconnect to prevent callbacks after UI starts closing
        self._disconnect_model_signals_safely()

        try:
            self.model.shutdown()
        except Exception:
            logger.exception("Model shutdown failed")

    # -------------------- Handlers --------------------
    def handle_drop_result(self, success: bool, rdml_path: str, file_name: str, message: str) -> None:
        if self._closing:
            return

        self.view.set_dragdrop_label(message)

        if success:
            self.view.set_analyze_enabled(True)
            self.model.import_rdml(rdml_path)
            self.model.set_file_name_from_rdml(file_name)
            self.view.set_title_label(self.model.state.file_name)
        else:
            self.view.set_analyze_enabled(False)

    def _on_import_requested(self) -> None:
        if self._closing:
            return

        file_path, file_name = self.view.select_rdml_file_dialog()
        if not file_path or self.drag_drop_controller is None:
            return

        self.model.set_file_name_from_rdml(file_name)
        self.view.set_title_label(self.model.state.file_name)
        self.drag_drop_controller.manual_drop(file_path, file_name)

    def _on_export_requested(self) -> None:
        if self._closing:
            return
        if self.table_controller is None:
            return

        self.export_controller.export_table_view(
            self.table_controller.table_widget,
            file_name=self.model.state.file_name,
            options=ExportOptions(fmt="xlsx", preset="full", include_headers=True),
        )

    def _on_analyze_requested(self) -> None:
        if self._closing:
            return
        self.model.run_analysis()

    def _on_stats_toggled(self, checked: bool) -> None:
        if self._closing:
            return
        self.model.colored_box_controller.set_check_box_status(bool(checked))
        self.model.set_checkbox_status(bool(checked))

    def _validate_and_set_range(self, val: float, range_type: str) -> None:
        """
        Performance: avoid redundant sets (esp. slider/spinbox rapidly firing).
        """
        if self._closing:
            return
        if self.table_controller is None:
            return

        try:
            if range_type == "carrier":
                current = self.model.get_carrier_range()
                if abs(val - float(current)) < 1e-12:
                    return
                if val < self.model.get_uncertain_range():
                    self.model.set_carrier_range(val)
                    self.table_controller.set_carrier_range(val)
                else:
                    raise ValueError("Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır.")

            elif range_type == "uncertain":
                current = self.model.get_uncertain_range()
                if abs(val - float(current)) < 1e-12:
                    return
                if val > self.model.get_carrier_range():
                    self.model.set_uncertain_range(val)
                    self.table_controller.set_uncertain_range(val)
                else:
                    raise ValueError("Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır.")

        except ValueError as e:
            self.view.show_warning(str(e))
        except Exception:
            # Release-grade: never crash UI from range change.
            logger.exception("Range validation/set failed")
            self.view.show_warning("Aralık ayarlanırken beklenmeyen bir hata oluştu.")

    def _on_analysis_progress(self, percent: int, message: str) -> None:
        if self._closing:
            return
        # Optional: update statusbar/label if needed
        # self.view.ui.statusbar.showMessage(f"{message} ({percent}%)")
        pass

    def _on_async_analysis_finished(self, success: bool) -> None:
        """
        Keep this callback fast: update minimal required UI.
        """
        if self._closing:
            return

        if not success:
            self.view.show_warning("Analiz başarısız oldu.")
            return

        # Color calc
        try:
            self.model.colored_box_controller.define_box_color()
        except Exception:
            logger.exception("define_box_color failed")

        # Table + graph
        if self.table_controller is not None:
            try:
                self.table_controller.load_csv_to_table()
            except Exception:
                logger.exception("load_csv_to_table failed")

        # Avoid heavy copying if possible; but keep compatibility with current DataStore API.
        try:
            df = DataStore.get_df_copy()
        except Exception:
            logger.exception("DataStore.get_df_copy failed")
            df = None

        if self.regression_graph_view is not None and df is not None:
            try:
                self.regression_graph_view.update(df)
            except Exception:
                logger.exception("RegressionGraphView.update failed")

    def _on_analysis_summary_ready(self, summary) -> None:
        if self._closing:
            return
        try:
            self.view.update_summary_labels(summary)
        except Exception:
            logger.exception("update_summary_labels failed")
