from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AnalysisSummary:
    analyzed_well_count: int = 0          # "Boş Kuyu" hariç toplam kuyu (total sample)
    safezone_count: int = 0               # Regresyon == "Güvenli Bölge" sayısı
    riskyarea_count: int = 0              # Regresyon == "Riskli Alan" sayısı

    healthy_count: int = 0                # Final sınıflandırma sonucunda
    carrier_count: int = 0
    uncertain_count: int = 0

    healthy_avg: float = 0.0              # sadece Güvenli Bölge ve 0.8-1.2 arası İstatistik/Standart Oranı üzerinden
    std: float = 0.0
    cv: float = 0.0                       # cv = std / healthy_avg (healthy_avg == 0 ise 0)
