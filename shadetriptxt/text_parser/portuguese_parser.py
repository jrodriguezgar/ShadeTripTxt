# Listas de palavras para operações categorizadas gramaticalmente:
# Listado de palavras de ligação em português, podem ser omitidas em certos processos de análise de texto.
# Mantidas em maiúsculas para comparações normalizadas.

# Prefixos e partículas em nomes próprios
_NAME_PREFIXES = ['SÃO', 'SANTA', 'DA', 'DAS', 'DO', 'DOS', 'DE', 'VAN', 'VON', 'DER', 'MC', 'MAC']

# Advérbios comuns/conectores
_ADVERBS = ['JÁ', 'AINDA', 'TAMBÉM', 'ASSIM', 'AGORA']

# Pronomes pessoais e objetos
_PRONOUNS = ['EU', 'TU', 'VOCÊ', 'VOCÊS', 'ELE', 'ELA', 'ELES', 'ELAS', 'NÓS', 'VÓS', 'ME', 'TE', 'SE', 'NOS', 'VOS', 'LHE', 'LHES', 'O', 'A']

# Determinantes (demonstrativos/possessivos)
_DETERMINANTS = ['ESTE', 'ESTA', 'ESTES', 'ESTAS', 'ESSE', 'ESSA', 'ESSES', 'ESSAS', 'AQUELE', 'AQUELA', 'MEU', 'MEUS', 'MINHA', 'MINHAS', 'TEU', 'TEUS', 'TUA', 'TUAS']

# Artigos
_ARTICLES = ['O', 'A', 'OS', 'AS', 'UM', 'UMA', 'UNS', 'UMAS']

# Preposições
_PREPOSITIONS = ['A', 'AO', 'AOS', 'ANTE', 'APÓS', 'ATÉ', 'COM', 'CONTRA', 'DE', 'DO', 'DA', 'DOS', 'DAS', 'DESDE', 'EM', 'NO', 'NA', 'NOS', 'NAS', 'ENTRE', 'PARA', 'POR', 'PELO', 'PELA', 'PELOS', 'PELAS', 'SEM', 'SOB', 'SOBRE', 'TRAS']

# Conjunções
_CONJUNCTIONS = ['E', 'NEM', 'OU', 'QUE', 'PORQUE', 'MAS', 'PORÉM', 'TODAVIA', 'CONTUDO', 'TAMBÉM']

# Listado de palavras para omitir em certos processos de análise de texto.
_SKIP_WORDS_MAP = [
    'E', 'OU', 'A', 'O',
    'AO', 'AS', 'OS', 'DE', 'DA', 'DO', 'NO', 'NA',
    'NOS', 'DAS', 'DOS', 'NAS', 'UM', 'UMA'
]


import re
from typing import Optional
from .encoding_fixer import EncodingFixer


# Precompile a regex for words to remove (articles, prepositions, conjunctions).
_REMOVE_WORDS_SET = {w.upper() for w in (_ARTICLES + _PREPOSITIONS + _CONJUNCTIONS)}
_REMOVE_WORDS_SORTED = sorted(_REMOVE_WORDS_SET, key=len, reverse=True)
_REMOVE_WORDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _REMOVE_WORDS_SORTED) + r")\b", flags=re.IGNORECASE)


def remove_portuguese_articles(input_string: Optional[str]) -> Optional[str]:
    """
    Remove artigos, preposições e conjunções comuns em português de uma string.

    Args:
        input_string: A string de entrada a ser limpa. Se None, retorna None.

    Returns:
        A string resultante com as palavras-alvo removidas e espaços normalizados;
        ou None se a entrada era None.

    Example Usage:
        >>> remove_portuguese_articles('João da Silva')
        'João Silva'
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    cleaned = _REMOVE_WORDS_PATTERN.sub('', input_string)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# Module-level EncodingFixer instance (map is built once, shared across calls)
_ENCODING_FIXER_PT = EncodingFixer(language='pt')

# Legacy pre-processing: codepage conventions that are NOT mojibake
_LEGACY_MAP_PT = {
    "§": "º",   # section sign → masculine ordinal
    "¥": "Ñ",   # yen sign → Ñ (CP437/CP850 convention)
}


def fix_portuguese_conversion_fails(input_string, add_charset=''):
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
    s = _ENCODING_FIXER_PT.fix(input_string)

    # Legacy post-processing (non-mojibake codepage conventions)
    for src, dst in _LEGACY_MAP_PT.items():
        if src in s:
            s = s.replace(src, dst)

    # Normalize spaces
    s = re.sub(r'\s+', ' ', s).strip()

    return s


def reduce_letters_portuguese(input_string, strength):
    """
    Reduz letras segundo regras fonéticas para comparações em português.

    Args:
        input_string: Texto de entrada. Se None, retorna None.
        strength: Nível de agressividade da transformação (0..3).
            - 0: sem mudanças (apenas normaliza acentos)
            - 1: mudanças leves (H mudo, dígrafos, homófonos básicos)
            - 2: mudanças intermédias (sibilantes unificadas, clusters consonânticos)
            - 3: mudanças agressivas (normalização internacional)

    Returns:
        Texto transformado.

    Example Usage:
        >>> reduce_letters_portuguese('João Silva', 1)
        'JOAO SILVA'
        >>> reduce_letters_portuguese('Gonçalves', 2)
        'GONSALVES'
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

    # NÍVEL 1: Reduções fonéticas básicas do português
    if level >= 1:
        replacements_level_1 = [
            ('RR', 'R'),   # RR -> R
            ('SS', 'S'),   # SS -> S (pássaro -> pasaro)
            ('QU', 'C'),   # QU -> C (quente -> cente)
            ('GU', 'G'),   # GU -> G (gueto -> geto)
            ('LH', 'LI'),  # LH -> LI (dígrafo palatal lateral: filho -> filio)
            ('NH', 'NI'),  # NH -> NI (dígrafo palatal nasal: ninho -> ninio)
            ('CH', 'X'),   # CH -> X (chave -> xave)
        ]
        for src, dst in replacements_level_1:
            oparse = oparse.replace(src, dst)

        single_level_1 = [
            ('H', ''),     # H é mudo em português (exceto em dígrafos)
            ('Y', 'I'),    # Y -> I
            ('K', 'C'),    # K -> C
            ('W', 'V'),    # W -> V
        ]
        for src, dst in single_level_1:
            oparse = oparse.replace(src, dst)

    # NÍVEL 2: Reduções intermédias (sibilantes e clusters)
    if level >= 2:
        replacements_level_2 = [
            ('X', 'S'),    # X -> S (pronúncia varia mas unificamos)
            ('Z', 'S'),    # Z -> S (final de palavras: vez -> ves)
            ('Ç', 'S'),    # Ç -> S (caça -> casa)
            ('C', 'S'),    # C -> S (ante e/i: cidade -> sidade)
            ('PS', 'S'),   # PS -> S (psicologia -> sicologia)
            ('PT', 'T'),   # PT -> T (ótimo de optimo)
            ('CT', 'T'),   # CT -> T (facto -> fato)
            ('GN', 'N'),   # GN -> N
            ('MN', 'N'),   # MN -> N
        ]
        for src, dst in replacements_level_2:
            oparse = oparse.replace(src, dst)

    # NÍVEL 3: Reduções agressivas (normalização internacional)
    if level >= 3:
        replacements_level_3 = [
            ('PH', 'F'),   # PH -> F
            ('TH', 'T'),   # TH -> T
            ('SCH', 'S'),  # SCH -> S
            ('L', 'R'),    # L/R confusão dialetal (ex: Brasil)
            ('D', 'T'),    # D final
            ('P', 'B'),    # P/B alternância
            ('T', 'D'),    # T -> D
            ('F', 'V'),    # F -> V
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


def raw_string_portuguese(input_string, accuracy):
    """
    Prepara uma string para comparações de texto em português aplicando
    limpeza e redução fonética.

    Args:
        input_string: Texto de entrada. Se None, retorna None.
        accuracy: Nível de agressividade na redução fonética (0..3).

    Returns:
        Texto processado pronto para comparações.

    Example Usage:
        >>> raw_string_portuguese('João da Silva', 2)
        'JOAO SILVA'
    """
    if input_string is None:
        return None

    cleaned = fix_portuguese_conversion_fails(input_string)
    reduced = reduce_letters_portuguese(cleaned, accuracy)
    return reduced
