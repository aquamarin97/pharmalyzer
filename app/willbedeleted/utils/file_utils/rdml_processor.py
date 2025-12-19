# app\willbedeleted\utils\file_utils\rdml_processor.py
import os
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from app.willbedeleted.managers.csv_manager import CSVManager
from app.willbedeleted.utils.file_utils.csv_utils import UtilsCSV
from app.willbedeleted.utils.file_utils.xml_utils import UtilsXML
from app.services.data_store import DataStore
from app.services.rdml_service import RDMLService

class UtilsRDMLProcessor:
    @staticmethod
    def process(file_path: str) -> None:
        """
        Parse RDML directly into the in-memory DataStore without creating CSV files.
        """
        try:
            df = RDMLService.rdml_to_dataframe(file_path)
            DataStore.set_df(df)
            CSVManager.update_csv_df()
        except Exception as e:
            raise ValueError(f"RDML işlenirken hata oluştu: {e}")

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
