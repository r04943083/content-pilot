"""
Internationalization (i18n) module for Content Pilot GUI.

Provides translation functions and language management.
"""

from .translations import (
    DEFAULT_LANGUAGE,
    LANGUAGE_NAMES,
    TranslationManager,
    get_available_languages,
    get_language,
    get_language_display_name,
    get_language_options,
    set_language,
    t,
)

__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_NAMES",
    "TranslationManager",
    "get_available_languages",
    "get_language",
    "get_language_display_name",
    "get_language_options",
    "set_language",
    "t",
]
