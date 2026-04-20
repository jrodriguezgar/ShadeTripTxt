"""
String Validation - Checksum and format validation algorithms.

This module provides standalone functions for validating common identifiers
(IBAN, ISBN, credit-card numbers, EAN-13 barcodes) using their respective
checksum algorithms.

Algorithms:
    - Luhn (credit cards, IMEI, etc.)
    - ISO 13616 Mod-97 (IBAN)
    - ISBN-10 / ISBN-13 check digit
    - EAN-13 check digit

Author: DatamanEdge
"""

import re
import unicodedata


# Pre-compiled patterns for data_type_inference
_DATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),
    re.compile(r"^\d{2}-\d{2}-\d{4}$"),
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),
]
_EMAIL_PATTERN: re.Pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URL_PATTERN: re.Pattern = re.compile(r"^https?://\S+$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Luhn algorithm
# ---------------------------------------------------------------------------


def luhn_checksum(number_str: str) -> int:
    """
    Compute the Luhn check digit for a numeric string.

    The Luhn algorithm (ISO/IEC 7812) is used to validate credit-card
    numbers, IMEI codes, and other identification numbers.

    Args:
        number_str: A string of digits (hyphens and spaces are stripped).

    Returns:
        The single check digit (0-9) that would make the full number
        pass Luhn validation when appended.

    Raises:
        ValueError: If *number_str* contains non-digit characters
            (after stripping hyphens and spaces).

    Example Usage:
        luhn_checksum("7992739871")  # 3

    Cost:
        O(n), where n is the number of digits.
    """
    clean = number_str.replace("-", "").replace(" ", "")

    if not clean.isdigit():
        raise ValueError(f"Non-digit characters in input: {number_str!r}")

    digits = [int(d) for d in clean]
    total = 0

    for idx, d in enumerate(reversed(digits)):
        if idx % 2 == 0:
            doubled = d * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += d

    return (10 - (total % 10)) % 10


def is_valid_luhn(number_str: str) -> bool:
    """
    Validate a number string using the Luhn algorithm.

    The last digit of *number_str* is treated as the check digit.

    Args:
        number_str: A string of digits (hyphens and spaces are stripped).

    Returns:
        ``True`` if the number passes Luhn validation.

    Raises:
        ValueError: If *number_str* contains non-digit characters.

    Example Usage:
        is_valid_luhn("79927398713")  # True
        is_valid_luhn("79927398710")  # False

    Cost:
        O(n).
    """
    clean = number_str.replace("-", "").replace(" ", "")

    if not clean.isdigit() or len(clean) < 2:
        raise ValueError(f"Invalid input for Luhn check: {number_str!r}")

    payload = clean[:-1]
    expected = int(clean[-1])
    return luhn_checksum(payload) == expected


# ---------------------------------------------------------------------------
# EAN-13
# ---------------------------------------------------------------------------


def ean13_check_digit(code_12: str) -> str:
    """
    Compute the EAN-13 check digit from a 12-digit barcode prefix.

    Args:
        code_12: A string of exactly 12 digits.

    Returns:
        The single check-digit character (``'0'``-``'9'``).

    Raises:
        ValueError: If *code_12* is not exactly 12 digits.

    Example Usage:
        ean13_check_digit("590123412345")  # "7"

    Cost:
        O(1) (fixed 12 iterations).
    """
    clean = code_12.replace("-", "").replace(" ", "")

    if not clean.isdigit() or len(clean) != 12:
        raise ValueError(f"Expected exactly 12 digits, got: {code_12!r}")

    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(clean))

    return str((10 - (total % 10)) % 10)


# ---------------------------------------------------------------------------
# IBAN  (ISO 13616, Mod-97)
# ---------------------------------------------------------------------------

# Country-code → expected total IBAN length (ISO 13616).
_IBAN_LENGTHS: dict[str, int] = {
    "AL": 28,
    "AD": 24,
    "AT": 20,
    "AZ": 28,
    "BH": 22,
    "BY": 28,
    "BE": 16,
    "BA": 20,
    "BR": 29,
    "BG": 22,
    "CR": 22,
    "HR": 21,
    "CY": 28,
    "CZ": 24,
    "DK": 18,
    "DO": 28,
    "TL": 23,
    "EE": 20,
    "FO": 18,
    "FI": 18,
    "FR": 27,
    "GE": 22,
    "DE": 22,
    "GI": 23,
    "GR": 27,
    "GL": 18,
    "GT": 28,
    "HU": 28,
    "IS": 26,
    "IQ": 23,
    "IE": 22,
    "IL": 23,
    "IT": 27,
    "JO": 30,
    "KZ": 20,
    "XK": 20,
    "KW": 30,
    "LV": 21,
    "LB": 28,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "MK": 19,
    "MT": 31,
    "MR": 27,
    "MU": 30,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "NL": 18,
    "NO": 15,
    "PK": 24,
    "PS": 29,
    "PL": 28,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "LC": 32,
    "SM": 27,
    "ST": 25,
    "SA": 24,
    "RS": 22,
    "SC": 31,
    "SK": 24,
    "SI": 19,
    "ES": 24,
    "SE": 24,
    "CH": 21,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "AE": 23,
    "GB": 22,
    "VA": 22,
    "VG": 24,
}


def is_valid_iban(iban: str) -> bool:
    """
    Validate an IBAN using the ISO 13616 Mod-97 algorithm.

    Checks country-code format, length per country, and the Mod-97
    checksum.

    Args:
        iban: An IBAN string (spaces and hyphens are stripped).

    Returns:
        ``True`` if the IBAN is valid.

    Raises:
        None

    Example Usage:
        is_valid_iban("GB29 NWBK 6016 1331 9268 19")  # True
        is_valid_iban("GB29 NWBK 6016 1331 9268 18")  # False

    Cost:
        O(n), where n is the length of the IBAN.
    """
    clean = iban.replace(" ", "").replace("-", "").upper()

    if len(clean) < 5:
        return False

    country = clean[:2]

    if not country.isalpha():
        return False

    # Length check (if country is known)
    if country in _IBAN_LENGTHS and len(clean) != _IBAN_LENGTHS[country]:
        return False

    # All characters must be alphanumeric
    if not clean.isalnum():
        return False

    # Move first 4 chars to the end, convert letters to digits (A=10 .. Z=35)
    rearranged = clean[4:] + clean[:4]
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)

    return int(numeric) % 97 == 1


# ---------------------------------------------------------------------------
# ISBN (International Standard Book Number)
# ---------------------------------------------------------------------------


def is_valid_isbn(isbn: str) -> bool:
    """
    Validate an ISBN-10 or ISBN-13 checksum.

    Automatically detects the ISBN type by length after stripping
    hyphens and spaces.

    Args:
        isbn: An ISBN string (hyphens and spaces are stripped).

    Returns:
        ``True`` if the checksum is correct.

    Raises:
        None

    Example Usage:
        is_valid_isbn("0-306-40615-2")    # True  (ISBN-10)
        is_valid_isbn("978-0-306-40615-7")  # True  (ISBN-13)
        is_valid_isbn("0-306-40615-3")    # False

    Cost:
        O(1) (fixed 10 or 13 iterations).
    """
    clean = isbn.replace("-", "").replace(" ", "")

    if len(clean) == 10:
        return _isbn10_valid(clean)

    if len(clean) == 13:
        return _isbn13_valid(clean)

    return False


def _isbn10_valid(isbn10: str) -> bool:
    """Check ISBN-10 with Mod-11 checksum."""
    if not isbn10[:9].isdigit():
        return False

    last = isbn10[9].upper()

    if last not in "0123456789X":
        return False

    total = sum((10 - i) * int(d) for i, d in enumerate(isbn10[:9]))
    total += 10 if last == "X" else int(last)

    return total % 11 == 0


def _isbn13_valid(isbn13: str) -> bool:
    """Check ISBN-13 with Mod-10 (EAN-13) checksum."""
    if not isbn13.isdigit():
        return False

    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn13))

    return total % 10 == 0


# ---------------------------------------------------------------------------
# Credit-card validation (Luhn + BIN prefix)
# ---------------------------------------------------------------------------

# Common BIN prefixes for major card networks
_CARD_PREFIXES: dict[str, list[tuple[str, ...]]] = {
    "visa": [("4",)],
    "mastercard": [("51",), ("52",), ("53",), ("54",), ("55",), ("2221",), ("2720",)],
    "amex": [("34",), ("37",)],
    "discover": [("6011",), ("65",), ("644",), ("649",)],
}


def is_valid_credit_card(number: str) -> dict:
    """
    Validate a credit-card number using Luhn checksum and BIN prefix.

    Detects Visa, Mastercard, American Express, and Discover networks.

    Args:
        number (str): Card number (hyphens/spaces are stripped).

    Returns:
        dict: ``{"valid": bool, "network": str | None}``.
            ``network`` is ``None`` when valid is ``False`` or the
            network is unrecognized.

    Raises:
        None

    Example Usage:
        is_valid_credit_card("4111 1111 1111 1111")
        # {'valid': True, 'network': 'visa'}

    Cost:
        O(n), where n is the length of the card number.
    """
    clean = number.replace("-", "").replace(" ", "")

    if not clean.isdigit() or len(clean) < 12 or len(clean) > 19:
        return {"valid": False, "network": None}

    # Luhn check
    if not is_valid_luhn(clean):
        return {"valid": False, "network": None}

    # Network detection
    network = None

    for name, prefix_groups in _CARD_PREFIXES.items():
        for prefixes in prefix_groups:
            if any(clean.startswith(p) for p in prefixes):
                network = name
                break

        if network:
            break

    return {"valid": True, "network": network}


# ---------------------------------------------------------------------------
# EU VAT number validation
# ---------------------------------------------------------------------------

# Country → (regex pattern, expected total length including country prefix)
_VAT_PATTERNS: dict[str, str] = {
    "AT": r"^ATU\d{8}$",
    "BE": r"^BE[01]\d{9}$",
    "BG": r"^BG\d{9,10}$",
    "CY": r"^CY\d{8}[A-Z]$",
    "CZ": r"^CZ\d{8,10}$",
    "DE": r"^DE\d{9}$",
    "DK": r"^DK\d{8}$",
    "EE": r"^EE\d{9}$",
    "EL": r"^EL\d{9}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "FI": r"^FI\d{8}$",
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "HR": r"^HR\d{11}$",
    "HU": r"^HU\d{8}$",
    "IE": r"^IE\d[A-Z0-9+*]\d{5}[A-Z]$",
    "IT": r"^IT\d{11}$",
    "LT": r"^LT\d{9,12}$",
    "LU": r"^LU\d{8}$",
    "LV": r"^LV\d{11}$",
    "MT": r"^MT\d{8}$",
    "NL": r"^NL\d{9}B\d{2}$",
    "PL": r"^PL\d{10}$",
    "PT": r"^PT\d{9}$",
    "RO": r"^RO\d{2,10}$",
    "SE": r"^SE\d{12}$",
    "SI": r"^SI\d{8}$",
    "SK": r"^SK\d{10}$",
    "GB": r"^GB\d{9}$|^GB\d{12}$|^GBGD\d{3}$|^GBHA\d{3}$",
}


def is_valid_vat(vat_number: str) -> bool:
    """
    Validate an EU VAT number format.

    Checks that the country prefix is recognized and that the remainder
    matches the expected pattern. Does **not** query the VIES web
    service.

    Args:
        vat_number (str): VAT number including the 2-letter country prefix
            (e.g. ``"DE123456789"``). Spaces are stripped.

    Returns:
        bool: ``True`` if the format is valid.

    Raises:
        None

    Example Usage:
        is_valid_vat("DE123456789")   # True
        is_valid_vat("XX123456789")   # False

    Cost:
        O(n), where n is the length of the VAT number.
    """
    clean = vat_number.replace(" ", "").upper()

    if len(clean) < 4:
        return False

    country = clean[:2]

    if country not in _VAT_PATTERNS:
        return False

    return bool(re.match(_VAT_PATTERNS[country], clean))


# ---------------------------------------------------------------------------
# EAN validation (EAN-8 and EAN-13)
# ---------------------------------------------------------------------------


def is_valid_ean(barcode: str) -> bool:
    """
    Validate an EAN-8 or EAN-13 barcode checksum.

    Args:
        barcode (str): Barcode string (hyphens/spaces stripped).

    Returns:
        bool: ``True`` if the check digit is correct.

    Raises:
        None

    Example Usage:
        is_valid_ean("5901234123457")   # True  (EAN-13)
        is_valid_ean("96385074")        # True  (EAN-8)
        is_valid_ean("5901234123458")   # False

    Cost:
        O(n), where n is the barcode length.
    """
    clean = barcode.replace("-", "").replace(" ", "")

    if not clean.isdigit():
        return False

    if len(clean) not in (8, 13):
        return False

    total = sum(int(d) * (1 if (len(clean) - 1 - i) % 2 == 0 else 3) for i, d in enumerate(clean))

    return total % 10 == 0


# ---------------------------------------------------------------------------
# SWIFT/BIC validation
# ---------------------------------------------------------------------------


def is_valid_swift_bic(code: str) -> bool:
    """
    Validate a SWIFT/BIC code format.

    A valid SWIFT/BIC code is 8 or 11 characters:
    - Positions 1-4: bank code (letters)
    - Positions 5-6: country code (letters, ISO 3166-1 alpha-2)
    - Positions 7-8: location code (alphanumeric)
    - Positions 9-11 (optional): branch code (alphanumeric)

    Args:
        code (str): SWIFT/BIC code to validate.

    Returns:
        bool: ``True`` if the format is valid.

    Raises:
        None

    Example Usage:
        is_valid_swift_bic("DEUTDEFF")      # True
        is_valid_swift_bic("DEUTDEFF500")   # True
        is_valid_swift_bic("DE")            # False

    Cost:
        O(1)
    """
    if not isinstance(code, str):
        return False

    c = code.strip().upper()

    if len(c) not in (8, 11):
        return False

    # Bank code: 4 letters
    if not c[:4].isalpha():
        return False

    # Country code: 2 letters
    if not c[4:6].isalpha():
        return False

    # Location code: 2 alphanumeric
    if not c[6:8].isalnum():
        return False

    # Optional branch code: 3 alphanumeric
    if len(c) == 11 and not c[8:11].isalnum():
        return False

    return True


# ---------------------------------------------------------------------------
# Data type inference
# ---------------------------------------------------------------------------


def data_type_inference(value: str) -> str:
    """
    Infer the likely data type of a string value.

    Attempts to classify the string into common data types without
    external dependencies.  Returns one of: ``'integer'``, ``'float'``,
    ``'boolean'``, ``'date'``, ``'email'``, ``'url'``, ``'empty'``,
    or ``'string'``.

    Args:
        value (str): The string to classify.

    Returns:
        str: Inferred type label.

    Raises:
        None

    Example Usage:
        data_type_inference("42")          # 'integer'
        data_type_inference("3.14")        # 'float'
        data_type_inference("true")        # 'boolean'
        data_type_inference("2024-01-15") # 'date'
        data_type_inference("a@b.com")    # 'email'

    Cost:
        O(n), where n is the string length.
    """
    if not isinstance(value, str):
        return "string"

    stripped = value.strip()

    if not stripped:
        return "empty"

    # Boolean
    if stripped.lower() in ("true", "false", "yes", "no", "1", "0"):
        return "boolean"

    # Integer
    try:
        int(stripped)
        return "integer"
    except ValueError:
        pass

    # Float
    try:
        float(stripped)
        return "float"
    except ValueError:
        pass

    # Date patterns (common ISO formats)
    for pat in _DATE_PATTERNS:
        if pat.match(stripped):
            return "date"

    # Email (simple check)
    if _EMAIL_PATTERN.match(stripped):
        return "email"

    # URL
    if _URL_PATTERN.match(stripped):
        return "url"

    return "string"


# ---------------------------------------------------------------------------
# Phone format validation
# ---------------------------------------------------------------------------

_PHONE_PATTERNS: dict[str, str] = {
    "ES": r"^(?:\+34)?[6-9]\d{8}$",
    "US": r"^(?:\+1)?[2-9]\d{9}$",
    "GB": r"^(?:\+44)?(?:0)?[1-9]\d{9,10}$",
    "FR": r"^(?:\+33)?(?:0)?[1-9]\d{8}$",
    "DE": r"^(?:\+49)?(?:0)?[1-9]\d{4,14}$",
    "IT": r"^(?:\+39)?(?:0)?[0-9]{6,12}$",
    "PT": r"^(?:\+351)?[2-9]\d{8}$",
}


def is_valid_phone_format(text: str, country: str = "ES") -> bool:
    """
    Validate a phone number format for a given country.

    Strips spaces, dashes and parentheses before matching against a
    country-specific regex.  Does NOT verify that the number is
    allocated or reachable.

    Args:
        text (str): Phone number string.
        country (str): ISO 3166-1 alpha-2 country code (default ``'ES'``).

    Returns:
        bool: ``True`` if the format matches the country pattern.

    Raises:
        None

    Example Usage:
        is_valid_phone_format("+34612345678")          # True
        is_valid_phone_format("612 345 678", "ES")     # True
        is_valid_phone_format("202-555-0100", "US")    # True

    Cost:
        O(n), where n is the string length.
    """
    if not isinstance(text, str):
        return False

    clean = re.sub(r"[\s\-()]", "", text.strip())
    cc = country.upper()

    pattern = _PHONE_PATTERNS.get(cc)

    if not pattern:
        return False

    return bool(re.match(pattern, clean))


# ---------------------------------------------------------------------------
# Email domain type classification
# ---------------------------------------------------------------------------

_FREE_EMAIL_DOMAINS: set[str] = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "aol.com",
    "icloud.com",
    "mail.com",
    "protonmail.com",
    "zoho.com",
    "yandex.com",
    "gmx.com",
    "gmx.net",
    "yahoo.es",
    "yahoo.co.uk",
    "hotmail.es",
    "hotmail.co.uk",
    "proton.me",
}

_DISPOSABLE_EMAIL_DOMAINS: set[str] = {
    "mailinator.com",
    "guerrillamail.com",
    "tempmail.com",
    "throwaway.email",
    "yopmail.com",
    "sharklasers.com",
    "guerrillamailblock.com",
    "grr.la",
    "dispostable.com",
    "trashmail.com",
    "maildrop.cc",
    "10minutemail.com",
    "temp-mail.org",
    "fakeinbox.com",
    "mailnesia.com",
}


def email_domain_type(email: str) -> str:
    """
    Classify the domain of an email address.

    Returns one of: ``'free'``, ``'disposable'``, ``'corporate'``,
    or ``'invalid'`` if the email cannot be parsed.

    Args:
        email (str): Email address string.

    Returns:
        str: Domain classification label.

    Raises:
        None

    Example Usage:
        email_domain_type("user@gmail.com")        # 'free'
        email_domain_type("user@company.com")       # 'corporate'
        email_domain_type("user@mailinator.com")    # 'disposable'

    Cost:
        O(1)
    """
    if not isinstance(email, str) or "@" not in email:
        return "invalid"

    parts = email.strip().lower().rsplit("@", 1)

    if len(parts) != 2 or not parts[1]:
        return "invalid"

    domain = parts[1]

    if domain in _DISPOSABLE_EMAIL_DOMAINS:
        return "disposable"

    if domain in _FREE_EMAIL_DOMAINS:
        return "free"

    return "corporate"


def has_mixed_case_anomaly(text: str) -> bool:
    """Detect anomalous mixed-case patterns in text.

    Flags strings where individual words have an unnatural mix of
    upper and lower-case letters (e.g. ``'hELLo WoRLd'``) that do
    not match title-case, UPPER, lower, or camelCase.

    Args:
        text (str): The input text.

    Returns:
        bool: ``True`` if anomalous casing is detected.

    Raises:
        None

    Example Usage:
        has_mixed_case_anomaly("hELLo WoRLd")   # True
        has_mixed_case_anomaly("Hello World")     # False

    Cost:
        O(n)
    """
    if not isinstance(text, str) or not text.strip():
        return False

    for word in text.split():
        alpha = [ch for ch in word if ch.isalpha()]

        if len(alpha) < 2:
            continue

        # Skip if all-upper, all-lower, title-case, or camelCase
        w = "".join(alpha)

        if w.isupper() or w.islower() or w.istitle():
            continue

        # camelCase: first char lower, at least one upper after
        if w[0].islower() and any(ch.isupper() for ch in w[1:]):
            # Valid camelCase: each upper starts a contiguous group
            # Heuristic: accept if upper chars < 50 % of word
            if sum(1 for ch in w if ch.isupper()) < len(w) / 2:
                continue

        return True

    return False


def contains_repeated_words(text: str) -> bool:
    """Detect immediately repeated words in text.

    Catches typos like ``'the the'`` or ``'is is'``.

    Args:
        text (str): The input text.

    Returns:
        bool: ``True`` if any word is immediately followed by itself
              (case-insensitive).

    Raises:
        None

    Example Usage:
        contains_repeated_words("the the cat")   # True
        contains_repeated_words("the cat sat")    # False

    Cost:
        O(n)
    """
    if not isinstance(text, str) or not text.strip():
        return False

    words = text.lower().split()

    for i in range(len(words) - 1):
        if words[i] == words[i + 1]:
            return True

    return False


# ---------------------------------------------------------------------------
# Homoglyph & mixed-script detection (data-quality / anti-spoofing)
# ---------------------------------------------------------------------------

# Known confusable mappings (subset — most common Latin ↔ Cyrillic/Greek).
_CONFUSABLES: dict = {
    "\u0410": "A",  # Cyrillic А → Latin A
    "\u0412": "B",  # Cyrillic В → Latin B
    "\u0421": "C",  # Cyrillic С → Latin C
    "\u0415": "E",  # Cyrillic Е → Latin E
    "\u041d": "H",  # Cyrillic Н → Latin H
    "\u041a": "K",  # Cyrillic К → Latin K
    "\u041c": "M",  # Cyrillic М → Latin M
    "\u041e": "O",  # Cyrillic О → Latin O
    "\u0420": "P",  # Cyrillic Р → Latin P
    "\u0422": "T",  # Cyrillic Т → Latin T
    "\u0425": "X",  # Cyrillic Х → Latin X
    "\u0430": "a",  # Cyrillic а → Latin a
    "\u0435": "e",  # Cyrillic е → Latin e
    "\u043e": "o",  # Cyrillic о → Latin o
    "\u0440": "p",  # Cyrillic р → Latin p
    "\u0441": "c",  # Cyrillic с → Latin c
    "\u0443": "y",  # Cyrillic у → Latin y
    "\u0445": "x",  # Cyrillic х → Latin x
    "\u0456": "i",  # Cyrillic і → Latin i
    "\u0391": "A",  # Greek Α → Latin A
    "\u0392": "B",  # Greek Β → Latin B
    "\u0395": "E",  # Greek Ε → Latin E
    "\u0397": "H",  # Greek Η → Latin H
    "\u0399": "I",  # Greek Ι → Latin I
    "\u039a": "K",  # Greek Κ → Latin K
    "\u039c": "M",  # Greek Μ → Latin M
    "\u039d": "N",  # Greek Ν → Latin N
    "\u039f": "O",  # Greek Ο → Latin O
    "\u03a1": "P",  # Greek Ρ → Latin P
    "\u03a4": "T",  # Greek Τ → Latin T
    "\u03a7": "X",  # Greek Χ → Latin X
    "\u03bf": "o",  # Greek ο → Latin o
}


def detect_mixed_scripts(text: str) -> dict:
    """Detect mixed Unicode scripts in text (potential spoofing indicator).

    Analyses each letter character's Unicode script category and returns
    the distinct scripts found together with the characters belonging
    to each.  Mixing Latin with Cyrillic or Greek is a common phishing
    technique (IDN homograph attacks).

    Args:
        text (str): The input text to analyse.

    Returns:
        dict: A dictionary mapping script names to the set of characters
              found for that script.  If only one script is present the
              dictionary contains a single key.

    Raises:
        TypeError: If *text* is not a string.

    Example Usage:
        >>> result = detect_mixed_scripts("Tеst")   # 'е' is Cyrillic
        >>> sorted(result.keys())
        ['CYRILLIC', 'LATIN']

    Cost:
        O(n)
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    scripts: dict = {}

    for ch in text:
        if not ch.isalpha():
            continue

        try:
            name = unicodedata.name(ch, "")
        except ValueError:
            continue

        # The script name is normally the first word of the Unicode name
        # (e.g. "LATIN SMALL LETTER A" → "LATIN").
        script = name.split()[0] if name else "UNKNOWN"

        if script not in scripts:
            scripts[script] = set()

        scripts[script].add(ch)

    return scripts


def homoglyph_risk_score(text: str) -> float:
    """Compute a homoglyph spoofing risk score for a string.

    Scans each character against a built-in table of visually confusable
    characters (Latin ↔ Cyrillic, Latin ↔ Greek, digit ↔ letter).  The
    score is the ratio of confusable characters to total alphanumeric
    characters, yielding a value in [0, 1].

    A score of 0 means no confusable characters were detected.  A score
    close to 1 means nearly every character has a look-alike from
    another script.

    Args:
        text (str): The input text to evaluate.

    Returns:
        float: Risk score in [0.0, 1.0].

    Raises:
        TypeError: If *text* is not a string.

    Example Usage:
        >>> homoglyph_risk_score("hello")
        0.0
        >>> homoglyph_risk_score("\u0430\u0435\u043e")  # Cyrillic а, е, о
        1.0

    Cost:
        O(n)
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text:
        return 0.0

    total = 0
    confusable = 0

    for ch in text:
        if not ch.isalnum():
            continue

        total += 1

        if ch in _CONFUSABLES:
            confusable += 1

    if total == 0:
        return 0.0

    return float(confusable / total)
