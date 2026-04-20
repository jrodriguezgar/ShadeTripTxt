"""
Text Anonymizer - PII detection & data anonymization tool.

This module provides tools to detect Personally Identifiable Information (PII)
in text and tabular data, and anonymize it using various strategies.
Supports multiple locales (country/language) with locale-specific PII patterns.

TextAnonymizer acts as the central hub for all anonymization techniques,
wrapping both internal shadetriptxt modules and external libraries:

  Internal (shadetriptxt):
  - TextDummy:   locale-aware fake data generation for replace/pseudonymize
  - TextParser:  text normalization, extraction, masking (mask_text)

  External (lazy-loaded — only imported when needed):
  - spacy:  NLP-based Named Entity Recognition (NER)
  - nltk:   Tokenization and NER fallback
  - python-anonymity:  k-anonymity / l-diversity / t-closeness on DataFrames
  - pycanon:  Privacy metric measurement on DataFrames
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum

from shadetriptxt.utils._locale import BaseLocaleProfile
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)


# ═══════════════════════════════════════════════════════════════════════════
# PII entity types
# ═══════════════════════════════════════════════════════════════════════════


class PiiType(str, Enum):
    """Types of Personally Identifiable Information that can be detected."""

    NAME = "NAME"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    ID_DOCUMENT = "ID_DOCUMENT"
    CREDIT_CARD = "CREDIT_CARD"
    IBAN = "IBAN"
    IP_ADDRESS = "IP_ADDRESS"
    DATE = "DATE"
    URL = "URL"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    NUMBER = "NUMBER"
    CURRENCY = "CURRENCY"
    CUSTOM = "CUSTOM"


# ═══════════════════════════════════════════════════════════════════════════
# Anonymization strategies
# ═══════════════════════════════════════════════════════════════════════════


class Strategy(str, Enum):
    """How to replace detected PII."""

    MASK = "mask"  # J*** D**  /  ****@****.***
    REPLACE = "replace"  # Replace with realistic fake data
    HASH = "hash"  # SHA-256 (truncated)
    REDACT = "redact"  # [REDACTED] or [NAME]
    GENERALIZE = "generalize"  # 34 → 30-40  /  15/03/1990 → 1990
    PSEUDONYMIZE = "pseudonymize"  # Consistent: same input → same output
    SUPPRESS = "suppress"  # Remove completely (empty string)


# ═══════════════════════════════════════════════════════════════════════════
# Detection result dataclass
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class DetectedEntity:
    """A PII entity found in text."""

    text: str
    pii_type: PiiType
    start: int
    end: int
    confidence: float = 1.0
    source: str = "regex"  # "regex" | "spacy" | "nltk"


@dataclass
class AnonymizationResult:
    """Result of anonymizing a text."""

    original: str
    anonymized: str
    entities: List[DetectedEntity] = field(default_factory=list)
    replacements: Dict[str, str] = field(default_factory=dict)


@dataclass
class PrivacyReport:
    """Privacy metric report for tabular data (pycanon)."""

    k_anonymity: Optional[int] = None
    l_diversity: Optional[int] = None
    t_closeness: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Locale-aware regex patterns for PII detection
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AnonymizerLocaleProfile(BaseLocaleProfile):
    """Locale profile with PII detection patterns and settings."""

    spacy_model: str  # e.g. "es_core_news_sm"
    nltk_language: str  # e.g. "spanish"
    id_patterns: List[Tuple[str, str]] = field(default_factory=list)
    phone_pattern: str = ""
    postcode_pattern: str = ""


LOCALE_PROFILES: Dict[str, AnonymizerLocaleProfile] = {
    # --- Spanish ---
    "es_ES": AnonymizerLocaleProfile(
        code="es_ES",
        country="Spain",
        language="Spanish",
        spacy_model="es_core_news_sm",
        nltk_language="spanish",
        id_patterns=[
            ("DNI/NIF", r"\b\d{8}[A-Z]\b"),
            ("NIE", r"\b[XYZ]\d{7}[A-Z]\b"),
        ],
        phone_pattern=r"(?:\+34[\s.-]?)?\b[6-9]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b",
        postcode_pattern=r"\b(?:0[1-9]|[1-4]\d|5[0-2])\d{3}\b",
    ),
    "es_MX": AnonymizerLocaleProfile(
        code="es_MX",
        country="Mexico",
        language="Spanish",
        spacy_model="es_core_news_sm",
        nltk_language="spanish",
        id_patterns=[
            ("CURP", r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b"),
            ("RFC", r"\b[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}\b"),
        ],
        phone_pattern=r"(?:\+52[\s.-]?)?\b\d{2,3}[\s.-]?\d{3,4}[\s.-]?\d{4}\b",
        postcode_pattern=r"\b\d{5}\b",
    ),
    "es_AR": AnonymizerLocaleProfile(
        code="es_AR",
        country="Argentina",
        language="Spanish",
        spacy_model="es_core_news_sm",
        nltk_language="spanish",
        id_patterns=[
            ("DNI", r"\b\d{7,8}\b"),
            ("CUIL", r"\b(?:20|23|24|27)-?\d{7,8}-?\d\b"),
        ],
        phone_pattern=r"(?:\+54[\s.-]?)?\b(?:11|[2-9]\d)[\s.-]?\d{4}[\s.-]?\d{4}\b",
        postcode_pattern=r"\b[A-Z]\d{4}[A-Z]{3}\b",
    ),
    "es_CO": AnonymizerLocaleProfile(
        code="es_CO",
        country="Colombia",
        language="Spanish",
        spacy_model="es_core_news_sm",
        nltk_language="spanish",
        id_patterns=[
            ("Cédula", r"\b\d{6,10}\b"),
        ],
        phone_pattern=r"(?:\+57[\s.-]?)?\b3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b",
        postcode_pattern=r"\b\d{6}\b",
    ),
    "es_CL": AnonymizerLocaleProfile(
        code="es_CL",
        country="Chile",
        language="Spanish",
        spacy_model="es_core_news_sm",
        nltk_language="spanish",
        id_patterns=[
            ("RUT", r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[0-9Kk]\b"),
        ],
        phone_pattern=r"(?:\+56[\s.-]?)?\b9[\s.-]?\d{4}[\s.-]?\d{4}\b",
        postcode_pattern=r"\b\d{7}\b",
    ),
    # --- English ---
    "en_US": AnonymizerLocaleProfile(
        code="en_US",
        country="United States",
        language="English",
        spacy_model="en_core_web_sm",
        nltk_language="english",
        id_patterns=[
            ("SSN", r"\b\d{3}-\d{2}-\d{4}\b"),
            ("EIN", r"\b\d{2}-\d{7}\b"),
        ],
        phone_pattern=(r"(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
        postcode_pattern=r"\b\d{5}(?:-\d{4})?\b",
    ),
    "en_GB": AnonymizerLocaleProfile(
        code="en_GB",
        country="United Kingdom",
        language="English",
        spacy_model="en_core_web_sm",
        nltk_language="english",
        id_patterns=[
            ("NINO", r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b"),
        ],
        phone_pattern=(r"(?:\+44[\s.-]?)?\b0?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b"),
        postcode_pattern=r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b",
    ),
    # --- Portuguese ---
    "pt_BR": AnonymizerLocaleProfile(
        code="pt_BR",
        country="Brazil",
        language="Portuguese",
        spacy_model="pt_core_news_sm",
        nltk_language="portuguese",
        id_patterns=[
            ("CPF", r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
            ("CNPJ", r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
        ],
        phone_pattern=(r"(?:\+55[\s.-]?)?\(?\d{2}\)?[\s.-]?9?\d{4}[\s.-]?\d{4}\b"),
        postcode_pattern=r"\b\d{5}-?\d{3}\b",
    ),
    "pt_PT": AnonymizerLocaleProfile(
        code="pt_PT",
        country="Portugal",
        language="Portuguese",
        spacy_model="pt_core_news_sm",
        nltk_language="portuguese",
        id_patterns=[
            ("NIF", r"\b[1-9]\d{8}\b"),
        ],
        phone_pattern=(r"(?:\+351[\s.-]?)?\b[29]\d{1,2}[\s.-]?\d{3}[\s.-]?\d{3,4}\b"),
        postcode_pattern=r"\b\d{4}-\d{3}\b",
    ),
    # --- French ---
    "fr_FR": AnonymizerLocaleProfile(
        code="fr_FR",
        country="France",
        language="French",
        spacy_model="fr_core_news_sm",
        nltk_language="french",
        id_patterns=[
            ("NIR", r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b"),
        ],
        phone_pattern=(r"(?:\+33[\s.-]?)?\b0?[1-9][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b"),
        postcode_pattern=r"\b\d{5}\b",
    ),
    # --- German ---
    "de_DE": AnonymizerLocaleProfile(
        code="de_DE",
        country="Germany",
        language="German",
        spacy_model="de_core_news_sm",
        nltk_language="german",
        id_patterns=[
            ("Personalausweis", r"\b[A-Z0-9]{10}\b"),
        ],
        phone_pattern=(r"(?:\+49[\s.-]?)0?\d{2,5}[\s.-]?\d{4,8}\b"),
        postcode_pattern=r"\b\d{5}\b",
    ),
    # --- Italian ---
    "it_IT": AnonymizerLocaleProfile(
        code="it_IT",
        country="Italy",
        language="Italian",
        spacy_model="it_core_news_sm",
        nltk_language="italian",
        id_patterns=[
            ("Codice Fiscale", r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"),
        ],
        phone_pattern=(r"(?:\+39[\s.-]?)0?\d{2,4}[\s.-]?\d{4,8}\b"),
        postcode_pattern=r"\b\d{5}\b",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# Universal (locale-independent) regex patterns
# ═══════════════════════════════════════════════════════════════════════════

_UNIVERSAL_PATTERNS: Dict[PiiType, re.Pattern] = {
    PiiType.EMAIL: re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"),
    PiiType.CREDIT_CARD: re.compile(
        r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))"
        r"[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{2,4}\b"
    ),
    PiiType.IBAN: re.compile(r"\b[A-Z]{2}\d{2}[\s]?[\dA-Z]{4}[\s]?(?:[\dA-Z]{4}[\s]?){2,7}[\dA-Z]{1,4}\b"),
    PiiType.IP_ADDRESS: re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        r"|"
        r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
    ),
    PiiType.URL: re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"),
    PiiType.DATE: re.compile(
        r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b"
        r"|"
        r"\b\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}\b"
    ),
    PiiType.CURRENCY: re.compile(
        r"[$€£¥₹R\$]\s?\d[\d.,]*\d"
        r"|"
        r"\d[\d.,]*\d\s?[$€£¥₹]"
        r"|"
        r"\d[\d.,]*\d\s?(?:EUR|USD|GBP|BRL|MXN|ARS|COP|CLP)\b"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# Main class
# ═══════════════════════════════════════════════════════════════════════════


class TextAnonymizer:
    """Locale-aware PII detection and data anonymization."""

    def __init__(
        self,
        locale: str = "es_ES",
        strategy: Union[str, Strategy] = Strategy.REDACT,
        seed: Optional[int] = None,
        mask_char: str = "*",
        custom_mask_fn: Optional[Callable[[str, PiiType], str]] = None,
    ):
        """
        Initialize the anonymizer.

        Args:
            locale: Language/country code (e.g. 'es_ES', 'en_US').
            strategy: Default anonymization strategy.
            seed: Optional seed for reproducible replacements.
            mask_char: Character used for masking (default '*').
                Must be a single character.
            custom_mask_fn: Optional callable ``(text, pii_type) -> str``
                that overrides the built-in mask logic entirely when the
                ``mask`` strategy is applied.  Receives the original PII
                value and its type; must return the masked string.
        """
        if len(mask_char) != 1:
            raise ValueError("mask_char must be a single character.")

        self.locale = locale
        self.strategy = Strategy(strategy) if isinstance(strategy, str) else strategy
        self.seed = seed
        self.mask_char: str = mask_char
        self.profile = LOCALE_PROFILES.get(locale)

        # Lazy-loaded references (None until first use)
        self._spacy_nlp: Any = None
        self._nltk_loaded: bool = False
        self._dummy: Any = None  # TextDummy instance (replaces raw Faker)

        # Pseudonymization cache: original → replacement
        self._pseudo_map: Dict[str, str] = {}

        # Custom PII patterns registered by the user
        self._custom_patterns: Dict[str, re.Pattern] = {}

        # Per-type strategy overrides
        self._type_strategies: Dict[PiiType, Strategy] = {}

        # Custom mask function: (text, pii_type) -> str
        self._custom_mask_fn: Optional[Callable[[str, PiiType], str]] = custom_mask_fn

        # Per-type custom mask functions
        self._type_mask_fns: Dict[PiiType, Callable[[str, PiiType], str]] = {}

        if seed is not None:
            import random as _rnd

            _rnd.seed(seed)

    # ───────────────────────────────────────────────────────────────────
    # Lazy loading helpers
    # ───────────────────────────────────────────────────────────────────

    def _get_spacy(self) -> Any:
        """Lazy-load spaCy with the locale-specific model."""
        if self._spacy_nlp is None:
            import spacy  # lazy

            model_name = self.profile.spacy_model if self.profile else "en_core_web_sm"
            try:
                self._spacy_nlp = spacy.load(model_name)
            except OSError:
                raise RuntimeError(f"spaCy model '{model_name}' not found. Install it with: python -m spacy download {model_name}")
        return self._spacy_nlp

    def _ensure_nltk(self) -> None:
        """Lazy-load NLTK resources (tokenizers, NER)."""
        if not self._nltk_loaded:
            import nltk  # lazy

            for resource in (
                "punkt",
                "punkt_tab",
                "averaged_perceptron_tagger",
                "averaged_perceptron_tagger_eng",
                "maxent_ne_chunker",
                "maxent_ne_chunker_tab",
                "words",
            ):
                try:
                    nltk.data.find(
                        f"tokenizers/{resource}"
                        if "punkt" in resource
                        else f"taggers/{resource}"
                        if "tagger" in resource
                        else f"chunkers/{resource}"
                        if "chunker" in resource
                        else f"corpora/{resource}"
                    )
                except LookupError:
                    nltk.download(resource, quiet=True)
            self._nltk_loaded = True

    def _get_dummy(self) -> Any:
        """Lazy-load TextDummy for locale-aware fake data generation."""
        if self._dummy is None:
            from shadetriptxt.text_dummy.text_dummy import TextDummy

            self._dummy = TextDummy(self.locale, seed=self.seed)
        return self._dummy

    # ───────────────────────────────────────────────────────────────────
    # Configuration
    # ───────────────────────────────────────────────────────────────────

    def set_strategy(
        self,
        strategy: Union[str, Strategy],
        pii_type: Optional[Union[str, PiiType]] = None,
    ) -> "TextAnonymizer":
        """
        Set the anonymization strategy (globally or per PII type).

        Args:
            strategy: Strategy to apply.
            pii_type: If given, set strategy only for this PII type.

        Returns:
            self (for chaining).
        """
        s = Strategy(strategy) if isinstance(strategy, str) else strategy
        if pii_type is not None:
            pt = PiiType(pii_type) if isinstance(pii_type, str) else pii_type
            self._type_strategies[pt] = s
        else:
            self.strategy = s
        return self

    def set_mask_function(
        self,
        fn: Callable[[str, PiiType], str],
        pii_type: Optional[Union[str, PiiType]] = None,
    ) -> "TextAnonymizer":
        """
        Register a custom mask function.

        When the ``mask`` strategy is applied, this callable is invoked
        instead of the built-in ``_mask`` logic.

        Args:
            fn: Callable ``(text, pii_type) -> str``.  Must return the
                masked version of *text*.
            pii_type: If given, the custom function applies **only** to
                this PII type.  If ``None`` (default), it applies globally
                to every PII type that uses ``mask``.

        Returns:
            self (for chaining).

        Example::

            anon = TextAnonymizer(strategy="mask")

            # Global custom mask
            anon.set_mask_function(lambda text, pt: "X" * len(text))

            # Per-type custom mask
            anon.set_mask_function(
                lambda text, pt: text[0] + "#" * (len(text) - 1),
                pii_type="EMAIL",
            )
        """
        if pii_type is not None:
            pt = PiiType(pii_type) if isinstance(pii_type, str) else pii_type
            self._type_mask_fns[pt] = fn
        else:
            self._custom_mask_fn = fn
        return self

    def add_pattern(
        self,
        name: str,
        pattern: str,
        pii_type: Union[str, PiiType] = PiiType.CUSTOM,
    ) -> "TextAnonymizer":
        """
        Register a custom regex pattern for PII detection.

        Args:
            name: Pattern identifier (e.g. 'employee_id').
            pattern: Regex pattern string.
            pii_type: PII type to associate with matches.

        Returns:
            self (for chaining).
        """
        self._custom_patterns[name] = re.compile(pattern)
        return self

    def _strategy_for(self, pii_type: PiiType) -> Strategy:
        """Return the strategy to use for the given PII type."""
        return self._type_strategies.get(pii_type, self.strategy)

    # ───────────────────────────────────────────────────────────────────
    # PII Detection — regex
    # ───────────────────────────────────────────────────────────────────

    def _detect_regex(self, text: str) -> List[DetectedEntity]:
        """Detect PII using universal + locale-specific regex patterns."""
        entities: List[DetectedEntity] = []

        # Universal patterns
        for pii_type, pattern in _UNIVERSAL_PATTERNS.items():
            for m in pattern.finditer(text):
                entities.append(
                    DetectedEntity(
                        text=m.group(),
                        pii_type=pii_type,
                        start=m.start(),
                        end=m.end(),
                        confidence=0.9,
                        source="regex",
                    )
                )

        # Locale-specific ID documents
        if self.profile:
            for doc_name, pat in self.profile.id_patterns:
                for m in re.finditer(pat, text):
                    entities.append(
                        DetectedEntity(
                            text=m.group(),
                            pii_type=PiiType.ID_DOCUMENT,
                            start=m.start(),
                            end=m.end(),
                            confidence=0.85,
                            source="regex",
                        )
                    )

            # Phone
            if self.profile.phone_pattern:
                for m in re.finditer(self.profile.phone_pattern, text):
                    entities.append(
                        DetectedEntity(
                            text=m.group(),
                            pii_type=PiiType.PHONE,
                            start=m.start(),
                            end=m.end(),
                            confidence=0.80,
                            source="regex",
                        )
                    )

            # Postcode
            if self.profile.postcode_pattern:
                for m in re.finditer(self.profile.postcode_pattern, text):
                    entities.append(
                        DetectedEntity(
                            text=m.group(),
                            pii_type=PiiType.ADDRESS,
                            start=m.start(),
                            end=m.end(),
                            confidence=0.60,
                            source="regex",
                        )
                    )

        # Custom patterns
        for _name, pattern in self._custom_patterns.items():
            for m in pattern.finditer(text):
                entities.append(
                    DetectedEntity(
                        text=m.group(),
                        pii_type=PiiType.CUSTOM,
                        start=m.start(),
                        end=m.end(),
                        confidence=0.70,
                        source="regex",
                    )
                )

        return entities

    # ───────────────────────────────────────────────────────────────────
    # PII Detection — spaCy NER (lazy)
    # ───────────────────────────────────────────────────────────────────

    _SPACY_LABEL_MAP: Dict[str, PiiType] = {
        "PER": PiiType.NAME,
        "PERSON": PiiType.NAME,
        "ORG": PiiType.ORGANIZATION,
        "GPE": PiiType.LOCATION,
        "LOC": PiiType.LOCATION,
        "DATE": PiiType.DATE,
        "MONEY": PiiType.CURRENCY,
        "CARDINAL": PiiType.NUMBER,
    }

    def _detect_spacy(self, text: str) -> List[DetectedEntity]:
        """Detect PII using spaCy NER (lazy-loaded)."""
        nlp = self._get_spacy()
        doc = nlp(text)
        entities: List[DetectedEntity] = []
        for ent in doc.ents:
            pii_type = self._SPACY_LABEL_MAP.get(ent.label_)
            if pii_type is not None:
                entities.append(
                    DetectedEntity(
                        text=ent.text,
                        pii_type=pii_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.75,
                        source="spacy",
                    )
                )
        return entities

    # ───────────────────────────────────────────────────────────────────
    # PII Detection — NLTK NER (lazy)
    # ───────────────────────────────────────────────────────────────────

    _NLTK_LABEL_MAP: Dict[str, PiiType] = {
        "PERSON": PiiType.NAME,
        "ORGANIZATION": PiiType.ORGANIZATION,
        "GPE": PiiType.LOCATION,
        "LOCATION": PiiType.LOCATION,
        "FACILITY": PiiType.LOCATION,
        "GSP": PiiType.LOCATION,
    }

    def _detect_nltk(self, text: str) -> List[DetectedEntity]:
        """Detect PII using NLTK NER (lazy-loaded)."""
        self._ensure_nltk()
        import nltk  # lazy

        entities: List[DetectedEntity] = []
        sentences = nltk.sent_tokenize(text)
        for sent in sentences:
            words = nltk.word_tokenize(sent)
            tagged = nltk.pos_tag(words)
            chunks = nltk.ne_chunk(tagged)
            for chunk in chunks:
                if hasattr(chunk, "label"):
                    label = chunk.label()
                    pii_type = self._NLTK_LABEL_MAP.get(label)
                    if pii_type is not None:
                        chunk_text = " ".join(c[0] for c in chunk)
                        # Find position in original text
                        idx = text.find(chunk_text)
                        if idx >= 0:
                            entities.append(
                                DetectedEntity(
                                    text=chunk_text,
                                    pii_type=pii_type,
                                    start=idx,
                                    end=idx + len(chunk_text),
                                    confidence=0.65,
                                    source="nltk",
                                )
                            )
        return entities

    # ───────────────────────────────────────────────────────────────────
    # Unified detection
    # ───────────────────────────────────────────────────────────────────

    def detect_pii(
        self,
        text: str,
        use_regex: bool = True,
        use_spacy: bool = False,
        use_nltk: bool = False,
        min_confidence: float = 0.0,
        pii_types: Optional[Sequence[Union[str, PiiType]]] = None,
    ) -> List[DetectedEntity]:
        """
        Detect PII entities in text using one or more detection engines.

        Args:
            text: Input text to scan.
            use_regex: Use regex patterns (fast, always available).
            use_spacy: Use spaCy NER (requires spaCy model installed).
            use_nltk: Use NLTK NER.
            min_confidence: Filter entities below this confidence (0.0-1.0).
            pii_types: Only return these PII types (None = all).

        Returns:
            List of DetectedEntity objects, sorted by position.
        """
        all_entities: List[DetectedEntity] = []

        if use_regex:
            all_entities.extend(self._detect_regex(text))
        if use_spacy:
            all_entities.extend(self._detect_spacy(text))
        if use_nltk:
            all_entities.extend(self._detect_nltk(text))

        # Deduplicate overlapping entities (keep highest confidence)
        all_entities = self._deduplicate(all_entities)

        # Filter by confidence
        if min_confidence > 0:
            all_entities = [e for e in all_entities if e.confidence >= min_confidence]

        # Filter by type
        if pii_types is not None:
            type_set: Set[PiiType] = {PiiType(t) if isinstance(t, str) else t for t in pii_types}
            all_entities = [e for e in all_entities if e.pii_type in type_set]

        # Sort by position
        all_entities.sort(key=lambda e: (e.start, -e.end))
        return all_entities

    @staticmethod
    def _deduplicate(entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Remove overlapping detections, keeping the highest confidence."""
        if not entities:
            return entities
        # Sort by confidence descending
        ranked = sorted(entities, key=lambda e: -e.confidence)
        kept: List[DetectedEntity] = []
        used_ranges: List[Tuple[int, int]] = []
        for ent in ranked:
            overlap = any(not (ent.end <= s or ent.start >= e) for s, e in used_ranges)
            if not overlap:
                kept.append(ent)
                used_ranges.append((ent.start, ent.end))
        return kept

    # ───────────────────────────────────────────────────────────────────
    # Anonymization primitives
    # ───────────────────────────────────────────────────────────────────

    def _mask(self, text: str, pii_type: PiiType) -> str:
        """Mask PII by replacing characters with ``mask_char``.

        If a custom mask function was registered (globally via the
        constructor / ``set_mask_function``, or per-type), it takes
        precedence over the built-in logic.
        """
        # 1. Per-type custom mask function wins
        if pii_type in self._type_mask_fns:
            return self._type_mask_fns[pii_type](text, pii_type)

        # 2. Global custom mask function
        if self._custom_mask_fn is not None:
            return self._custom_mask_fn(text, pii_type)

        # 3. Built-in mask logic using self.mask_char
        c = self.mask_char
        if pii_type == PiiType.EMAIL:
            parts = text.split("@")
            if len(parts) == 2:
                local = parts[0][0] + c * (len(parts[0]) - 1) if parts[0] else c * 3
                domain_parts = parts[1].split(".")
                masked_domain = c * len(domain_parts[0]) if domain_parts else c * 3
                return f"{local}@{masked_domain}.{c * 3}"
            return c * len(text)
        if pii_type == PiiType.PHONE:
            digits = re.sub(r"\D", "", text)
            if len(digits) > 4:
                return c * (len(digits) - 4) + digits[-4:]
            return c * len(text)
        if pii_type == PiiType.CREDIT_CARD:
            digits = re.sub(r"\D", "", text)
            if len(digits) > 4:
                return c * (len(digits) - 4) + digits[-4:]
            return c * len(text)
        if pii_type == PiiType.NAME:
            words = text.split()
            return " ".join(w[0] + c * (len(w) - 1) if len(w) > 1 else c for w in words)
        # Generic masking
        return text[0] + c * (len(text) - 2) + text[-1] if len(text) > 2 else c * len(text)

    def _replace(self, text: str, pii_type: PiiType) -> str:
        """Replace PII with realistic locale-aware fake data (via TextDummy)."""
        dummy = self._get_dummy()
        replacers: Dict[PiiType, Callable[[], str]] = {
            PiiType.NAME: dummy.name,
            PiiType.EMAIL: dummy.email,
            PiiType.PHONE: dummy.phone,
            PiiType.ADDRESS: dummy.address,
            PiiType.ORGANIZATION: dummy.company,
            PiiType.LOCATION: dummy.city,
            PiiType.URL: dummy.url,
            PiiType.DATE: dummy.date,
            PiiType.CREDIT_CARD: dummy.credit_card_number,
            PiiType.IBAN: dummy.iban,
            PiiType.ID_DOCUMENT: dummy.id_document,
            PiiType.CURRENCY: dummy.price,
        }
        replacer = replacers.get(pii_type)
        if replacer:
            return replacer()
        return dummy.word()

    def _hash(self, text: str, length: int = 12) -> str:
        """Replace PII with a truncated SHA-256 hash."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return h[:length]

    def _redact(self, text: str, pii_type: PiiType) -> str:
        """Replace PII with a redaction label like [NAME]."""
        return f"[{pii_type.value}]"

    def _generalize(self, text: str, pii_type: PiiType) -> str:
        """Generalize PII to reduce precision while keeping utility."""
        if pii_type == PiiType.DATE:
            # Try to extract year
            m = re.search(r"\b(19|20)\d{2}\b", text)
            if m:
                return m.group()
            # Try dd/mm/yy → 19yy/20yy
            m2 = re.search(r"\d{1,2}[/\-.]\d{1,2}[/\-.](\d{2,4})", text)
            if m2:
                return m2.group(1)
            return text
        if pii_type == PiiType.NUMBER:
            try:
                num = int(re.sub(r"\D", "", text))
                decade = (num // 10) * 10
                return f"{decade}-{decade + 9}"
            except ValueError:
                return text
        if pii_type in (PiiType.ADDRESS, PiiType.LOCATION):
            # Keep only the city/region part (first word)
            words = text.split(",")
            return words[0].strip() if words else text
        if pii_type == PiiType.EMAIL:
            parts = text.split("@")
            if len(parts) == 2:
                domain_parts = parts[1].split(".")
                return f"***@{'.'.join(domain_parts[-2:]) if len(domain_parts) >= 2 else parts[1]}"
            return "***@***"
        # Default: keep first and last char
        if len(text) > 4:
            return f"{text[:2]}...{text[-2:]}"
        return "***"

    def _pseudonymize(self, text: str, pii_type: PiiType) -> str:
        """Consistent replacement: same input text always maps to the same output."""
        if text in self._pseudo_map:
            return self._pseudo_map[text]
        replacement = self._replace(text, pii_type)
        self._pseudo_map[text] = replacement
        return replacement

    def _suppress(self, text: str, pii_type: PiiType) -> str:
        """Remove PII completely."""
        return ""

    def _apply_strategy(
        self,
        text: str,
        pii_type: PiiType,
        strategy: Optional[Strategy] = None,
    ) -> str:
        """Apply the chosen strategy to a PII value."""
        s = strategy or self._strategy_for(pii_type)
        dispatch: Dict[Strategy, Callable[[str, PiiType], str]] = {
            Strategy.MASK: self._mask,
            Strategy.REPLACE: self._replace,
            Strategy.HASH: lambda t, _pt: self._hash(t),
            Strategy.REDACT: self._redact,
            Strategy.GENERALIZE: self._generalize,
            Strategy.PSEUDONYMIZE: self._pseudonymize,
            Strategy.SUPPRESS: self._suppress,
        }
        handler = dispatch.get(s, self._redact)
        return handler(text, pii_type)

    # ───────────────────────────────────────────────────────────────────
    # High-level text anonymization
    # ───────────────────────────────────────────────────────────────────

    def anonymize_text(
        self,
        text: str,
        strategy: Optional[Union[str, Strategy]] = None,
        use_regex: bool = True,
        use_spacy: bool = False,
        use_nltk: bool = False,
        pii_types: Optional[Sequence[Union[str, PiiType]]] = None,
        min_confidence: float = 0.0,
    ) -> AnonymizationResult:
        """
        Detect and anonymize PII in a text string.

        Args:
            text: Input text.
            strategy: Override default strategy (None = use instance default).
            use_regex: Enable regex detection.
            use_spacy: Enable spaCy NER detection.
            use_nltk: Enable NLTK NER detection.
            pii_types: Only anonymize these PII types (None = all).
            min_confidence: Minimum confidence threshold for detections.

        Returns:
            AnonymizationResult with the anonymized text and metadata.
        """
        strat = Strategy(strategy) if isinstance(strategy, str) else strategy

        entities = self.detect_pii(
            text,
            use_regex=use_regex,
            use_spacy=use_spacy,
            use_nltk=use_nltk,
            min_confidence=min_confidence,
            pii_types=pii_types,
        )

        # Apply replacements from right to left to preserve positions
        result = text
        replacements: Dict[str, str] = {}
        for ent in sorted(entities, key=lambda e: -e.start):
            replacement = self._apply_strategy(ent.text, ent.pii_type, strat)
            result = result[: ent.start] + replacement + result[ent.end :]
            replacements[ent.text] = replacement

        return AnonymizationResult(
            original=text,
            anonymized=result,
            entities=entities,
            replacements=replacements,
        )

    # ───────────────────────────────────────────────────────────────────
    # Dictionary / record anonymization
    # ───────────────────────────────────────────────────────────────────

    # Mapping from field names to PII types (for automatic detection)
    _FIELD_PII_MAP: Dict[str, PiiType] = {
        "name": PiiType.NAME,
        "nombre": PiiType.NAME,
        "full_name": PiiType.NAME,
        "fullname": PiiType.NAME,
        "first_name": PiiType.NAME,
        "firstname": PiiType.NAME,
        "last_name": PiiType.NAME,
        "lastname": PiiType.NAME,
        "surname": PiiType.NAME,
        "apellido": PiiType.NAME,
        "email": PiiType.EMAIL,
        "correo": PiiType.EMAIL,
        "mail": PiiType.EMAIL,
        "email_address": PiiType.EMAIL,
        "phone": PiiType.PHONE,
        "telefono": PiiType.PHONE,
        "phone_number": PiiType.PHONE,
        "mobile": PiiType.PHONE,
        "telephone": PiiType.PHONE,
        "tel": PiiType.PHONE,
        "address": PiiType.ADDRESS,
        "direccion": PiiType.ADDRESS,
        "street": PiiType.ADDRESS,
        "street_address": PiiType.ADDRESS,
        "city": PiiType.LOCATION,
        "ciudad": PiiType.LOCATION,
        "state": PiiType.LOCATION,
        "provincia": PiiType.LOCATION,
        "country": PiiType.LOCATION,
        "pais": PiiType.LOCATION,
        "postcode": PiiType.ADDRESS,
        "zip_code": PiiType.ADDRESS,
        "zip": PiiType.ADDRESS,
        "codigo_postal": PiiType.ADDRESS,
        "dni": PiiType.ID_DOCUMENT,
        "nif": PiiType.ID_DOCUMENT,
        "ssn": PiiType.ID_DOCUMENT,
        "id_document": PiiType.ID_DOCUMENT,
        "document": PiiType.ID_DOCUMENT,
        "documento": PiiType.ID_DOCUMENT,
        "passport": PiiType.ID_DOCUMENT,
        "pasaporte": PiiType.ID_DOCUMENT,
        "curp": PiiType.ID_DOCUMENT,
        "rfc": PiiType.ID_DOCUMENT,
        "cpf": PiiType.ID_DOCUMENT,
        "cnpj": PiiType.ID_DOCUMENT,
        "credit_card": PiiType.CREDIT_CARD,
        "tarjeta": PiiType.CREDIT_CARD,
        "card_number": PiiType.CREDIT_CARD,
        "iban": PiiType.IBAN,
        "bban": PiiType.IBAN,
        "ip": PiiType.IP_ADDRESS,
        "ip_address": PiiType.IP_ADDRESS,
        "url": PiiType.URL,
        "website": PiiType.URL,
        "web": PiiType.URL,
        "date_of_birth": PiiType.DATE,
        "dob": PiiType.DATE,
        "birth_date": PiiType.DATE,
        "birthdate": PiiType.DATE,
        "fecha_nacimiento": PiiType.DATE,
        "company": PiiType.ORGANIZATION,
        "empresa": PiiType.ORGANIZATION,
        "organization": PiiType.ORGANIZATION,
    }

    def anonymize_dict(
        self,
        record: Dict[str, Any],
        field_types: Optional[Dict[str, Union[str, PiiType]]] = None,
        strategy: Optional[Union[str, Strategy]] = None,
        fields: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """
        Anonymize values in a dictionary / record.

        Field names are matched automatically to PII types using a built-in
        mapping.  You can override or extend with ``field_types``.

        Args:
            record: Dictionary with field names and values.
            field_types: Explicit mapping {field_name: PiiType} to override
                        auto-detection.
            strategy: Override default strategy.
            fields: If provided, **only** these fields are considered for
                    anonymization (whitelist). Fields not in the list are
                    left untouched regardless of auto-detection.

        Returns:
            New dictionary with anonymized values.
        """
        strat = Strategy(strategy) if isinstance(strategy, str) else strategy

        allowed: Optional[Set[str]] = set(fields) if fields is not None else None
        ft = dict(field_types) if field_types else {}
        result: Dict[str, Any] = {}
        for key, value in record.items():
            if value is None:
                result[key] = None
                continue

            # Skip fields not in the whitelist (when provided)
            if allowed is not None and key not in allowed:
                result[key] = value
                continue

            str_val = str(value)
            pii_type_raw = ft.get(key)
            if pii_type_raw is None:
                pii_type_raw = self._FIELD_PII_MAP.get(key.lower())
            if pii_type_raw is not None:
                pii_type = PiiType(pii_type_raw) if isinstance(pii_type_raw, str) else pii_type_raw
                result[key] = self._apply_strategy(str_val, pii_type, strat)
            else:
                result[key] = value
        return result

    def anonymize_records(
        self,
        records: Sequence[Dict[str, Any]],
        field_types: Optional[Dict[str, Union[str, PiiType]]] = None,
        strategy: Optional[Union[str, Strategy]] = None,
        fields: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Anonymize a list of dictionary records.

        Args:
            records: List of dictionaries.
            field_types: PII type mapping for fields.
            strategy: Override default strategy.
            fields: If provided, only these fields are anonymized (whitelist).

        Returns:
            List of anonymized dictionaries.
        """
        return [
            self.anonymize_dict(
                r,
                field_types=field_types,
                strategy=strategy,
                fields=fields,
            )
            for r in records
        ]

    # ───────────────────────────────────────────────────────────────────
    # DataFrame anonymization — python-anonymity (lazy)
    # ───────────────────────────────────────────────────────────────────

    def anonymize_dataframe(
        self,
        df: Any,
        identifiers: Sequence[str],
        quasi_identifiers: Sequence[str],
        k: int = 2,
        supp_threshold: int = 0,
        hierarchies: Optional[Dict[str, Any]] = None,
        method: str = "datafly",
    ) -> Any:
        """
        Apply k-anonymity generalization to a pandas DataFrame.

        Uses the *python-anonymity* library (lazy-loaded).

        Args:
            df: pandas DataFrame to anonymize.
            identifiers: Column names that are direct identifiers
                        (will be suppressed / removed).
            quasi_identifiers: Column names that are quasi-identifiers
                              (will be generalized).
            k: Desired k-anonymity level.
            supp_threshold: Maximum number of rows to suppress.
            hierarchies: Generalization hierarchies for quasi-identifiers.
                        ``{column_name: {value: generalized_value, ...}}``.
            method: Algorithm — ``"datafly"`` (default) or ``"incognito"``.

        Returns:
            Anonymized pandas DataFrame.
        """
        from anonymity.tools import k_anonymity as _k_anon  # lazy

        hier = hierarchies or {}
        return _k_anon(
            table=df,
            ident=list(identifiers),
            qi=list(quasi_identifiers),
            k=k,
            supp_threshold=supp_threshold,
            hierarchies=hier,
            method=method,
        )

    def apply_l_diversity(
        self,
        df: Any,
        sensitive_attrs: Sequence[str],
        quasi_identifiers: Sequence[str],
        l_value: int = 2,
        identifiers: Optional[Sequence[str]] = None,
        k: int = 2,
        supp_threshold: int = 0,
        hierarchies: Optional[Dict[str, Any]] = None,
        k_method: str = "datafly",
    ) -> Any:
        """
        Apply l-diversity to a pandas DataFrame.

        Uses the *python-anonymity* library (lazy-loaded).

        Args:
            df: pandas DataFrame.
            sensitive_attrs: Sensitive attribute columns.
            quasi_identifiers: Quasi-identifier columns.
            l_value: Desired l-diversity level.
            identifiers: Direct identifier columns.
            k: k-anonymity level to apply first.
            supp_threshold: Maximum rows to suppress.
            hierarchies: Generalization hierarchies.
            k_method: k-anonymity algorithm.

        Returns:
            Anonymized pandas DataFrame.
        """
        from anonymity.tools import l_diversity as _l_div  # lazy

        return _l_div(
            table=df,
            sa=list(sensitive_attrs),
            qi=list(quasi_identifiers),
            k_method=k_method,
            l=l_value,
            ident=list(identifiers or []),
            supp_threshold=supp_threshold,
            hierarchies=hierarchies or {},
            k=k,
        )

    def apply_t_closeness(
        self,
        df: Any,
        sensitive_attrs: Sequence[str],
        quasi_identifiers: Sequence[str],
        t: float = 0.2,
        identifiers: Optional[Sequence[str]] = None,
        supp_threshold: int = 0,
        hierarchies: Optional[Dict[str, Any]] = None,
        k_method: str = "datafly",
    ) -> Any:
        """
        Apply t-closeness to a pandas DataFrame.

        Uses the *python-anonymity* library (lazy-loaded).

        Args:
            df: pandas DataFrame.
            sensitive_attrs: Sensitive attribute columns.
            quasi_identifiers: Quasi-identifier columns.
            t: t-closeness threshold (0.0 – 1.0).
            identifiers: Direct identifier columns.
            supp_threshold: Maximum rows to suppress.
            hierarchies: Generalization hierarchies.
            k_method: k-anonymity algorithm.

        Returns:
            Anonymized pandas DataFrame.
        """
        from anonymity.tools import t_closeness as _t_close  # lazy

        return _t_close(
            table=df,
            sa=list(sensitive_attrs),
            qi=list(quasi_identifiers),
            t=t,
            k_method=k_method,
            ident=list(identifiers or []),
            supp_threshold=supp_threshold,
            hierarchies=hierarchies or {},
        )

    # ───────────────────────────────────────────────────────────────────
    # Privacy metrics — pycanon (lazy)
    # ───────────────────────────────────────────────────────────────────

    def measure_privacy(
        self,
        df: Any,
        quasi_identifiers: Sequence[str],
        sensitive_attrs: Optional[Sequence[str]] = None,
    ) -> PrivacyReport:
        """
        Measure privacy metrics on a pandas DataFrame using pycanon.

        Args:
            df: pandas DataFrame to evaluate.
            quasi_identifiers: Quasi-identifier column names.
            sensitive_attrs: Sensitive attribute column names
                            (needed for l-diversity and t-closeness).

        Returns:
            PrivacyReport with k-anonymity, l-diversity, and t-closeness values.
        """
        from pycanon.anonymity import (  # lazy
            k_anonymity as _check_k,
            l_diversity as _check_l,
            t_closeness as _check_t,
        )

        qi = list(quasi_identifiers)
        sa = list(sensitive_attrs) if sensitive_attrs else []

        report = PrivacyReport()
        report.k_anonymity = int(_check_k(df, qi))

        if sa:
            report.l_diversity = int(_check_l(df, qi, sa))
            report.t_closeness = float(_check_t(df, qi, sa))

        report.details = {
            "quasi_identifiers": qi,
            "sensitive_attrs": sa,
            "rows": len(df),
        }
        return report

    # ───────────────────────────────────────────────────────────────────
    # Column-level DataFrame anonymization (field-name mapping)
    # ───────────────────────────────────────────────────────────────────

    def anonymize_columns(
        self,
        df: Any,
        column_types: Optional[Dict[str, Union[str, PiiType]]] = None,
        strategy: Optional[Union[str, Strategy]] = None,
        columns: Optional[Sequence[str]] = None,
    ) -> Any:
        """
        Anonymize specific columns of a DataFrame using PII type detection.

        Columns are matched to PII types automatically  by name or via
        the explicit ``column_types`` mapping.

        Args:
            df: pandas DataFrame.
            column_types: Explicit mapping {column_name: PiiType}.
            strategy: Override default strategy.
            columns: If provided, only these columns are anonymized
                    (whitelist). All other columns are left untouched.

        Returns:
            New DataFrame with anonymized columns.
        """

        strat = Strategy(strategy) if isinstance(strategy, str) else strategy
        ct = dict(column_types) if column_types else {}
        allowed: Optional[Set[str]] = set(columns) if columns is not None else None
        result = df.copy()

        for col in result.columns:
            # Skip columns not in the whitelist (when provided)
            if allowed is not None and col not in allowed:
                continue

            pii_type_raw = ct.get(col)
            if pii_type_raw is None:
                pii_type_raw = self._FIELD_PII_MAP.get(col.lower())
            if pii_type_raw is not None:
                pii_type = PiiType(pii_type_raw) if isinstance(pii_type_raw, str) else pii_type_raw
                result[col] = result[col].apply(
                    lambda val, pt=pii_type: self._apply_strategy(str(val), pt, strat) if val is not None and str(val) != "nan" else val
                )
        return result

    # ───────────────────────────────────────────────────────────────────
    # Batch text anonymization
    # ───────────────────────────────────────────────────────────────────

    def anonymize_batch(
        self,
        texts: Sequence[str],
        strategy: Optional[Union[str, Strategy]] = None,
        use_regex: bool = True,
        use_spacy: bool = False,
        use_nltk: bool = False,
    ) -> List[AnonymizationResult]:
        """
        Anonymize a list of text strings.

        Args:
            texts: List of input texts.
            strategy: Override default strategy.
            use_regex: Enable regex detection.
            use_spacy: Enable spaCy detection.
            use_nltk: Enable NLTK detection.

        Returns:
            List of AnonymizationResult objects.
        """
        return [
            self.anonymize_text(
                t,
                strategy=strategy,
                use_regex=use_regex,
                use_spacy=use_spacy,
                use_nltk=use_nltk,
            )
            for t in texts
        ]

    # ───────────────────────────────────────────────────────────────────
    # Utility: summary / stats
    # ───────────────────────────────────────────────────────────────────

    def summary(self, result: AnonymizationResult) -> Dict[str, Any]:
        """
        Return a summary of an anonymization result.

        Args:
            result: An AnonymizationResult object.

        Returns:
            Dictionary with counts by PII type, total entities, etc.
        """
        by_type: Dict[str, int] = {}
        for ent in result.entities:
            by_type[ent.pii_type.value] = by_type.get(ent.pii_type.value, 0) + 1
        return {
            "total_entities": len(result.entities),
            "by_type": by_type,
            "replacements": len(result.replacements),
            "original_length": len(result.original),
            "anonymized_length": len(result.anonymized),
        }

    # ───────────────────────────────────────────────────────────────────
    # Reset / clear
    # ───────────────────────────────────────────────────────────────────

    def reset_pseudonyms(self) -> None:
        """Clear the pseudonymization cache so new mappings are generated."""
        self._pseudo_map.clear()

    def reset(self) -> None:
        """Reset all caches and lazy-loaded resources."""
        self._pseudo_map.clear()
        self._spacy_nlp = None
        self._nltk_loaded = False
        self._dummy = None
        self._custom_patterns.clear()
        self._type_strategies.clear()
        self._custom_mask_fn = None
        self._type_mask_fns.clear()
        self.mask_char = "*"

    # ───────────────────────────────────────────────────────────────────
    # Repr
    # ───────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"TextAnonymizer(locale={self.locale!r}, strategy={self.strategy.value!r})"


# ═══════════════════════════════════════════════════════════════════════════
# Module-level convenience functions
# ═══════════════════════════════════════════════════════════════════════════

_instances: Dict[str, TextAnonymizer] = {}


def get_anonymizer(
    locale: str = "es_ES",
    strategy: Union[str, Strategy] = Strategy.REDACT,
) -> TextAnonymizer:
    """
    Return a cached TextAnonymizer instance for the given locale & strategy.

    Args:
        locale: Locale code.
        strategy: Default strategy.

    Returns:
        TextAnonymizer instance.
    """
    s = Strategy(strategy) if isinstance(strategy, str) else strategy
    key = f"{locale}:{s.value}"
    if key not in _instances:
        _instances[key] = TextAnonymizer(locale=locale, strategy=s)
    return _instances[key]


def anonymize_text(
    text: str,
    locale: str = "es_ES",
    strategy: Union[str, Strategy] = Strategy.REDACT,
    use_regex: bool = True,
    use_spacy: bool = False,
    use_nltk: bool = False,
) -> AnonymizationResult:
    """Convenience: detect and anonymize PII in a text string."""
    anon = get_anonymizer(locale, strategy)
    return anon.anonymize_text(
        text,
        use_regex=use_regex,
        use_spacy=use_spacy,
        use_nltk=use_nltk,
    )


def detect_pii(
    text: str,
    locale: str = "es_ES",
    use_regex: bool = True,
    use_spacy: bool = False,
    use_nltk: bool = False,
) -> List[DetectedEntity]:
    """Convenience: detect PII entities in text."""
    anon = get_anonymizer(locale)
    return anon.detect_pii(
        text,
        use_regex=use_regex,
        use_spacy=use_spacy,
        use_nltk=use_nltk,
    )


def anonymize_dict(
    record: Dict[str, Any],
    locale: str = "es_ES",
    strategy: Union[str, Strategy] = Strategy.REDACT,
    field_types: Optional[Dict[str, Union[str, PiiType]]] = None,
    fields: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Convenience: anonymize a dictionary record."""
    anon = get_anonymizer(locale, strategy)
    return anon.anonymize_dict(record, field_types=field_types, fields=fields)


def anonymize_dataframe(
    df: Any,
    identifiers: Sequence[str],
    quasi_identifiers: Sequence[str],
    k: int = 2,
    locale: str = "es_ES",
    method: str = "datafly",
    hierarchies: Optional[Dict[str, Any]] = None,
) -> Any:
    """Convenience: apply k-anonymity to a DataFrame."""
    anon = get_anonymizer(locale)
    return anon.anonymize_dataframe(
        df,
        identifiers=identifiers,
        quasi_identifiers=quasi_identifiers,
        k=k,
        method=method,
        hierarchies=hierarchies,
    )


def measure_privacy(
    df: Any,
    quasi_identifiers: Sequence[str],
    sensitive_attrs: Optional[Sequence[str]] = None,
    locale: str = "es_ES",
) -> PrivacyReport:
    """Convenience: measure privacy metrics on a DataFrame."""
    anon = get_anonymizer(locale)
    return anon.measure_privacy(df, quasi_identifiers, sensitive_attrs)


# ═══════════════════════════════════════════════════════════════════════════
# Supported locales list
# ═══════════════════════════════════════════════════════════════════════════

SUPPORTED_LOCALES: List[str] = list(LOCALE_PROFILES.keys())


# ═══════════════════════════════════════════════════════════════════════════
# Standalone masking helpers
# ═══════════════════════════════════════════════════════════════════════════


def obfuscate_email(email: str) -> str:
    """Partially mask an email address for display.

    Keeps the first character of the local part, masks the rest,
    and preserves the full domain.

    Args:
        email (str): A valid email address string.

    Returns:
        str: Masked email (e.g. ``"j***@example.com"``).

    Raises:
        TypeError: If *email* is not a string.
        ValueError: If *email* does not contain ``@``.

    Usage Example:
        >>> obfuscate_email("john.doe@example.com")
        'j***@example.com'

    Cost:
        O(n), where n is the length of the email.
    """
    if not isinstance(email, str):
        raise TypeError("email must be a string")

    if "@" not in email:
        raise ValueError("email must contain '@'")

    local, domain = email.rsplit("@", 1)

    if len(local) <= 1:
        masked_local = local
    else:
        masked_local = local[0] + "***"

    return f"{masked_local}@{domain}"
