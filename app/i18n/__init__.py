# app/i18n/__init__.py
from .loader import Translator

# Kısa kullanım için
t = Translator.t
t_list = Translator.t_list
set_lang = Translator.set_language
current_lang = Translator.get_language

# Uygulama başında bir kere çalıştır
Translator.load_all()