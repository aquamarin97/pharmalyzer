# app\utils\validators\data_Validor.py
# app\willbedeleted\utils\validators\data_Validor.py
class DataValidator:
    @staticmethod
    def validate_columns(df, required_columns):
        """
        Verilen DataFrame'de gerekli sütunların olup olmadığını kontrol eder.

        Args:
            df (pd.DataFrame): Kontrol edilecek DataFrame.
            required_columns (list): Gerekli sütun adları.

        Raises:
            ValueError: Eksik sütunlar olduğunda.
        """
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"{column} sütunu eksik.")

