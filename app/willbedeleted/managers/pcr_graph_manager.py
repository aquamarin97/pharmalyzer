from app.willbedeleted.managers.csv_manager import CSVManager


class DataManager:
    def __init__(self):
        """
        DataManager sınıfı, dinamik olarak CSV dosyasını atayarak çalışır.
        """
        self.data = None

    def get_row_by_patient_no(self, patient_no):
        """
        Hasta No sütununa göre ilgili satırı getirir.

        Args:
            patient_no (str veya int): Aranacak Hasta No.

        Returns:
            dict: FAM ve HEX koordinat listelerini içeren bir sözlük.
        """
        self.data = CSVManager.get_csv_df()
        if self.data is None:
            raise ValueError("CSV dosyası yüklenmedi.")

        # Debug için mevcut Hasta Numaralarını yazdır
        # print("Mevcut Hasta Numaraları:", self.data["Hasta No"].tolist())
        # print(f"Aranan Hasta Numarası: {patient_no}")

        # Hasta No'yu karşılaştırırken tipi dönüştür
        patient_no = float(patient_no)  # Gelen hasta numarasını int'e çevir
        row = self.data[self.data["Hasta No"] == patient_no]

        if row.empty:
            raise ValueError(f"Hasta No '{patient_no}' için bir kayıt bulunamadı.")

        # Koordinat listelerini al
        try:
            fam_coords = eval(row.iloc[0]["FAM koordinat list"])
            hex_coords = eval(row.iloc[0]["HEX koordinat list"])
        except Exception as e:
            raise ValueError(f"Koordinat listesi dönüştürülürken hata: {e}")

        return {"FAM": fam_coords, "HEX": hex_coords}
