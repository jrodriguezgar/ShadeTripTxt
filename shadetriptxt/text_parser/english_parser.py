import re
import unicodedata
from typing import Optional

from .encoding_fixer import EncodingFixer

# Lists of words for grammatically categorized operations:
# List of join words in English, can be omitted in certain text analysis processes.
# Kept in uppercase for normalized comparisons.

# Prefixes and particles in proper names
_NAME_PREFIXES = ["MR", "MRS", "MS", "DR", "SIR", "LORD", "VAN", "VON", "DER", "DEN", "MC", "MAC", "O"]

# Adverbs common/connectors
_ADVERBS = ["ALSO", "NOW", "THEN", "HERE", "THERE"]

# Personal pronouns and objects
_PRONOUNS = ["I", "YOU", "HE", "SHE", "IT", "WE", "THEY", "ME", "HIM", "HER", "US", "THEM"]

# Determiners (includes demonstratives/possessives if desired to extend)
_DETERMINANTS = ["THIS", "THAT", "THESE", "THOSE", "MY", "YOUR", "HIS", "HER", "ITS", "OUR", "THEIR"]

# Articles
_ARTICLES = ["THE", "A", "AN"]

# Prepositions
_PREPOSITIONS = [
    "TO",
    "IN",
    "ON",
    "AT",
    "BY",
    "FOR",
    "WITH",
    "ABOUT",
    "AGAINST",
    "BETWEEN",
    "INTO",
    "THROUGH",
    "DURING",
    "BEFORE",
    "AFTER",
    "ABOVE",
    "BELOW",
    "FROM",
    "OF",
    "OFF",
    "OVER",
    "UNDER",
    "UP",
    "DOWN",
]

# Conjunctions
_CONJUNCTIONS = ["AND", "OR", "BUT", "NOR", "SO", "FOR", "YET", "THOUGH", "ALTHOUGH", "WHILE", "BECAUSE", "SINCE", "AS", "THAT"]

# List of words to skip in certain text analysis processes.
_SKIP_WORDS_MAP = [
    "AND",
    "OR",
    "BUT",
    "TO",
    "IN",
    "ON",
    "AT",
    "BY",
    "FOR",
    "WITH",
    "THE",
    "A",
    "AN",
    "OF",
    "FROM",
    "AS",
    "THAT",
    "THIS",
    "THESE",
    "THOSE",
]


# Precompile a regex for words to remove (articles, prepositions, conjunctions).
# Sorting by length prevents partial matches (e.g. matching 'A' inside 'AT').
_REMOVE_WORDS_SET = {w.upper() for w in (_ARTICLES + _PREPOSITIONS + _CONJUNCTIONS)}
_REMOVE_WORDS_SORTED = sorted(_REMOVE_WORDS_SET, key=len, reverse=True)
_REMOVE_WORDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _REMOVE_WORDS_SORTED) + r")\b", flags=re.IGNORECASE)


def remove_english_articles(input_string: Optional[str]) -> Optional[str]:
    """
    Removes common articles, prepositions, and conjunctions in English from a string.

    Description:
        Removes functional words (articles, prepositions, and conjunctions)
        defined in the lists `_ARTICLES`, `_PREPOSITIONS`, and `_CONJUNCTIONS`.

    Args:
        input_string: The input string to be cleaned. If `None`,
            returns `None`.

    Returns:
        The resulting string with target words removed and spaces
        normalized; or `None` if input was `None`.

    Raises:
        Does not raise explicit exceptions. Internally may propagate errors
        if a non-convertible type is passed.

    Example Usage:
        >>> remove_english_articles('John of the Hill')
        'John Hill'

    Cost:
        O(n) in the length of the input string (pattern compilation is O(m)
        where m is the total target words, but done once at module load).
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        # Attempt to convert to str for robustness
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    # Use the precompiled pattern to remove target words
    cleaned = _REMOVE_WORDS_PATTERN.sub("", input_string)

    # Normalize extra spaces and return
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


# Module-level EncodingFixer instance (map is built once, shared across calls)
_ENCODING_FIXER_EN = EncodingFixer(language="en")


def fix_english_conversion_fails(input_string, add_charset=""):
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
    s = _ENCODING_FIXER_EN.fix(s)

    # Normalize spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


def reduce_letters_english(input_string, strength):
    """
    Reduces letters according to phonetic/normalization rules for phonetic comparisons in English.

    Description:
        Applies progressive phonetic transformations based on sound similarities
        in English. Useful for fuzzy searches and name comparisons.

    Args:
        input_string: Input text. If `None`, returns `None`.
        strength: Level of transformation aggressiveness (0..3).
            - 0: no changes (only normalizes accents)
            - 1: mild changes (silent H, common digraphs, basic homophones)
            - 2: intermediate changes (C/S/Z/X unified, similar consonants)
            - 3: aggressive changes (international normalization: W->V, etc.)

    Returns:
        Transformed text maintaining original capitalization style when possible.

    Raises:
        Does not raise exceptions; returns unmodified input if conversion fails.

    Example Usage:
        >>> reduce_letters_english('Joseph Garcia', 1)
        'JOSEPH GARSIA'
        >>> reduce_letters_english('Smith', 2)
        'SMITH'

    Cost: O(n) in the text length.
    """
    if input_string is None:
        return None

    # Ensure types
    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    # Normalize strength level
    try:
        level = int(strength)
    except Exception:
        level = 1
    level = max(0, min(level, 3))

    # If level is 0, only normalize accents and return
    if level == 0:
        result = "".join(ch for ch in unicodedata.normalize("NFD", input_string) if not unicodedata.combining(ch))
        return result

    # Detect capitalization style to restore at the end
    def detect_style(s: str) -> str:
        if s.islower():
            return "lower"
        if s.isupper():
            return "upper"
        if s.istitle():
            return "title"
        return "mixed"

    orig_style = detect_style(input_string)

    # Safely remove accents (but keep base characters)
    def remove_accents(s: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch))

    oparse = remove_accents(input_string).upper()

    # LEVEL 1: Basic phonetic reductions in English
    # - Silent H (in some words)
    # - Common digraphs: PH->F, GH->G (silent), etc.
    # - Basic homophones: C/K, S/Z, etc.
    if level >= 1:
        # Process multi-character sequences first
        replacements_level_1 = [
            # Digraphs and special sequences
            ("PH", "F"),  # PH -> F (phone)
            ("GH", "G"),  # GH -> G (though often silent, normalize to G)
            ("WH", "W"),  # WH -> W (simplification)
            ("TH", "T"),  # TH -> T (simplification, though sound varies)
            ("CH", "C"),  # CH -> C (simplification)
            ("SH", "S"),  # SH -> S
            ("CK", "K"),  # CK -> K
        ]
        for src, dst in replacements_level_1:
            oparse = oparse.replace(src, dst)

        # Single letter replacements (homophones and silent letters)
        single_level_1 = [
            ("H", ""),  # H often silent in English
            ("K", "C"),  # K sounds like C
            ("Z", "S"),  # Z and S are homophones in some dialects
            ("X", "KS"),  # X -> KS (but keep for now, or simplify later)
        ]
        for src, dst in single_level_1:
            oparse = oparse.replace(src, dst)

    # LEVEL 2: Intermediate reductions (unify sibilants and similar consonants)
    # - Unify S/C/Z (sibilants)
    # - Simplify consonant clusters
    if level >= 2:
        replacements_level_2 = [
            # Unify sibilants (all to S)
            ("C", "S"),  # Unify C with S
            ("Z", "S"),  # Already done, but ensure
            ("X", "S"),  # X to S (simplification)
            # Consonant cluster simplifications
            ("KN", "N"),  # KN -> N (knight)
            ("WR", "R"),  # WR -> R (write)
            ("MB", "M"),  # MB -> M (lamb)
        ]
        for src, dst in replacements_level_2:
            oparse = oparse.replace(src, dst)

    # LEVEL 3: Aggressive reductions (international normalization)
    # - Remove English-specific characters
    # - Unify foreign sounds
    # - Maximum phonetic simplification
    if level >= 3:
        replacements_level_3 = [
            # Normalization of specific characters
            ("W", "V"),  # W -> V (international)
            ("Q", "K"),  # Q -> K
            # Extreme simplifications
            ("F", "V"),  # F and V can alternate
            ("P", "B"),  # P and B
            ("T", "D"),  # T and D
            ("S", "Z"),  # Reverse for some dialects
        ]
        for src, dst in replacements_level_3:
            oparse = oparse.replace(src, dst)

    # Restore original capitalization style
    if orig_style == "lower":
        return oparse.lower()
    if orig_style == "title":
        return oparse.title()
    if orig_style == "mixed":
        return oparse.lower()
    # 'upper'
    return oparse


def raw_string_english(input_string, accuracy):
    """
    Prepares a string for text comparisons in English by applying
    cleaning and phonetic reduction according to accuracy level.

    Description:
        Combines cleaning of conversion failures and phonetic reduction
        adapted to English for a "raw" representation suitable for fuzzy comparisons.

    Args:
        input_string: Input text. If `None`, returns `None`.
        accuracy: Level of aggressiveness in phonetic reduction (0..3).

    Returns:
        Processed text ready for comparisons.

    Raises:
        Does not raise exceptions; returns unmodified input if conversion fails.

    Example Usage:
        >>> raw_string_english('Joseph of the Hill', 2)
        'JOSEPH HILL'
        >>> raw_string_english('Smith', 3)
        'SMITH'

    Cost: O(n) in the text length.
    """
    if input_string is None:
        return None

    # First clean conversion failures
    cleaned = fix_english_conversion_fails(input_string)

    # Then apply phonetic reduction
    reduced = reduce_letters_english(cleaned, accuracy)

    return reduced
