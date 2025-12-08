# app/i18n/loader.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


class Translator:
    _translations: Dict[str, dict] = {}
    _current_lang: str = "tr"
    _fallback_lang: str = "tr"

    @classmethod
    def load_all(cls) -> None:
        """Uygulama başlangıcında bir kere çalıştır."""
        base_path = os.path.join(os.path.dirname(__file__), "translations")
        if not os.path.isdir(base_path):
            cls._translations.setdefault(cls._fallback_lang, {})
            return

        for filename in os.listdir(base_path):
            if not filename.endswith(".json"):
                continue

            lang = filename[:-5]  # tr.json -> tr
            path = os.path.join(base_path, filename)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    cls._translations[lang] = data
            except (OSError, json.JSONDecodeError):
                # Bozuk/erişilemeyen çeviri dosyası uygulamayı düşürmesin.
                continue

        cls._translations.setdefault(cls._fallback_lang, {})

    @classmethod
    def set_language(cls, lang: str) -> None:
        cls._current_lang = lang if lang in cls._translations else cls._fallback_lang

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def _get_bundle(cls, lang: str) -> dict:
        data = cls._translations.get(lang)
        return data if isinstance(data, dict) else {}

    @classmethod
    def _resolve(cls, data: dict, key: str) -> Optional[Any]:
        """
        Dotted key çözümleyici:
        "errors.license.missing" -> data["errors"]["license"]["missing"]
        """
        cur: Any = data
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    @classmethod
    def t(cls, key: str, **params: Any) -> str:
        """
        Tek string çeviri.
        - namespaced/dotted key destekler
        - parametrelerle formatlar: t("x.y", name="Ali")
        """
        current = cls._get_bundle(cls._current_lang)
        fallback = cls._get_bundle(cls._fallback_lang)

        value = cls._resolve(current, key)
        if value is None:
            value = cls._resolve(fallback, key)

        if not isinstance(value, str):
            return key

        if params:
            try:
                return value.format(**params)
            except Exception:
                return value

        return value

    @classmethod
    def t_list(cls, key: str) -> List[str]:
        """
        Liste çeviri (loading.messages gibi).
        """
        current = cls._get_bundle(cls._current_lang)
        fallback = cls._get_bundle(cls._fallback_lang)

        value = cls._resolve(current, key)
        if value is None:
            value = cls._resolve(fallback, key)

        return value if isinstance(value, list) else []
