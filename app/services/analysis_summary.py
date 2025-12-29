from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AnalysisSummary:
    analyzed_well_count: int = 0          # Boş Kuyu hariç toplam kuyu
    stats_source_count: int = 0           # Güvenli Bölge + (Uyarı null veya Düşük RFU) sayısı
    healthy_count: int = 0
    carrier_count: int = 0
    healthy_avg: float = 0.0
    carrier_avg: float = 0.0
    static_value: float = 0.0
    optimized_static_value: float = 0.0
