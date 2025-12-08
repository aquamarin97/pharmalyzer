import csv

import pandas as pd


class UtilsCSV:
    @staticmethod
    def write_csv(headers, rows, output_csv):
        """
        Verilen verileri bir CSV dosyasına yazar.

        Args:
            headers (list): CSV dosyasının başlıkları.
            rows (list): Her satırda bir sözlük bulunan veri listesi.
            output_csv (str): Yazılacak CSV dosyasının yolu.
        """
        with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row.get(header, "") for header in headers])

    @staticmethod
    def read_csv(input_file):
        """
        Verilen bir CSV dosyasını okur ve veriyi CSVManager'a aktarır.

        Args:
            input_file (str): Okunacak CSV dosyasının tam yolu.
        """
        if not input_file:
            raise ValueError("Geçersiz dosya yolu: None veya boş string.")

        try:
            # CSV dosyasını oku ve bir DataFrame oluştur
            df = pd.read_csv(input_file)

            # DataFrame boş mu kontrol et
            if df.empty:
                raise ValueError("CSV dosyası boş.")

            return df

        except FileNotFoundError:
            raise ValueError(f"CSV dosyası bulunamadı: {input_file}")
        except pd.errors.EmptyDataError:
            raise ValueError("CSV dosyası boş.")
        except Exception as e:
            raise ValueError(f"CSV okuma sırasında bir hata oluştu: {e}")


    def get_csv_value_with_well_no(well_no, column_name, csv_data):
        """
        CSV'de belirtilen kuyu numarasına (`well_no`) ve sütuna (`column_name`) göre değeri döndürür.
        """
        try:
            row = csv_data[csv_data["Kuyu No"] == well_no]
            if not row.empty:
                return row.iloc[0][column_name]
        except KeyError as e:
            print(f"CSV'de belirtilen sütun bulunamadı: {e}")
        return None
