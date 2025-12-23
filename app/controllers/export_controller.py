# app/controllers/export_controller.py

from __future__ import annotations

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from app.services.export.export_options import ExportOptions
from app.services.export.export_service import ExportService
from app.utils.qt_table_utils import table_view_to_dataframe


class ExportController:
    def __init__(self, export_service: ExportService | None = None):
        self.export_service = export_service or ExportService()

    def export_table_view(self, table_view, *, file_name: str, options: ExportOptions) -> None:
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)

        default_ext = "xlsx" if options.fmt == "xlsx" else "tsv"
        default_name = file_name if file_name else f"exported_file.{default_ext}"
        if not default_name.lower().endswith(f".{default_ext}"):
            default_name = f"{default_name}.{default_ext}"

        initial_path = f"{desktop_path}/{default_name}"

        file_filter = "Excel Files (*.xlsx)" if options.fmt == "xlsx" else "TSV Files (*.tsv)"
        file_path, _ = QFileDialog.getSaveFileName(None, "Dosyayı Kaydet", initial_path, file_filter)

        if not file_path:
            return

        try:
            df = table_view_to_dataframe(table_view, include_headers=True)  # df header'ı her zaman al
            self.export_service.export_dataframe(df, file_path, options)
            QMessageBox.information(None, "Başarılı", f"Dosya başarıyla kaydedildi:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(None, "Hata", f"Dosya kaydedilirken hata oluştu:\n{e}")
