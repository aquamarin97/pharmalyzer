# app/services/pcr_data_service.py
from __future__ import annotations

import ast
from typing import Any

import pandas as pd

from app.services.data_store import DataStore


class PCRDataService:
    """
    Grafik için gerekli koordinat verilerini DataStore'dan okur.
    """

    @staticmethod
    def get_row_by_patient_no(patient_no: Any) -> dict:
        df = DataStore.get_df_copy()
        if df is None or df.empty:
            raise ValueError("DataStore boş. Veri yüklenmedi.")

        if "Hasta No" not in df.columns:
            raise ValueError("DataFrame içinde 'Hasta No' sütunu yok.")
        if "FAM koordinat list" not in df.columns or "HEX koordinat list" not in df.columns:
            raise ValueError("Koordinat sütunları eksik (FAM/HEX koordinat list).")

        # Hasta No'yu int'e normalize et (1..96 bekleniyor gibi)
        try:
            pn = int(float(patient_no))
        except (TypeError, ValueError):
            raise ValueError(f"Geçersiz Hasta No: {patient_no}")

        # df tarafını da numeric'e çek (eşleşme garanti)
        hasta_no_series = pd.to_numeric(df["Hasta No"], errors="coerce").astype("Int64")
        row = df[hasta_no_series == pn]

        if row.empty:
            raise ValueError(f"Hasta No '{pn}' için bir kayıt bulunamadı.")

        fam_raw = row.iloc[0]["FAM koordinat list"]
        hex_raw = row.iloc[0]["HEX koordinat list"]

        try:
            fam_coords = ast.literal_eval(fam_raw) if isinstance(fam_raw, str) else fam_raw
            hex_coords = ast.literal_eval(hex_raw) if isinstance(hex_raw, str) else hex_raw
        except Exception as e:
            raise ValueError(f"Koordinat listesi parse edilemedi: {e}")

        # En azından liste bekliyoruz
        if not isinstance(fam_coords, list) or not isinstance(hex_coords, list):
            raise ValueError("Koordinat listeleri list formatında değil.")

        return {"FAM": fam_coords, "HEX": hex_coords}
