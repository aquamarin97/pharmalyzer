from __future__ import annotations

from .loader import Translator

t = Translator.t
t_list = Translator.t_list
set_lang = Translator.set_language
current_lang = Translator.get_language


def init_i18n() -> None:
    """
    Uygulama başında bir kere çağır.
    Import side-effect yok.
    """
    Translator.load_all()
