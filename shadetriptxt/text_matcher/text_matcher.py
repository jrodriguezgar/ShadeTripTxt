"""
Text Matcher - High-Level Text Comparison Utilities

This module provides high-level text comparison functions that utilize the
WordSimilarity class as a foundation. It offers advanced matching capabilities
for text analysis, name matching, and fuzzy text comparison scenarios.

Classes:
    TextMatcher: High-level text comparison and matching utilities
    
Functions:
    are_words_equivalent: Standalone function for word comparison (from shadetriptxt.utils.string_similarity)
    
Author: DatamanEdge
"""
import re
import difflib

from typing import Dict, Any, Tuple, List, Optional, Union, Set, Callable
from dataclasses import dataclass, field
from functools import lru_cache
from collections import defaultdict
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from collections import Counter

# Lazy imports: internal modules are imported on first use
# to avoid loading heavy optional dependencies at module import time.

def _import_similarity():
    """Lazy loader for similarity submodules. Returns (flat_vowels, WordSimilarity, are_words_equivalent, calculate_similarity)."""
    from ..utils.string_ops import flat_vowels
    from ..utils.string_similarity import (
        WordSimilarity,
        are_words_equivalent,
        calculate_similarity
    )
    return flat_vowels, WordSimilarity, are_words_equivalent, calculate_similarity

def _import_normalize_text():
    """Lazy loader for normalize_text."""
    from shadetriptxt.text_parser.text_normalizer import normalize_text
    return normalize_text


@dataclass
class MatcherConfig:
    """
    Configuration object for TextMatcher operations.
    
    This class encapsulates all comparison parameters to avoid repetitive
    parameter passing and provide a unified configuration approach.
    
    Attributes:
        levenshtein_threshold (float): Minimum Levenshtein ratio (0.0-1.0). Default: 0.85
        jaro_winkler_threshold (float): Minimum Jaro-Winkler score (0.0-1.0). Default: 0.9
        metaphone_required (bool): Whether phonetic similarity is required. Default: True
        ignore_case (bool): Whether to ignore case differences. Default: True
        normalize_whitespace (bool): Whether to normalize whitespace. Default: True
        normalize_punctuation (bool): Whether to remove punctuation before comparison. Default: True
        normalize_parentheses (bool): Whether to remove parentheses content. Default: False
        remove_accents (bool): Whether to remove accents before comparison. Default: False
        debug_mode (bool): Whether to include detailed match explanations. Default: False
        
    Example Usage:
        # Create a lenient configuration for name matching
        config = MatcherConfig(
            levenshtein_threshold=0.75,
            jaro_winkler_threshold=0.80,
            metaphone_required=False,
            debug_mode=True
        )
        
        # Create a strict configuration for legal/financial data
        strict_config = MatcherConfig(
            levenshtein_threshold=0.95,
            jaro_winkler_threshold=0.95,
            metaphone_required=True
        )
    
    Preset Configurations:
        Use class methods to get common configurations:
        - MatcherConfig.strict(): For legal/financial data
        - MatcherConfig.default(): Default balanced settings
        - MatcherConfig.lenient(): For names and user input
        - MatcherConfig.fuzzy(): For fuzzy search
    """
    levenshtein_threshold: float = 0.85
    jaro_winkler_threshold: float = 0.9
    metaphone_required: bool = True
    ignore_case: bool = True
    normalize_whitespace: bool = True
    normalize_punctuation: bool = True
    normalize_parentheses: bool = False
    remove_accents: bool = False
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not (0.0 <= self.levenshtein_threshold <= 1.0):
            raise ValueError("levenshtein_threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.jaro_winkler_threshold <= 1.0):
            raise ValueError("jaro_winkler_threshold must be between 0.0 and 1.0")
    
    @classmethod
    def strict(cls) -> 'MatcherConfig':
        """
        Create a strict configuration for legal/financial data.
        
        Returns:
            MatcherConfig: Strict matching configuration
            
        Example:
            config = MatcherConfig.strict()
            matcher = TextMatcher(config=config)
        """
        return cls(
            levenshtein_threshold=0.95,
            jaro_winkler_threshold=0.95,
            metaphone_required=True
        )
    
    @classmethod
    def default(cls) -> 'MatcherConfig':
        """
        Create default configuration with balanced settings.
        
        Returns:
            MatcherConfig: Default matching configuration
        """
        return cls()
    
    @classmethod
    def lenient(cls) -> 'MatcherConfig':
        """
        Create a lenient configuration for names and user input.
        
        Returns:
            MatcherConfig: Lenient matching configuration
            
        Example:
            config = MatcherConfig.lenient()
            matcher = TextMatcher(config=config)
        """
        return cls(
            levenshtein_threshold=0.75,
            jaro_winkler_threshold=0.80,
            metaphone_required=False
        )
    
    @classmethod
    def fuzzy(cls) -> 'MatcherConfig':
        """
        Create a very lenient configuration for fuzzy search.
        
        Returns:
            MatcherConfig: Fuzzy search configuration
            
        Example:
            config = MatcherConfig.fuzzy()
            matcher = TextMatcher(config=config)
        """
        return cls(
            levenshtein_threshold=0.65,
            jaro_winkler_threshold=0.70,
            metaphone_required=False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            'levenshtein_threshold': self.levenshtein_threshold,
            'jaro_winkler_threshold': self.jaro_winkler_threshold,
            'metaphone_required': self.metaphone_required,
            'ignore_case': self.ignore_case,
            'normalize_whitespace': self.normalize_whitespace,
            'normalize_punctuation': self.normalize_punctuation,
            'normalize_parentheses': self.normalize_parentheses,
            'remove_accents': self.remove_accents,
            'debug_mode': self.debug_mode
        }


class TextMatcher:
    """
    High-level text comparison and matching utilities.
    
    This class provides advanced text matching capabilities built on top of
    the WordSimilarity class. It is designed for real-world text comparison
    scenarios such as name matching, duplicate detection, and fuzzy text search.
    
    Description:
        TextMatcher encapsulates sophisticated text comparison logic that combines
        multiple similarity algorithms to provide robust matching decisions. It is
        particularly useful for identity resolution, deduplication, and text
        normalization tasks.
        
        The class maintains an internal WordSimilarity instance and provides
        methods that combine phonetic, edit-distance, and token-based similarity
        metrics for comprehensive text analysis.
    
    Attributes:
        word_similarity (WordSimilarity): Internal instance for similarity calculations
        config (MatcherConfig): Configuration object for default comparison settings
        
    Example Usage:
        # Basic initialization with default config
        matcher = TextMatcher()
        
        # Initialize with locale for English name matching
        matcher = TextMatcher(locale='en_US')
        
        # Initialize with custom config
        config = MatcherConfig.lenient()
        matcher = TextMatcher(config=config, locale='pt_BR')
        
        # Word comparison using internal engine
        matcher = TextMatcher()
        is_same, metrics = matcher._are_words_equivalent("Smith", "Smyth")
        # Returns: (True, {'metaphone_match': True, 'levenshtein_ratio': 0.83, ...})
        
        # Name comparison with config
        is_match, metrics = matcher.compare_names("José", "Jose")
        # Returns: (True, {...})
    
    Cost:
        Initialization: O(1)
    """
    
    # ── Locale-to-language mapping ─────────────────────────────────────────
    _LOCALE_TO_LANGUAGE: Dict[str, str] = {
        'es_ES': 'es', 'es_MX': 'es', 'es_AR': 'es', 'es_CO': 'es', 'es_CL': 'es',
        'en_US': 'en', 'en_GB': 'en',
        'pt_BR': 'pt', 'pt_PT': 'pt',
        'fr_FR': 'fr',
        'de_DE': 'de',
        'it_IT': 'it',
    }

    # ── Per-language name abbreviation / nickname dictionaries ────────────
    # Each entry maps a short form (nickname, abbreviation, initial) to a
    # list of full canonical names it may represent.  Used by
    # compare_with_abbreviation() and _align_lists().
    _NAME_ABBREVIATIONS: Dict[str, Dict[str, List[str]]] = {
        # ── Spanish ──────────────────────────────────────────────────────
        'es': {
            'FCO': ['FRANCISCO'],
            'FDO': ['FERNANDO'],
            'PACO': ['FRANCISCO'],
            'PEPE': ['JOSE'],
            'LOLA': ['DOLORES'],
            'CONCHA': ['CONCEPCION'],
            'CHARO': ['ROSARIO'],
            'MANU': ['MANUEL'],
            'MARGA': ['MARGARITA'],
            'TERE': ['TERESA'],
            'CHUS': ['JESUS', 'MARIA JESUS'],
            'PILI': ['PILAR'],
            'CRIS': ['CRISTINA', 'CRISTIAN'],
            'DANI': ['DANIEL', 'DANIELA'],
            'SANTI': ['SANTIAGO'],
            'RAFA': ['RAFAEL'],
            'NACHO': ['IGNACIO'],
            'CARLOS': ['CARLOS', 'KARL'],
            'GUILLE': ['GUILLERMO'],
            'J': ['JOSE', 'JUAN', 'JORGE', 'JESUS', 'JAVIER'],
            'M': ['MARIA', 'MANUEL', 'MIGUEL', 'MARCOS'],
            'R': ['RODRIGUEZ', 'RAMIREZ', 'RUIZ', 'RAMON', 'RAFAEL'],
            'G': ['GARCIA', 'GONZALEZ', 'GOMEZ', 'GUTIERREZ'],
            'L': ['LOPEZ', 'LUNA', 'LUIS', 'LAURA'],
            'A': ['ANTONIO', 'ANA', 'ALBERTO', 'ANDRES'],
            'F': ['FRANCISCO', 'FERNANDO', 'FELIX'],
            'P': ['PEREZ', 'PABLO', 'PEDRO'],
            'S': ['SANCHEZ', 'SANTOS', 'SERGIO'],
            'C': ['CARLOS', 'CARMEN', 'CRISTINA'],
        },
        # ── English ──────────────────────────────────────────────────────
        'en': {
            'BILL': ['WILLIAM'],
            'WILL': ['WILLIAM'],
            'WILLY': ['WILLIAM'],
            'BOB': ['ROBERT'],
            'ROB': ['ROBERT'],
            'ROBBIE': ['ROBERT'],
            'DICK': ['RICHARD'],
            'RICK': ['RICHARD'],
            'TED': ['THEODORE', 'EDWARD'],
            'ED': ['EDWARD', 'EDWIN'],
            'MIKE': ['MICHAEL'],
            'JIM': ['JAMES'],
            'JIMMY': ['JAMES'],
            'JACK': ['JOHN'],
            'CHUCK': ['CHARLES'],
            'CHARLIE': ['CHARLES'],
            'TONY': ['ANTHONY'],
            'ALEX': ['ALEXANDER', 'ALEXANDRA'],
            'DAN': ['DANIEL'],
            'DANNY': ['DANIEL'],
            'DAVE': ['DAVID'],
            'HARRY': ['HENRY', 'HAROLD'],
            'HANK': ['HENRY'],
            'CHRIS': ['CHRISTOPHER', 'CHRISTINE'],
            'NICK': ['NICHOLAS'],
            'PETE': ['PETER'],
            'PHIL': ['PHILIP'],
            'STEVE': ['STEVEN', 'STEPHEN'],
            'TOM': ['THOMAS'],
            'TOMMY': ['THOMAS'],
            'JOE': ['JOSEPH'],
            'JOEY': ['JOSEPH'],
            'BEN': ['BENJAMIN'],
            'MATT': ['MATTHEW'],
            'PAT': ['PATRICK', 'PATRICIA'],
            'PEGGY': ['MARGARET'],
            'MAGGIE': ['MARGARET'],
            'MEG': ['MARGARET'],
            'BETH': ['ELIZABETH'],
            'LIZ': ['ELIZABETH'],
            'LIZZY': ['ELIZABETH'],
            'KATE': ['KATHERINE', 'CATHERINE'],
            'KATIE': ['KATHERINE', 'CATHERINE'],
            'SUE': ['SUSAN'],
            'JENNY': ['JENNIFER'],
            'DEBBIE': ['DEBORAH'],
            'BECKY': ['REBECCA'],
            'SAM': ['SAMUEL', 'SAMANTHA'],
            'J': ['JOHN', 'JAMES', 'JOSEPH', 'JASON', 'JENNIFER'],
            'M': ['MICHAEL', 'MATTHEW', 'MARGARET', 'MARY'],
            'R': ['ROBERT', 'RICHARD', 'ROSE'],
            'D': ['DAVID', 'DANIEL', 'DOROTHY'],
            'W': ['WILLIAM', 'WALTER'],
            'A': ['ALEXANDER', 'ANTHONY', 'ANNA'],
            'C': ['CHARLES', 'CHRISTOPHER', 'CATHERINE'],
            'T': ['THOMAS', 'TIMOTHY'],
            'S': ['STEPHEN', 'SAMUEL', 'SARAH'],
            'P': ['PETER', 'PATRICK', 'PATRICIA'],
        },
        # ── Portuguese ───────────────────────────────────────────────────
        'pt': {
            'ZE': ['JOSE'],
            'NANDO': ['FERNANDO'],
            'GUI': ['GUILHERME'],
            'DUDU': ['EDUARDO'],
            'CADU': ['CARLOS EDUARDO'],
            'BIA': ['BEATRIZ'],
            'LULU': ['LUIZA'],
            'MANU': ['MANUELA', 'MANUEL'],
            'DANI': ['DANIEL', 'DANIELA'],
            'GABI': ['GABRIELA', 'GABRIEL'],
            'RAFA': ['RAFAEL', 'RAFAELA'],
            'TIAGO': ['SANTIAGO'],
            'CHICO': ['FRANCISCO'],
            'QUIM': ['JOAQUIM'],
            'TONI': ['ANTONIO'],
            'NETO': ['ERNESTO'],
            'J': ['JOSE', 'JOAO', 'JORGE'],
            'M': ['MARIA', 'MANUEL', 'MARCOS'],
            'A': ['ANTONIO', 'ANA', 'ANDRE'],
            'R': ['RODRIGO', 'RAFAEL', 'RICARDO'],
            'P': ['PEDRO', 'PAULO'],
            'C': ['CARLOS', 'CRISTINA'],
            'F': ['FRANCISCO', 'FERNANDO'],
            'L': ['LUIS', 'LUCAS', 'LUCIA'],
        },
        # ── French ───────────────────────────────────────────────────────
        'fr': {
            'JP': ['JEAN-PIERRE'],
            'JM': ['JEAN-MARC', 'JEAN-MICHEL'],
            'JC': ['JEAN-CLAUDE'],
            'JL': ['JEAN-LUC', 'JEAN-LOUIS'],
            'JF': ['JEAN-FRANCOIS'],
            'ALEX': ['ALEXANDRE', 'ALEXANDRA'],
            'CHRIS': ['CHRISTOPHE', 'CHRISTINE'],
            'NICO': ['NICOLAS'],
            'MANU': ['EMMANUEL', 'EMMANUELLE'],
            'FRED': ['FREDERIC'],
            'PHIL': ['PHILIPPE'],
            'STEPH': ['STEPHANE', 'STEPHANIE'],
            'DOM': ['DOMINIQUE'],
            'NATH': ['NATHALIE', 'NATHAN'],
            'PAT': ['PATRICK', 'PATRICIA'],
            'J': ['JEAN', 'JACQUES', 'JULIEN'],
            'M': ['MARIE', 'MICHEL', 'MARC'],
            'P': ['PIERRE', 'PHILIPPE', 'PAUL'],
            'A': ['ALEXANDRE', 'ANDRE', 'ANNE'],
            'C': ['CHARLES', 'CLAUDE', 'CATHERINE'],
            'F': ['FRANCOIS', 'FREDERIC'],
            'L': ['LAURENT', 'LOUIS', 'LUCIE'],
            'N': ['NICOLAS', 'NATHALIE'],
        },
        # ── German ───────────────────────────────────────────────────────
        'de': {
            'HANS': ['JOHANNES', 'HANS'],
            'FRITZ': ['FRIEDRICH'],
            'WILLI': ['WILHELM'],
            'TONI': ['ANTON', 'ANTONIA'],
            'SEPP': ['JOSEF'],
            'ANDI': ['ANDREAS'],
            'ALEX': ['ALEXANDER', 'ALEXANDRA'],
            'CHRIS': ['CHRISTIAN', 'CHRISTIANE'],
            'MICHI': ['MICHAEL', 'MICHAELA'],
            'STEFF': ['STEFAN', 'STEPHANIE'],
            'WOLFI': ['WOLFGANG'],
            'MANU': ['MANUEL', 'MANUELA'],
            'ULLI': ['ULRICH', 'ULRIKE'],
            'KATHI': ['KATHARINA'],
            'CONNI': ['CORNELIA'],
            'SUSI': ['SUSANNE'],
            'HEINI': ['HEINRICH'],
            'J': ['JOHANNES', 'JURGEN', 'JOSEF'],
            'M': ['MICHAEL', 'MARTIN', 'MARIA'],
            'A': ['ANDREAS', 'ALEXANDER', 'ANNA'],
            'K': ['KARL', 'KLAUS', 'KATHARINA'],
            'H': ['HANS', 'HEINRICH', 'HELMUT'],
            'W': ['WILHELM', 'WOLFGANG', 'WALTER'],
            'F': ['FRIEDRICH', 'FRANZ', 'FLORIAN'],
            'S': ['STEFAN', 'SEBASTIAN', 'SUSANNE'],
            'T': ['THOMAS', 'TOBIAS'],
            'P': ['PETER', 'PAUL', 'PETRA'],
        },
        # ── Italian ──────────────────────────────────────────────────────
        'it': {
            'GIGIO': ['LUIGI'],
            'PEPPE': ['GIUSEPPE'],
            'BEPPE': ['GIUSEPPE'],
            'NINO': ['ANTONINO', 'GIOVANNI'],
            'TINO': ['VALENTINO', 'AGOSTINO'],
            'SANDRO': ['ALESSANDRO'],
            'FRANCO': ['FRANCESCO'],
            'DANI': ['DANIELE', 'DANIELA'],
            'TONI': ['ANTONIO'],
            'MANU': ['EMANUELE', 'MANUELA'],
            'ALEX': ['ALESSANDRO', 'ALESSANDRA'],
            'GIANNI': ['GIOVANNI'],
            'LOLLO': ['LORENZO'],
            'RICKY': ['RICCARDO'],
            'FEDE': ['FEDERICO', 'FEDERICA'],
            'VALE': ['VALENTINA', 'VALENTINO'],
            'G': ['GIUSEPPE', 'GIOVANNI', 'GIORGIO'],
            'M': ['MARIO', 'MARCO', 'MARIA'],
            'A': ['ANTONIO', 'ANDREA', 'ANNA'],
            'F': ['FRANCESCO', 'FRANCESCA', 'FILIPPO'],
            'L': ['LUIGI', 'LORENZO', 'LUCIA'],
            'P': ['PAOLO', 'PIETRO'],
            'S': ['SALVATORE', 'STEFANO', 'SARA'],
            'R': ['RICCARDO', 'ROBERTO', 'ROSA'],
        },
    }

    # Backward-compatible class-level reference (Spanish abbreviations)
    ABBREVIATIONS_DICT = _NAME_ABBREVIATIONS['es']
    
    def __init__(
        self, 
        config: Optional[MatcherConfig] = None,
        locale: Optional[str] = None,
        enable_cache: bool = True,
        cache_size: int = 1024
    ):
        """
        Initialize the TextMatcher instance.
        
        Description:
            Creates a new TextMatcher with an internal WordSimilarity instance,
            optional configuration for default comparison settings, and intelligent
            caching for performance optimization.
        
        Args:
            config (Optional[MatcherConfig]): Configuration object for default settings.
                                             If None, uses MatcherConfig.default()
            locale (Optional[str]): Locale code for language-specific abbreviation
                                   handling (e.g. 'es_ES', 'en_US', 'pt_BR', 'fr_FR',
                                   'de_DE', 'it_IT'). Also accepts bare language codes
                                   ('es', 'en', etc.). If None, defaults to 'es' for
                                   backward compatibility.
                                   Supported locales: es_ES, es_MX, es_AR, es_CO,
                                   es_CL, en_US, en_GB, pt_BR, pt_PT, fr_FR, de_DE,
                                   it_IT.
            enable_cache (bool): Enable LRU cache for comparison results. Default: True
            cache_size (int): Maximum number of cached comparisons. Default: 1024
            
        Returns:
            None
            
        Raises:
            ValueError: If locale is not supported
            
        Example:
            # Default configuration with cache (Spanish abbreviations)
            matcher = TextMatcher()
            
            # English locale for English name matching
            matcher = TextMatcher(locale='en_US')
            
            # Custom configuration with locale
            config = MatcherConfig(levenshtein_threshold=0.80, debug_mode=True)
            matcher = TextMatcher(config=config, locale='pt_BR', cache_size=2048)
            
            # Disable cache for memory-constrained environments
            matcher = TextMatcher(enable_cache=False)
        
        Cost:
            O(1)
        """
        flat_vowels, WordSimilarity, are_words_equivalent, calculate_similarity = _import_similarity()
        self._flat_vowels = flat_vowels
        self._are_words_equivalent = are_words_equivalent
        self._calculate_similarity = calculate_similarity
        self.word_similarity = WordSimilarity()
        self.config = config if config is not None else MatcherConfig.default()
        self._enable_cache = enable_cache
        self._cache_size = cache_size
        
        # Locale-aware abbreviation setup
        self._locale = locale
        if locale is not None:
            lang = self._LOCALE_TO_LANGUAGE.get(locale)
            if lang is None:
                # Accept bare language codes ('es', 'en', 'pt', etc.)
                lang = locale.split('_')[0].lower()
            if lang not in self._NAME_ABBREVIATIONS:
                supported = ', '.join(sorted(self._LOCALE_TO_LANGUAGE))
                raise ValueError(
                    f"Unsupported locale '{locale}'. "
                    f"Supported: {supported}"
                )
            self._language = lang
        else:
            self._language = 'es'
        self._abbreviations_dict: Dict[str, List[str]] = self._NAME_ABBREVIATIONS[self._language]
        
        # Custom comparison functions registry
        self._custom_functions: Dict[str, Callable] = {}

        # Initialize cache if enabled
        if self._enable_cache:
            self._comparison_cache = {}
            self._cache_hits = 0
            self._cache_misses = 0
    
    # ------------------------------------------------------------------
    # Custom comparison functions
    # ------------------------------------------------------------------

    def register_custom(
        self,
        name: str,
        func: Callable[[str, str], Tuple[bool, Dict[str, Any]]],
    ) -> None:
        """
        Register a custom comparison function.

        The callable must accept two strings and return a tuple
        ``(is_match: bool, metrics: dict)``.

        Args:
            name: Unique name for the custom function.
            func: Callable with signature ``(str, str) -> (bool, dict)``.

        Raises:
            TypeError: If *func* is not callable.

        Example:
            def my_comparator(a: str, b: str) -> tuple[bool, dict]:
                ratio = difflib.SequenceMatcher(None, a, b).ratio()
                return ratio >= 0.8, {"ratio": ratio}

            matcher = TextMatcher()
            matcher.register_custom("seq_ratio", my_comparator)
            ok, info = matcher.run_custom("seq_ratio", "hello", "hallo")
        """
        if not callable(func):
            raise TypeError(f"func must be callable, got {type(func).__name__}")
        self._custom_functions[name] = func

    def unregister_custom(self, name: str) -> None:
        """Remove a registered custom comparison function."""
        self._custom_functions.pop(name, None)

    def run_custom(
        self,
        name: str,
        text1: str,
        text2: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute a registered custom comparison function.

        Args:
            name: Name of the registered function.
            text1: First text to compare.
            text2: Second text to compare.

        Returns:
            Tuple[bool, Dict[str, Any]]: Result returned by the custom function.

        Raises:
            ValueError: If *name* is not registered.
        """
        if name not in self._custom_functions:
            raise ValueError(
                f"Custom function '{name}' not registered. "
                f"Registered: {list(self._custom_functions.keys())}"
            )
        return self._custom_functions[name](text1, text2)

    def list_custom(self) -> Dict[str, str]:
        """
        List registered custom comparison functions.

        Returns:
            Dict mapping name to the callable's qualified name.
        """
        return {
            name: getattr(fn, '__qualname__', repr(fn))
            for name, fn in self._custom_functions.items()
        }

    # ------------------------------------------------------------------
    # Text normalization
    # ------------------------------------------------------------------

    def normalize_text(
        self,
        text: str,
        for_names: bool = False,
        case_mode: str = "upper",
        config: Optional[MatcherConfig] = None
    ) -> str:
        """
        Unified text normalization method for consistent preprocessing across all methods.

        Description:
            This method provides standardized text normalization that can be configured
            for different use cases (names vs general text).

            For names (for_names=True):
            - Keeps letters (all Latin scripts including accents and diacritics), spaces, hyphens, and apostrophes
            - Removes all other special characters and punctuation
            - Converts to uppercase by default

            For general text (for_names=False):
            - Applies configurable normalization based on MatcherConfig
            - Supports lowercase, punctuation removal, whitespace normalization, etc.

        Args:
            text (str): Text to normalize
            for_names (bool): Whether this is name-specific normalization. Default: False
            case_mode (str): Case conversion mode ("upper", "lower", "title", "none").
                           Default: "upper"
            config (Optional[MatcherConfig]): Configuration for general text normalization.
                                             If None, uses instance config. Default: None

        Returns:
            str: Normalized text

        Raises:
            ValueError: If case_mode is invalid

        Example:
            matcher = TextMatcher()

            # Name normalization
            normalized = matcher.normalize_text("José María O'Connor-Smith", for_names=True)
            # Returns: "JOSE MARIA O'CONNOR-SMITH"

            # General text normalization
            normalized = matcher.normalize_text("  John   Smith,  Inc.  ")
            # Returns: "john smith inc" (depending on config)

        Cost:
            O(n) where n is text length
        """
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")
        if case_mode not in ["upper", "lower", "title", "none"]:
            raise ValueError("case_mode must be 'upper', 'lower', 'title', or 'none'")

        if not text:
            return text

        if for_names:
            # Name-specific normalization
            import re
            # Keep only letters (all Latin scripts including accents), spaces, hyphens, and apostrophes
            normalized = re.sub(r"[^a-zA-Z\u00C0-\u024F\u1E00-\u1EFF\s\-']", "", text.upper())
            # Clean up multiple spaces
            normalized = ' '.join(normalized.split())
        else:
            # General text normalization using config
            cfg = config if config is not None else self.config

            from shadetriptxt.text_parser.text_normalizer import normalize_text  # lazy
            normalized = normalize_text(
                text,
                lowercase=(case_mode == "lower"),
                remove_punctuation=cfg.normalize_punctuation,
                normalize_whitespace=cfg.normalize_whitespace,
                remove_accents=cfg.remove_accents,
                remove_parentheses_content=cfg.normalize_parentheses,
                strip_quotes=True,
                preserve_alphanumeric_only=False
            )

        # Apply case conversion
        if case_mode == "upper":
            normalized = normalized.upper()
        elif case_mode == "lower":
            normalized = normalized.lower()
        elif case_mode == "title":
            normalized = normalized.title()

        return normalized

    # Hybrid Algorithm Enhancement: Detect abbreviations and apply special logic
    def is_abbreviation(self, word):
        """Check if a word is likely an abbreviation"""
        if not word:
            return False
        clean_word = word.rstrip('.')
        return len(clean_word) <= 3
        
    def compare_with_abbreviation(self, w1: str, w2: str, threshold_val: float) -> float:
        """
        Compare two words with special logic for abbreviations.
        Uses the locale-specific name abbreviation dictionary.
        
        Description:
            This method implements hybrid abbreviation handling for word comparison.
            It detects abbreviations (words ≤3 characters) and applies special logic:
            - If one word is an abbreviation and the other isn't, checks for prefix matching
              or dictionary lookup using the language set at construction time
            - If both are abbreviations or both are full words, uses standard similarity algorithms
            - Handles common patterns per locale: "Fco" → "Francisco" (es),
              "Bob" → "Robert" (en), "Zé" → "José" (pt), etc.
        
        Args:
            w1 (str): The first word to compare
            w2 (str): The second word to compare
            threshold_val (float): Similarity threshold (0.0 to 1.0)
        
        Returns:
            float: Similarity score (0.0 to 1.0)
        
        Raises:
            None
        
        Example:
            matcher = TextMatcher(locale='es_ES')
            score = matcher.compare_with_abbreviation("Fco", "Francisco", 0.9)
            # Returns: 1.0 (perfect match from dictionary)

            matcher_en = TextMatcher(locale='en_US')
            score = matcher_en.compare_with_abbreviation("Bob", "Robert", 0.9)
            # Returns: 1.0 (perfect match from dictionary)
        
        Cost:
            O(n) where n is the length of the words
        """
        if not w1 or not w2:
            return 0.0
        
        # Remove trailing periods and convert to uppercase
        clean_w1 = w1.rstrip('.').upper()
        clean_w2 = w2.rstrip('.').upper()
        
        # Early dictionary check — handles nicknames of any length
        # (e.g. BILL→WILLIAM, BEPPE→GIUSEPPE, FRITZ→FRIEDRICH)
        if clean_w1 in self._abbreviations_dict and clean_w2 in self._abbreviations_dict[clean_w1]:
            return 1.0
        if clean_w2 in self._abbreviations_dict and clean_w1 in self._abbreviations_dict[clean_w2]:
            return 1.0
        
        is_abbr1 = self.is_abbreviation(w1)
        is_abbr2 = self.is_abbreviation(w2)
        
        # Case 1: Both are abbreviations - use Jaro-Winkler (better for short strings)
        if is_abbr1 and is_abbr2:
            result = self._calculate_similarity(clean_w1, clean_w2, algorithm='jaro_winkler')
            return result.get('score', 0.0) / 100.0
        
        # Case 2: One is abbreviation, other is not
        if is_abbr1 and not is_abbr2:
            # Check if abbreviation is prefix of full word
            if clean_w2.startswith(clean_w1):
                return 1.0
            # Check if first letters match (for initials)
            if len(clean_w1) == 1 and clean_w2.startswith(clean_w1):
                return 1.0
            return 0.0
        
        if is_abbr2 and not is_abbr1:
            # Check if abbreviation is prefix of full word
            if clean_w1.startswith(clean_w2):
                return 1.0
            # Check if first letters match (for initials)
            if len(clean_w2) == 1 and clean_w1.startswith(clean_w2):
                return 1.0
            return 0.0
        
        # Case 3: Neither is abbreviation - use Jaro-Winkler for better name matching
        result = self._calculate_similarity(clean_w1, clean_w2, algorithm='jaro_winkler')
        return result.get('score', 0.0) / 100.0

    def _align_lists(
        self, 
        list1: List[str], 
        list2: List[str],
        fuzzy_match: bool = False
    ) -> Tuple[List[Optional[str]], List[Optional[str]]]:
        """
        Aligns two lists element by element for word-by-word comparison.
        
        Description:
            This internal helper method implements list alignment logic that ensures
            matching words maintain the same position in both lists. Words are aligned
            from left to right, inserting None where necessary to keep equal words at
            the same index.
            
            The algorithm:
            1. Scans both lists from left to right
            2. When words match, they are aligned together
            3. When words don't match, inserts None in the appropriate list
            4. Matching words preserve their relative position counting from left
        
        Args:
            list1 (List[str]): First list to align
            list2 (List[str]): Second list to align
            fuzzy_match (bool): If True, uses fuzzy matching (are_words_similar) to align
                               words like ROBERT/ROBERTO. If False (default), uses exact
                               match or abbreviation only (are_words_equal).
        
        Returns:
            Tuple[List[Optional[str]], List[Optional[str]]]: Two aligned lists
        
        Example:
            result1, result2 = self._align_lists(
                ["ESTELA", "COLLADO", "MARTINEZ"],
                ["ESTELA", "MARIA", "COLLADO"]
            )
            # Returns: (
            #   ["ESTELA", None, "COLLADO", "MARTINEZ", None],
            #   ["ESTELA", "MARIA", "COLLADO", None, None]
            # )
        
        Cost:
            O(n*m) where n and m are the lengths of list1 and list2
        """
        def could_be_abbreviation_of(abbr, full_word):
            """
            Check if abbr could be an abbreviation of full_word.
            Handles common abbreviation patterns.
            """
            if not abbr or not full_word:
                return False
            clean_abbr = abbr.rstrip('.').upper()
            clean_full = full_word.upper()
            
            # Direct prefix match (e.g., "G" for "GARCIA", "R" for "RODRIGUEZ")
            if clean_full.startswith(clean_abbr):
                return True
            
            # Check abbreviation dictionary
            if clean_abbr in self._abbreviations_dict:
                return clean_full in self._abbreviations_dict[clean_abbr]
            
            return False
        
        def are_words_equal(w1, w2):
            """Check if two words are equal (exact match, abbreviation match, or nickname match)."""
            if not w1 or not w2:
                return False
            
            # Exact match
            if w1 == w2:
                return True
            
            # Dictionary lookup for nicknames of any length (Bill↔William, Paco↔Francisco, etc.)
            u1, u2 = w1.rstrip('.').upper(), w2.rstrip('.').upper()
            if u1 in self._abbreviations_dict and u2 in self._abbreviations_dict[u1]:
                return True
            if u2 in self._abbreviations_dict and u1 in self._abbreviations_dict[u2]:
                return True
            
            # Check short abbreviations by prefix
            is_abbr1 = self.is_abbreviation(w1)
            is_abbr2 = self.is_abbreviation(w2)
            
            if is_abbr1 and not is_abbr2 and could_be_abbreviation_of(w1, w2):
                return True
            
            if is_abbr2 and not is_abbr1 and could_be_abbreviation_of(w2, w1):
                return True
            
            return False
        
        def are_words_similar(w1, w2):
            """
            Check if two words are similar enough to be aligned together.
            
            Uses fuzzy matching via are_words_equivalent for cases like:
            - ROBERT vs ROBERTO (similar names, one is a variant of the other)
            - FRANCISCO vs FCO (abbreviation)
            - JOSE vs JOSÉ (accent differences)
            - BILL vs WILLIAM (nickname from dictionary)
            """
            if not w1 or not w2:
                return False
            
            # Exact match (fast path)
            if w1 == w2:
                return True
            
            # Dictionary lookup for nicknames of any length
            u1, u2 = w1.rstrip('.').upper(), w2.rstrip('.').upper()
            if u1 in self._abbreviations_dict and u2 in self._abbreviations_dict[u1]:
                return True
            if u2 in self._abbreviations_dict and u1 in self._abbreviations_dict[u2]:
                return True
            
            # Check short abbreviations by prefix
            is_abbr1 = self.is_abbreviation(w1)
            is_abbr2 = self.is_abbreviation(w2)
            
            if is_abbr1 and not is_abbr2 and could_be_abbreviation_of(w1, w2):
                return True
            
            if is_abbr2 and not is_abbr1 and could_be_abbreviation_of(w2, w1):
                return True
            
            # Fuzzy matching for similar names (e.g., ROBERT vs ROBERTO)
            # Use lenient thresholds since this is for alignment purposes
            is_match, _ = self._are_words_equivalent(
                w1, w2,
                levenshtein_threshold=0.80,
                jaro_winkler_threshold=0.85,
                metaphone_required=False
            )
            
            return is_match
        
        # Select comparison function based on fuzzy_match parameter
        words_match = are_words_similar if fuzzy_match else are_words_equal
        
        result1 = []
        result2 = []
        
        i = 0  # Index for list1
        j = 0  # Index for list2
        
        while i < len(list1) or j < len(list2):
            # Both lists have elements remaining
            if i < len(list1) and j < len(list2):
                w1 = list1[i]
                w2 = list2[j]
                
                # Words match - align them together
                if words_match(w1, w2):
                    result1.append(w1)
                    result2.append(w2)
                    i += 1
                    j += 1
                    continue
                
                # Words don't match - check if w1 appears later in list2
                found_in_list2 = False
                for k in range(j + 1, len(list2)):
                    if words_match(w1, list2[k]):
                        # w1 appears later in list2, so w2 is unique
                        result1.append(None)
                        result2.append(w2)
                        j += 1
                        found_in_list2 = True
                        break
                
                if found_in_list2:
                    continue
                
                # w1 doesn't appear in remaining list2, check if w2 appears in remaining list1
                found_in_list1 = False
                for k in range(i + 1, len(list1)):
                    if words_match(list1[k], w2):
                        # w2 appears later in list1, so w1 is unique
                        result1.append(w1)
                        result2.append(None)
                        i += 1
                        found_in_list1 = True
                        break
                
                if found_in_list1:
                    continue
                
                # Neither word appears in the other list - both are unique
                # Insert w1 first with None in list2
                result1.append(w1)
                result2.append(None)
                i += 1
                # Then insert w2 with None in list1
                # (will be processed in next iteration or at the end)
            
            elif i < len(list1):
                # Only list1 has elements remaining
                result1.append(list1[i])
                result2.append(None)
                i += 1
            
            elif j < len(list2):
                # Only list2 has elements remaining
                result1.append(None)
                result2.append(list2[j])
                j += 1
        
        return result1, result2

    @staticmethod
    def space_pattern(s: str) -> str:
        """
        Normalize whitespace in a string by collapsing consecutive spaces and trimming.

        Args:
            s (str): Input string

        Returns:
            str: Normalized string with single spaces and trimmed
        """
        import re
        return re.sub(r'\s+', ' ', s.strip())

    @staticmethod
    def pattern_string(s1: str, s2: str) -> str:
        """
        Create a pattern string showing character-by-character alignment.

        Args:
            s1 (str): First string
            s2 (str): Second string

        Returns:
            str: Pattern string with '.' for mismatches
        """
        result = []
        for c1, c2 in zip(s1, s2):
            if c1 == c2:
                result.append(c1)
            else:
                result.append('.')
        # Add remaining characters from longer string as dots
        longer = s1 if len(s1) > len(s2) else s2
        result.extend(['.'] * (len(longer) - len(result)))
        return ''.join(result)

    @staticmethod
    def similarity_percentage(p_str1: str, p_str2: str) -> float:
        """
        Calculates a similarity score between two strings, returning a value between 0 and 100.

        This function normalizes both input strings by collapsing consecutive spaces and trimming
        whitespace. It then compares them using three levels of similarity:
        1. Exact match: returns 100.0
        2. Substring match: returns proportional score based on length ratio
        3. Character-by-character alignment: uses pattern_string to count matching characters

        Args:
            p_str1 (str): The first string to compare
            p_str2 (str): The second string to compare

        Returns:
            float: Similarity score between 0.0 and 100.0

        Raises:
            TypeError: If inputs are not strings

        Example:
            >>> similarity_percentage("hello", "hello")
            100.0
            >>> similarity_percentage("hel", "hello")
            60.0
            >>> similarity_percentage("hxl", "hello")
            60.0
        """
        if not isinstance(p_str1, str) or not isinstance(p_str2, str):
            raise TypeError("Both inputs must be strings")

        s1 = TextMatcher.space_pattern(p_str1)
        s2 = TextMatcher.space_pattern(p_str2)

        # Ensure s1 is the shorter string
        if len(s1) > len(s2):
            s1, s2 = s2, s1

        if s1 == s2:
            return 100.0
        elif s1 in s2:
            return len(s1) / len(s2) * 100.0
        else:
            # Use pattern matching for partial similarity
            pattern = TextMatcher.pattern_string(s1, s2)
            pattern_no_spaces = pattern.replace(' ', '')
            dots = pattern_no_spaces.count('.')
            s2_no_spaces = s2.replace(' ', '')
            return (len(s2_no_spaces) - dots) / len(s2_no_spaces) * 100.0

    def same_chars(self, str1: str, str2: str) -> bool:
        """
        Compares if two strings contain exactly the same characters (ignoring case, accents, and spaces),
        regardless of order and frequency.
        
        Description:
            This method normalizes both input strings by:
            - Removing accents (flattening vowels)
            - Converting to uppercase
            - Removing spaces
            Then compares the character frequency using Counter to ensure both strings
            contain the same characters with the same frequency.
            
            Uses internal string utilities for accent removal (flat_vowels) and
            consistent space handling (normalize_spaces).
        
        Args:
            str1 (str): The first string to compare
            str2 (str): The second string to compare
        
        Returns:
            bool: True if both strings contain the same characters with the same frequency,
                  False otherwise
        
        Raises:
            None
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Same characters, different order
            result = matcher.same_chars("amor", "roma")
            # Returns: True
            
            # Example 2: Same characters with accents
            result = matcher.same_chars("José María", "Maria Jose")
            # Returns: True (accents removed, spaces ignored)
            
            # Example 3: Different characters
            result = matcher.same_chars("hello", "world")
            # Returns: False
            
            # Example 4: Different frequency
            result = matcher.same_chars("aaa", "aa")
            # Returns: False
        
        Cost:
            O(n + m) where n and m are the lengths of str1 and str2
        """

        # Input validation
        if not isinstance(str1, str):
            raise TypeError("str1 must be a string")
        
        if not isinstance(str2, str):
            raise TypeError("str2 must be a string")
        
        # Early return for empty strings
        if not str1 or not str2:
            return False

        # Normalize: remove accents, convert to uppercase, and remove spaces
        norm1 = self._flat_vowels(str1).replace(' ', '').upper()
        norm2 = self._flat_vowels(str2).replace(' ', '').upper()

        # Compare character frequency
        return Counter(norm1) == Counter(norm2)

    def same_chars_similarity(self, str1: str, str2: str) -> Dict[str, float]:
        """
        Calculate character similarity between two strings using Jaccard index.
        
        Description:
            Unlike same_chars() which returns a boolean, this method provides a gradual
            similarity score (0.0 to 1.0) based on character overlap. Uses the Jaccard
            index algorithm which is ideal for set similarity.
            
            The method normalizes both strings (removes accents, converts to uppercase)
            and then calculates how similar they are based on shared characters.
            
            Useful when you need to know "how similar" rather than just "same or different".
        
        Args:
            str1 (str): The first string to compare
            str2 (str): The second string to compare
        
        Returns:
            Dict[str, float]: Dictionary with:
                - 'distance': Jaccard distance (1 - similarity)
                - 'similarity': Jaccard index (0.0 to 1.0)
                - 'score': Similarity as percentage (0.0 to 100.0)
        
        Raises:
            TypeError: If inputs are not strings
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Very similar strings
            result = matcher.same_chars_similarity("hello", "hallo")
            # Returns: {'distance': 0.17, 'similarity': 0.83, 'score': 83.0}
            
            # Example 2: Partially similar
            result = matcher.same_chars_similarity("python", "java")
            # Returns: {'distance': 0.78, 'similarity': 0.22, 'score': 22.0}
            
            # Example 3: With accents
            result = matcher.same_chars_similarity("José", "Jose")
            # Returns: {'distance': 0.0, 'similarity': 1.0, 'score': 100.0}
        
        Cost:
            O(n + m) where n and m are the lengths of str1 and str2
        """
        # Input validation
        if not isinstance(str1, str):
            raise TypeError("str1 must be a string")
        
        if not isinstance(str2, str):
            raise TypeError("str2 must be a string")
        
        # Early return for empty strings
        if not str1 or not str2:
            return {'distance': 1.0, 'similarity': 0.0, 'score': 0.0}

        # Normalize: remove accents, convert to uppercase
        norm1 = self._flat_vowels(str1).upper()
        norm2 = self._flat_vowels(str2).upper()

        # Use Jaccard algorithm for character-level similarity
        return self._calculate_similarity(norm1, norm2, algorithm='jaccard')

    def compare_tokens(self, name1, name2, keep_order: bool = True, require_same_len: bool = False):
        """
        Compare two tokenized lists of words with configurable position and length requirements.
        
        Description:
            Optimized token comparison using set operations and sorting for O(n log n) complexity
            instead of O(n²). When keep_order=False, uses sorted list comparison for direct equality
            check, avoiding nested loops entirely.
            
            **Token Difference Validation:**
            - If number of tokens < 4: difference in matching tokens must be 0 (all must match)
            - If number of tokens >= 4: difference in matching tokens can be at most 1
        
        Args:
            name1 (List[str]): First list of tokens
            name2 (List[str]): Second list of tokens
            keep_order (bool): Whether tokens must maintain relative positions. Default: True
            require_same_len (bool): Whether both lists must have the same number of tokens. Default: False
            
        Returns:
            bool: True if tokens match according to the specified criteria
            
        Cost:
            - Without keep_order: O(n log n) - sorting + O(n) comparison
            - With keep_order: O(n*m) worst case, but optimized with early exits
        """
        # Validación tautológica
        if not name1 or  not name2:
            return False
        
        if name1 == name2:
            return True

        name1_split = name1.split()
        name2_split = name2.split()

        # Validación temprana de longitud
        if require_same_len and len(name1_split) != len(name2_split):
            return False
        
        # Calcular tokens comunes para validación
        set1 = set(name1_split)
        set2 = set(name2_split)
        common_tokens = set1.intersection(set2)
        num_common_tokens = len(common_tokens)
        
        # Determinar longitudes
        len1 = len(name1_split)
        len2 = len(name2_split)
        min_tokens = min(len1, len2)
        max_tokens = max(len1, len2)
        token_diff = abs(len1 - len2)
        
        # Regla 1: Si ambos tienen la misma longitud, todos los tokens deben coincidir
        if len1 == len2:
            if num_common_tokens == len1:
                return True
            else:
                return False
        
        # Regla 2: Si tienen diferente longitud, aplicar validación según el número de tokens
        # Si uno tiene 4 o más tokens, la diferencia de longitud debe ser exactamente 1
        if max_tokens >= 4:
            if token_diff == 1 and num_common_tokens == min_tokens:
                # Continuar con verificación de orden más adelante
                pass
            else:
                return False
        else:
            # Si ambos tienen menos de 4 tokens, todos deben coincidir (no se permite diferencia)
            return False
        
        # Optimización: Si no importa el orden, ordenar y comparar directamente
        if not keep_order:
            # Crear copias ordenadas
            sorted1 = sorted(name1_split)
            sorted2 = sorted(name2_split)
            
            # Si tienen la misma longitud, deben ser idénticas después del sort
            if len(sorted1) == len(sorted2):
                return sorted1 == sorted2
            
            # Si no tienen la misma longitud, la lista más corta debe ser subconjunto
            shorter = sorted1 if len(sorted1) < len(sorted2) else sorted2
            longer = sorted2 if len(sorted1) < len(sorted2) else sorted1
            
            # Usar two-pointer technique para verificar si shorter es subconjunto de longer
            i = j = 0
            while i < len(shorter) and j < len(longer):
                if shorter[i] == longer[j]:
                    i += 1
                    j += 1
                else:
                    j += 1
            
            return i == len(shorter)
        
        # Cuando keep_order=True, mantener la lógica original pero optimizada
        # Optimización: Usar sets para chequeo rápido de pertenencia (O(1) vs O(n))
        
        # Verificar si todos los tokens de name2 están en name1
        if set2.issubset(set1):
            # Solo verificar orden si keep_order=True
            # Verificar que cada palabra en name2 aparece en orden en name1
            last_found_idx = -1
            for name2_word in name2_split:
                try:
                    # Buscar palabra comenzando desde la última posición encontrada
                    current_idx = name1.index(name2_word, last_found_idx + 1)
                    last_found_idx = current_idx
                except ValueError:
                    # Palabra no encontrada en el rango válido
                    break
            else:
                # Todas las palabras se encontraron en orden
                return True
        
        # Verificar dirección inversa: todos los tokens de name1 están en name2
        if set1.issubset(set2):
            # Verificar que cada palabra en name1 aparece en orden en name2
            last_found_idx = -1
            for fn_word in name1_split:
                try:
                    current_idx = name2_split.index(fn_word, last_found_idx + 1)
                    last_found_idx = current_idx
                except ValueError:
                    break
            else:
                return True
        
        return False

    def compare_phrases(self, phrase1: str, phrase2: str, threshold: float = 0.8) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare two phrases or sentences using Sørensen-Dice coefficient.
        
        Description:
            Sørensen-Dice is specifically designed for comparing sets of tokens (words),
            making it ideal for phrase and sentence comparison. It measures similarity
            based on common words between the two phrases.
            
            This method is particularly useful for:
            - Comparing product descriptions
            - Finding similar document titles
            - Matching user queries to stored phrases
            - Detecting near-duplicate content
        
        Args:
            phrase1 (str): The first phrase to compare
            phrase2 (str): The second phrase to compare
            threshold (float): Minimum similarity score (0.0-1.0) to consider phrases as matching.
                             Default: 0.8
        
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if similarity >= threshold, False otherwise
                - Dict: Detailed metrics including:
                    - 'distance': Sørensen-Dice distance
                    - 'similarity': Normalized similarity (0.0-1.0)
                    - 'score': Similarity as percentage (0.0-100.0)
                    - 'common_words': List of words found in both phrases
                    - 'unique_to_phrase1': Words only in phrase1
                    - 'unique_to_phrase2': Words only in phrase2
        
        Raises:
            TypeError: If inputs are not strings
            ValueError: If threshold is not between 0.0 and 1.0
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Very similar descriptions
            is_match, metrics = matcher.compare_phrases(
                "Premium leather wallet with card slots",
                "Leather wallet premium with slots for cards"
            )
            # Returns: (True, {'similarity': 0.89, 'score': 89.0, ...})
            
            # Example 2: Partial overlap
            is_match, metrics = matcher.compare_phrases(
                "Fast delivery service",
                "Quick shipping options",
                threshold=0.6
            )
            # Returns: (False, {'similarity': 0.0, 'score': 0.0, ...})
            
            # Example 3: Examine detailed results
            is_match, metrics = matcher.compare_phrases(
                "Red apple on the table",
                "Green apple on the chair"
            )
            print(f"Common words: {metrics['common_words']}")
            # Output: Common words: ['apple', 'on', 'the']
        
        Cost:
            O(n + m) where n and m are the number of words in each phrase
        """
        # Input validation
        if not isinstance(phrase1, str):
            raise TypeError("phrase1 must be a string")
        if not isinstance(phrase2, str):
            raise TypeError("phrase2 must be a string")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        
        # Early return for empty strings
        if not phrase1 or not phrase2:
            return False, {'distance': 1.0, 'similarity': 0.0, 'score': 0.0,
                          'common_words': [], 'unique_to_phrase1': [], 'unique_to_phrase2': []}
        
        # Normalize phrases
        norm1 = self.normalize_text(phrase1, for_names=False, case_mode="lower")
        norm2 = self.normalize_text(phrase2, for_names=False, case_mode="lower")
        
        # Get Sørensen-Dice similarity
        similarity_result = self._calculate_similarity(norm1, norm2, algorithm='sorensen_dice')
        
        # Calculate additional useful information
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        common = words1.intersection(words2)
        unique1 = words1 - words2
        unique2 = words2 - words1
        
        # Enhance result dictionary
        result = {
            'distance': similarity_result.get('distance', 1.0),
            'similarity': similarity_result.get('similarity', 0.0),
            'score': similarity_result.get('score', 0.0),
            'common_words': sorted(list(common)),
            'unique_to_phrase1': sorted(list(unique1)),
            'unique_to_phrase2': sorted(list(unique2))
        }
        
        is_match = result['similarity'] >= threshold
        return is_match, result

    def find_phonetic_duplicates(
        self,
        names: List[str],
        threshold: float = 0.8,
        use_mra: bool = True
    ) -> List[List[str]]:
        """
        Find groups of phonetically similar names using Match Rating Approach (MRA).
        
        Description:
            MRA is a phonetic algorithm specifically designed for name matching.
            It's particularly effective for finding duplicate entries in databases
            where names may be spelled differently but sound the same.
            
            This method is ideal for:
            - Deduplication of customer databases
            - Finding potential duplicate accounts
            - Matching names across different systems
            - Identity resolution in data integration
        
        Args:
            names (List[str]): List of names to analyze for duplicates
            threshold (float): Minimum similarity score (0.0-1.0) to consider names as duplicates.
                             Default: 0.8
            use_mra (bool): If True, uses MRA algorithm; if False, uses metaphone.
                          Default: True
        
        Returns:
            List[List[str]]: List of groups, where each group contains phonetically similar names
        
        Raises:
            TypeError: If names is not a list or contains non-string elements
            ValueError: If threshold is not between 0.0 and 1.0
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Find duplicate names
            names = ["Smith", "Smyth", "Schmidt", "Johnson", "Jonson"]
            duplicates = matcher.find_phonetic_duplicates(names, threshold=0.75)
            # Returns: [['Smith', 'Smyth', 'Schmidt'], ['Johnson', 'Jonson']]
            
            # Example 2: Spanish names with variations
            names = ["José María", "Jose Maria", "Maria Jose", "Pedro"]
            duplicates = matcher.find_phonetic_duplicates(names)
            # Returns: [['José María', 'Jose Maria']]
            
            # Example 3: Strict matching
            names = ["Catherine", "Katherine", "Kathryn"]
            duplicates = matcher.find_phonetic_duplicates(names, threshold=0.9)
            # Returns: [['Catherine', 'Katherine', 'Kathryn']]
        
        Cost:
            O(n²) where n is the number of names (pairwise comparison)
        """
        # Input validation
        if not isinstance(names, list):
            raise TypeError("names must be a list")
        if not all(isinstance(name, str) for name in names):
            raise TypeError("all elements in names must be strings")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be between 0.0 and 1.0")
        
        if len(names) < 2:
            return []
        
        # Use union-find (disjoint set) for efficient grouping
        parent = {name: name for name in names}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent[root_y] = root_x
        
        # Compare all pairs
        algorithm = 'mra' if use_mra else 'metaphone'
        
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name1 = names[i]
                name2 = names[j]
                
                # Normalize names
                norm1 = self.normalize_text(name1, for_names=True)
                norm2 = self.normalize_text(name2, for_names=True)
                
                if algorithm == 'metaphone':
                    # Metaphone returns boolean
                    is_similar = self._calculate_similarity(norm1, norm2, algorithm='metaphone')
                else:
                    # MRA returns dict with similarity
                    result = self._calculate_similarity(norm1, norm2, algorithm='mra')
                    similarity = result.get('similarity', 0.0)
                    is_similar = similarity >= threshold
                
                if is_similar:
                    union(name1, name2)
        
        # Group names by their root parent
        groups = defaultdict(list)
        for name in names:
            root = find(name)
            groups[root].append(name)
        
        # Return only groups with more than one name
        return [group for group in groups.values() if len(group) > 1]

    def find_common_patterns(
        self,
        text1: str,
        text2: str,
        min_length: int = 3
    ) -> Dict[str, Any]:
        """
        Find common patterns and subsequences between two texts using LCS.
        
        Description:
            Uses the Longest Common Subsequence (LCS) algorithm to identify
            shared patterns between texts. Unlike simple substring matching,
            LCS can find non-contiguous common elements.
            
            This method is useful for:
            - Plagiarism detection
            - Text similarity analysis
            - Finding shared structure in documents
            - Code similarity detection
        
        Args:
            text1 (str): The first text to analyze
            text2 (str): The second text to analyze
            min_length (int): Minimum length of common subsequence to report.
                            Default: 3
        
        Returns:
            Dict[str, Any]: Dictionary with:
                - 'lcs_length': Length of longest common subsequence
                - 'lcs_ratio': Ratio of LCS length to average text length
                - 'similarity': LCS-based similarity score (0.0-1.0)
                - 'score': Similarity as percentage (0.0-100.0)
                - 'has_significant_overlap': True if ratio exceeds min_length threshold
        
        Raises:
            TypeError: If inputs are not strings
            ValueError: If min_length is not positive
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Find common structure
            result = matcher.find_common_patterns(
                "The quick brown fox jumps",
                "The fast brown dog runs"
            )
            # Returns: {'lcs_length': 15, 'similarity': 0.65, ...}
            
            # Example 2: Code similarity
            code1 = "def calculate_sum(a, b): return a + b"
            code2 = "def compute_sum(x, y): return x + y"
            result = matcher.find_common_patterns(code1, code2, min_length=5)
            print(f"Similarity: {result['score']:.1f}%")
            
            # Example 3: Check for significant overlap
            result = matcher.find_common_patterns("hello world", "world hello")
            if result['has_significant_overlap']:
                print("Texts share significant patterns")
        
        Cost:
            O(m × n) where m and n are the lengths of the texts
        """
        # Input validation
        if not isinstance(text1, str):
            raise TypeError("text1 must be a string")
        if not isinstance(text2, str):
            raise TypeError("text2 must be a string")
        if not isinstance(min_length, int) or min_length < 1:
            raise ValueError("min_length must be a positive integer")
        
        # Early return for empty strings
        if not text1 or not text2:
            return {
                'lcs_length': 0,
                'lcs_ratio': 0.0,
                'similarity': 0.0,
                'score': 0.0,
                'has_significant_overlap': False
            }
        
        # Normalize texts
        norm1 = self.normalize_text(text1, for_names=False, case_mode="lower")
        norm2 = self.normalize_text(text2, for_names=False, case_mode="lower")
        
        # Calculate LCS similarity
        lcs_result = self._calculate_similarity(norm1, norm2, algorithm='lcs')
        
        # Calculate average length for ratio
        avg_length = (len(norm1) + len(norm2)) / 2.0
        lcs_length = lcs_result.get('lcs_length', 0)
        lcs_ratio = lcs_length / avg_length if avg_length > 0 else 0.0
        
        # Determine if there's significant overlap
        has_significant = lcs_length >= min_length and lcs_ratio >= 0.3
        
        return {
            'lcs_length': lcs_length,
            'lcs_ratio': lcs_ratio,
            'similarity': lcs_result.get('similarity', 0.0),
            'score': lcs_result.get('score', 0.0),
            'has_significant_overlap': has_significant
        }

    def compare_text_detailed(
        self,
        text1: str,
        text2: str,
        case_sensitive: bool = False,
        show_diff: bool = True,
        context_lines: int = 3
    ) -> Dict[str, Any]:
        """
        Compare two texts or code blocks using difflib.SequenceMatcher with detailed diff analysis.
        
        Description:
            This method provides a comprehensive comparison using Python's difflib.SequenceMatcher,
            which is excellent for:
            - Code comparison and version control
            - Text diff visualization
            - Line-by-line change tracking
            - Finding matching blocks
            
            Unlike other algorithms focused on overall similarity, this method gives you
            detailed information about exactly what changed, where, and provides a unified
            diff format similar to git diff.
        
        Args:
            text1 (str): The first text/code to compare (often the "original")
            text2 (str): The second text/code to compare (often the "modified")
            case_sensitive (bool): Whether comparison should be case-sensitive.
                                  Default: False
            show_diff (bool): Whether to generate unified diff output.
                            Default: True
            context_lines (int): Number of context lines to show in diff.
                               Default: 3
        
        Returns:
            Dict[str, Any]: Dictionary with:
                - 'ratio': Overall similarity ratio (0.0 to 1.0)
                - 'score': Similarity as percentage (0.0 to 100.0)
                - 'matching_blocks': List of matching blocks (start1, start2, length)
                - 'opcodes': Detailed operation codes ('equal', 'replace', 'delete', 'insert')
                - 'diff': Unified diff output (if show_diff=True)
                - 'lines_added': Number of lines added
                - 'lines_removed': Number of lines removed
                - 'lines_changed': Number of lines changed
                - 'total_lines_text1': Total lines in text1
                - 'total_lines_text2': Total lines in text2
        
        Raises:
            TypeError: If inputs are not strings
            ValueError: If context_lines is negative
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Compare two versions of code
            code_v1 = '''def calculate(x, y):
                return x + y'''
            
            code_v2 = '''def calculate(x, y, z=0):
                result = x + y + z
                return result'''
            
            result = matcher.compare_text_detailed(code_v1, code_v2)
            print(f"Similarity: {result['score']:.1f}%")
            print(f"Lines added: {result['lines_added']}")
            print(f"Lines changed: {result['lines_changed']}")
            print(result['diff'])
            
            # Example 2: Compare text documents
            doc1 = "The quick brown fox jumps over the lazy dog"
            doc2 = "The fast brown fox runs over the sleepy dog"
            
            result = matcher.compare_text_detailed(doc1, doc2, case_sensitive=True)
            for op, i1, i2, j1, j2 in result['opcodes']:
                if op == 'replace':
                    print(f"Changed: '{doc1[i1:i2]}' -> '{doc2[j1:j2]}'")
            
            # Example 3: Simple similarity check
            text1 = "Hello World"
            text2 = "Hello Universe"
            result = matcher.compare_text_detailed(text1, text2, show_diff=False)
            if result['ratio'] > 0.5:
                print("Texts are similar")
        
        Cost:
            O(n × m) where n and m are the lengths of the texts
        """
        import difflib
        
        # Input validation
        if not isinstance(text1, str):
            raise TypeError("text1 must be a string")
        if not isinstance(text2, str):
            raise TypeError("text2 must be a string")
        if not isinstance(context_lines, int) or context_lines < 0:
            raise ValueError("context_lines must be a non-negative integer")
        
        # Handle case sensitivity
        if not case_sensitive:
            compare_text1 = text1.lower()
            compare_text2 = text2.lower()
        else:
            compare_text1 = text1
            compare_text2 = text2
        
        # Create SequenceMatcher for character-level comparison
        char_matcher = difflib.SequenceMatcher(None, compare_text1, compare_text2)
        
        # Get basic similarity ratio
        ratio = char_matcher.ratio()
        score = ratio * 100.0
        
        # Get matching blocks
        matching_blocks = char_matcher.get_matching_blocks()
        
        # Get opcodes for detailed differences
        opcodes = char_matcher.get_opcodes()
        
        # Split into lines for line-level analysis
        lines1 = compare_text1.splitlines(keepends=True)
        lines2 = compare_text2.splitlines(keepends=True)
        
        # Create line-level matcher
        line_matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        # Count line changes
        lines_added = 0
        lines_removed = 0
        lines_changed = 0
        
        for op, i1, i2, j1, j2 in line_matcher.get_opcodes():
            if op == 'insert':
                lines_added += (j2 - j1)
            elif op == 'delete':
                lines_removed += (i2 - i1)
            elif op == 'replace':
                lines_changed += max(i2 - i1, j2 - j1)
        
        # Build result dictionary
        result = {
            'ratio': ratio,
            'score': score,
            'matching_blocks': [
                {
                    'text1_start': block.a,
                    'text2_start': block.b,
                    'length': block.size
                }
                for block in matching_blocks
            ],
            'opcodes': [
                {
                    'operation': op,
                    'text1_start': i1,
                    'text1_end': i2,
                    'text2_start': j1,
                    'text2_end': j2,
                    'text1_content': text1[i1:i2] if op in ('delete', 'replace') else '',
                    'text2_content': text2[j1:j2] if op in ('insert', 'replace') else ''
                }
                for op, i1, i2, j1, j2 in opcodes
            ],
            'lines_added': lines_added,
            'lines_removed': lines_removed,
            'lines_changed': lines_changed,
            'total_lines_text1': len(lines1),
            'total_lines_text2': len(lines2)
        }
        
        # Generate unified diff if requested
        if show_diff:
            # Use original text for diff (not lowercased)
            original_lines1 = text1.splitlines(keepends=True)
            original_lines2 = text2.splitlines(keepends=True)
            
            diff_generator = difflib.unified_diff(
                original_lines1,
                original_lines2,
                fromfile='text1',
                tofile='text2',
                lineterm='',
                n=context_lines
            )
            
            result['diff'] = '\n'.join(diff_generator)
        else:
            result['diff'] = None
        
        return result

    def compare_code_blocks(
        self,
        code1: str,
        code2: str,
        language: str = 'python',
        ignore_whitespace: bool = True,
        ignore_comments: bool = False
    ) -> Dict[str, Any]:
        """
        Compare two code blocks with code-specific preprocessing.
        
        Description:
            Specialized version of compare_text_detailed optimized for source code comparison.
            Provides additional preprocessing options relevant to code:
            - Whitespace normalization
            - Comment removal (optional)
            - Language-aware comparison
            
            This method is ideal for:
            - Code review automation
            - Detecting code duplication
            - Version comparison in CI/CD
            - Plagiarism detection in programming assignments
        
        Args:
            code1 (str): First code block to compare
            code2 (str): Second code block to compare
            language (str): Programming language ('python', 'javascript', 'java', etc.)
                          Used for comment detection. Default: 'python'
            ignore_whitespace (bool): Whether to ignore leading/trailing whitespace.
                                     Default: True
            ignore_comments (bool): Whether to remove comments before comparison.
                                  Default: False
        
        Returns:
            Dict[str, Any]: Same as compare_text_detailed, plus:
                - 'code1_normalized': Normalized version of code1
                - 'code2_normalized': Normalized version of code2
                - 'structural_similarity': Similarity ignoring whitespace/comments
        
        Raises:
            TypeError: If inputs are not strings
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Compare Python functions
            code1 = '''
            def hello(name):
                # Print greeting
                print(f"Hello {name}")
            '''
            
            code2 = '''
            def hello(name):
                print(f"Hello {name}")  # Greeting function
            '''
            
            result = matcher.compare_code_blocks(
                code1, code2,
                language='python',
                ignore_comments=True
            )
            print(f"Structural similarity: {result['structural_similarity']:.1f}%")
            
            # Example 2: Detect code duplication
            snippet1 = "for i in range(10): print(i)"
            snippet2 = "for i in range(10):\\n    print(i)"
            
            result = matcher.compare_code_blocks(snippet1, snippet2)
            if result['score'] > 90:
                print("Potential code duplication detected")
        
        Cost:
            O(n × m) where n and m are the lengths of the code blocks
        """
        # Input validation
        if not isinstance(code1, str):
            raise TypeError("code1 must be a string")
        if not isinstance(code2, str):
            raise TypeError("code2 must be a string")
        
        # Define comment patterns for different languages
        comment_patterns = {
            'python': r'#.*?$',
            'javascript': r'//.*?$|/\*.*?\*/',
            'java': r'//.*?$|/\*.*?\*/',
            'c': r'//.*?$|/\*.*?\*/',
            'cpp': r'//.*?$|/\*.*?\*/',
            'ruby': r'#.*?$',
            'php': r'#.*?$|//.*?$|/\*.*?\*/',
            'sql': r'--.*?$|/\*.*?\*/',
        }
        
        def normalize_code(code: str) -> str:
            """Normalize code according to settings"""
            normalized = code
            
            # Remove comments if requested
            if ignore_comments and language.lower() in comment_patterns:
                pattern = comment_patterns[language.lower()]
                normalized = re.sub(pattern, '', normalized, flags=re.MULTILINE | re.DOTALL)
            
            # Normalize whitespace if requested
            if ignore_whitespace:
                # Normalize each line's whitespace
                lines = normalized.splitlines()
                normalized_lines = [line.strip() for line in lines if line.strip()]
                normalized = '\n'.join(normalized_lines)
            
            return normalized
        
        # Normalize both code blocks
        norm_code1 = normalize_code(code1)
        norm_code2 = normalize_code(code2)
        
        # Compare normalized code
        normalized_result = self.compare_text_detailed(
            norm_code1,
            norm_code2,
            case_sensitive=True,  # Code is typically case-sensitive
            show_diff=True,
            context_lines=3
        )
        
        # Also compare original code for reference
        original_result = self.compare_text_detailed(
            code1,
            code2,
            case_sensitive=True,
            show_diff=False
        )
        
        # Combine results
        result = {
            **normalized_result,
            'original_similarity': original_result['score'],
            'structural_similarity': normalized_result['score'],
            'code1_normalized': norm_code1,
            'code2_normalized': norm_code2,
            'preprocessing': {
                'language': language,
                'ignore_whitespace': ignore_whitespace,
                'ignore_comments': ignore_comments
            }
        }
        
        return result
    
    def compare_name_bytokens(
        self,
        name1: str,
        name2: str,
        threshold: float = 0.9,
        keep_order: bool = True,
        normalize_names: bool = True,
        fuzzy_align: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Compares two full names (multiple words) and determines if they refer to the same person.
        
        Description:
            This method implements advanced multi-word name comparison logic that handles:
            - Different word order ("John Smith" vs "Smith John")
            - Missing or additional middle names ("John Smith" vs "John Michael Smith")
            - Abbreviations ("J. Smith" vs "John Smith", "Fco" vs "Francisco")
            - Spelling variations and typos
            
            **Key Features:**
            - **Word-by-word comparison**: Uses `compare_names` for each word pair
            - **Smart alignment**: Matches words even when positions differ
            - **Abbreviation handling**: Detects and matches common abbreviations
            - **Flexible matching**: Supports both strict order and order-insensitive comparison
            
            **Matching Rules:**
            - Rule #1: If both names have the same word count, all words must match
            - Rule #2: If word counts differ, the difference must equal the number of non-matching words
              (e.g., "John Smith" matches "John Michael Smith" because 1 word differs)
            
            **Comparison Process:**
            1. Normalize names (remove special characters, convert to uppercase)
            2. Tokenize into words
            3. Optionally sort words (if keep_order=False)
            4. Align word lists (matching words get same position)
            5. Compare each word pair using `compare_names` method
            6. Apply matching rules to determine final result
        
        Args:
            name1 (str): The first name to compare
            name2 (str): The second name to compare
            threshold (float): Similarity threshold (0.0 to 1.0). Default: 0.9
            keep_order (bool): Whether to preserve word order. Default: True
            normalize_names (bool): Whether to normalize names (remove special chars). Default: True
            fuzzy_align (bool): Alignment mode for word lists. Default: True
                - True: Uses fuzzy matching to align similar words (e.g., ROBERT ≈ ROBERTO)
                - False: Uses exact match or abbreviation only for alignment
        
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if names are considered alike, False otherwise
                - Dict[str, Any]: Detailed metrics including:
                    - 'normalized_name1': Normalized version of name1
                    - 'normalized_name2': Normalized version of name2
                    - 'words_name1': Tokenized words from name1
                    - 'words_name2': Tokenized words from name2
                    - 'aligned_words1': Aligned words list for name1
                    - 'aligned_words2': Aligned words list for name2
                    - 'word_pair_comparisons': List of comparison results for each word pair
                    - 'min_coincidences': Total number of matching word pairs
                    - 'word_count_diff': Absolute difference in word counts
                    - 'split_comparison_match': Boolean from compare_tokens (position-based validation)
                    - 'rule_applied': Which rule determined the result (1 or 2, or None if no match)
        
        Raises:
            TypeError: If name1 or name2 is not a string
            ValueError: If threshold is not between 0.0 and 1.0
        
        Example Usage:
            matcher = TextMatcher()
            
            # Example 1: Exact match with different order
            is_match, metrics = matcher.compare_name_bytokens(
                "Fernando Marcos", 
                "Marcos Fernando",
                keep_order=False
            )
            # Returns: (True, {...})
            
            # Example 2: Subset match (rule #2)
            is_match, metrics = matcher.compare_name_bytokens(
                "Fernando Marcos",
                "Jose Fernando Marcos Bernabé"
            )
            # Returns: (True, {...})
            
            # Example 3: Similar names with typos
            is_match, metrics = matcher.compare_name_bytokens(
                "Juan Francisco Dieguez",
                "Juan Fco Dieguez",
                threshold=0.85
            )
            # Returns: (True, {...})
            
            # Example 4: Different names
            is_match, metrics = matcher.compare_name_bytokens(
                "Juan Garcia",
                "Pedro Lopez"
            )
            # Returns: (False, {...})
            
            # Example 5: Order-insensitive comparison
            is_match, metrics = matcher.compare_name_bytokens(
                "Maria Garcia Lopez",
                "Lopez Garcia Maria",
                keep_order=False
            )
            # Returns: (True, {...})
        
        Cost:
            O(n*m*w) where n, m are average word lengths and w is the number of word pairs
        """
        # Initialize metrics dictionary with default values
        metrics = {
            'normalized_name1': '',
            'normalized_name2': '',
            'words_name1': [],
            'words_name2': [],
            'aligned_words1': [],
            'aligned_words2': [],
            'word_pair_comparisons': [],
            'word_count_diff': 0,
            'min_coincidences': 0,
            'rule_applied': None,
            'exact_match': False,
            'error': None
        }
        
        # Input validation - type and empty checks
        if not isinstance(name1, str) or not isinstance(name2, str):
            metrics['error'] = 'One or both inputs are not strings'
            return False, metrics
        
        if not name1 or not name2:
            metrics['error'] = 'One or both names are empty'
            return False, metrics
        
        if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be a float between 0.0 and 1.0.")
        if not isinstance(keep_order, bool):
            raise TypeError("keep_order must be a boolean.")
        if not isinstance(normalize_names, bool):
            raise TypeError("normalize_names must be a boolean.")
        if not isinstance(fuzzy_align, bool):
            raise TypeError("fuzzy_align must be a boolean.")
        
        # Normalize names (basic normalization: remove special chars except space, hyphen, apostrophe)
        if normalize_names:
            name1 = self.normalize_text(name1, for_names=True, case_mode="upper")
            name2 = self.normalize_text(name2, for_names=True, case_mode="upper")
        else:
            # Even without normalization, ensure consistent case
            name1 = name1.upper()
            name2 = name2.upper()
        
        # Caso trivial: nombres idénticos después de normalización
        if name1 == name2:
            metrics.update({
                'normalized_name1': name1,
                'normalized_name2': name2,
                'words_name1': name1.split(),
                'words_name2': name2.split(),
                'exact_match': True,
                'rule_applied': 'Exact match after normalization'
            })
            return True, metrics
        
        # Tokenize into words
        split_name1 = name1.split()
        split_name2 = name2.split()
        
        # Sort words if order doesn't matter
        if not keep_order:
            split_name1.sort()
            split_name2.sort()
        
        # Align lists for word-by-word comparison
        list_name1, list_name2 = self._align_lists(split_name1, split_name2, fuzzy_match=fuzzy_align)

        # Update metrics dictionary with calculated values
        metrics.update({
            'normalized_name1': name1,
            'normalized_name2': name2,
            'words_name1': split_name1,
            'words_name2': split_name2,
            'aligned_words1': list_name1,
            'aligned_words2': list_name2,
            'word_count_diff': abs(len(split_name1) - len(split_name2))
        })
        
        # Track minimum coincidences using compare_names for each word pair
        word_pair_matches = []
        
        for word1, word2 in zip(list_name1, list_name2):
            w1 = word1 if word1 else ''
            w2 = word2 if word2 else ''
            
            if w1 and w2:
                # Use compare_names for each word pair
                is_word_match, word_metrics = self.compare_names(
                    w1, 
                    w2, 
                    strict=False
                )
                
                word_pair_matches.append(1 if is_word_match else 0)
                metrics['word_pair_comparisons'].append({
                    'word1': w1,
                    'word2': w2,
                    'match': is_word_match,
                    'metrics': word_metrics
                })
            else:
                word_pair_matches.append(0)
                metrics['word_pair_comparisons'].append({
                    'word1': w1,
                    'word2': w2,
                    'match': False,
                    'metrics': {'note': 'One or both words empty'}
                })
        
        # Calculate total coincidences
        min_coincidences = sum(word_pair_matches)
        metrics['min_coincidences'] = min_coincidences
        
        # Apply decision rules
        result = False
        
        # Rule #1: Same word count - all words must be similar
        if len(split_name1) == len(split_name2) and (min_coincidences == len(split_name1)):
            result = True
            metrics['rule_applied'] = '#1 : Same word count - all words must be similar'
        
        # Rule #2: Word count difference - number of differences equals number of non-similar words
        elif len(split_name1) > 2 and len(split_name2) > 2 and min_coincidences > 2 and abs(len(split_name1) - len(split_name2)) == max(len(split_name1), len(split_name2)) - min_coincidences:
            result = True
            metrics['rule_applied'] = '#2 : Word count difference - number of differences equals number of non-similar words'
        else:
            metrics['rule_applied'] = None
        
        return result, metrics

    
    def compare_names(
        self,
        name1: str,
        name2: str,
        strict: bool = False,
        config: Optional[MatcherConfig] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Compares two names considering common variations and nicknames.
        
        Description:
            Specialized method for name comparison that handles common variations,
            initials, and cultural name differences. It normalizes names before
            comparison and uses appropriate thresholds for name-specific matching.
            
            In strict mode, phonetic matching is required. In non-strict mode,
            edit-distance metrics alone can determine a match.
            
            If config is provided with debug_mode enabled, returns detailed
            explanation of the matching decision.
        
        Args:
            name1 (str): The first name to compare
            name2 (str): The second name to compare
            strict (bool): Whether to require phonetic matching. Default: False
            config (Optional[MatcherConfig]): Configuration for comparison.
                                             If None, uses instance config.
                                             Default: None
        
        Returns:
            Tuple[bool, Dict[str, Any]]: A tuple containing:
                - bool: True if names match, False otherwise
                - Dict: Detailed comparison metrics
        
        Raises:
            TypeError: If name1 or name2 is not a string
        
        Example Usage:
            matcher = TextMatcher()
            
            # Common name variants
            is_match, metrics = matcher.compare_names("José", "Jose")
            # Returns: (True, {...})
            
            # Different names
            is_match, metrics = matcher.compare_names("Juan", "Pedro")
            # Returns: (False, {...})
            
            # Strict matching
            is_match, metrics = matcher.compare_names(
                "Michael", 
                "Mikhail", 
                strict=True
            )
            # Returns: (False or True depending on phonetic match)
        
        Cost:
            O(n*m) where n and m are the lengths of name1 and name2
        """
        # Input validation - type and empty checks
        if not isinstance(name1, str) or not isinstance(name2, str):
            return False, {'error': 'One or both inputs are not strings'}
        
        if not name1 or not name2:
            return False, {'error': 'One or both names are empty'}
        
        # Validación tautológica
        if name1 == name2:
            return True, {
                'exact_match': True,
                'levenshtein_ratio': 1.0,
                'jaro_winkler_score': 100.0,
                'metaphone_match': True
            }
        
        cfg = config if config is not None else self.config
        
        # Apply text normalization based on config settings
        normalized_name1 = self.normalize_text(name1, for_names=True, case_mode="title")
        normalized_name2 = self.normalize_text(name2, for_names=True, case_mode="title")
        
        # Use config thresholds, but allow strict parameter to override metaphone_required
        metaphone_req = strict if strict is not None else cfg.metaphone_required
        
        # Check abbreviation/nickname dictionary first (e.g. Bill↔William, Paco↔Francisco)
        abbr_score = self.compare_with_abbreviation(normalized_name1, normalized_name2, cfg.levenshtein_threshold)
        if abbr_score == 1.0:
            return True, {
                'abbreviation_match': True,
                'levenshtein_ratio': 1.0,
                'jaro_winkler_score': 100.0,
                'metaphone_match': True,
                'name1_normalized': normalized_name1,
                'name2_normalized': normalized_name2,
            }
        
        is_match, metrics = self._are_words_equivalent(
            normalized_name1,
            normalized_name2,
            levenshtein_threshold=cfg.levenshtein_threshold,
            jaro_winkler_threshold=cfg.jaro_winkler_threshold,
            metaphone_required=metaphone_req
        )
        
        # Add debug info if enabled
        if cfg.debug_mode:
            # Create temporary config with the thresholds used
            name_config = MatcherConfig(
                levenshtein_threshold=cfg.levenshtein_threshold,
                jaro_winkler_threshold=cfg.jaro_winkler_threshold,
                metaphone_required=metaphone_req,
                debug_mode=True
            )
            metrics = self._add_debug_info(metrics, normalized_name1, normalized_name2, is_match, name_config)
        
        return is_match, metrics

    def compare_text(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare two texts using token-based and subsequence algorithms.

        Args:
            text1 (str): The first text to compare.
            text2 (str): The second text to compare.

        Returns:
            Dict[str, Any]: A dictionary with similarity metrics.

        Example:
            matcher = TextMatcher()
            metrics = matcher.compare_text("this is a test", "this is test")
            print(metrics)
        """
        # Caso trivial: textos idénticos
        if text1 == text2:
            return {
                "sorensen_dice": 1.0,
                "ratcliff_obershelp": 1.0,
                "exact_match": True
            }
        
        return {
            "sorensen_dice": self.word_similarity.sorensen_dice_score(text1, text2),
            "ratcliff_obershelp": self.word_similarity.ratcliff_obershelp_score(text1, text2),
            "exact_match": False
        }
    
    def find_best_match(
        self,
        target: str,
        candidates: List[str],
        threshold: float = 0.85
    ) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """
        Finds the best matching string from a list of candidates.
        
        **Note:** For getting multiple matches, use compare_lists() instead.
        
        Description:
            Compares the target string against a list of candidate strings and
            returns the best match (if any) that meets the similarity threshold.
            This is useful for fuzzy search, autocomplete, and record linkage tasks.
            
            The method evaluates each candidate using combined similarity metrics
            and returns the candidate with the highest similarity score.
        
        Args:
            target (str): The string to match against
            candidates (List[str]): List of candidate strings to compare
            threshold (float): Minimum similarity threshold (0.0 to 1.0).
                             Default: 0.85
        
        Returns:
            Tuple[Optional[str], float, Dict[str, Any]]: A tuple containing:
                - str or None: The best matching candidate, or None if no match meets threshold
                - float: The similarity score of the best match (0.0 if no match)
                - Dict: Detailed metrics for the best match
        
        Raises:
            TypeError: If target is not a string or candidates is not a list
            ValueError: If threshold is outside valid range
        
        Example Usage:
            matcher = TextMatcher()
            
            candidates = ["Smith", "Smyth", "Jones", "Johnson"]
            best, score, metrics = matcher.find_best_match("Smithe", candidates)
            # Returns: ("Smith", 0.92, {...})
            
            # No match case
            best, score, metrics = matcher.find_best_match("Garcia", candidates)
            # Returns: (None, 0.0, {})
            
            # With custom threshold
            best, score, metrics = matcher.find_best_match(
                "Smit", 
                candidates,
                threshold=0.70
            )
            # Returns: ("Smith", 0.75, {...})
        
        Cost:
            O(k*n*m) where k is the number of candidates, n is the length of target,
            and m is the average length of candidates
        """
        if not isinstance(target, str):
            raise TypeError("Target must be a string.")
        if not isinstance(candidates, list):
            raise TypeError("Candidates must be a list.")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        if not candidates:
            return None, 0.0, {}
        
        # Validación tautológica: check if target exists exactly in candidates
        for candidate in candidates:
            if target == candidate:
                return candidate, 1.0, {
                    'exact_match': True,
                    'levenshtein_ratio': 1.0,
                    'jaro_winkler_score': 100.0,
                    'metaphone_match': True
                }
        
        # Apply text normalization to target
        normalized_target = self.normalize_text(target, for_names=False, case_mode="lower", config=self.config)
        
        best_match = None
        best_score = 0.0
        best_metrics = {}
        
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            
            # Apply text normalization to candidate
            normalized_candidate = self.normalize_text(candidate, for_names=False, case_mode="lower", config=self.config)
            
            # Caso trivial: candidato idéntico al target después de normalización
            if normalized_target == normalized_candidate:
                return candidate, 1.0, {
                    'exact_match': True,
                    'levenshtein_ratio': 1.0,
                    'jaro_winkler_score': 100.0,
                    'metaphone_match': True
                }
            
            is_match, metrics = self._are_words_equivalent(
                normalized_target,
                normalized_candidate,
                levenshtein_threshold=threshold,
                jaro_winkler_threshold=self.config.jaro_winkler_threshold,
                metaphone_required=False  # Use edit distance only for flexibility
            )
            
            # Use Levenshtein ratio as primary score
            current_score = metrics.get('levenshtein_ratio', 0.0)
            
            if current_score > best_score:
                best_score = current_score
                best_match = candidate
                best_metrics = metrics
        
        # Return None if no match meets threshold
        if best_score < threshold:
            return None, 0.0, {}
        
        return best_match, best_score, best_metrics

    def detect_duplicates(
        self,
        items: List[str],
        threshold: float = 0.85,
        use_blocking: bool = True,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        config: Optional[MatcherConfig] = None
    ) -> List[Tuple[str, str, float]]:
        """
        Detect duplicate strings in a list based on similarity threshold.
        
        **Performance Optimizations**:
        - **Blocking**: Reduces comparisons from O(n²) to O(n*k) where k << n
        - **Caching**: Avoids recalculating identical comparisons
        - **Parallelization**: Distributes work across multiple cores
        
        Description:
            This method efficiently finds duplicate or near-duplicate strings in a list.
            For large lists (>1000 items), it uses phonetic blocking to dramatically
            reduce the number of comparisons needed.
            
            Without blocking: 10,000 items = 49,995,000 comparisons
            With blocking: 10,000 items ≈ 50,000 - 500,000 comparisons (100x faster)

        Args:
            items (List[str]): List of strings to check for duplicates.
            threshold (float): Minimum similarity threshold (0.0-1.0). Default: 0.85
            use_blocking (bool): Use phonetic blocking to reduce comparisons.
                                Recommended for >1000 items. Default: True
            parallel (bool): Enable parallel processing.
                           Recommended for >5000 items. Default: False
            max_workers (Optional[int]): Number of parallel workers.
                                        If None, uses CPU count. Default: None
            config (Optional[MatcherConfig]): Configuration for comparison.
                                             If None, uses instance config.

        Returns:
            List[Tuple[str, str, float]]: List of tuples containing:
                - str: First item
                - str: Second item
                - float: Similarity score (0.0-1.0)

        Raises:
            TypeError: If items is not a list
            ValueError: If threshold is outside valid range

        Example Usage:
            matcher = TextMatcher()
            
            # Basic usage (small list)
            items = ["apple", "aple", "banana", "bananna"]
            duplicates = matcher.detect_duplicates(items, threshold=0.8)
            # Returns: [("apple", "aple", 0.91), ("banana", "bananna", 0.92)]
            
            # Large list with blocking (10x-100x faster)
            large_items = load_10000_names()
            duplicates = matcher.detect_duplicates(
                large_items,
                use_blocking=True,
                threshold=0.85
            )
            
            # Very large list with blocking + parallel (even faster)
            huge_items = load_100000_names()
            duplicates = matcher.detect_duplicates(
                huge_items,
                use_blocking=True,
                parallel=True,
                max_workers=8
            )
            
            # Check performance
            stats = matcher.get_cache_stats()
            print(f"Cache hit rate: {stats['hit_rate']:.2%}")
            
        Performance Comparison:
            1,000 items:
                - Without blocking: ~500K comparisons (slow)
                - With blocking: ~5K-50K comparisons (10x-100x faster)
            
            10,000 items:
                - Without blocking: ~50M comparisons (very slow)
                - With blocking: ~50K-500K comparisons (100x faster)
                - With blocking + parallel: Even faster (multi-core)
            
        Cost:
            Without blocking: O(n²) comparisons
            With blocking: O(n*k) comparisons where k is avg block size (k << n)
            Memory: O(n) for blocking index
        """
        if not isinstance(items, list):
            raise TypeError("Items must be a list.")
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        cfg = config if config is not None else self.config
        
        # For small lists, use simple O(n²) approach
        if len(items) < 100 or not use_blocking:
            duplicates = []
            
            for i, item1 in enumerate(items):
                for j in range(i + 1, len(items)):
                    item2 = items[j]
                    
                    # Apply text normalization to both items
                    normalized_item1 = self.normalize_text(item1, for_names=False, case_mode="lower", config=cfg)
                    normalized_item2 = self.normalize_text(item2, for_names=False, case_mode="lower", config=cfg)
                    
                    # Caso trivial: items idénticos después de normalización
                    if normalized_item1 == normalized_item2:
                        duplicates.append((item1, item2, 1.0))
                        continue
                    
                    # Check cache first
                    cache_key_params = {
                        'levenshtein_threshold': threshold,
                        'jaro_winkler_threshold': cfg.jaro_winkler_threshold,
                        'metaphone_required': cfg.metaphone_required
                    }
                    
                    cached_result = self._get_cached_comparison(normalized_item1, normalized_item2, **cache_key_params)
                    if cached_result is not None:
                        is_match, metrics = cached_result
                    else:
                        is_match, metrics = self._are_words_equivalent(
                            normalized_item1, normalized_item2,
                            levenshtein_threshold=threshold,
                            jaro_winkler_threshold=cfg.jaro_winkler_threshold,
                            metaphone_required=cfg.metaphone_required
                        )
                        self._cache_comparison(normalized_item1, normalized_item2, (is_match, metrics), **cache_key_params)
                    
                    score = metrics.get('levenshtein_ratio', 0.0)
                    if score >= threshold:
                        duplicates.append((item1, item2, score))
            
            return duplicates
        
        # For large lists, use parallel processing if requested
        duplicates = []
        
        # Generate all pairs
        pairs_to_compare = []
        pair_indices = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                normalized_item1 = self.normalize_text(items[i], for_names=False, case_mode="lower", config=cfg)
                normalized_item2 = self.normalize_text(items[j], for_names=False, case_mode="lower", config=cfg)
                pairs_to_compare.append((normalized_item1, normalized_item2))
                pair_indices.append((i, j))
        
        # Use batch_compare with optional parallelization
        results = self.batch_compare(
            pairs_to_compare,
            config=cfg,
            parallel=parallel,
            max_workers=max_workers,
            levenshtein_threshold=threshold
        )
        
        # Filter and format results (return original items, not normalized)
        for (idx1, idx2), (is_match, metrics) in zip(pair_indices, results):
            score = metrics.get('levenshtein_ratio', 0.0)
            if score >= threshold:
                duplicates.append((items[idx1], items[idx2], score))
        
        # Sort by score (descending)
        duplicates.sort(key=lambda x: x[2], reverse=True)
        
        return duplicates

    def compare_lists(
        self,
        target: str,
        candidates: List[str],
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        config: Optional[MatcherConfig] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Compare target string against multiple candidates and return top K matches.
        
        Description:
            This method extends find_best_match by returning multiple candidates
            ranked by similarity score. Useful for fuzzy search, autocomplete,
            and providing users with multiple matching options.
            
            Returns candidates sorted by score in descending order, optionally
            limited to top K results and filtered by threshold.
        
        Args:
            target (str): The string to match against
            candidates (List[str]): List of candidate strings to compare
            top_k (Optional[int]): Maximum number of results to return.
                                  If None, returns all matches above threshold.
                                  Default: None
            threshold (Optional[float]): Minimum similarity threshold (0.0-1.0).
                                        If None, uses config threshold.
                                        Default: None
            config (Optional[MatcherConfig]): Configuration for comparison.
                                             If None, uses instance config.
                                             Default: None
        
        Returns:
            List[Tuple[str, float, Dict[str, Any]]]: List of tuples containing:
                - str: The candidate string
                - float: The similarity score (0.0-1.0)
                - Dict: Detailed metrics for the match
                
            Results are sorted by score (highest first) and limited to top_k if specified.
        
        Raises:
            TypeError: If target is not a string or candidates is not a list
            ValueError: If threshold is outside valid range or top_k is negative
        
        Example Usage:
            matcher = TextMatcher()
            
            # Get top 3 matches
            candidates = ["Smith", "Smyth", "Jones", "Johnson", "Smithson"]
            results = matcher.compare_lists("Smithe", candidates, top_k=3)
            for candidate, score, metrics in results:
                print(f"{candidate}: {score:.4f}")
            # Output:
            # Smith: 0.9167
            # Smyth: 0.8333
            # Smithson: 0.7500
            
            # Get all matches above 0.7
            results = matcher.compare_lists("Smithe", candidates, threshold=0.70)
            
            # With debug mode
            config = MatcherConfig(debug_mode=True)
            results = matcher.compare_lists("test", ["test1", "test2"], config=config)
            for candidate, score, metrics in results:
                if 'debug_info' in metrics:
                    print(f"{candidate}: {metrics['debug_info']['summary']}")
        
        Cost:
            O(n*m*k) where n is number of candidates, m is average string length,
            and k is the sorting cost (n log n for all results, n log k for top_k)
        """
        if not isinstance(target, str):
            raise TypeError("Target must be a string.")
        if not isinstance(candidates, list):
            raise TypeError("Candidates must be a list.")
        if top_k is not None and (not isinstance(top_k, int) or top_k < 1):
            raise ValueError("top_k must be a positive integer.")
        
        cfg = config if config is not None else self.config
        thresh = threshold if threshold is not None else cfg.levenshtein_threshold
        
        if not (0.0 <= thresh <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        if not candidates:
            return []
        
        # Validación tautológica: check for exact matches first
        exact_matches = []
        for candidate in candidates:
            if target == candidate:
                exact_matches.append((candidate, 1.0, {
                    'exact_match': True,
                    'levenshtein_ratio': 1.0,
                    'jaro_winkler_score': 100.0,
                    'metaphone_match': True
                }))
        
        # If we have exact matches and top_k=1, return immediately
        if exact_matches and top_k == 1:
            return exact_matches[:1]
        
        # Apply text normalization to target
        normalized_target = self.normalize_text(target, for_names=False, case_mode="lower", config=cfg)
        
        results = []
        
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            
            # Apply text normalization to candidate
            normalized_candidate = self.normalize_text(candidate, for_names=False, case_mode="lower", config=cfg)
            
            # Caso trivial: candidato idéntico al target después de normalización
            if normalized_target == normalized_candidate:
                results.append((candidate, 1.0, {
                    'exact_match': True,
                    'levenshtein_ratio': 1.0,
                    'jaro_winkler_score': 100.0,
                    'metaphone_match': True
                }))
                continue
            
            is_match, metrics = self._are_words_equivalent(
                normalized_target,
                normalized_candidate,
                levenshtein_threshold=thresh,
                jaro_winkler_threshold=cfg.jaro_winkler_threshold,
                metaphone_required=cfg.metaphone_required
            )
            
            # Add debug info if enabled
            if cfg.debug_mode:
                metrics = self._add_debug_info(metrics, target, candidate, is_match, cfg)
            
            # Use Levenshtein ratio as primary score
            score = metrics.get('levenshtein_ratio', 0.0)
            
            # Only include if meets threshold
            if score >= thresh:
                results.append((candidate, score, metrics))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top_k if specified
        if top_k is not None:
            results = results[:top_k]
        
        return results

    
    def batch_compare(
        self,
        pairs: List[Tuple[str, str]],
        config: Optional[MatcherConfig] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        **kwargs
    ) -> List[Tuple[bool, Dict[str, Any]]]:
        """
        Performs batch comparison of multiple word pairs with optional parallelization.
        
        Description:
            Efficiently compares multiple pairs of words in a single operation.
            This is useful for bulk processing scenarios like deduplication,
            record linkage, or batch validation tasks.
            
            Can use MatcherConfig for consistent settings or pass individual
            parameters via kwargs (which override config settings).
            
            **Performance Features**:
            - Automatic caching of results (if enabled)
            - Optional parallel processing for large batches
            - Chunking support for memory efficiency
        
        Args:
            pairs (List[Tuple[str, str]]): List of (word1, word2) tuples to compare
            config (Optional[MatcherConfig]): Configuration for comparison.
                                             If None, uses instance config.
                                             Default: None
            parallel (bool): Enable parallel processing. Default: False
                            Recommended for >1000 pairs
            max_workers (Optional[int]): Number of parallel workers.
                                        If None, uses CPU count.
                                        Default: None
            **kwargs: Additional arguments passed to are_words_equivalent
                     (levenshtein_threshold, jaro_winkler_threshold, metaphone_required)
                     These override config settings if provided.
        
        Returns:
            List[Tuple[bool, Dict[str, Any]]]: List of (is_match, metrics) tuples,
                                                one for each input pair
        
        Raises:
            TypeError: If pairs is not a list or contains invalid tuple formats
        
        Example Usage:
            matcher = TextMatcher()
            
            pairs = [
                ("Smith", "Smyth"),
                ("casa", "caza"),
                ("python", "pithon")
            ]
            
            results = matcher.batch_compare(pairs)
            # Returns: [
            #   (True, {'metaphone_match': True, ...}),
            #   (True, {'metaphone_match': False, ...}),
            #   (True, {'metaphone_match': True, ...})
            # ]
            
            # With custom thresholds
            results = matcher.batch_compare(
                pairs,
                levenshtein_threshold=0.90,
                metaphone_required=False
            )
        
        Cost:
            O(k*n*m) where k is the number of pairs, n and m are average word lengths
        """
        if not isinstance(pairs, list):
            raise TypeError("Pairs must be a list of tuples.")
        
        cfg = config if config is not None else self.config
        
        # Merge config with kwargs (kwargs take precedence)
        compare_params = {
            'levenshtein_threshold': kwargs.get('levenshtein_threshold', cfg.levenshtein_threshold),
            'jaro_winkler_threshold': kwargs.get('jaro_winkler_threshold', cfg.jaro_winkler_threshold),
            'metaphone_required': kwargs.get('metaphone_required', cfg.metaphone_required)
        }
        
        # Sequential processing
        if not parallel or len(pairs) < 100:  # Use parallel only for larger batches
            results = []
            
            for pair in pairs:
                if not isinstance(pair, tuple) or len(pair) != 2:
                    raise TypeError("Each pair must be a tuple of two strings.")
                
                word1, word2 = pair
                
                # Validación tautológica
                if word1 == word2:
                    results.append((True, {
                        'exact_match': True,
                        'levenshtein_ratio': 1.0,
                        'jaro_winkler_score': 100.0,
                        'metaphone_match': True
                    }))
                    continue
                
                # Apply text normalization to both words
                normalized_word1 = self.normalize_text(word1, for_names=False, case_mode="lower", config=cfg)
                normalized_word2 = self.normalize_text(word2, for_names=False, case_mode="lower", config=cfg)
                
                # Caso trivial: palabras idénticas después de normalización
                if normalized_word1 == normalized_word2:
                    results.append((True, {
                        'exact_match': True,
                        'levenshtein_ratio': 1.0,
                        'jaro_winkler_score': 100.0,
                        'metaphone_match': True
                    }))
                    continue
                
                # Check cache first
                cached_result = self._get_cached_comparison(normalized_word1, normalized_word2, **compare_params)
                if cached_result is not None:
                    is_match, metrics = cached_result
                else:
                    is_match, metrics = self._are_words_equivalent(normalized_word1, normalized_word2, **compare_params)
                    self._cache_comparison(normalized_word1, normalized_word2, (is_match, metrics), **compare_params)
                
                # Add debug info if enabled
                if cfg.debug_mode:
                    debug_config = MatcherConfig(
                        levenshtein_threshold=compare_params['levenshtein_threshold'],
                        jaro_winkler_threshold=compare_params['jaro_winkler_threshold'],
                        metaphone_required=compare_params['metaphone_required'],
                        debug_mode=True
                    )
                    metrics = self._add_debug_info(metrics, word1, word2, is_match, debug_config)
                
                results.append((is_match, metrics))
            
            return results
        
        # Parallel processing for large batches
        workers = max_workers if max_workers is not None else mp.cpu_count()
        results = [None] * len(pairs)  # Pre-allocate results list
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(self._compare_pair_worker, pair, compare_params): idx
                for idx, pair in enumerate(pairs)
                if isinstance(pair, tuple) and len(pair) == 2
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    is_match, metrics = future.result()
                    
                    # Add debug info if enabled
                    if cfg.debug_mode:
                        word1, word2 = pairs[idx]
                        debug_config = MatcherConfig(
                            levenshtein_threshold=compare_params['levenshtein_threshold'],
                            jaro_winkler_threshold=compare_params['jaro_winkler_threshold'],
                            metaphone_required=compare_params['metaphone_required'],
                            debug_mode=True
                        )
                        metrics = self._add_debug_info(metrics, word1, word2, is_match, debug_config)
                    
                    results[idx] = (is_match, metrics)
                except Exception as e:
                    # Handle errors gracefully
                    results[idx] = (False, {'error': str(e)})
        
        return results

    def _get_cache_key(self, word1: str, word2: str, **kwargs) -> str:
        """
        Generate cache key for comparison results.
        
        Args:
            word1 (str): First word
            word2 (str): Second word
            **kwargs: Comparison parameters
            
        Returns:
            str: Cache key
        """
        # Normalize words (order-independent key)
        w1, w2 = sorted([word1.lower().strip(), word2.lower().strip()])
        
        # Include relevant parameters in key
        params = tuple(sorted(kwargs.items()))
        return f"{w1}|{w2}|{params}"
    
    def _get_cached_comparison(
        self,
        word1: str,
        word2: str,
        **kwargs
    ) -> Optional[Tuple[bool, Dict[str, Any]]]:
        """
        Retrieve cached comparison result if available.
        
        Args:
            word1 (str): First word
            word2 (str): Second word
            **kwargs: Comparison parameters
            
        Returns:
            Optional[Tuple[bool, Dict[str, Any]]]: Cached result or None
        """
        if not self._enable_cache:
            return None
        
        cache_key = self._get_cache_key(word1, word2, **kwargs)
        
        if cache_key in self._comparison_cache:
            self._cache_hits += 1
            return self._comparison_cache[cache_key]
        
        self._cache_misses += 1
        return None
    
    def _cache_comparison(
        self,
        word1: str,
        word2: str,
        result: Tuple[bool, Dict[str, Any]],
        **kwargs
    ):
        """
        Cache comparison result.
        
        Args:
            word1 (str): First word
            word2 (str): Second word
            result: Comparison result to cache
            **kwargs: Comparison parameters
        """
        if not self._enable_cache:
            return
        
        # Implement simple LRU by removing oldest entries when full
        if len(self._comparison_cache) >= self._cache_size:
            # Remove first 10% of entries (oldest)
            remove_count = max(1, self._cache_size // 10)
            keys_to_remove = list(self._comparison_cache.keys())[:remove_count]
            for key in keys_to_remove:
                del self._comparison_cache[key]
        
        cache_key = self._get_cache_key(word1, word2, **kwargs)
        self._comparison_cache[cache_key] = result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics including hits, misses, and hit rate
            
        Example:
            stats = matcher.get_cache_stats()
            print(f"Cache hit rate: {stats['hit_rate']:.2%}")
            print(f"Cache size: {stats['size']}")
        """
        if not self._enable_cache:
            return {
                'enabled': False,
                'size': 0,
                'hits': 0,
                'misses': 0,
                'hit_rate': 0.0
            }
        
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'enabled': True,
            'size': len(self._comparison_cache),
            'max_size': self._cache_size,
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate
        }
    
    def clear_cache(self):
        """
        Clear the comparison cache and reset statistics.
        
        Example:
            matcher.clear_cache()
        """
        if self._enable_cache:
            self._comparison_cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0
        
    def _compare_pair_worker(
        self,
        pair: Tuple[str, str],
        compare_params: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Worker function for parallel comparison.
        
        Args:
            pair: Tuple of (word1, word2)
            compare_params: Parameters for comparison
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Comparison result
        """
        word1, word2 = pair
        
        # Apply text normalization
        normalized_word1 = self.normalize_text(word1, for_names=False, case_mode="lower", config=self.config)
        normalized_word2 = self.normalize_text(word2, for_names=False, case_mode="lower", config=self.config)
        
        # Caso trivial: palabras idénticas después de normalización
        if normalized_word1 == normalized_word2:
            return True, {
                'exact_match': True,
                'levenshtein_ratio': 1.0,
                'jaro_winkler_score': 100.0,
                'metaphone_match': True
            }
        
        return self._are_words_equivalent(normalized_word1, normalized_word2, **compare_params)

    def _add_debug_info(
        self,
        metrics: Dict[str, Any],
        word1: str,
        word2: str,
        is_match: bool,
        config: Optional[MatcherConfig] = None
    ) -> Dict[str, Any]:
        """
        Add debug information to metrics dictionary.
        
        Description:
            Enhances the metrics dictionary with human-readable explanations
            of why a match succeeded or failed. This is activated when
            debug_mode is enabled in the configuration.
        
        Args:
            metrics (Dict[str, Any]): Original metrics dictionary
            word1 (str): First word compared
            word2 (str): Second word compared
            is_match (bool): Whether the comparison resulted in a match
            config (Optional[MatcherConfig]): Configuration used for comparison
            
        Returns:
            Dict[str, Any]: Enhanced metrics with debug information
            
        Example:
            Enhanced metrics include:
            {
                'match': True,
                'levenshtein_ratio': 0.92,
                'jaro_winkler_score': 93.5,
                'metaphone_match': True,
                'debug_info': {
                    'match_decision': 'MATCH',
                    'reasons': [
                        'Metaphone Pass (Sound alike)',
                        'Levenshtein Pass (0.92 >= 0.85)',
                        'Jaro-Winkler Pass (93.5 >= 0.9)'
                    ],
                    'config_used': {
                        'levenshtein_threshold': 0.85,
                        'jaro_winkler_threshold': 0.9,
                        'metaphone_required': True
                    }
                }
            }
        """
        cfg = config if config is not None else self.config
        
        if not cfg.debug_mode:
            return metrics
        
        # Build debug information
        debug_info = {
            'match_decision': 'MATCH' if is_match else 'NO_MATCH',
            'compared_words': f"'{word1}' vs '{word2}'",
            'reasons': [],
            'config_used': {
                'levenshtein_threshold': cfg.levenshtein_threshold,
                'jaro_winkler_threshold': cfg.jaro_winkler_threshold,
                'metaphone_required': cfg.metaphone_required
            }
        }
        
        # Analyze each metric
        metaphone_match = metrics.get('metaphone_match', False)
        lev_ratio = metrics.get('levenshtein_ratio', 0.0)
        jaro_score = metrics.get('jaro_winkler_score', 0.0)
        
        # Metaphone analysis
        if cfg.metaphone_required:
            if metaphone_match:
                debug_info['reasons'].append(
                    '✓ Metaphone Pass (Phonetically similar)'
                )
            else:
                debug_info['reasons'].append(
                    '✗ Metaphone Fail (Different phonetic sounds)'
                )
        else:
            debug_info['reasons'].append(
                '○ Metaphone Not Required'
            )
        
        # Levenshtein analysis
        if lev_ratio >= cfg.levenshtein_threshold:
            debug_info['reasons'].append(
                f'✓ Levenshtein Pass ({lev_ratio:.4f} >= {cfg.levenshtein_threshold})'
            )
        else:
            debug_info['reasons'].append(
                f'✗ Levenshtein Fail ({lev_ratio:.4f} < {cfg.levenshtein_threshold})'
            )
        
        # Jaro-Winkler analysis (convert from 0-100 scale to 0-1 scale)
        jaro_score_normalized = jaro_score / 100.0
        if jaro_score_normalized >= cfg.jaro_winkler_threshold:
            debug_info['reasons'].append(
                f'✓ Jaro-Winkler Pass ({jaro_score_normalized:.4f} >= {cfg.jaro_winkler_threshold})'
            )
        else:
            debug_info['reasons'].append(
                f'✗ Jaro-Winkler Fail ({jaro_score_normalized:.4f} < {cfg.jaro_winkler_threshold})'
            )
        
        # Add final decision explanation
        if is_match:
            debug_info['summary'] = 'All required criteria met for match'
        else:
            failed_criteria = [r for r in debug_info['reasons'] if r.startswith('✗')]
            debug_info['summary'] = f'Match failed: {len(failed_criteria)} criteria not met'
        
        metrics['debug_info'] = debug_info
        return metrics
    

    def run_difflib_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive tests for difflib.SequenceMatcher functionality.
        
        Description:
            This method executes all the test scenarios from test_difflib_comparison.py
            directly within the TextMatcher class. It provides a convenient way to
            validate the difflib functionality and demonstrate its capabilities.
            
            Tests include:
            - Text comparison with unified diff
            - Python code comparison
            - JavaScript code comparison
            - Code duplication detection
            - Version control simulation
            - Simple similarity checks
        
        Args:
            verbose (bool): Whether to print detailed test output. Default: True
            
        Returns:
            Dict[str, Any]: Test results summary with:
                - 'total_tests': Number of tests executed
                - 'passed_tests': Number of tests that passed
                - 'failed_tests': Number of tests that failed
                - 'test_results': Detailed results for each test
                - 'execution_time': Time taken to run all tests
        
        Raises:
            None
        
        Example Usage:
            matcher = TextMatcher()
            results = matcher.run_difflib_tests(verbose=True)
            print(f"Tests passed: {results['passed_tests']}/{results['total_tests']}")
        
        Cost:
            O(n) where n is the size of test data (typically small)
        """
        import time
        start_time = time.time()
        
        test_results = {}
        passed_tests = 0
        total_tests = 0
        
        def print_separator(title=""):
            """Print a formatted separator"""
            if verbose:
                if title:
                    print(f"\n{'='*80}")
                    print(f"  {title}")
                    print(f"{'='*80}\n")
                else:
                    print(f"{'='*80}\n")
        
        def run_test(test_name: str, test_func) -> bool:
            """Run a single test and return success status"""
            nonlocal passed_tests, total_tests
            total_tests += 1
            
            try:
                if verbose:
                    print(f"\n▶️  Running {test_name}...")
                test_func()
                test_results[test_name] = {'status': 'PASSED', 'error': None}
                passed_tests += 1
                if verbose:
                    print(f"✅ {test_name} PASSED")
                return True
            except Exception as e:
                test_results[test_name] = {'status': 'FAILED', 'error': str(e)}
                if verbose:
                    print(f"❌ {test_name} FAILED: {e}")
                return False
        
        # Test 1: Text Comparison with Unified Diff
        def test_text_comparison():
            text1 = """The quick brown fox jumps over the lazy dog.
A journey of a thousand miles begins with a single step.
To be or not to be, that is the question."""

            text2 = """The fast brown fox runs over the sleepy dog.
A journey of a thousand kilometers begins with a single step.
To be or not to be, that remains the question."""
            
            result = self.compare_text_detailed(
                text1, text2,
                case_sensitive=False,
                show_diff=True,
                context_lines=2
            )
            
            # Validate results
            assert result['score'] > 80, f"Expected similarity > 80%, got {result['score']}%"
            assert result['lines_changed'] > 0, "Expected some lines to be changed"
            assert 'diff' in result and result['diff'], "Expected diff output"
            assert len(result['opcodes']) > 0, "Expected opcodes"
        
        # Test 2: Python Code Comparison
        def test_code_comparison_python():
            code1 = """def calculate_sum(numbers):
    # Calculate the sum of a list
    total = 0
    for num in numbers:
        total += num
    return total

def calculate_average(numbers):
    return calculate_sum(numbers) / len(numbers)"""

            code2 = """def calculate_sum(numbers):
    # Calculate total
    total = 0
    for num in numbers:
        total = total + num  # Addition
    return total

def calculate_mean(numbers):
    return calculate_sum(numbers) / len(numbers)"""
            
            # Compare without ignoring comments
            result1 = self.compare_code_blocks(
                code1, code2,
                language='python',
                ignore_comments=False,
                ignore_whitespace=True
            )
            
            # Compare ignoring comments
            result2 = self.compare_code_blocks(
                code1, code2,
                language='python',
                ignore_comments=True,
                ignore_whitespace=True
            )
            
            # Validate results
            assert result1['structural_similarity'] > 70, f"Expected structural similarity > 70%, got {result1['structural_similarity']}%"
            assert result2['structural_similarity'] > result1['structural_similarity'], "Expected higher similarity when ignoring comments"
            assert 'code1_normalized' in result2, "Expected normalized code"
            assert 'code2_normalized' in result2, "Expected normalized code"
        
        # Test 3: JavaScript Code Comparison
        def test_code_comparison_javascript():
            code1 = """function fetchData(url) {
    // Fetch data from API
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Data received');
            return data;
        });
}"""

            code2 = """function fetchData(url) {
    /* Fetch data from API endpoint */
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Data loaded');  // Log message
            return data;
        });
}"""
            
            result = self.compare_code_blocks(
                code1, code2,
                language='javascript',
                ignore_comments=True,
                ignore_whitespace=True
            )
            
            # Validate results
            assert result['structural_similarity'] > 90, f"Expected high structural similarity, got {result['structural_similarity']}%"
            assert result['lines_changed'] <= 2, f"Expected few line changes, got {result['lines_changed']}"
            assert 'code1_normalized' in result, "Expected normalized code"
            assert 'code2_normalized' in result, "Expected normalized code"
        
        # Test 4: Code Duplication Detection
        def test_code_duplication_detection():
            # Test case 1: Identical logic, different formatting
            snippet1 = "for i in range(10): print(i)"
            snippet2 = """for i in range(10):
    print(i)"""
            
            result = self.compare_code_blocks(
                snippet1, snippet2,
                language='python',
                ignore_whitespace=True
            )
            
            assert result['structural_similarity'] > 90, f"Expected high similarity for formatting differences, got {result['structural_similarity']}%"
            
            # Test case 2: Similar but not identical
            code_a = """def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result"""
            
            code_b = """def transform_list(elements):
    output = []
    for element in elements:
        if element > 0:
            output.append(element * 3)
    return output"""
            
            result2 = self.compare_code_blocks(code_a, code_b, language='python')
            
            assert 60 < result2['structural_similarity'] < 90, f"Expected moderate similarity, got {result2['structural_similarity']}%"
            assert len(result2['matching_blocks']) > 0, "Expected some matching blocks"
        
        # Test 5: Version Control Scenario
        def test_version_control_scenario():
            version_old = """class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def get_info(self):
        return f"{self.name} ({self.email})"
    
    def validate_email(self):
        return '@' in self.email"""

            version_new = """class User:
    def __init__(self, name, email, age=None):
        self.name = name
        self.email = email
        self.age = age
    
    def get_info(self):
        info = f"{self.name} ({self.email})"
        if self.age:
            info += f" - Age: {self.age}"
        return info
    
    def validate_email(self):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, self.email) is not None"""
            
            result = self.compare_text_detailed(
                version_old, version_new,
                case_sensitive=True,
                show_diff=True,
                context_lines=3
            )
            
            # Validate results
            assert result['score'] > 60, f"Expected reasonable similarity, got {result['score']}%"
            assert result['lines_added'] > 0, "Expected some lines added"
            assert result['lines_changed'] > 0, "Expected some lines changed"
            assert 'diff' in result and result['diff'], "Expected diff output"
        
        # Test 6: Simple Similarity Checks
        def test_simple_similarity_check():
            test_cases = [
                ("Hello World", "Hello Universe", 60),  # Different words
                ("Python programming", "Python programming", 100),  # Exact match
                ("The cat sat on the mat", "The dog sat on the mat", 85),  # One word different
                ("abc123", "ABC123", 100),  # Case difference (case_sensitive=False)
            ]
            
            for text1, text2, expected_min_score in test_cases:
                result = self.compare_text_detailed(
                    text1, text2,
                    case_sensitive=False,
                    show_diff=False
                )
                
                assert result['score'] >= expected_min_score, f"Expected score >= {expected_min_score}%, got {result['score']}% for '{text1}' vs '{text2}'"
        
        # Run all tests
        if verbose:
            print_separator("DIFFLIB SEQUENCEMATCHER - TEXT & CODE COMPARISON TESTS")
        
        run_test("Text Comparison with Unified Diff", test_text_comparison)
        run_test("Python Code Comparison", test_code_comparison_python)
        run_test("JavaScript Code Comparison", test_code_comparison_javascript)
        run_test("Code Duplication Detection", test_code_duplication_detection)
        run_test("Version Control Scenario", test_version_control_scenario)
        run_test("Simple Similarity Checks", test_simple_similarity_check)
        
        execution_time = time.time() - start_time
        
        if verbose:
            print_separator("ALL TESTS COMPLETED!")
            print(f"Results: {passed_tests}/{total_tests} tests passed")
            print(f"Execution time: {execution_time:.2f} seconds")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'test_results': test_results,
            'execution_time': execution_time
        }
    
    def demo_difflib_features(self, interactive: bool = False) -> None:
        """
        Interactive demonstration of difflib.SequenceMatcher features.
        
        Description:
            This method provides an interactive demonstration of all difflib
            functionality, showing real examples and use cases. It's designed
            for learning and validation purposes.
            
            Features demonstrated:
            - Text comparison with unified diff
            - Code comparison across languages
            - Code duplication detection
            - Version control simulation
            - Similarity analysis
        
        Args:
            interactive (bool): Whether to run in interactive mode (wait for user input).
                               Default: False (runs all demos sequentially)
        
        Returns:
            None
        
        Raises:
            None
        
        Example Usage:
            matcher = TextMatcher()
            matcher.demo_difflib_features(interactive=True)  # Interactive mode
            # or
            matcher.demo_difflib_features()  # Run all demos
        """
        def print_separator(title=""):
            """Print a formatted separator"""
            if title:
                print(f"\n{'='*80}")
                print(f"  {title}")
                print(f"{'='*80}\n")
            else:
                print(f"{'='*80}\n")
        
        def wait_if_interactive():
            """Wait for user input if in interactive mode"""
            if interactive:
                input("\nPress Enter to continue...")
        
        print_separator("DIFFLIB SEQUENCEMATCHER - FEATURE DEMONSTRATION")
        
        # Demo 1: Text Comparison
        print_separator("DEMO 1: Text Comparison with Unified Diff")
        
        text1 = """The quick brown fox jumps over the lazy dog.
A journey of a thousand miles begins with a single step.
To be or not to be, that is the question."""

        text2 = """The fast brown fox runs over the sleepy dog.
A journey of a thousand kilometers begins with a single step.
To be or not to be, that remains the question."""
        
        print("ORIGINAL TEXT:")
        print(text1)
        print("\nMODIFIED TEXT:")
        print(text2)
        print()
        
        result = self.compare_text_detailed(
            text1, text2,
            case_sensitive=False,
            show_diff=True,
            context_lines=2
        )
        
        print(f"📊 Similarity: {result['score']:.2f}%")
        print(f"📝 Lines Added: {result['lines_added']}")
        print(f"📝 Lines Removed: {result['lines_removed']}")
        print(f"📝 Lines Changed: {result['lines_changed']}")
        print(f"📦 Matching Blocks: {len(result['matching_blocks'])}")
        
        print("\n--- UNIFIED DIFF ---")
        print(result['diff'])
        
        print("\n--- DETAILED CHANGES ---")
        for op_info in result['opcodes']:
            if op_info['operation'] != 'equal':
                print(f"\n{op_info['operation'].upper()}:")
                if op_info['text1_content']:
                    print(f"  Original: '{op_info['text1_content']}'")
                if op_info['text2_content']:
                    print(f"  Modified: '{op_info['text2_content']}'")
        
        wait_if_interactive()
        
        # Demo 2: Python Code Comparison
        print_separator("DEMO 2: Python Code Comparison")
        
        code1 = """def calculate_sum(numbers):
    # Calculate the sum of a list
    total = 0
    for num in numbers:
        total += num
    return total

def calculate_average(numbers):
    return calculate_sum(numbers) / len(numbers)"""

        code2 = """def calculate_sum(numbers):
    # Calculate total
    total = 0
    for num in numbers:
        total = total + num  # Addition
    return total

def calculate_mean(numbers):
    return calculate_sum(numbers) / len(numbers)"""
        
        print("VERSION 1:")
        print(code1)
        print("\nVERSION 2:")
        print(code2)
        print()
        
        # Compare without ignoring comments
        result1 = self.compare_code_blocks(
            code1, code2,
            language='python',
            ignore_comments=False,
            ignore_whitespace=True
        )
        
        # Compare ignoring comments
        result2 = self.compare_code_blocks(
            code1, code2,
            language='python',
            ignore_comments=True,
            ignore_whitespace=True
        )
        
        print(f"🔍 Original Similarity: {result1['original_similarity']:.2f}%")
        print(f"🔍 Structural Similarity (with comments): {result1['structural_similarity']:.2f}%")
        print(f"🔍 Structural Similarity (without comments): {result2['structural_similarity']:.2f}%")
        
        print("\n--- DIFF (with comments) ---")
        print(result1['diff'])
        
        wait_if_interactive()
        
        # Demo 3: Code Duplication Detection
        print_separator("DEMO 3: Code Duplication Detection")
        
        # Test case 1: Identical logic, different formatting
        snippet1 = "for i in range(10): print(i)"
        snippet2 = """for i in range(10):
    print(i)"""
        
        print(f"Snippet 1: {snippet1}")
        print(f"Snippet 2:\n{snippet2}")
        print()
        
        result = self.compare_code_blocks(
            snippet1, snippet2,
            language='python',
            ignore_whitespace=True
        )
        
        print(f"🔍 Structural Similarity: {result['structural_similarity']:.2f}%")
        
        if result['structural_similarity'] > 90:
            print("⚠️  HIGH SIMILARITY - Potential code duplication detected!")
        
        # Test case 2: Similar but not identical
        code_a = """def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result"""
        
        code_b = """def transform_list(elements):
    output = []
    for element in elements:
        if element > 0:
            output.append(element * 3)
    return output"""
        
        print("\n\nCODE BLOCK A:")
        print(code_a)
        print("\nCODE BLOCK B:")
        print(code_b)
        print()
        
        result2 = self.compare_code_blocks(code_a, code_b, language='python')
        
        print(f"🔍 Structural Similarity: {result2['structural_similarity']:.2f}%")
        print(f"📦 Matching Blocks: {len(result2['matching_blocks'])}")
        
        if result2['structural_similarity'] > 70:
            print("⚠️  MODERATE SIMILARITY - Review for potential duplication")
        
        wait_if_interactive()
        
        # Demo 4: Version Control Simulation
        print_separator("DEMO 4: Version Control Diff Simulation")
        
        version_old = """class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def get_info(self):
        return f"{self.name} ({self.email})"
    
    def validate_email(self):
        return '@' in self.email"""

        version_new = """class User:
    def __init__(self, name, email, age=None):
        self.name = name
        self.email = email
        self.age = age
    
    def get_info(self):
        info = f"{self.name} ({self.email})"
        if self.age:
            info += f" - Age: {self.age}"
        return info
    
    def validate_email(self):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, self.email) is not None"""
        
        print("OLD VERSION (commit abc123):")
        print(version_old)
        print("\nNEW VERSION (commit def456):")
        print(version_new)
        print()
        
        result = self.compare_text_detailed(
            version_old, version_new,
            case_sensitive=True,
            show_diff=True,
            context_lines=3
        )
        
        print(f"🔍 Code Similarity: {result['score']:.2f}%")
        print(f"📝 Lines Added: {result['lines_added']}")
        print(f"📝 Lines Removed: {result['lines_removed']}")
        print(f"📝 Lines Changed: {result['lines_changed']}")
        
        print("\n--- GIT-STYLE DIFF ---")
        print(result['diff'])
        
        wait_if_interactive()
        
        # Demo 5: Simple Similarity Analysis
        print_separator("DEMO 5: Simple Similarity Analysis")
        
        test_cases = [
            ("Hello World", "Hello Universe", "Different words"),
            ("Python programming", "Python programming", "Exact match"),
            ("The cat sat on the mat", "The dog sat on the mat", "One word different"),
            ("abc123", "ABC123", "Case difference"),
        ]
        
        for text1, text2, description in test_cases:
            result = self.compare_text_detailed(
                text1, text2,
                case_sensitive=False,
                show_diff=False
            )
            
            print(f"\n{description}")
            print(f"  Text 1: '{text1}'")
            print(f"  Text 2: '{text2}'")
            print(f"  Similarity: {result['score']:.2f}%")
            print(f"  Ratio: {result['ratio']:.4f}")
        
        print_separator("DEMONSTRATION COMPLETED!")
        print("All difflib.SequenceMatcher features have been demonstrated.")
        print("Use run_difflib_tests() to validate functionality.")


if __name__ == "__main__":
    print("=" * 70)
    print("TextMatcher Demo - Enhanced Features")
    print("=" * 70)
    
    # Example: Compare Tokens
    print("\n\n🔤 Example 0: Compare Tokens - Token-Based Validation with Difference Rules")
    print("-" * 70)
    print("This method validates token lists with specific rules:")
    print("- If < 4 tokens: difference in non-matching tokens must be 0 (all must match)")
    print("- If >= 4 tokens: difference in non-matching tokens can be at most 1")
    print()
    
    test_cases = [
        # Cases with < 4 tokens (must have 0 difference)
        ("Juan Perez", "Juan Perez", "Exact match (<4 tokens)"),
        ("Juan Perez", "Juan Garcia", "1 token difference (<4 tokens) - Should FAIL"),
        ("Ana Maria", "Ana Maria Lopez", "Different lengths (<4 tokens) - Should FAIL"),
        
        # Cases with >= 4 tokens (allow 1 difference)
        ("Juan Carlos Maria Perez", "Juan Carlos Maria Garcia", "1 token difference (>=4 tokens) - Should PASS"),
        ("Pedro Luis Antonio Ruiz", "Pedro Luis Antonio Ruiz Gomez", "1 token difference (>=4 tokens) - Should PASS"),
        ("Maria Jose Carmen Rodriguez", "Maria Jose Carmen Lopez", "1 token difference (>=4 tokens) - Should PASS"),
        ("Fernando Marcos Antonio Silva", "Fernando Marcos Antonio Silva Ruiz", "1 token difference (>=4 tokens) - Should PASS"),
        
        # Cases that should fail (>=4 tokens with >1 difference)
        ("Juan Carlos Maria Perez", "Juan Carlos Ana Garcia", "2 token differences (>=4 tokens) - Should FAIL"),
        ("Pedro Luis Antonio Ruiz", "Pedro Maria Jose Gomez", "3 token differences (>=4 tokens) - Should FAIL"),
        
        # Real-world examples
        ("EDUARDO RUBIO RIOJA SILVEIRINHA", "EDUARDO PRECIADO DIAZ RUBIO", "Complex name comparison"),
        ("MARIA DEL CARMEN LOPEZ GARCIA", "MARIA DEL CARMEN LOPEZ RODRIGUEZ", "Long name with 1 difference"),
    ]
    
    matcher = TextMatcher()
    for name1, name2, description in test_cases:
        is_match = matcher.compare_tokens(name1, name2)
        tokens1 = name1.split()
        tokens2 = name2.split()
        min_tokens = min(len(tokens1), len(tokens2))
        common = len(set(tokens1).intersection(set(tokens2)))
        difference = min_tokens - common
        
        print(f"\nTest: {description}")
        print(f"  '{name1}' ({len(tokens1)} tokens) vs '{name2}' ({len(tokens2)} tokens)")
        print(f"  Common tokens: {common}, Difference: {difference}, Min tokens: {min_tokens}")
        print(f"  Match: {is_match}")
        if min_tokens < 4:
            expected = difference == 0
        else:
            expected = difference <= 1
        status = "✓ PASS" if is_match == expected else "✗ FAIL"
        print(f"  Validation: {status}")
        

    # Example: Debug Mode
    print("\n\n🔍 Example 2: Debug Mode - Understanding Match Decisions")
    print("-" * 70)
    
    debug_config = MatcherConfig(debug_mode=True, levenshtein_threshold=0.85)
    matcher_debug = TextMatcher(config=debug_config)
    
    test_pairs = [
        ("Smith", "Smyth"),
        ("casa", "perro"),
        ("python", "pithon")
    ]
    
    for word1, word2 in test_pairs:
        _, _, are_words_equivalent, _ = _import_similarity()
        is_match, metrics = are_words_equivalent(word1, word2)
        print(f"\n'{word1}' vs '{word2}':")
        print(f"  Match: {is_match}")
        
        # Add debug info manually
        metrics = matcher_debug._add_debug_info(metrics, word1, word2, is_match)
        
        if 'debug_info' in metrics:
            debug = metrics['debug_info']
            print(f"  Decision: {debug['match_decision']}")
            print(f"  Reasons:")
            for reason in debug['reasons']:
                print(f"    {reason}")
            print(f"  Summary: {debug['summary']}")


    # Example: Basic Configuration
    print("\n\n📋 Example 1: Configuration Presets")
    print("-" * 70)
    
    print("\n1.1 Default Configuration:")
    default_config = MatcherConfig.default()
    print(f"  Levenshtein threshold: {default_config.levenshtein_threshold}")
    print(f"  Jaro-Winkler threshold: {default_config.jaro_winkler_threshold}")
    print(f"  Metaphone required: {default_config.metaphone_required}")
    
    print("\n1.2 Lenient Configuration:")
    lenient_config = MatcherConfig.lenient()
    print(f"  Levenshtein threshold: {lenient_config.levenshtein_threshold}")
    print(f"  Jaro-Winkler threshold: {lenient_config.jaro_winkler_threshold}")
    print(f"  Metaphone required: {lenient_config.metaphone_required}")
    
    print("\n1.3 Strict Configuration:")
    strict_config = MatcherConfig.strict()
    print(f"  Levenshtein threshold: {strict_config.levenshtein_threshold}")
    print(f"  Jaro-Winkler threshold: {strict_config.jaro_winkler_threshold}")
    print(f"  Metaphone required: {strict_config.metaphone_required}")
    
    
    # Example: Compare Lists (Top K)
    print("\n\n📊 Example 3: Compare Lists - Finding Top K Matches")
    print("-" * 70)
    
    matcher = TextMatcher()
    target = "Smithe"
    candidates = ["Smith", "Smyth", "Jones", "Johnson", "Smithson", "Smythe"]
    
    print(f"\nTarget: '{target}'")
    print(f"Candidates: {candidates}")
    
    print("\n3.1 Top 3 matches:")
    top3 = matcher.compare_lists(target, candidates, top_k=3)
    for i, (candidate, score, _) in enumerate(top3, 1):
        print(f"  {i}. {candidate}: {score:.4f}")
    
    print("\n3.2 All matches above 0.70:")
    all_matches = matcher.compare_lists(target, candidates, threshold=0.70)
    for candidate, score, _ in all_matches:
        print(f"  - {candidate}: {score:.4f}")
    
    print("\n3.3 Top 3 with debug info:")
    debug_matcher = TextMatcher(config=MatcherConfig(debug_mode=True))
    top3_debug = debug_matcher.compare_lists(target, candidates, top_k=3)
    for i, (candidate, score, metrics) in enumerate(top3_debug, 1):
        print(f"\n  {i}. {candidate} (score: {score:.4f})")
        if 'debug_info' in metrics:
            print(f"     Summary: {metrics['debug_info']['summary']}")
    
    # Example 4: Using Config with Methods
    print("\n\n⚙️ Example 4: Using Config with Different Methods")
    print("-" * 70)
    
    # Create matcher with lenient config
    lenient_matcher = TextMatcher(config=MatcherConfig.lenient())
    
    print("\n4.1 Name comparison with lenient config:")
    is_match, metrics = lenient_matcher.compare_names("José", "Jose")
    print(f"  'José' vs 'Jose': {is_match}")
    
    print("\n4.2 Batch comparison with debug config:")
    debug_config = MatcherConfig(debug_mode=True, levenshtein_threshold=0.80)
    debug_matcher = TextMatcher(config=debug_config)
    
    pairs = [
        ("aplicacion", "aplikacion"),
        ("telefono", "telefno")
    ]
    
    results = debug_matcher.batch_compare(pairs)
    for (word1, word2), (is_match, metrics) in zip(pairs, results):
        print(f"\n  '{word1}' vs '{word2}':")
        print(f"    Match: {is_match}")
        if 'debug_info' in metrics:
            print(f"    Summary: {metrics['debug_info']['summary']}")
    
    # Example 5: Practical Use Case - Fuzzy Search
    print("\n\n🔎 Example 5: Practical Use Case - Fuzzy Product Search")
    print("-" * 70)
    
    products = [
        "iPhone 15 Pro Max",
        "Samsung Galaxy S24 Ultra",
        "Google Pixel 8 Pro",
        "OnePlus 12 Pro",
        "Xiaomi 14 Ultra"
    ]
    
    search_query = "iphone 15 pro"
    
    print(f"\nSearch query: '{search_query}'")
    print("Available products:")
    for p in products:
        print(f"  - {p}")
    
    fuzzy_matcher = TextMatcher(config=MatcherConfig.fuzzy())
    results = fuzzy_matcher.compare_lists(search_query, products, top_k=3, threshold=0.50)
    
    print(f"\nTop 3 results:")
    for i, (product, score, _) in enumerate(results, 1):
        print(f"  {i}. {product} (relevance: {score:.2%})")
    
    # Example 6: difflib.SequenceMatcher Features
    print("\n\n📄 Example 6: difflib.SequenceMatcher - Text & Code Comparison")
    print("-" * 70)
    
    print("\n6.1 Running difflib tests...")
    test_results = matcher.run_difflib_tests(verbose=False)
    print(f"   Tests passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    print(f"   Execution time: {test_results['execution_time']:.2f} seconds")
    
    print("\n6.2 Quick text comparison demo:")
    text_result = matcher.compare_text_detailed(
        "The quick brown fox",
        "The fast brown fox",
        show_diff=False
    )
    print(f"   Similarity: {text_result['score']:.1f}%")
    print(f"   Lines changed: {text_result['lines_changed']}")
    
    print("\n6.3 Quick code comparison demo:")
    code_result = matcher.compare_code_blocks(
        "def hello(): print('hi')",
        "def hello(): print('hello')",
        language='python'
    )
    print(f"   Structural similarity: {code_result['structural_similarity']:.1f}%")
    
    print("\n6.4 For full interactive demo, run:")
    print("   matcher = TextMatcher()")
    print("   matcher.demo_difflib_features(interactive=True)")
    
    print("\n\n" + "=" * 70)
    print("End of Demo")
    print("=" * 70)
