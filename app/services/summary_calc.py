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
    use_without_reference=True  => CalculateWithoutReference çıktısı beklenir:
        - final label kolonu: "Yazılım Hasta Sonucu"
        - oran kolonu: "İstatistik Oranı"
    use_without_reference=False => CalculateWithReferance çıktısı beklenir:
        - final label kolonu: "Referans Hasta Sonucu"
        - oran kolonu: "Standart Oranı"
    Ortak:
        - "Uyarı", "Regresyon" kolonları mevcut.
    """

    if df is None or df.empty:
        return AnalysisSummary()

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

    # healthy_avg / std / cv:
    # sadece (Regresyon == Güvenli Bölge) ve oran 0.8-1.2 arasında olanlar
    if "Regresyon" in df.columns and ratio_col in df.columns:
        mask = (df["Regresyon"] == "Güvenli Bölge") & (df[ratio_col].between(0.8, 1.2))
        series = pd.to_numeric(df.loc[mask, ratio_col], errors="coerce").dropna()
    else:
        series = pd.Series(dtype=float)

    if series.empty:
        healthy_avg = 0.0
        std = 0.0
        cv = 0.0
    else:
        healthy_avg = float(series.mean())
        std = float(series.std(ddof=0))  # populasyon std; istersen ddof=1 yapabilirsin ama sabit seç
        cv = float(std / healthy_avg) if healthy_avg != 0.0 else 0.0

    return AnalysisSummary(
        analyzed_well_count=analyzed_well_count,
        safezone_count=safezone_count,
        riskyarea_count=riskyarea_count,
        healthy_count=healthy_count,
        carrier_count=carrier_count,
        uncertain_count=uncertain_count,
        healthy_avg=healthy_avg,
        std=std,
        cv=cv,
    )