# app\constants\asset_paths.py
import os

# Uygulamanın ana dizinini (projeye göre değişebilir) veya 
# statik varlıkların bulunduğu temel klasörü tanımlayın.
BASE_ASSETS_DIR = "assets"

# Varlık yollarını gruplayan bir sınıf
class ICON_PATHS:
    """Tüm ikon dosyalarının yolları."""
    APP_ICON_ICO = os.path.join(BASE_ASSETS_DIR, "appicon.ico")

class IMAGE_PATHS:
    """Tüm resim dosyalarının yolları."""
    APP_LOGO_PNG = os.path.join(BASE_ASSETS_DIR, "appicon.png")

class LOGO_PATHS:
    """Marka logo dosyalarının yolları."""

    BRAND_LOGO_SVG = os.path.join(BASE_ASSETS_DIR, "pharmalinelogo.svg")