# app\services\analysis_steps\configurate_result_csv.py

import string

from app.constants.table_config import CSV_FILE_HEADERS


class ConfigurateResultCSV:
    def __init__(self, checkbox_status: bool):
        self.df = None
        self.checkbox_status = checkbox_status

    def process(self, df=None):
        if df is None:
            raise ValueError("ConfigurateResultCSV.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek veri bulunamadı.")

        self.df = df.copy(deep=True)
        self.add_hasta_no()
        self.add_nihai_sonuc()
        self.sort_by_hasta_no()
        self.reorder_columns()
        return self.df
    
    def add_hasta_no(self):
        """Hasta No sütununu ekler."""
        # Tüm Kuyu No listesini oluştur
        kuyu_no_list = self.generate_kuyu_no(96)

        # Hasta No için bir harita oluştur (kolon öncelikli sıralama)
        hasta_no_map = {kuyu: idx + 1 for idx, kuyu in enumerate(kuyu_no_list)}

        # Hasta No sütununu ekle
        self.df["Hasta No"] = self.df["Kuyu No"].map(hasta_no_map)

    def generate_kuyu_no(self, num_rows):
        """Kuyu No sütunu için değerler oluşturur."""
        kuyu_no_list = []
        letters = string.ascii_uppercase[:8]  # A'dan H'ye kadar
        for number in range(1, 13):  # 1'den 12'ye kadar kolonlar
            for letter in letters:  # A'dan H'ye kadar satırlar
                kuyu_no_list.append(
                    f"{letter}{number:02}"
                )  # Sayıyı 2 basamaklı hale getir
                if len(kuyu_no_list) >= num_rows:
                    return kuyu_no_list
        return kuyu_no_list[:num_rows]

    def add_nihai_sonuc(self):
        """'Nihai Sonuç' sütununu ekler ve 'Yazılım Hasta Sonucu' değerlerini kopyalar."""
        if self.checkbox_status == True:
            if "Yazılım Hasta Sonucu" in self.df.columns:
                self.df["Nihai Sonuç"] = self.df["Yazılım Hasta Sonucu"]
            else:
                raise ValueError("'Yazılım Hasta Sonucu' sütunu mevcut değil.")
        else:
            if "Referans Hasta Sonucu" in self.df.columns:
                self.df["Nihai Sonuç"] = self.df["Referans Hasta Sonucu"]
            else:
                raise ValueError("'Referans Hasta Sonucu' sütunu mevcut değil.")

    def reorder_columns(self):
        """Kolon sırasını düzenler."""
        desired_order = CSV_FILE_HEADERS
        # Sadece mevcut kolonları al
        columns_to_include = [col for col in desired_order if col in self.df.columns]
        self.df = self.df[columns_to_include]

    def sort_by_hasta_no(self):
        """Hasta No sütununa göre sıralama yapar."""
        if "Hasta No" in self.df.columns:
            self.df = self.df.sort_values(by="Hasta No").reset_index(drop=True)
        else:
            raise ValueError("Hasta No sütunu mevcut değil.")
