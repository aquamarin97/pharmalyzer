# app\willbedeleted\config\config.py
##### --- TABLO AYARLARI --- #####
from PyQt5.QtGui import QColor

DROPDOWN_COLUMN = "Nihai Sonuç"
DROPDOWN_OPTIONS = ["Sağlıklı", "Taşıyıcı", "Belirsiz", "Test Tekrarı", "Yeni Numune"]
ITEM_STYLES = {
    DROPDOWN_OPTIONS[0]: QColor("#81B563"),  # Sağlıklı - Pastel Yeşil
    DROPDOWN_OPTIONS[1]: QColor("#FFE599"),  # Taşıyıcı - Pastel Sarı
    DROPDOWN_OPTIONS[2]: QColor("#E87E2C"),  # Belirsiz - Sıcak Turuncu
    DROPDOWN_OPTIONS[3]: QColor("#B4A7D6"),  # Test Tekrarı - Pastel Mor
    DROPDOWN_OPTIONS[4]: QColor("#FF6B6B"),  # Yeni Numune - Canlı Kırmızı
}

ROUND_COLUMNS = {
    "FAM Ct": 2,
    "HEX Ct": 2,
    "Δ Ct": 2,
    "İstatistik Oranı": 4,
    "Standart Oranı": 4,
}
CSV_FILE_HEADERS = [
    "React ID",
    "Barkot No",
    "Hasta Adı",
    "Uyarı",
    "Kuyu No",
    "Hasta No",
    "İstatistik Oranı",
    "Yazılım Hasta Sonucu",
    "Nihai Sonuç",
    "Standart Oranı",
    "Referans Hasta Sonucu",
    "Regresyon",
    "FAM Ct",
    "HEX Ct",
    "Δ Ct",
    "Δ_Δ Ct",
    "rfu_diff",
    "fam_end_rfu",
    "hex_end_rfu",
    "FAM koordinat list",
    "HEX koordinat list",
]
TABLE_WIDGET_HEADERS = [
    "Hasta No",
    "Kuyu No",
    "Barkot No",
    "Hasta Adı",
    "Uyarı",
    "FAM Ct",
    "HEX Ct",
    "Δ Ct",
    "Regresyon",
    "İstatistik Oranı",
    "Standart Oranı",
    "Nihai Sonuç",
]

DEFAULT_WELL_VALUES = {
    "homozigot_kontrol": "F12",
    "hoterozigot_kontrol": "G12",
    "ntc_kontrol": "H12",
}

COLUMN_SOFTWARE_RESULT = "İstatistik Oranı"
COLUMN_REFERENCE_RESULT = "Standart Oranı"
COLUMN_WARNING = "Uyarı"
