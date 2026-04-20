"""
Text Parser — locale-aware text parsing, extraction, and normalization.

Parse, normalize, and extract structured data from text with support
for 6 languages and 12 locales.

Quick start::

    from shadetriptxt.text_parser import TextParser

    parser = TextParser(locale="es_ES")
    clean = parser.normalize("  José  García-López  ")
    phones = parser.extract_phones("+34 91 303 20 60")
"""

from .text_parser import TextParser, ParserLocaleProfile, LOCALE_PROFILES

from .config import (
    Config,
    ConfigSchema,
    ConfigValue,
    ConfigSource,
    ConfigFormat,
    load_config,
    create_sample_config,
)
