import threading

import pandas as pd

from app.willbedeleted.utils.file_utils.csv_utils import UtilsCSV


class CSVManager:
    """
    Geçici dosya yollarını ve merkezi veriyi yöneten statik sınıf.
    """

    _csv_file_path = None  # Sınıf düzeyinde bir değişken
    _csv_df = None  # DataFrame'in merkezi değişkeni
    _lock = threading.Lock()  # Çoklu iş parçacığı güvenliği için kilit

    @staticmethod
    def set_csv_file_path(file_path: str):
        """
        Geçici CSV dosyasının yolunu ayarlar.

        Args:
            file_path (str): Geçici CSV dosyasının tam yolu.
        """
        CSVManager._csv_file_path = file_path

    @staticmethod
    def get_csv_file_path() -> str:
        """
        Geçici CSV dosyasının yolunu döndürür.

        Returns:
            str: Geçici CSV dosyasının tam yolu.
        """

        return CSVManager._csv_file_path

    @staticmethod
    def clear_csv_file_path():
        """
        Geçici CSV dosya yolunu temizler.
        """
        CSVManager._csv_file_path = None

    @staticmethod
    def set_csv_df(df):
        """
        Geçici bir DataFrame bilgisini ayarlar.

        Args:
            df (pd.DataFrame): Ayarlanacak DataFrame.
        """
        with CSVManager._lock:  # Çoklu iş parçacığında güvenli işlem
            CSVManager._csv_df = df
        # print("DataFrame merkezi olarak ayarlandı.")

    @staticmethod
    def get_csv_df() -> pd.DataFrame:
        """
        Merkezi DataFrame bilgisini döndürür.

        Returns:
            pd.DataFrame: Merkezi olarak tutulan DataFrame.
        """

        if CSVManager._csv_df is None:
            raise ValueError("Merkezi DataFrame ayarlanmamış.")
        return CSVManager._csv_df

    @staticmethod
    def clear_csv_df():
        """
        Merkezi DataFrame bilgisini temizler.
        """
        with CSVManager._lock:
            CSVManager._csv_df = None
        print("Merkezi DataFrame temizlendi.")

    @staticmethod
    def update_csv_df():
        """_dataframi günceller_"""
        df = UtilsCSV.read_csv(CSVManager._csv_file_path)
        # DataFrame'i CSVManager'a aktar
        CSVManager.set_csv_df(df)

        # print("CSV verisi başarıyla güncellendi.")
