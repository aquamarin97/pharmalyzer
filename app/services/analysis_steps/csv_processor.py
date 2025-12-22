# app\willbedeleted\scripts\csv_processor\csv_processor.py

import pandas as pd


class CSVProcessor:

    @staticmethod
    def process(df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Tüm işlemleri sırayla yapar ve DataFrame döndürür."""
        try:
            if df is None:
                raise ValueError("CSVProcessor.process Pipeline tarafından df ile çağrılmalıdır.")

            if df.empty:
                raise ValueError("İşlenecek merkezi DataFrame mevcut değil veya boş.")

            processed_df = CSVProcessor.improved_preprocess(df)
            return processed_df
        
        except ValueError as e:
            print(f"İşleme sırasında hata: {e}")
            raise
        except Exception as e:
            print(f"Bilinmeyen hata: {e}")
            raise

    @staticmethod
    def improved_preprocess(df):
        import ast

        def safe_literal_eval(val):
            if isinstance(val, str):
                try:
                    return ast.literal_eval(val)
                except Exception:
                    return None
            return None

        cols_to_clear = [
            "Δ Ct", "Δ_Δ Ct", "İstatistik Oranı", "Yazılım Hasta Sonucu",
            "rfu_diff", "fam_end_rfu", "hex_end_rfu", "Kuyu No", "Cluster"
        ]
        df = df.drop(columns=[col for col in cols_to_clear if col in df.columns], errors='ignore')

        df = CSVProcessor.fill_missing_react_ids(df)

        if "FAM koordinat list" not in df.columns:
            df["FAM koordinat list"] = "[]"
        if "HEX koordinat list" not in df.columns:
            df["HEX koordinat list"] = "[]"

        df["FAM koordinat list"] = df["FAM koordinat list"].fillna("[]").astype(str)
        df["HEX koordinat list"] = df["HEX koordinat list"].fillna("[]").astype(str)

        fam_end_rfu_list = []
        hex_end_rfu_list = []

        for val in df["FAM koordinat list"]:
            parsed = safe_literal_eval(val)
            if parsed:
                fam_end_rfu_list.append(parsed[-1][-1])
            else:
                fam_end_rfu_list.append("")

        for val in df["HEX koordinat list"]:
            parsed = safe_literal_eval(val)
            if parsed:
                hex_end_rfu_list.append(parsed[-1][-1])
            else:
                hex_end_rfu_list.append("")

        df["fam_end_rfu"] = fam_end_rfu_list
        df["hex_end_rfu"] = hex_end_rfu_list

        df["rfu_diff"] = df["fam_end_rfu"].apply(lambda x: float(x) if x != "" else 0) - \
                         df["hex_end_rfu"].apply(lambda x: float(x) if x != "" else 0)

        df["FAM Ct"] = pd.to_numeric(df["FAM Ct"], errors="coerce")
        df["HEX Ct"] = pd.to_numeric(df["HEX Ct"], errors="coerce")
        df["Δ Ct"] = df["FAM Ct"] - df["HEX Ct"]

        df["Kuyu No"] = CSVProcessor.generate_kuyu_no(len(df))

        df = CSVProcessor.apply_conditions(df)

        return df

    @staticmethod
    def generate_kuyu_no(num_rows):
        import string
        kuyu_no_list = []
        letters = string.ascii_uppercase[:8]
        for letter in letters:
            for number in range(1, 13):
                kuyu_no_list.append(f"{letter}{number:02}")
                if len(kuyu_no_list) >= num_rows:
                    return kuyu_no_list
        return kuyu_no_list[:num_rows]

    @staticmethod
    def fill_missing_react_ids(df):
        # React ID her zaman 1..96 numeric olmalı; karışık tipleri temizle
        df["React ID"] = pd.to_numeric(df["React ID"], errors="coerce")

        # Mevcut ID’leri al (NaN hariç), int set’e çevir
        current_ids = set(df["React ID"].dropna().astype(int).tolist())

        all_ids = set(range(1, 97))
        missing_ids = all_ids - current_ids

        # Eksik ID’ler için boş satır ekle
        for missing_id in sorted(missing_ids):
            empty_row = {col: "" for col in df.columns}
            empty_row["React ID"] = int(missing_id)
            df = pd.concat([df, pd.DataFrame([empty_row])], ignore_index=True)

        # Sıralama artık güvenli (numeric)
        df = df.sort_values("React ID", kind="mergesort").reset_index(drop=True)
        return df
    @staticmethod
    def apply_conditions(df):
        df["Uyarı"] = None

        df.loc[
            (df["Barkot No"].isna() | (df["Barkot No"] == "")) & (df["Uyarı"].isnull()),
            "Uyarı"
        ] = "Boş Kuyu"

        df.loc[
            (
                (df["FAM Ct"] > 40)
                | (df["HEX Ct"] > 40)
                | (df["FAM Ct"].isna())
                | (df["HEX Ct"].isna())
            )
            & (df["Uyarı"].isnull()),
            "Uyarı"
        ] = "Yetersiz DNA"

        df["fam_end_rfu"] = df["fam_end_rfu"].apply(lambda x: float(x) if x not in [None, ""] else 0)
        df["hex_end_rfu"] = df["hex_end_rfu"].apply(lambda x: float(x) if x not in [None, ""] else 0)

        df.loc[
            (((df["fam_end_rfu"]) < 1200) | (df["hex_end_rfu"] < 1200)) & (df["Uyarı"].isnull()),
            "Uyarı"
        ] = "Düşük RFU Değeri"
        
        column_order = [
            "React ID", "Barkot No", "Hasta Adı", "Uyarı", "Kuyu No",
            "FAM Ct", "HEX Ct", "Δ Ct", "rfu_diff", "fam_end_rfu", "hex_end_rfu",
            "FAM koordinat list", "HEX koordinat list"
        ]
        df = df[[col for col in column_order if col in df.columns]]
        
        return df
