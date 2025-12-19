# app\views\main_view.py
# main_view.py
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog
from PyQt5 import QtWidgets
from app.views.ui.ui import Ui_MainWindow

# UI importunu projene göre düzelt


class MainView(QMainWindow):
    """
    Sadece UI kurar ve UI günceller.
    Sinyal/iş mantığı Controller'da.
    """
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.controller = None
    # ---- UI helpers ----
    def set_title_label(self, text: str):
        self.ui.label_title.setText(text)

    def set_dragdrop_label(self, text: str):
        self.ui.label_drag_drop_area.setText(text)

    def set_analyze_enabled(self, enabled: bool):
        self.ui.pushButton_analiz_et.setEnabled(enabled)

    def show_warning(self, message: str):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Hata")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_() # Mevcut QApplication'ı kullanır

    # ---- Colored boxes ----
    def set_widget_color(self, widget, color_code: str):
        if not isinstance(color_code, str) or not color_code.startswith("#"):
            raise ValueError(f"Geçersiz renk kodu: {color_code}")

        widget.setStyleSheet(
            f"""
            background-color: {color_code};
            border: 2px solid #333333;
            border-radius: 5px;
        """
        )

    def reset_box_colors(self):
        init_color = "#87CEEB"
        self.set_widget_color(self.ui.saglikli_kontrol_color_box, init_color)
        self.set_widget_color(self.ui.tasiyici_kontrol_color_box, init_color)
        self.set_widget_color(self.ui.ntc_kontrol_color_box, init_color)

    def update_colored_box_widgets(self, result: list):
        if len(result) != 3:
            print("Hata: Sonuç listesi beklenenden farklı uzunlukta!")
            return
        colors = ["#00FF00" if res else "#FF0000" for res in result]
        self.set_widget_color(self.ui.saglikli_kontrol_color_box, colors[0])
        self.set_widget_color(self.ui.tasiyici_kontrol_color_box, colors[1])
        self.set_widget_color(self.ui.ntc_kontrol_color_box, colors[2])

    # ---- Graph container setup ----
    def ensure_graph_drawer(self):
        """
        pcr graph alanına GraphDrawer yerleştirmek için container hazırlar.
        GraphDrawer instance'ı controller/model tarafından yaratılıp set edilebilir.
        """
        layout = self.ui.PCR_graph_container.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(self.ui.PCR_graph_container)
            self.ui.PCR_graph_container.setLayout(layout)

        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        layout.setContentsMargins(10, 10, 10, 10)
        return layout

    def select_rdml_file_dialog(self) -> tuple[str, str]:
        """
        Controller çağırır, View sadece dialog döndürür.
        Returns: (file_path, file_name)
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "RDML Dosyası Seç",
            "",
            "RDML Dosyaları (*.rdml);;Tüm Dosyalar (*)",
            options=options,
        )
        if not file_path:
            return "", ""
        file_name = file_path.split("/")[-1]
        return file_path, file_name
