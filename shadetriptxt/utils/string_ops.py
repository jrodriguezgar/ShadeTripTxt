"""
String Operations Utility Module

This module provides a comprehensive set of string manipulation functions
for cleaning, formatting, and normalizing text, especially focused on
names and entities.

Author: DatamanEdge
"""

import re
from typing import Optional, List


# --- Constants & Translation Tables ---

# Mapping for accent removal and special character normalization
_FLAT_VOWELS_REPLACE_MAP = {
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "Ä": "A",
    "Ë": "E",
    "Ï": "I",
    "Ö": "O",
    "Ü": "U",
    "ä": "a",
    "ë": "e",
    "ï": "i",
    "ö": "o",
    "ü": "u",
    "Â": "A",
    "Ê": "E",
    "Î": "I",
    "Ô": "O",
    "Û": "U",
    "â": "a",
    "ê": "e",
    "î": "i",
    "ô": "o",
    "û": "u",
    "À": "A",
    "È": "E",
    "Ì": "I",
    "Ò": "O",
    "Ù": "U",
    "à": "a",
    "è": "e",
    "ì": "i",
    "ò": "o",
    "ù": "u",
    "Ã": "A",
    "Ñ": "N",
    "Õ": "O",
    "Ũ": "U",
    "ã": "a",
    "ñ": "n",
    "õ": "o",
    "ũ": "u",
    "Ç": "C",
    "ç": "c",
    "Å": "A",
    "å": "a",
    "Ā": "A",
    "Ē": "E",
    "Ī": "I",
    "Ō": "O",
    "Ū": "U",
    "ā": "a",
    "ē": "e",
    "ī": "i",
    "ō": "o",
    "ū": "u",
    "Ă": "A",
    "Ĕ": "E",
    "Ĭ": "I",
    "Ŏ": "O",
    "Ŭ": "U",
    "ă": "a",
    "ĕ": "e",
    "ĭ": "i",
    "ŏ": "o",
    "ŭ": "u",
    "Ő": "O",
    "Ű": "U",
    "ő": "o",
    "ű": "u",
    "Ą": "A",
    "Ę": "E",
    "Į": "I",
    "Ų": "U",
    "ą": "a",
    "ę": "e",
    "į": "i",
    "ų": "u",
    "Ǎ": "A",
    "Ě": "E",
    "Ǐ": "I",
    "Ǒ": "O",
    "Ǔ": "U",
    "ǎ": "a",
    "ě": "e",
    "ǐ": "i",
    "ǒ": "o",
    "ǔ": "u",
    "Ė": "E",
    "ė": "e",
    "Æ": "AE",
    "Œ": "OE",
    "æ": "ae",
    "œ": "oe",
    "ẞ": "SS",
    "ß": "ss",
}

_FLAT_VOWELS_TABLE = str.maketrans(_FLAT_VOWELS_REPLACE_MAP)

# Translation table for normalize_symbols (single-pass via str.translate)
_SYMBOLS_TABLE = str.maketrans(
    {
        "\u00b4": "'",
        "`": "'",
        "\u2018": "'",
        "\u2019": "'",
        "\u2021": "'",
        "\u2020": "'",
        "\u017d": "'",
        "\u00ab": '"',
        "\u00bb": '"',
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": "-",
        "\u2013": "-",
        "\u00a7": "\u00ba",
        "\u00a5": "\u00d1",
    }
)

# Pre-built frozenset for erase_specialchar base allowed characters
_BASE_ALLOWED_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\u00f1\u00d1\u00e1\u00e9\u00ed\u00f3\u00fa\u00fc\u00c1\u00c9\u00cd\u00d3\u00da\u00dc\u00e7\u00c7 "
)


# --- Core Functions ---


def flat_vowels(text: str) -> str:
    """
    Remove accents and normalize special characters in a string.

    Args:
        text: Input string.

    Returns:
        Normalized string with ASCII-equivalent characters.
    """
    if not text:
        return ""
    return text.translate(_FLAT_VOWELS_TABLE)


def normalize_spaces(text: str) -> str:
    """
    Collapse multiple whitespace characters into a single space and trim.

    Args:
        text: Input string.

    Returns:
        Cleaned string.
    """
    if not text:
        return ""
    return " ".join(text.split())


def erase_allspaces(text: str) -> str:
    """
    Remove ALL whitespace characters from a string.

    Args:
        text: Input string.

    Returns:
        String without any spaces.
    """
    if not text:
        return ""
    return "".join(text.split())


def normalize_symbols(text: str) -> str:
    """
    Replace various symbol variations with standardized equivalents.

    Args:
        text: Input string.

    Returns:
        String with normalized symbols.
    """
    if not text:
        return ""
    return text.translate(_SYMBOLS_TABLE)


def erase_specialchar(text: str, allowed_chars: str = "") -> str:
    """
    Remove all non-alphanumeric characters except those explicitly allowed.

    Args:
        text: Input string.
        allowed_chars: String containing additional characters to preserve.

    Returns:
        Filtered string.
    """
    if not text:
        return ""

    allowed_set = _BASE_ALLOWED_CHARS | set(allowed_chars) if allowed_chars else _BASE_ALLOWED_CHARS
    return "".join(char for char in text if char in allowed_set)


def fix_spanish(text: str, additional_allowed: str = "") -> str:
    """
    Standard Spanish-specific cleaning pipeline.

    Args:
        text: Input string.
        additional_allowed: Extra characters to preserve.

    Returns:
        Cleaned string.
    """
    if not text:
        return ""
    return erase_specialchar(normalize_symbols(text), additional_allowed)


# --- Filtering Functions ---


def string_filter(text: str, pattern: str, keep_spaces: bool = True) -> str:
    """
    Generic string filter using regex.

    Args:
        text: Input string.
        pattern: Regex pattern of characters to KEEP.
        keep_spaces: Whether to preserve spaces regardless of pattern.

    Returns:
        Filtered string.
    """
    if not text:
        return ""

    if "^" not in pattern:
        full_pattern = f"[^{pattern}\\s]" if keep_spaces else f"[^{pattern}]"
    else:
        full_pattern = pattern

    result = re.sub(full_pattern, " ", text)
    return normalize_spaces(result)


def string_aZ(text: str, allowed: str = "", keep_spaces: bool = True) -> str:
    """Keep only letters and specific allowed characters."""
    return string_filter(text, f"a-zA-ZñÑáéíóúüÁÉÍÓÚÜçÇ{re.escape(allowed)}", keep_spaces)


def string_aZ09(text: str, allowed: str = "", keep_spaces: bool = True) -> str:
    """Keep only letters, numbers, and specific allowed characters."""
    return string_filter(text, f"a-zA-Z0-9ñÑáéíóúüÁÉÍÓÚÜçÇ{re.escape(allowed)}", keep_spaces)


# --- Identity & Entity Parsing Functions ---


def reorder_comma_fullname(name: str) -> Optional[str]:
    """
    Rearrange "Surname1 Surname2, Name" to "Name Surname1 Surname2".

    Args:
        name: Name string with comma.

    Returns:
        Reordered name or None if no comma found.
    """
    if not name or "," not in name:
        return None

    parts = name.split(",", 1)
    if len(parts) == 2:
        return f"{parts[1].strip()} {parts[0].strip()}".strip()
    return name.strip()


# --- Utility Functions ---


def split_all(text: str, dividers: str = " \t\n\r\f\v-()./,;:!?@#$%^&*+=") -> List[str]:
    """
    Split a string by any character in dividers.
    """
    if not text:
        return []
    pattern = "[" + re.escape(dividers) + "]"
    return [t for t in re.split(pattern, text) if t]


def get_in_text_by_pattern(text: str, pattern_name: str) -> List[str]:
    """
    Extract substrings using predefined regex patterns.
    """
    patterns = {
        "text_in_parentheses": r"\((.*?)\)",
        "broad_email": r"[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "ipv4_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "basic_url": r"https?://[^\s/$.?#].[^\s]*",
    }

    pat = patterns.get(pattern_name)
    if not pat or not text:
        return []

    return re.findall(pat, text)


# ---------------------------------------------------------------------------
# Phone normalisation
# ---------------------------------------------------------------------------

_COUNTRY_CODES: dict[str, str] = {
    "ES": "+34",
    "US": "+1",
    "GB": "+44",
    "FR": "+33",
    "DE": "+49",
    "IT": "+39",
    "PT": "+351",
    "MX": "+52",
    "AR": "+54",
    "BR": "+55",
    "CO": "+57",
    "CL": "+56",
}


def normalize_phone(text: str, country: str = "ES") -> str:
    """
    Normalise a phone number to E.164 format.

    Strips spaces, dashes, parentheses and dots, then prepends the
    international calling code if absent.

    Args:
        text (str): Raw phone number string.
        country (str): ISO 3166-1 alpha-2 country code (default ``'ES'``).

    Returns:
        str: Phone in E.164 format (e.g. ``'+34612345678'``) or
             original text if it cannot be normalised.

    Raises:
        None

    Example Usage:
        normalize_phone("612 345 678")         # '+34612345678'
        normalize_phone("(202) 555-0100", "US") # '+12025550100'

    Cost:
        O(n), where n is the string length.
    """
    if not isinstance(text, str):
        return text

    clean = re.sub(r"[\s\-().]", "", text.strip())

    if not clean:
        return text

    # Already has international prefix
    if clean.startswith("+"):
        return clean

    cc = country.upper()
    prefix = _COUNTRY_CODES.get(cc, "")

    if not prefix:
        return clean

    # Strip leading 0 (national trunk prefix) for non-US
    if cc != "US" and clean.startswith("0"):
        clean = clean[1:]

    return prefix + clean
