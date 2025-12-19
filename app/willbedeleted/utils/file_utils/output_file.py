# app\willbedeleted\utils\file_utils\output_file.py


import pandas as pd
from PyQt5.QtCore import QStandardPaths, Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def export_table_to_excel_with_path(table_view, file_name):
    """
    Kullanıcıdan dosya yolu seçtirerek QTableView verilerini Excel'e kaydeder.
    """
    # Masaüstü yolu
    desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    initial_path = f"{desktop_path}/{file_name if file_name else 'exported_file.xlsx'}"
    
    # Dosya kaydetme dialogunu aç, file_name'i default isim olarak kullan
    file_path, _ = QFileDialog.getSaveFileName(
        None, "Excel Dosyasını Kaydet", initial_path, "Excel Files (*.xlsx)"
    )

    # Kullanıcı bir dosya seçtiyse devam et
    if file_path:
        model = table_view.model()
        if model is None:
            QMessageBox.warning(None, "Hata", "Tablo modeli boş!")
            return

        # Veriyi toplamak için
        rows = model.rowCount()
        columns = model.columnCount()
        data = []

        # Model verilerini oku
        for row in range(rows):
            row_data = []
            for column in range(columns):
                index = model.index(row, column)
                value = model.data(index)
                row_data.append(value)
            data.append(row_data)

        # Sütun başlıklarını al
        headers = [model.headerData(i, Qt.Horizontal) for i in range(columns)]
        df = pd.DataFrame(data, columns=headers)

        # Excel'e kaydet
        try:
            df.to_excel(file_path, index=False)
            QMessageBox.information(
                None, "Başarılı", f"Dosya başarıyla kaydedildi:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(None, "Hata", f"Dosya kaydedilirken hata oluştu:\n{e}")



