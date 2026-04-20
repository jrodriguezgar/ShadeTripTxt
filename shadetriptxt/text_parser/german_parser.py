import re
import unicodedata
from typing import Optional

from .encoding_fixer import EncodingFixer

# Wortlisten für grammatisch kategorisierte Operationen:
# Liste von Bindeswörtern auf Deutsch, die in bestimmten Textanalyseprozessen ausgelassen werden können.
# In Großbuchstaben für normalisierte Vergleiche.

# Präfixe und Partikel in Eigennamen
_NAME_PREFIXES = ["VON", "VOM", "ZU", "ZUM", "ZUR", "VAN", "DER", "DEN", "MC", "MAC"]

# Häufige Adverbien/Konnektoren
_ADVERBS = ["SCHON", "NOCH", "AUCH", "SO", "JETZT"]

# Personalpronomen und Objekte
_PRONOUNS = ["ICH", "DU", "ER", "SIE", "ES", "WIR", "IHR", "MICH", "DICH", "SICH", "UNS", "EUCH", "MIR", "DIR", "IHM", "IHNEN"]

# Determinanten (Demonstrativa/Possessiva)
_DETERMINANTS = [
    "DIESER",
    "DIESE",
    "DIESES",
    "JENER",
    "JENE",
    "JENES",
    "MEIN",
    "MEINE",
    "DEIN",
    "DEINE",
    "SEIN",
    "SEINE",
    "UNSER",
    "UNSERE",
    "EUER",
    "EURE",
]

# Artikel
_ARTICLES = ["DER", "DIE", "DAS", "DEN", "DEM", "DES", "EIN", "EINE", "EINEM", "EINEN", "EINER", "EINES"]

# Präpositionen
_PREPOSITIONS = [
    "AN",
    "AUF",
    "AUS",
    "BEI",
    "BIS",
    "DURCH",
    "FÜR",
    "GEGEN",
    "HINTER",
    "IN",
    "IM",
    "MIT",
    "NACH",
    "NEBEN",
    "OHNE",
    "SEIT",
    "ÜBER",
    "UM",
    "UNTER",
    "VOR",
    "VON",
    "VOM",
    "WÄHREND",
    "WEGEN",
    "ZU",
    "ZUM",
    "ZUR",
    "ZWISCHEN",
]

# Konjunktionen
_CONJUNCTIONS = ["UND", "ODER", "ABER", "DENN", "SONDERN", "WEIL", "DASS", "WENN", "ALS", "OBWOHL", "DAMIT", "DOCH"]

# Liste von Wörtern, die in bestimmten Analyseprozessen übersprungen werden.
_SKIP_WORDS_MAP = [
    "UND",
    "ODER",
    "ABER",
    "DER",
    "DIE",
    "DAS",
    "DEN",
    "DEM",
    "DES",
    "EIN",
    "EINE",
    "IN",
    "IM",
    "AN",
    "AUF",
    "VON",
    "VOM",
    "ZU",
    "ZUM",
    "ZUR",
    "MIT",
    "FÜR",
    "BEI",
    "AUS",
]


# Precompile a regex for words to remove (articles, prepositions, conjunctions).
_REMOVE_WORDS_SET = {w.upper() for w in (_ARTICLES + _PREPOSITIONS + _CONJUNCTIONS)}
_REMOVE_WORDS_SORTED = sorted(_REMOVE_WORDS_SET, key=len, reverse=True)
_REMOVE_WORDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _REMOVE_WORDS_SORTED) + r")\b", flags=re.IGNORECASE)


def remove_german_articles(input_string: Optional[str]) -> Optional[str]:
    """
    Entfernt gebräuchliche Artikel, Präpositionen und Konjunktionen im Deutschen aus einer Zeichenkette.

    Args:
        input_string: Die zu bereinigende Eingabezeichenkette. Bei None wird None zurückgegeben.

    Returns:
        Die bereinigte Zeichenkette mit entfernten Zielwörtern und normalisierten Leerzeichen;
        oder None, wenn die Eingabe None war.

    Example Usage:
        >>> remove_german_articles('Hans von der Heide')
        'Hans Heide'
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    cleaned = _REMOVE_WORDS_PATTERN.sub("", input_string)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Module-level EncodingFixer instance (map is built once, shared across calls)
_ENCODING_FIXER_DE = EncodingFixer(language="de")


def fix_german_conversion_fails(input_string, add_charset=""):
    """
    Fix text conversion failures using EncodingFixer.

    Delegates mojibake repair to ``EncodingFixer`` (universal detection
    and repair) and applies language-specific legacy substitutions.

    Args:
        input_string: Text to clean. If ``None``, returns ``None``.
        add_charset: Kept for backward compatibility (no effect).

    Returns:
        Cleaned text or ``None`` if input is ``None``.
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    s = input_string

    # Universal mojibake repair via EncodingFixer
    s = _ENCODING_FIXER_DE.fix(s)

    # Normalize spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


def reduce_letters_german(input_string, strength):
    """
    Reduziert Buchstaben nach phonetischen Regeln für Vergleiche auf Deutsch.

    Args:
        input_string: Eingabetext. Bei None wird None zurückgegeben.
        strength: Aggressivitätsstufe der Transformation (0..3).
            - 0: keine Änderungen (normalisiert nur Akzente)
            - 1: leichte Änderungen (Umlaute, häufige Digraphen, stumme Buchstaben)
            - 2: mittlere Änderungen (Sibilanten vereinheitlicht, Konsonantencluster)
            - 3: aggressive Änderungen (internationale Normalisierung)

    Returns:
        Transformierter Text.

    Example Usage:
        >>> reduce_letters_german('Müller Straße', 1)
        'MUELLER STRASSE'
        >>> reduce_letters_german('Schneider', 2)
        'SNEIDER'
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    try:
        level = int(strength)
    except Exception:
        level = 1
    level = max(0, min(level, 3))

    if level == 0:
        return "".join(ch for ch in unicodedata.normalize("NFD", input_string) if not unicodedata.combining(ch))

    def detect_style(s: str) -> str:
        if s.islower():
            return "lower"
        if s.isupper():
            return "upper"
        if s.istitle():
            return "title"
        return "mixed"

    orig_style = detect_style(input_string)

    # First handle umlauts and ß BEFORE accent removal (they have specific expansions)
    s = input_string.upper()
    umlaut_map = [
        ("Ä", "AE"),
        ("Ö", "OE"),
        ("Ü", "UE"),
        ("ß", "SS"),
    ]
    for src, dst in umlaut_map:
        s = s.replace(src, dst)
        s = s.replace(src.lower(), dst)

    def remove_accents(text: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch))

    oparse = remove_accents(s).upper()

    # STUFE 1: Grundlegende phonetische Reduktionen des Deutschen
    if level >= 1:
        replacements_level_1 = [
            ("SCH", "S"),  # SCH -> S (Sch-Laut: Schule -> Sule)
            ("CK", "K"),  # CK -> K (Stück -> Stük)
            ("PH", "F"),  # PH -> F (Philosophie -> Filosofie)
            ("QU", "KV"),  # QU -> KV (Quelle -> Kvelle)
            ("TH", "T"),  # TH -> T (Theater -> Teater)
            ("CH", "H"),  # CH -> H (ich/ach-Laut: Buch -> Buh)
            ("RH", "R"),  # RH -> R (Rhein -> Rein)
            ("DT", "T"),  # DT -> T (Stadt -> Stat)
            ("TZ", "Z"),  # TZ -> Z (Katze -> Kaze)
        ]
        for src, dst in replacements_level_1:
            oparse = oparse.replace(src, dst)

        single_level_1 = [
            ("H", ""),  # H stumm nach Vokal (Ruhe -> Rue)
            ("V", "F"),  # V -> F (Vater -> Fater)
            ("Y", "I"),  # Y -> I (Gymnasium -> Gimnasium)
        ]
        for src, dst in single_level_1:
            oparse = oparse.replace(src, dst)

    # STUFE 2: Mittlere Reduktionen (Sibilanten und Konsonantengruppen)
    if level >= 2:
        replacements_level_2 = [
            ("Z", "S"),  # Z -> S (TS-Laut vereinfacht zu S)
            ("C", "K"),  # C -> K (vor a/o/u)
            ("X", "KS"),  # X -> KS
            ("SS", "S"),  # SS -> S (Doppel-S vereinfacht)
            ("KN", "N"),  # KN -> N (Knecht -> Necht)
            ("GN", "N"),  # GN -> N
            ("PF", "F"),  # PF -> F (Pferd -> Ferd)
            ("NG", "N"),  # NG -> N (Ring -> Rin)
            ("NK", "N"),  # NK -> N (Bank -> Ban)
            ("MB", "M"),  # MB -> M
        ]
        for src, dst in replacements_level_2:
            oparse = oparse.replace(src, dst)

    # STUFE 3: Aggressive Reduktionen (internationale Normalisierung)
    if level >= 3:
        replacements_level_3 = [
            ("W", "V"),  # W -> V
            ("Q", "K"),  # Q -> K
            ("D", "T"),  # D -> T (Auslautverhärtung)
            ("B", "P"),  # B -> P (Auslautverhärtung)
            ("G", "K"),  # G -> K (Auslautverhärtung)
            ("F", "V"),  # F/V Vereinheitlichung
        ]
        for src, dst in replacements_level_3:
            oparse = oparse.replace(src, dst)

    if orig_style == "lower":
        return oparse.lower()
    if orig_style == "title":
        return oparse.title()
    if orig_style == "mixed":
        return oparse.lower()
    return oparse


def raw_string_german(input_string, accuracy):
    """
    Bereitet eine Zeichenkette für Textvergleiche auf Deutsch vor, indem
    Bereinigung und phonetische Reduktion angewendet werden.

    Args:
        input_string: Eingabetext. Bei None wird None zurückgegeben.
        accuracy: Aggressivitätsstufe der phonetischen Reduktion (0..3).

    Returns:
        Verarbeiteter Text für Vergleiche.

    Example Usage:
        >>> raw_string_german('Hans von der Heide', 2)
        'HANS HEIDE'
    """
    if input_string is None:
        return None

    cleaned = fix_german_conversion_fails(input_string)
    reduced = reduce_letters_german(cleaned, accuracy)
    return reduced
