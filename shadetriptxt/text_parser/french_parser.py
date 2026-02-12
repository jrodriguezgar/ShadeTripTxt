# Listes de mots pour opérations catégorisées grammaticalement :
# Liste de mots de liaison en français, pouvant être omis dans certains processus d'analyse de texte.
# Conservés en majuscules pour des comparaisons normalisées.

# Préfixes et particules dans les noms propres
_NAME_PREFIXES = ['SAINT', 'SAINTE', 'DE', 'DU', 'DES', 'LE', 'LA', 'VAN', 'VON', 'DER', 'MC', 'MAC']

# Adverbes communs/connecteurs
_ADVERBS = ['DÉJÀ', 'ENCORE', 'AUSSI', 'AINSI', 'MAINTENANT']

# Pronoms personnels et objets
_PRONOUNS = ['JE', 'TU', 'IL', 'ELLE', 'ON', 'NOUS', 'VOUS', 'ILS', 'ELLES', 'ME', 'TE', 'SE', 'LUI', 'LEUR', 'MOI', 'TOI']

# Déterminants (démonstratifs/possessifs)
_DETERMINANTS = ['CE', 'CET', 'CETTE', 'CES', 'MON', 'MA', 'MES', 'TON', 'TA', 'TES', 'SON', 'SA', 'SES', 'NOTRE', 'VOTRE', 'LEUR', 'LEURS']

# Articles
_ARTICLES = ['LE', 'LA', 'LES', 'UN', 'UNE', 'DES', "L'"]

# Prépositions
_PREPOSITIONS = ['À', 'AU', 'AUX', 'AVEC', 'CHEZ', 'CONTRE', 'DANS', 'DE', 'DU', 'DES', 'DEPUIS', 'EN', 'ENTRE', 'ENVERS', 'HORS', 'PAR', 'PARMI', 'PENDANT', 'POUR', 'SANS', 'SOUS', 'SUR', 'VERS']

# Conjonctions
_CONJUNCTIONS = ['ET', 'OU', 'NI', 'MAIS', 'OR', 'DONC', 'CAR', 'QUE', 'PUISQUE', 'QUOIQUE', 'LORSQUE', 'PARCE']

# Liste de mots à omettre dans certains processus d'analyse.
_SKIP_WORDS_MAP = [
    'ET', 'OU', 'DE', 'DU', 'DES', 'LE', 'LA', 'LES',
    'AU', 'AUX', 'UN', 'UNE', 'EN', 'À', 'PAR', 'POUR', 'DANS'
]


import re
from typing import Optional
from .encoding_fixer import EncodingFixer


# Precompile a regex for words to remove (articles, prepositions, conjunctions).
_REMOVE_WORDS_SET = {w.upper() for w in (_ARTICLES + _PREPOSITIONS + _CONJUNCTIONS)}
_REMOVE_WORDS_SORTED = sorted(_REMOVE_WORDS_SET, key=len, reverse=True)
_REMOVE_WORDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _REMOVE_WORDS_SORTED) + r")\b", flags=re.IGNORECASE)

# Special pattern for French elided articles: l', d', n', s', j', qu'
_ELISION_PATTERN = re.compile(r"\b[ldnsjLDNSJ]'", flags=re.IGNORECASE)


def remove_french_articles(input_string: Optional[str]) -> Optional[str]:
    """
    Supprime les articles, prépositions et conjonctions courants en français d'une chaîne.

    Args:
        input_string: La chaîne d'entrée à nettoyer. Si None, retourne None.

    Returns:
        La chaîne résultante avec les mots cibles supprimés et les espaces normalisés ;
        ou None si l'entrée était None.

    Example Usage:
        >>> remove_french_articles('Jean de la Fontaine')
        'Jean Fontaine'
        >>> remove_french_articles("l'hôtel du centre")
        "hôtel centre"
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    # Remove elided articles first (l', d', etc.)
    cleaned = _ELISION_PATTERN.sub('', input_string)

    # Then remove standard words
    cleaned = _REMOVE_WORDS_PATTERN.sub('', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# Module-level EncodingFixer instance (map is built once, shared across calls)
_ENCODING_FIXER_FR = EncodingFixer(language='fr')

# Legacy pre-processing: codepage conventions that are NOT mojibake
_LEGACY_MAP_FR = {
    "§": "º",   # section sign → masculine ordinal
}


def fix_french_conversion_fails(input_string, add_charset=''):
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
    s = _ENCODING_FIXER_FR.fix(input_string)

    # Legacy post-processing (non-mojibake codepage conventions)
    for src, dst in _LEGACY_MAP_FR.items():
        if src in s:
            s = s.replace(src, dst)

    # Normalize spaces
    s = re.sub(r'\s+', ' ', s).strip()

    return s


def reduce_letters_french(input_string, strength):
    """
    Réduit les lettres selon des règles phonétiques pour des comparaisons en français.

    Args:
        input_string: Texte d'entrée. Si None, retourne None.
        strength: Niveau d'agressivité de la transformation (0..3).
            - 0 : pas de changements (normalise uniquement les accents)
            - 1 : changements légers (H muet, digraphes, homophones de base)
            - 2 : changements intermédiaires (sibilantes unifiées, groupes consonantiques)
            - 3 : changements agressifs (normalisation internationale)

    Returns:
        Texte transformé.

    Example Usage:
        >>> reduce_letters_french('François Lefèvre', 1)
        'FRANCOIS LEFEVRE'
        >>> reduce_letters_french('Philippe', 2)
        'FILIPE'
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
        import unicodedata
        return ''.join(ch for ch in unicodedata.normalize('NFD', input_string) if not unicodedata.combining(ch))

    def detect_style(s: str) -> str:
        if s.islower():
            return 'lower'
        if s.isupper():
            return 'upper'
        if s.istitle():
            return 'title'
        return 'mixed'

    orig_style = detect_style(input_string)

    import unicodedata
    def remove_accents(s: str) -> str:
        return ''.join(ch for ch in unicodedata.normalize('NFD', s) if not unicodedata.combining(ch))

    oparse = remove_accents(input_string).upper()

    # NIVEAU 1 : Réductions phonétiques basiques du français
    if level >= 1:
        replacements_level_1 = [
            ('OU', 'U'),    # OU -> U (son /u/: ou, nous, tout)
            ('AU', 'O'),    # AU -> O (son /o/: au, beau, chaud)
            ('EAU', 'O'),   # EAU -> O (son /o/: beau, château)
            ('PH', 'F'),    # PH -> F (philosophie -> filosofie)
            ('QU', 'K'),    # QU -> K (que -> ke)
            ('GU', 'G'),    # GU -> G (guerre -> gere)
            ('CH', 'S'),    # CH -> S (son /ʃ/: chat, cher)
            ('GN', 'NI'),   # GN -> NI (son /ɲ/: campagne -> campanie)
            ('OI', 'OA'),   # OI -> OA (son /wa/: roi -> roa)
            ('AI', 'E'),    # AI -> E (son /ɛ/: maison -> meson)
            ('EI', 'E'),    # EI -> E (son /ɛ/: reine -> rene)
        ]
        for src, dst in replacements_level_1:
            oparse = oparse.replace(src, dst)

        single_level_1 = [
            ('H', ''),      # H est muet en français (hôtel, homme)
            ('Y', 'I'),     # Y -> I (bicycle -> bicisle)
            ('K', 'C'),     # K -> C (kilo -> cilo)
            ('W', 'V'),     # W -> V (Wagner -> Vagner)
        ]
        for src, dst in single_level_1:
            oparse = oparse.replace(src, dst)

    # NIVEAU 2 : Réductions intermédiaires (sibilantes et nasales)
    if level >= 2:
        replacements_level_2 = [
            ('AN', 'EN'),   # AN/EN nasale unifiée
            ('AM', 'EM'),   # AM/EM nasale unifiée
            ('IN', 'EN'),   # IN unifier avec EN
            ('IM', 'EM'),   # IM unifier avec EM
            ('ON', 'EN'),   # ON unifier avec EN (agressif)
            ('SS', 'S'),    # SS -> S (poisson -> poison... simplification)
            ('SC', 'S'),    # SC -> S (ante e/i: science -> sience)
            ('Ç', 'S'),     # Ç -> S (français -> francais via S)
            ('C', 'S'),     # C -> S (ante e/i)
            ('X', 'S'),     # X -> S en fin de mot (voix -> vois)
            ('Z', 'S'),     # Z -> S (nez -> nes)
        ]
        for src, dst in replacements_level_2:
            oparse = oparse.replace(src, dst)

    # NIVEAU 3 : Réductions agressives (normalisation internationale)
    if level >= 3:
        replacements_level_3 = [
            ('TH', 'T'),    # TH -> T (théâtre -> teatre)
            ('Œ', 'E'),     # Œ -> E (cœur -> ceur)
            ('Æ', 'E'),     # Æ -> E
            ('Q', 'K'),     # Q -> K (sans QU)
            ('D', 'T'),     # D -> T (fin de mot)
            ('P', 'B'),     # P/B
            ('T', 'D'),     # T -> D
            ('F', 'V'),     # F -> V
        ]
        for src, dst in replacements_level_3:
            oparse = oparse.replace(src, dst)

    if orig_style == 'lower':
        return oparse.lower()
    if orig_style == 'title':
        return oparse.title()
    if orig_style == 'mixed':
        return oparse.lower()
    return oparse


def raw_string_french(input_string, accuracy):
    """
    Prépare une chaîne pour des comparaisons de texte en français en appliquant
    nettoyage et réduction phonétique.

    Args:
        input_string: Texte d'entrée. Si None, retourne None.
        accuracy: Niveau d'agressivité de la réduction phonétique (0..3).

    Returns:
        Texte traité prêt pour des comparaisons.

    Example Usage:
        >>> raw_string_french('Jean de la Fontaine', 2)
        'JEAN FONTAINE'
    """
    if input_string is None:
        return None

    cleaned = fix_french_conversion_fails(input_string)
    reduced = reduce_letters_french(cleaned, accuracy)
    return reduced
