import os
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from app.willbedeleted.managers.csv_manager import CSVManager
from app.willbedeleted.utils.file_utils.csv_utils import UtilsCSV
from app.willbedeleted.utils.file_utils.xml_utils import UtilsXML


class UtilsRDMLProcessor:
    @staticmethod
    def process(file_path: str) -> str:
        """
        RDML dosyasını geçici bir CSV dosyasına dönüştürür.
        Çıktı, geçici dosya dizininde 'tmp.csv' olarak kaydedilir.
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {"rdml": "http://www.rdml.org"}

            headers = [
                "React ID",
                "Barkot No",
                "Hasta Adı",
                "FAM Ct",
                "HEX Ct",
                "FAM koordinat list",
                "HEX koordinat list",
            ]

            # Geçici bir dosya yolu oluştur
            temp_dir = tempfile.mkdtemp()
            output_csv = os.path.join(temp_dir, "tmp.csv")

            fam_run = UtilsXML.extract_run(root, "Amp Step 3_FAM", namespace)
            hex_run = UtilsXML.extract_run(root, "Amp Step 3_HEX", namespace)

            rows = []
            for fam_react in fam_run.findall("rdml:react", namespaces=namespace):
                # FAM'den bilgileri al
                row = UtilsXML.parse_react_data(fam_react, namespace, run_id="FAM")

                # HEX'deki eşleşen React ID'yi al
                hex_react = hex_run.find(f"rdml:react[@id='{row['React ID']}']", namespaces=namespace)
                if hex_react:
                    hex_row = UtilsXML.parse_react_data(hex_react, namespace, run_id="HEX")
                    # HEX'e ait alanları güncelle
                    row["HEX Ct"] = hex_row["HEX Ct"]
                    row["HEX koordinat list"] = hex_row["HEX koordinat list"]
                else:
                    # HEX verisi yoksa varsayılan değerleri ekle
                    row["HEX Ct"] = ""
                    row["HEX koordinat list"] = ""

                rows.append(row)


            UtilsCSV.write_csv(headers, rows, output_csv)

            # CSV dosya yolunu central bilgiye kayıt ediyoruz.
            CSVManager.set_csv_file_path(output_csv)

            return
        except ET.ParseError as e:
            raise ValueError(f"XML dosyası çözümlenirken bir hata oluştu: {e}")
        except Exception as e:
            raise ValueError(f"Hata: {e}")

    @staticmethod
    def take_rdml_file_path(file_path: str):
        """
        Verilen RDML dosyasını (ZIP formatında) işleyerek içindeki ilk XML dosyasını çıkarır
        ve geçici bir klasöre kaydeder.
        """
        try:
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                xml_file = next(
                    (name for name in zip_ref.namelist() if name.endswith(".xml")), None
                )
                if xml_file:
                    zip_ref.extract(xml_file, temp_dir)
                    return True, os.path.join(temp_dir, xml_file)
            return False, ""
        except zipfile.BadZipFile:
            return False, "Geçersiz RDML dosyası."
        except Exception as e:
            return False, str(e)
