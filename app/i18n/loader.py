# app\i18n\loader.py
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.bootstrap.resources import resource_path

logger = logging.getLogger(__name__)


class Translator:
    _translations: Dict[str, dict] = {}
    _current_lang: str = "tr"
    _fallback_lang: str = "tr"
    _loaded: bool = False

    @classmethod
    def load_all(cls) -> None:
        if cls._loaded:
            return

        base = Path(resource_path(str(Path(__file__).resolve().parent / "translations")))
        if not base.is_dir():
            cls._translations.setdefault(cls._fallback_lang, {})
            cls._loaded = True
            return

        for path in base.glob("*.json"):
            lang = path.stem
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    cls._translations[lang] = data
            except Exception as e:
                logger.warning("Translation load failed: %s (%s)", path.name, e)

        cls._translations.setdefault(cls._fallback_lang, {})
        cls._loaded = True

    @classmethod
    def set_language(cls, lang: str) -> None:
        if not cls._loaded:
            cls.load_all()
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
        cur: Any = data
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    @classmethod
    def t(cls, key: str, **params: Any) -> str:
        if not cls._loaded:
            cls.load_all()

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
        if not cls._loaded:
            cls.load_all()

        current = cls._get_bundle(cls._current_lang)
        fallback = cls._get_bundle(cls._fallback_lang)

        value = cls._resolve(current, key)
        if value is None:
            value = cls._resolve(fallback, key)

        if not isinstance(value, list):
            return []

        return [x for x in value if isinstance(x, str)]
