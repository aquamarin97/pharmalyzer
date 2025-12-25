# app\constants\app_styles.py
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

# --- FONT STİLLERİ ---
class FONT_STYLES:
    # Splash Ekranı Fontları
    SPLASH_APP_NAME = QFont("Arial", 36, QFont.Bold)
    SPLASH_BRAND_NAME = QFont("Arial", 28, QFont.Bold)
    SPLASH_MESSAGE = QFont("Arial", 12) # Yükleniyor mesajı için

# --- RENK SABİTLERİ ---
class COLOR_STYLES:
    BRAND_COLOR = QColor(36, 69, 132)
    PRIMARY_TEXT = Qt.black
    SPLASH_BG = Qt.lightGray

    # Plot theme (tek kaynak)
    PLOT_BG_HEX = "#0B0F14"

    # Arka planla uyumlu, “subtle” grid
    PLOT_GRID_HEX = "#2A3441"

    # Typography (off-white)
    PLOT_TEXT_HEX = "#D7DEE9"
    PLOT_TITLE_HEX = "#EEF2F7"

    # Legend frame
    PLOT_LEGEND_BG_HEX = "#141A22"

