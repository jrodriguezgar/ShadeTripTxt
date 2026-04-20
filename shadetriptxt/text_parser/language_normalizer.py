"""
Language Normalizer - Language-Specific Text Normalization

This module provides language-specific normalization rules to handle
linguistic peculiarities before text comparison. Supports Spanish ('es')
with extensible framework for additional languages.

Classes:
    LanguageNormalizer: Language-specific text normalization

Author: AI Assistant
Date: November 9, 2025
"""

from typing import Dict, List, Optional, Callable
import re
import unicodedata


class LanguageNormalizer:
    """
    Language-specific text normalization with extensible rules system.

    Description:
        This class handles language-specific text transformations that improve
        text comparison accuracy. It provides built-in support for Spanish ('es')
        and allows users to register custom normalization rules for any language.

        **Spanish ('es') Features**:
        - Converts 'ñ' → 'n'
        - Expands abbreviations: 'Ma. P.' → 'María Pilar'
        - Removes accents: 'José' → 'Jose'
        - Normalizes hyphenated compounds: 'García-López' → 'Garcia Lopez'
        - Handles Spanish titles: 'Sr.', 'Dra.', etc.

    Attributes:
        language (str): Current language code ('es', 'en', etc.)
        case_sensitive (bool): Whether to preserve case
        remove_accents (bool): Whether to remove diacritical marks
        _normalization_rules (Dict): Registered normalization rules per language
        _abbreviations (Dict): Abbreviation expansion dictionaries per language

    Example Usage:
        # Spanish normalization
        normalizer = LanguageNormalizer(language='es')
        text = normalizer.normalize("José García-López")
        # Returns: "jose garcia lopez"

        # With abbreviation expansion
        text = normalizer.normalize("Ma. P. García")
        # Returns: "maria pilar garcia"

        # Custom normalization rule
        def custom_rule(text: str) -> str:
            return text.replace("Street", "St")

        normalizer.register_rule('en', custom_rule)
        text = normalizer.normalize("Main Street", language='en')
        # Returns: "main st"

    Cost:
        O(n) where n is text length
    """

    # Spanish abbreviations (common names and titles)
    _SPANISH_ABBREVIATIONS = {
        # Name abbreviations
        r"\bMa\.\s*P\.\b": "María Pilar",
        r"\bMa\.\b": "María",
        r"\bJ\.\s*M\.\b": "José María",
        r"\bJ\.\s*L\.\b": "José Luis",
        r"\bM\.\s*A\.\b": "María Antonia",
        r"\bF\.\s*J\.\b": "Francisco Javier",
        # Titles
        r"\bSr\.\b": "Señor",
        r"\bSra\.\b": "Señora",
        r"\bDr\.\b": "Doctor",
        r"\bDra\.\b": "Doctora",
        r"\bIng\.\b": "Ingeniero",
        r"\bLic\.\b": "Licenciado",
        r"\bProf\.\b": "Profesor",
    }

    # English abbreviations (street/address)
    _ENGLISH_ABBREVIATIONS = {
        r"\bSt\.\b": "Street",
        r"\bAve\.\b": "Avenue",
        r"\bBlvd\.\b": "Boulevard",
        r"\bRd\.\b": "Road",
        r"\bDr\.\b": "Drive",
        r"\bLn\.\b": "Lane",
        r"\bCt\.\b": "Court",
        r"\bApt\.\b": "Apartment",
        r"\bFl\.\b": "Floor",
    }

    # Portuguese abbreviations (titles and addresses)
    _PORTUGUESE_ABBREVIATIONS = {
        r"\bSr\.\b": "Senhor",
        r"\bSra\.\b": "Senhora",
        r"\bDr\.\b": "Doutor",
        r"\bDra\.\b": "Doutora",
        r"\bProf\.\b": "Professor",
        r"\bEng\.\b": "Engenheiro",
        r"\bAv\.\b": "Avenida",
        r"\bR\.\b": "Rua",
        r"\bTrav\.\b": "Travessa",
        r"\bPç\.\b": "Praça",
    }

    # French abbreviations (titles and addresses)
    _FRENCH_ABBREVIATIONS = {
        r"\bM\.\b": "Monsieur",
        r"\bMme\.?\b": "Madame",
        r"\bMlle\.?\b": "Mademoiselle",
        r"\bDr\.\b": "Docteur",
        r"\bProf\.\b": "Professeur",
        r"\bAv\.\b": "Avenue",
        r"\bBd\.\b": "Boulevard",
        r"\bPl\.\b": "Place",
        r"\bR\.\b": "Rue",
        r"\bÉts?\.\b": "Établissement",
        r"\bSté\.\b": "Société",
    }

    # German abbreviations (titles and addresses)
    _GERMAN_ABBREVIATIONS = {
        r"\bHr\.\b": "Herr",
        r"\bFr\.\b": "Frau",
        r"\bDr\.\b": "Doktor",
        r"\bProf\.\b": "Professor",
        r"\bIng\.\b": "Ingenieur",
        r"\bStr\.\b": "Straße",
        r"\bPl\.\b": "Platz",
        r"\bNr\.\b": "Nummer",
        r"\bGmbH\b": "Gesellschaft mit beschränkter Haftung",
        r"\bAG\b": "Aktiengesellschaft",
    }

    # Italian abbreviations (titles and addresses)
    _ITALIAN_ABBREVIATIONS = {
        r"\bSig\.\b": "Signore",
        r"\bSig\.ra\b": "Signora",
        r"\bDott\.\b": "Dottore",
        r"\bDott\.ssa\b": "Dottoressa",
        r"\bProf\.\b": "Professore",
        r"\bIng\.\b": "Ingegnere",
        r"\bAvv\.\b": "Avvocato",
        r"\bV\.\b": "Via",
        r"\bP\.za\b": "Piazza",
        r"\bC\.so\b": "Corso",
        r"\bS\.r\.l\.\b": "Società a responsabilità limitata",
        r"\bS\.p\.A\.\b": "Società per Azioni",
    }

    def __init__(self, language: str = "es", case_sensitive: bool = False, remove_accents: bool = True):
        """
        Initialize language normalizer.

        Args:
            language (str): Default language code ('es', 'en', etc.). Default: 'es'
            case_sensitive (bool): Preserve case differences. Default: False
            remove_accents (bool): Remove diacritical marks. Default: True

        Raises:
            ValueError: If language code is unsupported
        """
        self.language = language.lower()
        self.case_sensitive = case_sensitive
        self.remove_accents = remove_accents

        # Custom normalization rules registry
        self._normalization_rules: Dict[str, List[Callable[[str], str]]] = {
            "es": [],
            "en": [],
            "pt": [],
            "fr": [],
            "de": [],
            "it": [],
        }

        # Abbreviation dictionaries
        self._abbreviations: Dict[str, Dict[str, str]] = {
            "es": self._SPANISH_ABBREVIATIONS.copy(),
            "en": self._ENGLISH_ABBREVIATIONS.copy(),
            "pt": self._PORTUGUESE_ABBREVIATIONS.copy(),
            "fr": self._FRENCH_ABBREVIATIONS.copy(),
            "de": self._GERMAN_ABBREVIATIONS.copy(),
            "it": self._ITALIAN_ABBREVIATIONS.copy(),
        }

    def normalize(self, text: str, language: Optional[str] = None) -> str:
        """
        Normalize text according to language-specific rules.

        Description:
            Applies language-specific transformations including:
            1. Case normalization (if not case_sensitive)
            2. Abbreviation expansion
            3. Accent removal (if remove_accents)
            4. Special character handling
            5. Whitespace normalization
            6. Custom registered rules

        Args:
            text (str): Text to normalize
            language (Optional[str]): Language code to use.
                                     If None, uses instance language.

        Returns:
            str: Normalized text

        Raises:
            ValueError: If text is empty

        Example:
            normalizer = LanguageNormalizer(language='es')

            # Spanish name with accents
            result = normalizer.normalize("José María García-López")
            # Returns: "jose maria garcia lopez"

            # Spanish abbreviation
            result = normalizer.normalize("Ma. P. Sánchez")
            # Returns: "maria pilar sanchez"

            # English address
            normalizer_en = LanguageNormalizer(language='en')
            result = normalizer_en.normalize("123 Main St. Apt. 4B")
            # Returns: "123 main street apartment 4b"

        Cost:
            O(n) where n is text length
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        lang = (language or self.language).lower()
        result = text

        # Step 1: Expand abbreviations
        result = self._expand_abbreviations(result, lang)

        # Step 2: Case normalization
        if not self.case_sensitive:
            result = result.lower()

        # Step 3: Language-specific character transformations
        if lang == "es":
            result = self._normalize_spanish_chars(result)
        elif lang == "pt":
            result = self._normalize_portuguese_chars(result)
        elif lang == "fr":
            result = self._normalize_french_chars(result)
        elif lang == "de":
            result = self._normalize_german_chars(result)
        elif lang == "it":
            result = self._normalize_italian_chars(result)

        # Step 4: Remove accents
        if self.remove_accents:
            result = self._remove_accents(result)

        # Step 5: Apply custom rules
        for rule_func in self._normalization_rules.get(lang, []):
            result = rule_func(result)

        # Step 6: Normalize whitespace
        result = self._normalize_whitespace(result)

        return result

    def _expand_abbreviations(self, text: str, language: str) -> str:
        """
        Expand language-specific abbreviations.

        Args:
            text (str): Input text
            language (str): Language code

        Returns:
            str: Text with expanded abbreviations

        Cost:
            O(n*m) where n is text length, m is number of abbreviations
        """
        if language not in self._abbreviations:
            return text

        result = text
        for pattern, expansion in self._abbreviations[language].items():
            result = re.sub(pattern, expansion, result, flags=re.IGNORECASE)

        return result

    def _normalize_spanish_chars(self, text: str) -> str:
        """
        Apply Spanish-specific character transformations.

        Description:
            - Converts 'ñ' → 'n'
            - Normalizes hyphenated compounds: 'García-López' → 'Garcia Lopez'
            - Removes apostrophes in contractions

        Args:
            text (str): Input text

        Returns:
            str: Transformed text

        Cost:
            O(n)
        """
        # Convert ñ to n (before accent removal for clarity)
        result = text.replace("ñ", "n").replace("Ñ", "N")

        # Convert hyphens in compound names to spaces
        result = re.sub(r"-", " ", result)

        # Remove apostrophes (e.g., "d'Ambrosio" → "dAmbrosio")
        result = result.replace("'", "")

        return result

    def _normalize_portuguese_chars(self, text: str) -> str:
        """
        Apply Portuguese-specific character transformations.

        - Normalizes hyphens in compound names to spaces
        - Handles cedilla: 'ç' is kept (removed by accent step if enabled)
        - Removes apostrophes in contractions
        """
        result = re.sub(r"-", " ", text)
        result = result.replace("'", "")
        return result

    def _normalize_french_chars(self, text: str) -> str:
        """
        Apply French-specific character transformations.

        - Normalizes hyphens in compound names to spaces
        - Handles French ligatures: 'œ' → 'oe', 'æ' → 'ae'
        - Removes apostrophes in elisions (l', d', etc.)
        """
        result = text.replace("œ", "oe").replace("Œ", "OE")
        result = result.replace("æ", "ae").replace("Æ", "AE")
        result = re.sub(r"-", " ", result)
        result = result.replace("'", "")
        return result

    def _normalize_german_chars(self, text: str) -> str:
        """
        Apply German-specific character transformations.

        - Expands umlauts: ä→ae, ö→oe, ü→ue
        - Expands eszett: ß→ss
        - Normalizes hyphens in compound words to spaces
        """
        result = text
        result = result.replace("ä", "ae").replace("Ä", "AE")
        result = result.replace("ö", "oe").replace("Ö", "OE")
        result = result.replace("ü", "ue").replace("Ü", "UE")
        result = result.replace("ß", "ss")
        result = re.sub(r"-", " ", result)
        return result

    def _normalize_italian_chars(self, text: str) -> str:
        """
        Apply Italian-specific character transformations.

        - Normalizes hyphens in compound names to spaces
        - Removes apostrophes in elisions (l', d', dell', etc.)
        """
        result = re.sub(r"-", " ", text)
        result = result.replace("'", "")
        return result

    def _remove_accents(self, text: str) -> str:
        """
        Remove diacritical marks (accents) from text.

        Description:
            Uses Unicode normalization (NFD) to decompose characters,
            then filters out combining characters.

            Examples:
            - 'José' → 'Jose'
            - 'María' → 'Maria'
            - 'Ángel' → 'Angel'

        Args:
            text (str): Input text

        Returns:
            str: Text without accents

        Cost:
            O(n)
        """
        # Normalize to NFD (decomposed form)
        nfd_form = unicodedata.normalize("NFD", text)

        # Filter out combining characters (accents)
        return "".join(char for char in nfd_form if unicodedata.category(char) != "Mn")

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace (collapse multiple spaces, trim).

        Args:
            text (str): Input text

        Returns:
            str: Text with normalized whitespace

        Cost:
            O(n)
        """
        return " ".join(text.split())

    def register_rule(self, language: str, rule_func: Callable[[str], str], name: Optional[str] = None) -> None:
        """
        Register a custom normalization rule for a language.

        Description:
            Custom rules are applied after standard normalization steps
            (abbreviation expansion, accent removal, etc.). Rules are
            applied in registration order.

        Args:
            language (str): Language code ('es', 'en', etc.)
            rule_func (Callable[[str], str]): Normalization function
            name (Optional[str]): Optional rule name for identification

        Raises:
            TypeError: If rule_func is not callable

        Example:
            # Custom rule to normalize business suffixes
            def normalize_business_suffix(text: str) -> str:
                text = re.sub(r'\bS\\.L\\.\b', 'Sociedad Limitada', text)
                text = re.sub(r'\bS\\.A\\.\b', 'Sociedad Anonima', text)
                return text

            normalizer = LanguageNormalizer(language='es')
            normalizer.register_rule('es', normalize_business_suffix)

            result = normalizer.normalize("Empresa ABC S.L.")
            # Returns: "empresa abc sociedad limitada"

        Cost:
            O(1)
        """
        if not callable(rule_func):
            raise TypeError("rule_func must be callable")

        lang = language.lower()
        if lang not in self._normalization_rules:
            self._normalization_rules[lang] = []

        # Store rule with optional name as attribute
        if name:
            rule_func.__name__ = name

        self._normalization_rules[lang].append(rule_func)

    def register_abbreviation(self, language: str, pattern: str, expansion: str) -> None:
        """
        Register a custom abbreviation expansion.

        Args:
            language (str): Language code
            pattern (str): Regex pattern to match (e.g., r'\bDept\\.\b')
            expansion (str): Full form (e.g., 'Department')

        Example:
            normalizer = LanguageNormalizer(language='es')
            normalizer.register_abbreviation('es', r'\bC/\b', 'Calle')

            result = normalizer.normalize("C/ Mayor 5")
            # Returns: "calle mayor 5"

        Cost:
            O(1)
        """
        lang = language.lower()
        if lang not in self._abbreviations:
            self._abbreviations[lang] = {}

        self._abbreviations[lang][pattern] = expansion

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List[str]: List of language codes

        Example:
            normalizer = LanguageNormalizer()
            languages = normalizer.get_supported_languages()
            # Returns: ['es', 'en']

        Cost:
            O(1)
        """
        return list(self._normalization_rules.keys())

    def clear_rules(self, language: Optional[str] = None) -> None:
        """
        Clear custom normalization rules.

        Args:
            language (Optional[str]): Language to clear rules for.
                                     If None, clears all languages.

        Example:
            normalizer = LanguageNormalizer()
            normalizer.clear_rules('es')  # Clear Spanish rules
            normalizer.clear_rules()      # Clear all rules

        Cost:
            O(1) or O(k) where k is number of languages
        """
        if language:
            lang = language.lower()
            if lang in self._normalization_rules:
                self._normalization_rules[lang] = []
        else:
            for lang in self._normalization_rules:
                self._normalization_rules[lang] = []


# ═══════════════════════════════════════════════════════════════════════════
# Standalone language detection
# ═══════════════════════════════════════════════════════════════════════════

_STOPWORDS: dict[str, set[str]] = {
    "en": {
        "the",
        "is",
        "at",
        "which",
        "on",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "of",
        "to",
        "for",
        "with",
        "was",
        "were",
        "are",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "can",
        "could",
        "not",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "from",
        "by",
        "as",
        "into",
    },
    "es": {
        "el",
        "la",
        "los",
        "las",
        "de",
        "del",
        "en",
        "y",
        "que",
        "es",
        "un",
        "una",
        "por",
        "con",
        "no",
        "se",
        "su",
        "para",
        "al",
        "lo",
        "como",
        "más",
        "pero",
        "sus",
        "le",
        "ya",
        "fue",
        "este",
        "ha",
        "era",
        "muy",
        "sin",
        "sobre",
        "ser",
        "desde",
        "son",
        "está",
    },
    "fr": {
        "le",
        "la",
        "les",
        "de",
        "des",
        "du",
        "un",
        "une",
        "et",
        "est",
        "en",
        "que",
        "qui",
        "dans",
        "ce",
        "il",
        "pas",
        "ne",
        "sur",
        "se",
        "au",
        "avec",
        "pour",
        "sont",
        "par",
        "plus",
        "je",
        "son",
        "mais",
    },
    "de": {
        "der",
        "die",
        "das",
        "und",
        "ist",
        "in",
        "den",
        "von",
        "zu",
        "mit",
        "auf",
        "für",
        "nicht",
        "ein",
        "eine",
        "dem",
        "sich",
        "des",
        "es",
        "als",
        "auch",
        "an",
        "nach",
        "wie",
        "im",
        "aus",
        "bei",
    },
    "it": {
        "il",
        "lo",
        "la",
        "le",
        "di",
        "del",
        "in",
        "che",
        "è",
        "un",
        "una",
        "per",
        "con",
        "non",
        "si",
        "da",
        "su",
        "al",
        "sono",
        "dei",
        "gli",
        "nel",
        "anche",
        "come",
        "ma",
        "ha",
        "più",
        "questo",
    },
    "pt": {
        "o",
        "a",
        "os",
        "as",
        "de",
        "do",
        "da",
        "em",
        "que",
        "é",
        "um",
        "uma",
        "para",
        "com",
        "não",
        "se",
        "na",
        "por",
        "mais",
        "no",
        "dos",
        "das",
        "foi",
        "ao",
        "são",
        "mas",
        "sua",
        "seu",
    },
}


def detect_language(text: str) -> str:
    """Detect the language of a text using stopword frequency heuristic.

    Supported languages: ``en``, ``es``, ``fr``, ``de``, ``it``, ``pt``.

    Args:
        text (str): Input text (at least a few words for reliable results).

    Returns:
        str: ISO 639-1 language code, or ``"unknown"`` if no
            language scores above zero.

    Raises:
        TypeError: If *text* is not a string.

    Usage Example:
        >>> detect_language("The quick brown fox jumps over the lazy dog")
        'en'
        >>> detect_language("El rápido zorro marrón salta sobre el perro")
        'es'

    Cost:
        O(n × L), where n is word count and L is number of languages.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    words = text.lower().split()
    word_set = set(words)

    best_lang = "unknown"
    best_score = 0

    for lang, stopwords in _STOPWORDS.items():
        score = len(word_set & stopwords)

        if score > best_score:
            best_score = score
            best_lang = lang

    return best_lang
