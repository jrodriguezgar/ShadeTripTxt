import re
import unicodedata
from typing import Optional

from .encoding_fixer import EncodingFixer

# Liste di parole per operazioni categorizzate grammaticalmente:
# Elenco di parole di collegamento in italiano, omettibili in certi processi di analisi del testo.
# Mantenute in maiuscolo per confronti normalizzati.

# Prefissi e particelle nei nomi propri
_NAME_PREFIXES = ["SAN", "SANTA", "DI", "DA", "DEL", "DELLA", "DELLO", "DEGLI", "DELLE", "VAN", "VON", "DER", "MC", "MAC"]

# Avverbi comuni/connettori
_ADVERBS = ["GIÀ", "ANCORA", "ANCHE", "COSÌ", "ADESSO"]

# Pronomi personali e oggetti
_PRONOUNS = ["IO", "TU", "LUI", "LEI", "NOI", "VOI", "LORO", "ME", "TE", "SI", "CE", "VI", "CI", "GLI", "LE"]

# Determinanti (dimostrativi/possessivi)
_DETERMINANTS = [
    "QUESTO",
    "QUESTA",
    "QUESTI",
    "QUESTE",
    "QUELLO",
    "QUELLA",
    "MIO",
    "MIA",
    "MIEI",
    "MIE",
    "TUO",
    "TUA",
    "TUOI",
    "TUE",
    "SUO",
    "SUA",
    "SUOI",
    "SUE",
]

# Articoli
_ARTICLES = ["IL", "LO", "LA", "I", "GLI", "LE", "UN", "UNO", "UNA", "L'", "UN'"]

# Preposizioni (semplici + articolate)
_PREPOSITIONS = [
    "A",
    "AL",
    "ALLO",
    "ALLA",
    "AI",
    "AGLI",
    "ALLE",
    "CON",
    "DA",
    "DAL",
    "DALLO",
    "DALLA",
    "DAI",
    "DAGLI",
    "DALLE",
    "DI",
    "DEL",
    "DELLO",
    "DELLA",
    "DEI",
    "DEGLI",
    "DELLE",
    "FRA",
    "TRA",
    "IN",
    "NEL",
    "NELLO",
    "NELLA",
    "NEI",
    "NEGLI",
    "NELLE",
    "PER",
    "SU",
    "SUL",
    "SULLO",
    "SULLA",
    "SUI",
    "SUGLI",
    "SULLE",
    "SECONDO",
    "SENZA",
    "SOPRA",
    "SOTTO",
    "VERSO",
]

# Congiunzioni
_CONJUNCTIONS = ["E", "ED", "O", "NÉ", "MA", "PERÒ", "ANCHE", "OPPURE", "PERCHÉ", "CHE", "QUANDO", "MENTRE", "SEBBENE"]

# Elenco di parole da omettere in certi processi di analisi.
_SKIP_WORDS_MAP = ["E", "ED", "O", "A", "DI", "DA", "IL", "LO", "LA", "LE", "GLI", "UN", "UNA", "AL", "DEL", "NEL", "CON", "PER", "IN", "SU"]


# Precompile a regex for words to remove (articles, prepositions, conjunctions).
_REMOVE_WORDS_SET = {w.upper() for w in (_ARTICLES + _PREPOSITIONS + _CONJUNCTIONS)}
_REMOVE_WORDS_SORTED = sorted(_REMOVE_WORDS_SET, key=len, reverse=True)
_REMOVE_WORDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _REMOVE_WORDS_SORTED) + r")\b", flags=re.IGNORECASE)

# Special pattern for Italian elided articles: l', d', un', dell', nell', sull', all', dall'
_ELISION_PATTERN = re.compile(r"\b(?:dell|nell|sull|all|dall|[ld]|un)'", flags=re.IGNORECASE)


def remove_italian_articles(input_string: Optional[str]) -> Optional[str]:
    """
    Rimuove articoli, preposizioni e congiunzioni comuni in italiano da una stringa.

    Args:
        input_string: La stringa di input da pulire. Se None, restituisce None.

    Returns:
        La stringa risultante con le parole obiettivo rimosse e gli spazi normalizzati;
        o None se l'input era None.

    Example Usage:
        >>> remove_italian_articles('Giovanni della Rovere')
        'Giovanni Rovere'
        >>> remove_italian_articles("l'albergo del centro")
        "albergo centro"
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    # Remove elided articles first (l', d', dell', etc.)
    cleaned = _ELISION_PATTERN.sub("", input_string)

    # Then remove standard words
    cleaned = _REMOVE_WORDS_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Module-level EncodingFixer instance (map is built once, shared across calls)
_ENCODING_FIXER_IT = EncodingFixer(language="it")

# Legacy pre-processing: codepage conventions that are NOT mojibake
_LEGACY_MAP_IT = {
    "§": "º",  # section sign → masculine ordinal
}


def fix_italian_conversion_fails(input_string, add_charset=""):
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

    # Universal mojibake repair via EncodingFixer (must run first
    # to avoid legacy substitutions corrupting mojibake sequences)
    s = _ENCODING_FIXER_IT.fix(input_string)

    # Legacy post-processing (non-mojibake codepage conventions)
    for src, dst in _LEGACY_MAP_IT.items():
        if src in s:
            s = s.replace(src, dst)

    # Normalize spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


def reduce_letters_italian(input_string, strength):
    """
    Riduce le lettere secondo regole fonetiche per confronti in italiano.

    Args:
        input_string: Testo di input. Se None, restituisce None.
        strength: Livello di aggressività della trasformazione (0..3).
            - 0: nessun cambiamento (normalizza solo gli accenti)
            - 1: cambiamenti leggeri (H muta, digrafi, omofoni base)
            - 2: cambiamenti intermedi (sibilanti unificate, cluster consonantici)
            - 3: cambiamenti aggressivi (normalizzazione internazionale)

    Returns:
        Testo trasformato.

    Example Usage:
        >>> reduce_letters_italian('Giuseppe Bianchi', 1)
        'GIUSEPPE BIANCHI'
        >>> reduce_letters_italian('Chiara Gnocchi', 2)
        'CIARA NOCI'
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

    def remove_accents(s: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch))

    oparse = remove_accents(input_string).upper()

    # LIVELLO 1: Riduzioni fonetiche basiche dell'italiano
    if level >= 1:
        replacements_level_1 = [
            ("GLI", "LI"),  # GLI -> LI (suono palatale: figlio -> filio)
            ("GN", "NI"),  # GN -> NI (suono palatale: gnocchi -> niocchi)
            ("SCE", "SE"),  # SCE -> SE (scena -> sena)
            ("SCI", "SI"),  # SCI -> SI (scienza -> sienza)
            ("CHI", "KI"),  # CHI -> KI (chiave -> kiave)
            ("CHE", "KE"),  # CHE -> KE (che -> ke)
            ("GHI", "GI"),  # GHI -> GI (ghiaccio -> giaccio)
            ("GHE", "GE"),  # GHE -> GE (ghetto -> getto)
            ("QU", "CU"),  # QU -> CU (questo -> cuesto)
            ("CQ", "C"),  # CQ -> C (acqua -> acua)
        ]
        for src, dst in replacements_level_1:
            oparse = oparse.replace(src, dst)

        single_level_1 = [
            ("H", ""),  # H è muta in italiano (hotel -> otel)
            ("Y", "I"),  # Y -> I
            ("K", "C"),  # K -> C
            ("W", "V"),  # W -> V
            ("J", "I"),  # J -> I (Juventus -> Iuventus)
            ("X", "CS"),  # X -> CS
        ]
        for src, dst in single_level_1:
            oparse = oparse.replace(src, dst)

    # LIVELLO 2: Riduzioni intermedie (sibilanti e cluster)
    if level >= 2:
        replacements_level_2 = [
            ("SS", "S"),  # SS -> S (doppia semplificata)
            ("ZZ", "Z"),  # ZZ -> Z (piazza -> piaza)
            ("CC", "C"),  # CC -> C
            ("LL", "L"),  # LL -> L
            ("RR", "R"),  # RR -> R
            ("NN", "N"),  # NN -> N
            ("TT", "T"),  # TT -> T
            ("PP", "P"),  # PP -> P
            ("BB", "B"),  # BB -> B
            ("MM", "M"),  # MM -> M
            ("FF", "F"),  # FF -> F
            ("GG", "G"),  # GG -> G
            ("Z", "S"),  # Z -> S (unificazione sibilanti)
            ("SC", "S"),  # SC -> S (ante e/i)
        ]
        for src, dst in replacements_level_2:
            oparse = oparse.replace(src, dst)

    # LIVELLO 3: Riduzioni aggressive (normalizzazione internazionale)
    if level >= 3:
        replacements_level_3 = [
            ("PH", "F"),  # PH -> F
            ("TH", "T"),  # TH -> T
            ("D", "T"),  # D -> T
            ("P", "B"),  # P -> B
            ("T", "D"),  # T -> D
            ("G", "C"),  # G -> C
            ("V", "F"),  # V -> F
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


def raw_string_italian(input_string, accuracy):
    """
    Prepara una stringa per confronti testuali in italiano applicando
    pulizia e riduzione fonetica.

    Args:
        input_string: Testo di input. Se None, restituisce None.
        accuracy: Livello di aggressività nella riduzione fonetica (0..3).

    Returns:
        Testo elaborato pronto per confronti.

    Example Usage:
        >>> raw_string_italian('Giovanni della Rovere', 2)
        'GIOVANNI ROVERE'
    """
    if input_string is None:
        return None

    cleaned = fix_italian_conversion_fails(input_string)
    reduced = reduce_letters_italian(cleaned, accuracy)
    return reduced
