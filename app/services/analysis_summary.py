# app\services\analysis_summary.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AnalysisSummary:
    analyzed_well_count: str = ""          # "Boş Kuyu" hariç toplam kuyu (total sample)
    safezone_count: str = ""               # Regresyon == "Güvenli Bölge" sayısı
    riskyarea_count: str = ""              # Regresyon == "Riskli Alan" sayısı

    healthy_count: str = ""                # Final sınıflandırma sonucunda
    carrier_count: str = ""
    uncertain_count: str = ""

    healthy_avg: str = ""              # sadece Güvenli Bölge ve 0.8-1.2 arası İstatistik/Standart Oranı üzerinden
    std: str = ""
    cv: str = ""                       # cv = std / healthy_avg (healthy_avg == 0 ise 0)
