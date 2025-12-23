from __future__ import annotations

# Preset -> export edilecek kolon listesi.
# None: modelde/df'de ne varsa onu kullan
EXPORT_PRESETS: dict[str, list[str] | None] = {
    "full": None,

    # Örnek preset (istersen değiştir)
    "report_v1": [
        "Hasta No",
        "Barkot No",
        "Hasta Adı",
        "Nihai Sonuç",
        "Uyarı",
        "FAM Ct",
        "HEX Ct",
        "Δ Ct",
        "İstatistik Oranı",
        "Standart Oranı",
        "Regresyon",
    ],
}