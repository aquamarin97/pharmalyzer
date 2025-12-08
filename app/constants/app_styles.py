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
    BRAND_COLOR = QColor(36, 69, 132) # Marka rengi
    PRIMARY_TEXT = Qt.black
    SPLASH_BG = Qt.lightGray

