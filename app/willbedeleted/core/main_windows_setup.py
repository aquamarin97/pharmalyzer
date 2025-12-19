# app\willbedeleted\core\main_windows_setup.py
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from config.config import TABLE_WIDGET_HEADERS
from controllers.regression_controller import RegressionGraphViewer
from controllers.table_controller import TableController
from handlers.analyze_button import AnalyzeButton
from handlers.colored_box_handler import ColoredBoxHandler
from handlers.drag_handler import DragDropHandler
from handlers.table_view_handler import TableViewHandler
from main_python import Ui_MainWindow
from managers.csv_manager import CSVManager
from managers.pcr_graph_manager import DataManager
from managers.table_manager import TableManager
from managers.well_manager import WellEditManager
from scripts.pcr_graph_drawer import GraphDrawer
from utils.file_utils.output_file import export_table_to_excel_with_path
from utils.file_utils.rdml_processor import UtilsRDMLProcessor
from widgets.table_view_widget import TableViewWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ColoredBoxHandler başlat
        self.colored_box_handler = ColoredBoxHandler()
        self.colored_box_handler.calculationCompleted.connect(
            self._update_colored_box_widgets
        )

        # AnalyzeButton başlat
        self.analyze_button = AnalyzeButton()
        self.analyze_button.analysisCompleted.connect(self.on_analysis_completed)
        self.ui.doubleSpinBox_tasiyici

        # DataManager sınıfını başlat (erken başlatma)
        self.data_manager = DataManager()

        # RegressionGraphManager başlat
        self.regression_graph_manager = RegressionGraphViewer(
            self.ui.regration_container
        )

        # Bileşenleri başlat
        self._initialize_components()

        # Sinyalleri bağla
        self._setup_signals()

    ### Yardımcı Fonksiyonlar ###

    # Bileşenlerin Başlatılması
    def initialize_components(self):
        self._initialize_components()

    # Drag drop alanına bırakılan dosyanın kontrolü eder ve analiz et butonunu aktive eder
    def handle_drop_result(self, success: bool, file_path: str, file_name: str):
        self._handle_drop_result(success, file_path)
        self.file_name = file_name.split(".rdml")[0]
        # QLabel güncellemesi
        self.ui.label_title.setText(
            self.file_name
        )  # QLabel üzerinde dosya adını göster

    def reset_data():
        CSVManager.clear_csv_file_path()
        CSVManager.clear_csv_df()

    # Well managerları oluşturur
    def setup_well_managers(self):
        self._setup_well_managers()

    # Table View Widget ile ilgili işlemleri gerçekleştirir.
    def setup_table_in_main_window(self):
        self._setup_table_in_main_window()

    ### Sinyaller ###

    def _setup_signals(self):
        """
        Uygulama içindeki sinyalleri bağlar.
        """
        self.ui.pushButton_analiz_et.clicked.connect(self._on_analyze_button_click)
        self.ui.checkBox_istatistik.stateChanged.connect(
            self._on_checkbox_state_changed
        )
        self.ui.pushButton_disaaktar.clicked.connect(
            lambda: export_table_to_excel_with_path(self.table_widget, self.file_name)
        )
        self.ui.pushButton_iceaktar.clicked.connect(self._select_rdml_file)
        # Spin box değişiminde kontrol ekle
        self.ui.doubleSpinBox_tasiyici.valueChanged.connect(
            lambda val: self._validate_and_set_range(val, "carrier")
        )
        self.ui.doubleSpinBox_belirsiz.valueChanged.connect(
            lambda val: self._validate_and_set_range(val, "uncertain")
        )
        # Yeni eklenen sinyal
        self.ui.pushButton_temizle.clicked.connect(self._initialize_components)

    def _validate_and_set_range(self, val, range_type):
        """
        Spin box değişikliklerinde taşıyıcı veya belirsiz aralığı kontrol eder.
        """
        try:
            if range_type == "carrier":
                if val < self.analyze_button.uncertain_range:
                    self.analyze_button.set_carrier_range(val)
                    self.table_controller.set_carrier_range(val)
                else:
                    raise ValueError(
                        "Taşıyıcı aralığı belirsiz aralığından düşük olmalıdır."
                    )
            elif range_type == "uncertain":
                if val > self.analyze_button.carrier_range:
                    self.analyze_button.set_uncertain_range(val)
                    self.table_controller.set_uncertain_range(val)
                else:
                    raise ValueError(
                        "Belirsiz aralığı taşıyıcı aralığından yüksek olmalıdır."
                    )
        except ValueError as e:
            ### Warnings
            self.show_warning(str(e))

    def show_warning(self, message):
        """PyQt5 ile uyarı mesajı gösterir."""
        app = QApplication.instance()  # PyQt5 uygulama instance kontrolü
        if not app:
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def on_analysis_completed(self):
        """
        AnalyzeButton sinyaline bağlanan slot.
        Analiz tamamlandığında tabloyu günceller.
        """
        self._on_analysis_completed()

    def _on_analyze_button_click(self):
        """
        Analiz işlemini başlatır ve hesaplama sonucunu tetikler.
        """
        success = self.analyze_button.analyze()
        if success:
            print("Analiz başarıyla tamamlandı.")

            self.colored_box_handler.define_box_color()  # Hesaplama işlemini doğrudan tetikle

        else:
            print("Analiz sırasında bir hata oluştu.")

    ### extacted methods ###
    def _setup_well_managers(self):
        """
        WellManager bileşenlerini başlatır ve varsayılan değerleri ayarlar.
        """

        # WellEditManager örneklerini oluştur
        self.referans_kuyu_manager = WellEditManager(
            line_edit=self.ui.lineEdit_standart_kuyu,
            default_value="F12",
            callback=self.analyze_button.set_referance_well,
        )
        self.homozigot_manager = WellEditManager(
            line_edit=self.ui.line_edit_saglikli_kontrol,
            default_value="F12",
            callback=self.colored_box_handler.set_homozigot_line_edit,
        )
        self.heterozigot_manager = WellEditManager(
            line_edit=self.ui.line_edit_tasiyici_kontrol,
            default_value="G12",
            callback=self.colored_box_handler.set_heterozigot_line_edit,
        )
        self.ntc_manager = WellEditManager(
            line_edit=self.ui.line_edit_NTC_kontrol,
            default_value="H12",
            callback=self.colored_box_handler.set_NTC_line_edit,
        )

    def _handle_drop_result(self, success, file_path):
        """
        Drag-drop işlemi tamamlandığında çağrılır.
        Dosya başarıyla bırakıldıysa analiz butonunu etkinleştirir.
        Args:
            success (bool): Drag-drop işleminin başarı durumu.
            file_path (str): Bırakılan dosyanın tam yolu.
        """
        if success:
            self.ui.pushButton_analiz_et.setEnabled(True)
            UtilsRDMLProcessor.process(
                file_path
            )  # RDML dosyasını işleyerek geçici CSV dosyasını oluştur
        else:
            self.ui.pushButton_analiz_et.setEnabled(False)

    ### --- Check Box
    def _on_checkbox_state_changed(self, state):
        """
        CheckBox durumunu yönetir.
        """
        is_checked = state == Qt.Checked
        self.colored_box_handler.set_check_box_status(is_checked)
        self.analyze_button.set_checkbox_status(is_checked)

    def _initialize_components(self):
        """
        Bileşenleri hazırlar ve başlangıç ayarlarını yapar.
        """
        # Grafik bileşenlerini başlat
        self._initialize_graphics()
        # Dosya ismi
        self.file_name = ""
        # Drag-drop işlemlerini ayarla
        self._setup_drag_and_drop()
        # Analiz butonu başlangıçta devre dışı
        self.ui.pushButton_analiz_et.setEnabled(False)
        # Tablo ve bileşenleri başlat
        self.setup_table_in_main_window()
        self.setup_well_managers()
        self.reset_box_colors()
        self.handle_drop_result(False, "", self.file_name)
        self.ui.label_drag_drop_area.setText("RDML dosyanızı sürükleyip bırakınız")
        # Regresyon grafiğini tamamen resetle
        self._reset_regression_graph()

    def _setup_table_in_main_window(self):
        """
        Ana pencerede tabloyu hazırlar ve gerekli kontrol sınıflarını bağlar.
        """
        original_widget = self.ui.table_widget_resulttable
        self.ui.table_widget_resulttable = TableViewWidget(original_widget)

        # Eski widget'ın yerine geçmesini sağlıyoruz
        self.ui.verticalLayout_3.replaceWidget(
            original_widget, self.ui.table_widget_resulttable
        )
        original_widget.deleteLater()
        self.ui.table_widget_resulttable.set_column_expansion_ratios(
            [2, 2, 2, 10, 5, 2, 2, 2, 3, 3, 3, 3]
        )

        headers = TABLE_WIDGET_HEADERS
        manager = TableManager(self.ui.table_widget_resulttable, headers)
        manager.create_empty_table()

        print(f"Başlangıç Tablo Modeli: {type(manager.model)}")

        controller = TableController(
            table_widget=self.ui.table_widget_resulttable,
            model=None,
        )

        handler = TableViewHandler(
            table_widget=self.ui.table_widget_resulttable,
            model=controller.model,
            data_manager=self.data_manager,
            graph_drawer=self.graph_drawer,
        )
        self.table_widget = self.ui.table_widget_resulttable
        self.table_manager = manager
        self.table_controller = controller
        self.table_handler = handler

    def _on_analyze_button_click(self):
        """
        Analiz işlemini başlatır.
        """
        success = self.analyze_button.analyze()
        if success:
            print("on_analyze_button_click : Analiz başarıyla tamamlandı.")
            self.colored_box_handler.define_box_color()
            self._on_analysis_completed()  # Tabloyu doğrudan güncelle
        else:
            print("Analiz sırasında bir hata oluştu.")

    def _on_analysis_completed(self):
        """
        Analiz tamamlandığında tabloyu günceller.
        """
        # CSV verisini yükle ve tablo modelini güncelle
        self.table_controller.load_csv()
        self.table_widget.setModel(self.table_controller.model)

        # TableViewHandler'e güncel modeli ata
        self.table_handler.model = self.table_controller.model
        self.table_handler.table_widget.setModel(self.table_handler.model)
        # print("Tablo modeli güncellendi.")

        # Regresyon grafiğini güncelle
        # print("Regresyon grafiği güncelleniyor...")
        self.regression_graph_manager.update_graph()

    def _setup_drag_and_drop(self):
        self.drag_drop_handler = DragDropHandler(self.ui.label_drag_drop_area)
        self.drag_drop_handler.setup()
        self.drag_drop_handler.dropCompleted.connect(self.handle_drop_result)

    def _initialize_colored_box_widgets(self):
        """
        Widget'ların başlangıç durumunu kırmızıya ayarlar.
        """
        for widget_name in [
            "saglikli_kontrol_color_box",
            "tasiyici_kontrol_color_box",
            "ntc_kontrol_color_box",
        ]:
            widget = getattr(self.ui, widget_name, None)
            if widget:
                print(f"{widget_name} bulundu ve görünür hale getiriliyor.")
                widget.setVisible(True)  # Widget'ı görünür yap
                widget.setStyleSheet(
                    "background-color: #FF0000; border: 2px solid #333333; border-radius: 5px;border-color: white"
                )  # Renk testi
            else:
                print(f"{widget_name} bulunamadı!")

    def _set_widget_color(self, widget, color_code):
        """
        Verilen widget'ın arka plan rengini ayarlar.

        Args:
            widget (QFrame): Rengi değiştirilecek widget.
            color_code (str): Hex renk kodu (örneğin, "#FF0000").
        """
        # Hata kontrolü ekleyin
        if not isinstance(color_code, str) or not color_code.startswith("#"):
            print(f"HATALI RENK KODU: {color_code}")  # Hatalı değerleri loglayın
            raise ValueError(f"Geçersiz renk kodu: {color_code}")

        widget.setStyleSheet(
            f"""
            background-color: {color_code};
            border: 2px solid #333333;
            border-radius: 5px;
        """
        )

    def _update_colored_box_widgets(self, result):
        """
        Hesaplama sonucu widget'ların rengini günceller.

        Args:
            result (list): Hesaplanan sonuçların listesi.
                        Sırasıyla [homozigot, heterozigot, NTC] sonuçlarını içerir.
        """
        if len(result) != 3:
            print("Hata: Sonuç listesi beklenenden farklı uzunlukta!")
            return

        # Renkleri belirle
        colors = ["#00FF00" if res else "#FF0000" for res in result]

        # Widget'ları güncelle
        self._set_widget_color(self.ui.saglikli_kontrol_color_box, colors[0])
        self._set_widget_color(self.ui.tasiyici_kontrol_color_box, colors[1])
        self._set_widget_color(self.ui.ntc_kontrol_color_box, colors[2])

        # print(
        #     f"Homozigot: {'Yeşil' if colors[0] == '#00FF00' else 'Kırmızı'}, "
        #     f"Heterozigot: {'Yeşil' if colors[1] == '#00FF00' else 'Kırmızı'}, "
        #     f"NTC: {'Yeşil' if colors[2] == '#00FF00' else 'Kırmızı'}"
        # )

    def reset_box_colors(self):
        init_color = "#87CEEB"
        # Widget'ları güncelle
        self._set_widget_color(self.ui.saglikli_kontrol_color_box, init_color)
        self._set_widget_color(self.ui.tasiyici_kontrol_color_box, init_color)
        self._set_widget_color(self.ui.ntc_kontrol_color_box, init_color)

    def on_table_click(self, index):
        """
        Tablo hücresine tıklandığında grafiği günceller.

        Args:
            index (QModelIndex): Tıklanan hücrenin modeli.
        """
        try:
            # Satır numarasını al
            row = index.row()

            # Hasta numarasını al ve int'e dönüştür
            patient_no = self.table_handler.get_patient_no(row)
            patient_no = int(patient_no)  # Eğer tipi farklıysa int'e dönüştür

            print(f"Tıklanan Hasta No: {patient_no}")

            # FAM ve HEX verilerini al
            data = self.data_manager.get_row_by_patient_no(patient_no)
            fam_coords = data["FAM"]
            hex_coords = data["HEX"]

            # GraphDrawer'a başlığı ilet
            self.graph_drawer.set_title(f"Hasta {patient_no}")
            self.graph_drawer.animate_graph(fam_coords, hex_coords)
        except Exception as e:
            print(f"Tablo tıklama işlenirken hata: {e}")

    def _initialize_graphics(self):
        """
        GraphDrawer'ı pcr_graph widget'ına entegre eder.
        Mevcut bir GraphDrawer varsa kaldırır ve yenisini oluşturur.
        """
        # Eğer mevcutsa, varolan GraphDrawer'ı kaldır
        if hasattr(self, "graph_drawer") and self.graph_drawer is not None:
            self.graph_drawer.deleteLater()
            self.graph_drawer = None

        # Mevcut layout'u kontrol et
        layout = self.ui.PCR_graph_container.layout()

        # Eğer layout yoksa yeni oluştur
        if layout is None:
            layout = QtWidgets.QVBoxLayout(self.ui.PCR_graph_container)
            self.ui.PCR_graph_container.setLayout(layout)

        # Layout içindeki eski widget'ları temizle
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        # Yeni GraphDrawer oluştur ve ekle
        self.graph_drawer = GraphDrawer(parent=self.ui.PCR_graph_container)
        layout.addWidget(self.graph_drawer)
        layout.setContentsMargins(10, 10, 10, 10)

    def _select_rdml_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "RDML Dosyası Seç",
            "",
            "RDML Dosyaları (*.rdml);;Tüm Dosyalar (*)",
            options=options,
        )

        if file_path:
            self.file_name = file_path.split("/")[-1].split(".rdml")[0]
            self.ui.label_title.setText(self.file_name)
            file_name = file_path.split("/")[-1]

            # _drop_event doğrudan tetikleniyor
            self.drag_drop_handler._drop_event_manual(file_path, file_name)

    def _reset_regression_graph(self):
        """
        Regresyon grafiğini baştan başlatır.
        """
        # Eski QWebEngineView'i kaldır ve yeniden oluştur
        if self.regression_graph_manager.web_view:
            self.regression_graph_manager.web_view.deleteLater()
            self.regression_graph_manager.web_view = None
            print("Eski grafik temizlendi.")

        # Regresyon grafiğini sıfırla
        self.regression_graph_manager.reset_regression_graph()
