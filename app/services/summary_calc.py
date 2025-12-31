# app\services\summary_calc.py
from __future__ import annotations
import numpy as np
import pandas as pd
from app.services.analysis_summary import AnalysisSummary

def build_summary_from_df(
    df: pd.DataFrame,
    *,
    use_without_reference: bool,
) -> AnalysisSummary:
    """
    CV: %x.xx formatında,
    Ortalama ve Std: .2f formatında,
    Tüm değerlerin önünde ":" olacak şekilde güncellendi.
    """

    if df is None or df.empty:
        return AnalysisSummary()

    # Temel sayımlar
    analyzed_well_count = int((df["Uyarı"] != "Boş Kuyu").sum()) if "Uyarı" in df.columns else int(len(df))
    safezone_count = int((df.get("Regresyon") == "Güvenli Bölge").sum()) if "Regresyon" in df.columns else 0
    riskyarea_count = int((df.get("Regresyon") == "Riskli Alan").sum()) if "Regresyon" in df.columns else 0

    if use_without_reference:
        result_col = "Yazılım Hasta Sonucu"
        ratio_col = "İstatistik Oranı"
    else:
        result_col = "Referans Hasta Sonucu"
        ratio_col = "Standart Oranı"

    healthy_count = int((df.get(result_col) == "Sağlıklı").sum())
    carrier_count = int((df.get(result_col) == "Taşıyıcı").sum())
    uncertain_count = int((df.get(result_col) == "Belirsiz").sum())

    # İstatistiksel hesaplamalar
    if "Regresyon" in df.columns and ratio_col in df.columns:
        mask = (df["Regresyon"] == "Güvenli Bölge") & (df[ratio_col].between(0.70, 1.3)) # (df["Nihai Sonuç"] == "Sağlıklı")
        series = pd.to_numeric(df.loc[mask, ratio_col], errors="coerce").dropna()
    else:
        series = pd.Series(dtype=float)

    if series.empty:
        h_avg_val, std_val, cv_val = 0.0, 0.0, 0.0
    else:
        h_avg_val = float(series.mean())
        std_val = float(series.std(ddof=0))
        cv_val = float((std_val / h_avg_val) * 100) if h_avg_val != 0 else 0.0

    # Formatlama İşlemleri
# --- YENİ EKLENEN LOGLAMA BÖLÜMÜ ---
    print("-" * 30)
    print("DEBUG: Yuvarlanmadan Önceki Ham Değerler")
    print(f"Ham Ortalama (h_avg_val): {h_avg_val}")
    print(f"Ham Std Sapma (std_val): {std_val}")
    print(f"Ham CV (%): {cv_val}")
    print("-" * 30)
    # -----------------------------------
    # Değerlerin başına ":" ekleyerek ve istenen basamak hassasiyetiyle stringe çeviriyoruz
    return AnalysisSummary(
        analyzed_well_count=f": {analyzed_well_count}",
        safezone_count=f": {safezone_count}",
        riskyarea_count=f": {riskyarea_count}",
        healthy_count=f": {healthy_count}",
        carrier_count=f": {carrier_count}",
        uncertain_count=f": {uncertain_count}",
        healthy_avg=f": {h_avg_val:.3f}",
        std=f": {std_val:.3f}",
        cv=f": {cv_val:.2f}"
    )