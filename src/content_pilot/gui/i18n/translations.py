"""
Translation manager for internationalization support.

Manages loading translations, language preferences, and provides
translation lookup with dot notation and fallback support.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from nicegui import app

from . import en_US, zh_CN

logger = logging.getLogger(__name__)

# Default language
DEFAULT_LANGUAGE = "zh_CN"

# Language display names
LANGUAGE_NAMES = {
    "zh_CN": "中文",
    "en_US": "English",
}


class TranslationManager:
    """Manages translations and language preferences."""

    def __init__(self) -> None:
        """Initialize the translation manager."""
        self._translations: Dict[str, Dict[str, Any]] = {
            "zh_CN": zh_CN.TRANSLATIONS,
            "en_US": en_US.TRANSLATIONS,
        }

    def get_language(self) -> str:
        """Get the current language preference from client storage."""
        try:
            return app.storage.client.get("language", DEFAULT_LANGUAGE)
        except (AttributeError, RuntimeError):
            return DEFAULT_LANGUAGE

    def set_language(self, language: str) -> None:
        """Set the language preference in client storage."""
        try:
            app.storage.client["language"] = language
            logger.info(f"Language set to: {language}")
        except (AttributeError, RuntimeError) as e:
            logger.warning(f"Could not set language: {e}")

    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return list(self._translations.keys())

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        """
        Get a value from a nested dictionary using dot notation.

        Args:
            data: The nested dictionary to search
            key: The dot-separated key path (e.g., "nav.dashboard")

        Returns:
            The value at the key path, or None if not found
        """
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def t(self, key: str, **kwargs: Any) -> str:
        """
        Get a translation by key with dot notation.

        Args:
            key: The translation key using dot notation (e.g., "nav.dashboard")
            **kwargs: Optional format arguments for the translation

        Returns:
            The translated string, or the key itself if not found
        """
        language = self.get_language()

        # Try to get translation in current language
        translations = self._translations.get(language, {})
        value = self._get_nested_value(translations, key)

        # Fallback to Chinese if not found in current language
        if value is None and language != DEFAULT_LANGUAGE:
            translations = self._translations.get(DEFAULT_LANGUAGE, {})
            value = self._get_nested_value(translations, key)

        # If still not found, return the key itself
        if value is None:
            return key

        # Format the translation with provided arguments
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value

        return str(value)


# Global translation manager instance
_translation_manager = TranslationManager()


def t(key: str, **kwargs: Any) -> str:
    """
    Get a translation by key with dot notation.

    Args:
        key: The translation key using dot notation (e.g., "nav.dashboard")
        **kwargs: Optional format arguments for the translation

    Returns:
        The translated string, or the key itself if not found
    """
    return _translation_manager.t(key, **kwargs)


def set_language(language: str) -> None:
    """Set the language preference in client storage."""
    _translation_manager.set_language(language)


def get_language() -> str:
    """Get the current language preference from client storage."""
    return _translation_manager.get_language()


def get_available_languages() -> list[str]:
    """Get list of available language codes."""
    return _translation_manager.get_available_languages()


def get_language_display_name(code: str) -> str:
    """Get the display name for a language code.

    Args:
        code: Language code (e.g., "zh_CN", "en_US")

    Returns:
        Display name (e.g., "中文", "English")
    """
    return LANGUAGE_NAMES.get(code, code)


def get_language_options() -> list[dict]:
    """Get list of language options for select components.

    Returns:
        List of dicts with 'value' and 'label' keys
    """
    return [
        {"value": code, "label": LANGUAGE_NAMES.get(code, code)}
        for code in get_available_languages()
    ]
