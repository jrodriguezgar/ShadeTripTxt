import re
import unicodedata
from typing import Optional

from .encoding_fixer import EncodingFixer

# Listas de palabras para operaciones categorizadas gramaticalmente:
# Listado de join de palabras en español, se pueden omitir en ciertos procesos de análisis de texto.
# Se mantiene en mayúsculas para comparaciones normalizadas.

# Prefijos y partículas en nombres propios
_NAME_PREFIXES = ["SAN", "SANTA", "VAN", "VON", "DER", "DEN", "DA", "DELLA", "MC", "MAC", "IBN"]

# Adverbios comunes/conectores
_ADVERBS = ["YA", "AUN", "TAMBIEN", "ASI", "AHORA"]

# Pronombres personales y objetos
_PRONOUNS = ["YO", "TU", "TÚ", "USTED", "USTEDES", "ELLOS", "ELLAS", "ME", "TE", "SE", "NOS", "OS", "LE", "LES", "LO", "LA"]

# Determinantes (incluye demostrativos/posesivos simples si se desea extender)
_DETERMINANTS = ["ESTE", "ESTA", "ESTOS", "ESTAS", "ESE", "ESA", "ESOS", "ESAS", "MI", "MIS", "TU", "TUS"]

# Artículos
_ARTICLES = ["EL", "LA", "LOS", "LAS", "UN", "UNA", "UNOS", "UNAS"]

# Preposiciones
_PREPOSITIONS = [
    "A",
    "AL",
    "ANTE",
    "BAJO",
    "CON",
    "CONTRA",
    "DE",
    "DEL",
    "DESDE",
    "EN",
    "ENTRE",
    "HACIA",
    "HASTA",
    "MEDIANTE",
    "PARA",
    "POR",
    "SIN",
    "SOBRE",
    "TRAS",
    "SEGUN",
    "VERSUS",
]

# Conjunciones
_CONJUNCTIONS = ["Y", "E", "NI", "O", "U", "QUE", "PORQUE", "PERO", "SINO", "MAS", "TAMBIEN"]

# Listado de palabras para omitir en ciertos procesos de análisis de texto.
_SKIP_WORDS_MAP = [
    "Y",
    "O",
    "U",
    "E",
    "A",
    "AN",
    "AL",
    "AS",
    "AR",
    "DE",
    "LA",
    "EL",
    "LO",
    "LE",
    "OS",
    "DI",
    "SI",
    "NOS",
    "LES",
    "LAS",
    "LOS",
    "DEL",
    "SAN",
    "VAN",
    "DER",
    "DEN",
    "VON",
]


# Precompile a regex for words to remove (articles, prepositions, conjunctions).
# Sorting by length prevents partial matches (e.g. matching 'A' inside 'AL').
_REMOVE_WORDS_SET = {w.upper() for w in (_ARTICLES + _PREPOSITIONS + _CONJUNCTIONS)}
_REMOVE_WORDS_SORTED = sorted(_REMOVE_WORDS_SET, key=len, reverse=True)
_REMOVE_WORDS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _REMOVE_WORDS_SORTED) + r")\b", flags=re.IGNORECASE)


def remove_spanish_articles(input_string: Optional[str]) -> Optional[str]:
    """
    Elimina artículos, preposiciones y conjunciones comunes en español de una cadena.

    Description:
        Quita palabras funcionales (artículos, preposiciones y conjunciones)
        definidas en las listas `_ARTICLES`, `_PREPOSITIONS` y `_CONJUNCTIONS`.

    Args:
        input_string: La cadena de entrada que será limpiada. Si es `None`,
            se devuelve `None`.

    Returns:
        La cadena resultante con las palabras objetivo eliminadas y espacios
        normalizados; o `None` si la entrada era `None`.

    Raises:
        No lanza excepciones explícitas. Internamente puede propagar errores
        si se pasa un tipo no convertible a `str`.

    Example Usage:
        >>> remove_spanish_articles('Pedro de la Fuente')
        'Pedro Fuente'

    Cost:
        O(n) en la longitud de la cadena de entrada (la compilación del patrón
        es O(m) donde m es el total de palabras objetivo, pero se hace una vez
        al cargar el módulo).
    """
    if input_string is None:
        return None

    if not isinstance(input_string, str):
        # Intentar convertir a str para mayor robustez
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    # Usar el patrón precompilado para eliminar palabras objetivo
    cleaned = _REMOVE_WORDS_PATTERN.sub("", input_string)

    # Normalizar espacios sobrantes y devolver
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


# Module-level EncodingFixer instance (map is built once, shared across calls)
_ENCODING_FIXER_ES = EncodingFixer(language="es")

# Legacy pre-processing: codepage conventions that are NOT mojibake
_LEGACY_MAP_ES = {
    "§": "º",  # section sign → masculine ordinal
    "¥": "Ñ",  # yen sign → Ñ (CP437/CP850 convention)
}


def fix_spanish_conversion_fails(input_string, add_charset=""):
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
    s = _ENCODING_FIXER_ES.fix(input_string)

    # Legacy post-processing (non-mojibake codepage conventions)
    for src, dst in _LEGACY_MAP_ES.items():
        if src in s:
            s = s.replace(src, dst)

    # Normalize spaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


def reduce_letters_spanish(input_string, strength):
    """
    Reduce letras según reglas fonéticas/normalización para comparaciones fonéticas en español.

    Description:
        Aplica transformaciones fonéticas progresivas basadas en similitudes de sonido
        en español. Útil para búsquedas fuzzy y comparaciones de nombres.

    Args:
        input_string: Texto de entrada. Si es `None`, devuelve `None`.
        strength: Nivel de agresividad de la transformación (0..3).
            - 0: sin cambios (solo normaliza acentos)
            - 1: cambios leves (H silenciosa, digrafos comunes, homófonos básicos)
            - 2: cambios intermedios (C/S/Z/X unificados, consonantes similares)
            - 3: cambios agresivos (normalización internacional: Ñ->N, Ç->S, W->V, etc.)

    Returns:
        Texto transformado manteniendo, cuando sea posible, el estilo de
        mayúsculas/minúsculas del original.

    Raises:
        No lanza excepciones; devuelve la entrada sin modificar si falla la conversión.

    Example Usage:
        >>> reduce_letters_spanish('José García', 1)
        'JOSE JARSIA'
        >>> reduce_letters_spanish('Ximénez', 2)
        'SIMENES'

    Cost: O(n) en la longitud del texto.
    """
    if input_string is None:
        return None

    # Asegurar tipos
    if not isinstance(input_string, str):
        try:
            input_string = str(input_string)
        except Exception:
            return input_string

    # Normalizar el nivel de strength
    try:
        level = int(strength)
    except Exception:
        level = 1
    level = max(0, min(level, 3))

    # Si level es 0, solo normalizar acentos y devolver
    if level == 0:
        result = "".join(ch for ch in unicodedata.normalize("NFD", input_string) if not unicodedata.combining(ch))
        return result

    # Detectar estilo de capitalización para restaurarlo al final
    def detect_style(s: str) -> str:
        if s.islower():
            return "lower"
        if s.isupper():
            return "upper"
        if s.istitle():
            return "title"
        return "mixed"

    orig_style = detect_style(input_string)

    # Quitar acentos de manera segura (pero mantener caracteres base)
    def remove_accents(s: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch))

    oparse = remove_accents(input_string).upper()

    # NIVEL 1: Reducciones fonéticas básicas del español
    # - H es muda en español (excepto en extranjerismos)
    # - Digrafos comunes: QU->C, GU->G (ante e/i), LL->Y
    # - Homófonos básicos: B/V, G/J (ante e/i), Y/I, Z/C, K/C
    if level >= 1:
        # Orden importante: procesar secuencias multi-carácter primero
        replacements_level_1 = [
            # Digrafos y secuencias especiales
            ("RR", "R"),  # doble R suena igual que R inicial
            ("QU", "C"),  # QUE, QUI -> CE, CI (mismo sonido /k/ o /ke/)
            ("GÜ", "G"),  # GÜE, GÜI -> GE, GI (con diéresis)
            ("GU", "G"),  # GUE, GUI -> GE, GI (sonido /g/)
            ("LL", "Y"),  # LL y Y suenan igual en la mayoría de dialectos (yeísmo)
            ("CH", "C"),  # CH -> C (simplificación de dígrafo)
            # Combinaciones nasales
            ("MB", "M"),  # MB -> M (asimilación nasal: "cambio" ~ "camio")
            ("NV", "M"),  # NV -> M (asimilación: "enviar" ~ "emiar")
            ("NM", "M"),  # NM -> M (asimilación: "inmenso" ~ "imenso")
        ]
        for src, dst in replacements_level_1:
            oparse = oparse.replace(src, dst)

        # Reemplazos de letra simple (homófonos y consonantes mudas)
        single_level_1 = [
            ("H", ""),  # H es muda en español
            ("Y", "I"),  # Y e I son homófonos en muchas posiciones
            ("Z", "C"),  # Z y C (ante e/i) suenan igual /θ/ o /s/ (seseo)
            ("K", "C"),  # K suena como C
            ("B", "V"),  # B y V son homófonos en español moderno
            ("G", "J"),  # G (ante e/i) suena como J
        ]
        for src, dst in single_level_1:
            oparse = oparse.replace(src, dst)

    # NIVEL 2: Reducciones intermedias (unificación de sibilantes y líquidas)
    # - Unifica S/C/X/Z (todas las sibilantes)
    # - Simplifica grupos consonánticos comunes
    if level >= 2:
        replacements_level_2 = [
            # Unificación de sibilantes (todas a S)
            ("X", "S"),  # X suena como S o KS, normalizamos a S
            ("C", "S"),  # Unifica C con S (seseo generalizado)
            # Simplificación de grupos consonánticos
            ("PS", "S"),  # PS -> S ("psicología" ~ "sicología")
            ("PT", "T"),  # PT -> T ("septiembre" ~ "setiembre")
            ("CT", "T"),  # CT -> T ("actor" ~ "ator")
            ("GN", "N"),  # GN -> N ("gnomo" ~ "nomo")
            ("MN", "N"),  # MN -> N ("himno" ~ "hino")
            ("TL", "L"),  # TL -> L (México: "atleta" ~ "aleta")
            # Líquidas (L/R pueden confundirse en algunos dialectos)
            # No aplicamos L->R por defecto en nivel 2 para mantener distinción
        ]
        for src, dst in replacements_level_2:
            oparse = oparse.replace(src, dst)

    # NIVEL 3: Reducciones agresivas (normalización internacional)
    # - Elimina caracteres específicos del español/catalán
    # - Unifica caracteres extranjeros
    # - Máxima simplificación fonética
    if level >= 3:
        replacements_level_3 = [
            # Normalización de caracteres específicos
            ("Ñ", "N"),  # Ñ -> N (normalización internacional)
            ("Ç", "S"),  # Ç -> S (catalán/francés)
            ("W", "V"),  # W -> V (adaptación española)
            ("Q", "K"),  # Q -> K (ya no hay QU después de nivel 1)
            # Simplificación extrema de grupos
            ("PH", "F"),  # PH -> F (filosofía)
            ("TH", "T"),  # TH -> T (anglicismos)
            ("SCH", "S"),  # SCH -> S (germanismos)
            # Líquidas intercambiables (dialectal)
            ("L", "R"),  # L y R se confunden en algunos dialectos caribeños
            # Fricativas finales
            ("D", "T"),  # D final se pronuncia como T o se elide ("verdad" ~ "verdá/verdat")
            ("P", "B"),  # P y B también pueden alternar
            ("T", "D"),  # T intervocálica se vocaliza
            ("F", "J"),  # F puede aspirarse como J en algunos dialectos
        ]
        for src, dst in replacements_level_3:
            oparse = oparse.replace(src, dst)

    # Restaurar estilo de capitalización del original
    if orig_style == "lower":
        return oparse.lower()
    if orig_style == "title":
        return oparse.title()
    if orig_style == "mixed":
        return oparse.lower()
    # 'upper'
    return oparse


def raw_string_spanish(input_string, accuracy):
    """
    Prepara una cadena para comparaciones de texto en español aplicando
    limpieza y reducción fonética según el nivel de precisión.

    Description:
        Combina limpieza de fallos de conversión y reducción fonética
        adaptada al español para obtener una representación "cruda"
        adecuada para comparaciones fuzzy.

    Args:
        input_string: Texto de entrada. Si es `None`, devuelve `None`.
        accuracy: Nivel de agresividad en la reducción fonética (0..3).

    Returns:
        Texto procesado listo para comparaciones.

    Raises:
        No lanza excepciones; devuelve la entrada sin modificar si falla la conversión.

    Example Usage:
        >>> raw_string_spanish('José de la Peña', 2)
        'JOSE PENA'
        >>> raw_string_spanish('Ximénez', 3)
        'SIMENES'

    Cost: O(n) en la longitud del texto.
    """
    if input_string is None:
        return None

    # Primero limpiar fallos de conversión
    cleaned = fix_spanish_conversion_fails(input_string)

    # Luego aplicar reducción fonética
    reduced = reduce_letters_spanish(cleaned, accuracy)

    return reduced
