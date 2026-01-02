# app\services\analysis_steps\csv_processor.py
# app/services/analysis_steps/csv_processor.py
from __future__ import annotations

import ast
import pandas as pd


class CSVProcessor:
    @staticmethod
    def process(df: pd.DataFrame | None = None) -> pd.DataFrame:
        if df is None:
            raise ValueError("CSVProcessor.process Pipeline tarafından df ile çağrılmalıdır.")
        if df.empty:
            raise ValueError("İşlenecek merkezi DataFrame mevcut değil veya boş.")
        return CSVProcessor.improved_preprocess(df)

    @staticmethod
    def improved_preprocess(df: pd.DataFrame) -> pd.DataFrame:
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
        df = df.drop(columns=[c for c in cols_to_clear if c in df.columns], errors="ignore")

        df = CSVProcessor.fill_missing_react_ids(df)

        df["FAM koordinat list"] = df.get("FAM koordinat list", "[]")
        df["HEX koordinat list"] = df.get("HEX koordinat list", "[]")

        df["FAM koordinat list"] = df["FAM koordinat list"].fillna("[]").astype(str)
        df["HEX koordinat list"] = df["HEX koordinat list"].fillna("[]").astype(str)

        fam_end = []
        hex_end = []

        for val in df["FAM koordinat list"].values:
            parsed = safe_literal_eval(val)
            fam_end.append(parsed[-1][-1] if parsed else None)

        for val in df["HEX koordinat list"].values:
            parsed = safe_literal_eval(val)
            hex_end.append(parsed[-1][-1] if parsed else None)

        df["fam_end_rfu"] = pd.to_numeric(pd.Series(fam_end), errors="coerce").fillna(0.0)
        df["hex_end_rfu"] = pd.to_numeric(pd.Series(hex_end), errors="coerce").fillna(0.0)
        df["rfu_diff"] = df["fam_end_rfu"] - df["hex_end_rfu"]

        df["FAM Ct"] = pd.to_numeric(df.get("FAM Ct"), errors="coerce")
        df["HEX Ct"] = pd.to_numeric(df.get("HEX Ct"), errors="coerce")
        df["Δ Ct"] = df["FAM Ct"] - df["HEX Ct"]

        df["Kuyu No"] = CSVProcessor.generate_kuyu_no(len(df))
        df = CSVProcessor.apply_conditions(df)
        return df

    @staticmethod
    def generate_kuyu_no(num_rows: int):
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
    def fill_missing_react_ids(df: pd.DataFrame) -> pd.DataFrame:
        if "React ID" not in df.columns:
            raise ValueError("'React ID' sütunu bulunamadı.")

        df["React ID"] = pd.to_numeric(df["React ID"], errors="coerce")
        current_ids = set(df["React ID"].dropna().astype(int).tolist())

        missing_ids = set(range(1, 97)) - current_ids
        if missing_ids:
            empty_rows = []
            for mid in sorted(missing_ids):
                row = {col: "" for col in df.columns}
                row["React ID"] = int(mid)
                empty_rows.append(row)
            df = pd.concat([df, pd.DataFrame(empty_rows)], ignore_index=True)

        return df.sort_values("React ID", kind="mergesort").reset_index(drop=True)

    @staticmethod
    def apply_conditions(df: pd.DataFrame) -> pd.DataFrame:
        df["Uyarı"] = None

        if "Barkot No" in df.columns:
            df.loc[(df["Barkot No"].isna() | (df["Barkot No"] == "")) & (df["Uyarı"].isnull()), "Uyarı"] = "Boş Kuyu"

        df.loc[
            (
                (df["FAM Ct"] > 30)
                | (df["HEX Ct"] > 30)
                | (df["FAM Ct"].isna())
                | (df["HEX Ct"].isna())
            )
            & (df["Uyarı"].isnull()),
            "Uyarı",
        ] = "Yetersiz DNA"

        df.loc[
            ((df["fam_end_rfu"] < 1200) | (df["hex_end_rfu"] < 1200)) & (df["Uyarı"].isnull()),
            "Uyarı",
        ] = "Düşük RFU Değeri"

        column_order = [
            "React ID", "Barkot No", "Hasta Adı", "Uyarı", "Kuyu No",
            "FAM Ct", "HEX Ct", "Δ Ct", "rfu_diff", "fam_end_rfu", "hex_end_rfu",
            "FAM koordinat list", "HEX koordinat list",
        ]
        return df[[c for c in column_order if c in df.columns]]
