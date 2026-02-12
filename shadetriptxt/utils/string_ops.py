"""
String Operations Utility Module

This module provides a comprehensive set of string manipulation functions
for cleaning, formatting, and normalizing text, especially focused on
names and entities.

Author: DatamanEdge
"""

import re
import unicodedata
from typing import Optional, List, Set, Union, Tuple, Dict


# --- Constants & Translation Tables ---

# Mapping for accent removal and special character normalization
_FLAT_VOWELS_REPLACE_MAP = {
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "Ä": "A", "Ë": "E", "Ï": "I", "Ö": "O", "Ü": "U",
    "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u",
    "Â": "A", "Ê": "E", "Î": "I", "Ô": "O", "Û": "U",
    "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
    "À": "A", "È": "E", "Ì": "I", "Ò": "O", "Ù": "U",
    "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
    "Ã": "A", "Ñ": "N", "Õ": "O", "Ũ": "U",
    "ã": "a", "ñ": "n", "õ": "o", "ũ": "u",
    "Ç": "C", "ç": "c",
    "Å": "A", "å": "a",
    "Ā": "A", "Ē": "E", "Ī": "I", "Ō": "O", "Ū": "U",
    "ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u",
    "Ă": "A", "Ĕ": "E", "Ĭ": "I", "Ŏ": "O", "Ŭ": "U",
    "ă": "a", "ĕ": "e", "ĭ": "i", "ŏ": "o", "ŭ": "u",
    "Ő": "O", "Ű": "U", "ő": "o", "ű": "u",
    "Ą": "A", "Ę": "E", "Į": "I", "Ų": "U",
    "ą": "a", "ę": "e", "į": "i", "ų": "u",
    "Ǎ": "A", "Ě": "E", "Ǐ": "I", "Ǒ": "O", "Ǔ": "U",
    "ǎ": "a", "ě": "e", "ǐ": "i", "ǒ": "o", "ǔ": "u",
    "Ė": "E", "ė": "e",
    "Æ": "AE", "Œ": "OE", "æ": "ae", "œ": "oe",
    "ẞ": "SS", "ß": "ss"
}

_FLAT_VOWELS_TABLE = str.maketrans(_FLAT_VOWELS_REPLACE_MAP)


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
    return ' '.join(text.split())


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
    
    replace_map = {
        "´": "'", "`": "'", "’": "'", "‘": "'",
        "‡": "'", "†": "'", "Ž": "'",
        "«": '"', "»": '"', "“": '"', "”": '"',
        "—": "-", "–": "-",
        "§": "º", "¥": "Ñ"
    }
    
    result = text
    for old, new in replace_map.items():
        result = result.replace(old, new)
    return result


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
        
    # Standard allowed: Alpha, Numeric, Space, and Spanish chars
    base_allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ñÑáéíóúüÁÉÍÓÚÜçÇ "
    allowed_set = set(base_allowed + allowed_chars)
    
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
    
    # 1. Normalize symbols first
    result = normalize_symbols(text)
    
    # 2. Filter characters
    # Note: fix_spanish in original often includes basic punctuation logic
    return erase_specialchar(result, additional_allowed)


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
    
    if keep_spaces:
        # Pre-process spaces to ensure they are normalized but not stripped if they are internal
        # Actually, let the regex handle it if requested
        pass
        
    # We want to KEEP what matches the pattern
    # So we remove what DOES NOT match the pattern
    if "^" not in pattern:
        # If pattern doesn't start with ^, it's a "chars to allow" list
        full_pattern = f"[^{pattern}]"
        if keep_spaces:
            full_pattern = f"[^{pattern}\\s]"
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


def string_aZ_plus(text: str, allowed: str = "", keep_spaces: bool = True) -> str:
    """Extended letter filter (includes symbols like @, #)."""
    return string_filter(text, f"a-zA-ZñÑáéíóúüÁÉÍÓÚÜçÇ@#\\-_{re.escape(allowed)}", keep_spaces)


def string_aZ09_plus(text: str, allowed: str = "", keep_spaces: bool = True) -> str:
    """Extended alphanumeric filter (includes symbols)."""
    return string_filter(text, f"a-zA-Z0-9ñÑáéíóúüÁÉÍÓÚÜçÇ@#\\-_{re.escape(allowed)}", keep_spaces)


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


def parse_company(text: str, legal_forms: Set[str]) -> Tuple[str, Optional[str]]:
    """
    Logic for separating company name from legal form.
    
    Args:
        text: Raw company name.
        legal_forms: Set of uppercase legal forms (SL, SA, etc.) to detect.
        
    Returns:
        Tuple of (clean_name, legal_form).
    """
    if not text:
        return "", None
        
    # 1. Clean and normalize
    # (Implementation detail: usually we clean before looking at end of string)
    oparse = normalize_spaces(text.upper())
    
    # Remove markers
    oparse = oparse.replace("(EXTINGUIDA)", "").replace("- EXTINGUIDA", "").replace("-EXTINGUIDA", "")
    oparse = oparse.replace("(EN LIQUIDACION)", "").replace(" EN LIQUIDACION", "")
    
    # Simple check from end
    # We look for legal forms at the end of the string
    # (Optimized: check against pre-calculated set)
    words = oparse.split()
    if not words:
        return "", None
        
    last_word = words[-1].strip(".")
    if last_word in legal_forms:
        comtype = last_word
        comname = " ".join(words[:-1])
        return comname, comtype
        
    # Check for cases like "EMPRESA SLU." where "." is at the end
    # Or "EMPRESA (SL)"
    
    return oparse, None


def format_company_name(name: str, com_type: Optional[str], fmt: str = "dots") -> str:
    """
    Apply formatting style to company name and type.
    """
    if not name:
        return ""
    if not com_type:
        return name
        
    if fmt == "brackets":
        return f"{name} ({com_type})"
    elif fmt == "dots":
        # S.L. instead of SL
        dotted = ".".join(com_type) + "." if len(com_type) <= 3 else com_type + "."
        return f"{name} {dotted}"
    elif fmt == "comma&dots":
        dotted = ".".join(com_type) + "." if len(com_type) <= 3 else com_type + "."
        return f"{name}, {dotted}"
    
    return f"{name} {com_type}"


# --- Utility Functions ---

def get_string_between(text: str, marker: str) -> Optional[str]:
    """
    Extract text found between two occurrences of a marker.
    
    Args:
        text: Input string.
        marker: Character or substring used as delimiter.
        
    Returns:
        Extracted content or None.
    """
    if not text or not marker:
        return None
        
    pattern = f"{re.escape(marker)}(.*?){re.escape(marker)}"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None


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
        'text_in_parentheses': r'\((.*?)\)',
        'broad_email': r'[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'ipv4_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'basic_url': r'https?://[^\s/$.?#].[^\s]*'
    }
    
    pat = patterns.get(pattern_name)
    if not pat or not text:
        return []
    
    return re.findall(pat, text)


def is_internet_domain_format(domain_string: str) -> bool:
    """Checks if a given string has the format of an internet domain."""
    if not isinstance(domain_string, str):
        return False
    # Simplified regex for domain format
    domain_pattern = re.compile(
        r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,})$"
    )
    return bool(domain_pattern.match(domain_string))


def is_url_format(url_string: str) -> bool:
    """Checks if a given string has the format of a URL."""
    if not isinstance(url_string, str):
        return False
    # Regex for URL format (simplified)
    url_pattern = re.compile(
        r"^(?:http|ftp)s?://"  # scheme
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$", re.IGNORECASE)
    return bool(url_pattern.match(url_string))


def erase_lrspaces(text: str) -> str:
    """Strip leading and trailing spaces."""
    return text.strip() if text else ""


def erase_digits(text: str) -> str:
    """Remove all digits from a string."""
    return re.sub(r'\d', '', text) if text else ""


def username_from_email(email: str) -> Optional[str]:
    """Extract username part from an email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[0]


def list_intersection(list1: list, list2: list) -> list:
    """Return intersection of two lists preserving order if possible (set used here)."""
    return list(set(list1) & set(list2))


def list_to_string(lst: list, separator: str = ',') -> str:
    """Convert a list to a string joined by separator."""
    if not lst:
        return ""
    return separator.join(map(str, lst))


def extract_and_decode_json(text: str) -> Optional[Dict]:
    """Extracts and decodes the first JSON object found in a string."""
    if not text:
        return None
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            import json
            return json.loads(json_str)
    except Exception:
        pass
    return None
