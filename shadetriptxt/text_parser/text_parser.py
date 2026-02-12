"""
TextParser - Locale-aware text parsing, extraction, and normalization.

This module provides a unified, locale-configurable class that routes
text extraction, normalization, phonetic reduction, name parsing, and
ID validation to the appropriate language-specific implementations.

Supported locales mirror those in TextDummy: es_ES, es_MX, es_AR,
es_CO, es_CL, en_US, en_GB, pt_BR, pt_PT, fr_FR, de_DE, it_IT.
"""

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any, Tuple

from .text_extract import TextExtractor, get_string_between
from .text_normalizer import (
    normalize_text,
    normalize_whitespace,
    remove_punctuation_marks,
    remove_special_characters,
    remove_parentheses_and_content,
    strip_quotes,
    prepare_for_comparison,
    mask_text,
)
from .language_normalizer import LanguageNormalizer
from .idcard_parser import (
    nif_parse,
    nif_padding,
    nif_letter,
    is_valid_dni,
    is_valid_nie,
    is_valid_cif,
    validate_spanish_nif,
    european_nif,
    validate_id_document,
    is_valid_ssn,
    is_valid_cpf,
    is_valid_cnpj,
    is_valid_bsn,
    is_valid_codice_fiscale,
    is_valid_curp,
    is_valid_rut,
    is_valid_cuil,
    is_valid_nino,
    is_valid_portuguese_nif,
)
from .spanish_parser import (
    remove_spanish_articles,
    fix_spanish_conversion_fails,
    reduce_letters_spanish,
    raw_string_spanish,
)
from .english_parser import (
    remove_english_articles,
    fix_english_conversion_fails,
    reduce_letters_english,
    raw_string_english,
)
from .portuguese_parser import (
    remove_portuguese_articles,
    fix_portuguese_conversion_fails,
    reduce_letters_portuguese,
    raw_string_portuguese,
)
from .french_parser import (
    remove_french_articles,
    fix_french_conversion_fails,
    reduce_letters_french,
    raw_string_french,
)
from .german_parser import (
    remove_german_articles,
    fix_german_conversion_fails,
    reduce_letters_german,
    raw_string_german,
)
from .italian_parser import (
    remove_italian_articles,
    fix_italian_conversion_fails,
    reduce_letters_italian,
    raw_string_italian,
)
from .encoding_fixer import EncodingFixer


# ---------------------------------------------------------------------------
# Locale profiles: metadata and capabilities per country/language
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ParserLocaleProfile:
    """Profile for a supported locale with parsing-specific metadata."""
    code: str
    country: str
    language: str           # 'es', 'en', 'pt', 'fr', 'de', 'it'
    postal_code_digits: int  # 4 or 5
    phone_prefix: str
    phone_min_digits: int
    id_document_name: str
    id_regex: str            # Regex pattern for the primary ID document
    name_order: str          # 'first_last' or 'last_first'
    has_legal_forms: bool
    date_format: str
    decimal_separator: str
    thousands_separator: str
    extra_id_documents: Dict[str, str] = field(default_factory=dict)


LOCALE_PROFILES: Dict[str, ParserLocaleProfile] = {
    # --- Spanish ---
    "es_ES": ParserLocaleProfile(
        code="es_ES", country="Spain", language="es",
        postal_code_digits=5, phone_prefix="+34", phone_min_digits=9,
        id_document_name="DNI/NIF", id_regex=r'\b\d{8}[A-Z]\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
        extra_id_documents={"NIE": r'\b[XYZ]\d{7}[A-Z]\b', "CIF": r'\b[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]\b'},
    ),
    "es_MX": ParserLocaleProfile(
        code="es_MX", country="Mexico", language="es",
        postal_code_digits=5, phone_prefix="+52", phone_min_digits=10,
        id_document_name="CURP", id_regex=r'\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=".", thousands_separator=",",
        extra_id_documents={"RFC": r'\b[A-Z]{3,4}\d{6}[A-Z0-9]{3}\b'},
    ),
    "es_AR": ParserLocaleProfile(
        code="es_AR", country="Argentina", language="es",
        postal_code_digits=4, phone_prefix="+54", phone_min_digits=10,
        id_document_name="DNI", id_regex=r'\b\d{7,8}\b',
        name_order="last_first", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
        extra_id_documents={"CUIL": r'\b\d{2}-\d{7,8}-\d\b'},
    ),
    "es_CO": ParserLocaleProfile(
        code="es_CO", country="Colombia", language="es",
        postal_code_digits=6, phone_prefix="+57", phone_min_digits=10,
        id_document_name="Cédula", id_regex=r'\b\d{6,10}\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
    ),
    "es_CL": ParserLocaleProfile(
        code="es_CL", country="Chile", language="es",
        postal_code_digits=7, phone_prefix="+56", phone_min_digits=9,
        id_document_name="RUT", id_regex=r'\b\d{1,2}\.\d{3}\.\d{3}-[0-9K]\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
    ),
    # --- English ---
    "en_US": ParserLocaleProfile(
        code="en_US", country="United States", language="en",
        postal_code_digits=5, phone_prefix="+1", phone_min_digits=10,
        id_document_name="SSN", id_regex=r'\b\d{3}-\d{2}-\d{4}\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%m/%d/%Y", decimal_separator=".", thousands_separator=",",
        extra_id_documents={"EIN": r'\b\d{2}-\d{7}\b'},
    ),
    "en_GB": ParserLocaleProfile(
        code="en_GB", country="United Kingdom", language="en",
        postal_code_digits=0, phone_prefix="+44", phone_min_digits=10,
        id_document_name="NINO", id_regex=r'\b[A-Z]{2}\d{6}[A-D]\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=".", thousands_separator=",",
    ),
    # --- Portuguese ---
    "pt_BR": ParserLocaleProfile(
        code="pt_BR", country="Brazil", language="pt",
        postal_code_digits=8, phone_prefix="+55", phone_min_digits=10,
        id_document_name="CPF", id_regex=r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
        extra_id_documents={"CNPJ": r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'},
    ),
    "pt_PT": ParserLocaleProfile(
        code="pt_PT", country="Portugal", language="pt",
        postal_code_digits=4, phone_prefix="+351", phone_min_digits=9,
        id_document_name="NIF", id_regex=r'\b\d{9}\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
    ),
    # --- French ---
    "fr_FR": ParserLocaleProfile(
        code="fr_FR", country="France", language="fr",
        postal_code_digits=5, phone_prefix="+33", phone_min_digits=10,
        id_document_name="INSEE/NIR", id_regex=r'\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=" ",
    ),
    # --- German ---
    "de_DE": ParserLocaleProfile(
        code="de_DE", country="Germany", language="de",
        postal_code_digits=5, phone_prefix="+49", phone_min_digits=10,
        id_document_name="Personalausweis", id_regex=r'\b[A-Z0-9]{10}\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d.%m.%Y", decimal_separator=",", thousands_separator=".",
    ),
    # --- Italian ---
    "it_IT": ParserLocaleProfile(
        code="it_IT", country="Italy", language="it",
        postal_code_digits=5, phone_prefix="+39", phone_min_digits=9,
        id_document_name="Codice Fiscale", id_regex=r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b',
        name_order="first_last", has_legal_forms=True,
        date_format="%d/%m/%Y", decimal_separator=",", thousands_separator=".",
    ),
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class TextParser:
    """
    Locale-configurable text parsing, extraction, and normalization.

    Provides a unified API that routes operations to the appropriate
    language-specific implementations based on the configured locale.

    Args:
        locale: Language/country code (e.g. 'es_ES', 'en_US', 'fr_FR').
                Defaults to 'es_ES'.
        separators: Separators for TextExtractor (str, list, or 'all').

    Example:
        parser = TextParser("es_ES")
        parser.normalize("  José García-López  ")   # "jose garcia lopez"
        parser.extract_phones("+34 91 303 20 60")   # ['34913032060']
        parser.validate_id("12345678Z")              # "12345678Z"

        parser_us = TextParser("en_US")
        parser_us.remove_articles("John of the Hill") # "John Hill"
    """

    def __init__(self, locale: str = "es_ES", separators=None):
        self.locale = locale
        self.profile = LOCALE_PROFILES.get(locale)
        self._language = self.profile.language if self.profile else locale[:2]

        # Initialize sub-components
        self._extractor = TextExtractor(separators=separators)
        self._lang_normalizer = LanguageNormalizer(
            language=self._language,
            case_sensitive=False,
            remove_accents=True,
        )
        self._encoding_fixer = EncodingFixer(language=self._language)

    # ------------------------------------------------------------------
    # Locale information
    # ------------------------------------------------------------------

    def locale_info(self) -> Dict[str, Any]:
        """
        Return information about the current locale.

        Returns:
            Dict with locale metadata.
        """
        if not self.profile:
            return {
                "locale": self.locale,
                "has_profile": False,
                "note": "Core parsing still works but without country-specific rules.",
            }
        p = self.profile
        return {
            "locale": p.code,
            "country": p.country,
            "language": p.language,
            "phone_prefix": p.phone_prefix,
            "postal_code_digits": p.postal_code_digits,
            "id_document": p.id_document_name,
            "extra_documents": list(p.extra_id_documents.keys()) or None,
            "name_order": p.name_order,
            "date_format": p.date_format,
            "decimal_separator": p.decimal_separator,
            "thousands_separator": p.thousands_separator,
        }

    @staticmethod
    def supported_locales() -> Dict[str, str]:
        """Return all supported locale codes with country names."""
        return {code: p.country for code, p in LOCALE_PROFILES.items()}

    # ------------------------------------------------------------------
    # Text normalization (locale-aware)
    # ------------------------------------------------------------------

    def normalize(
        self,
        text: str,
        lowercase: bool = True,
        remove_punctuation: bool = True,
        remove_accents: bool = True,
        remove_parentheses_content: bool = False,
    ) -> str:
        """
        Normalize text using the locale's language rules.

        Applies language-specific abbreviation expansion, character
        transformations, and accent removal via LanguageNormalizer.

        Args:
            text: Text to normalize.
            lowercase: Convert to lowercase.
            remove_punctuation: Remove punctuation marks.
            remove_accents: Remove diacritical marks.
            remove_parentheses_content: Remove content in parentheses.

        Returns:
            Normalized text.

        Example:
            parser = TextParser("es_ES")
            parser.normalize("Ma. P. García-López")
            # "maria pilar garcia lopez"

            parser = TextParser("en_US")
            parser.normalize("123 Main St. Apt. 4B")
            # "123 main street apartment 4b"
        """
        self._lang_normalizer.case_sensitive = not lowercase
        self._lang_normalizer.remove_accents = remove_accents

        result = text
        if remove_parentheses_content:
            result = remove_parentheses_and_content(result)

        result = self._lang_normalizer.normalize(result, language=self._language)

        if remove_punctuation:
            result = remove_punctuation_marks(result)
            result = normalize_whitespace(result)

        return result

    def mask(
        self,
        text: str,
        keep_first: int = 1,
        keep_last: int = 1,
        mask_char: str = "*",
        keep_chars: Optional[str] = None
    ) -> str:
        """
        Mask sensitive text while keeping parts visible.

        Args:
            text: Text to mask.
            keep_first: Number of chars to keep at start.
            keep_last: Number of chars to keep at end.
            mask_char: Character to use for masking.
            keep_chars: Specific chars to NEVER mask (e.g. "@.").

        Returns:
            Masked string.

        Example:
            parser.mask("12345678Z", keep_first=2, keep_last=1)
            # "12******Z"
        """
        return mask_text(
            text,
            keep_first=keep_first,
            keep_last=keep_last,
            mask_char=mask_char,
            keep_chars=keep_chars
        )

    def prepare_for_comparison(self, text: str, aggressive: bool = False) -> str:
        """
        Prepare text for comparison using locale-appropriate preprocessing.

        Combines encoding fix, article removal, and normalization.

        Args:
            text: Text to prepare.
            aggressive: If True, also applies phonetic reduction (level 1).

        Returns:
            Cleaned text ready for comparison.

        Example:
            parser = TextParser("es_ES")
            parser.prepare_for_comparison("José de la García")
            # "jose garcia"

            parser.prepare_for_comparison("José de la García", aggressive=True)
            # "JOSE JARSIA"
        """
        result = self.fix_encoding(text)
        result = self.remove_articles(result)
        result = self.normalize(result)

        if aggressive:
            result = self.reduce_phonetic(result, strength=1)

        return result

    # ------------------------------------------------------------------
    # Article / particle removal (locale-aware)
    # ------------------------------------------------------------------

    def remove_articles(self, text: str) -> Optional[str]:
        """
        Remove articles, prepositions, and conjunctions for the locale's language.

        Args:
            text: Input text.

        Returns:
            Cleaned text.

        Example:
            TextParser("es_ES").remove_articles("Pedro de la Fuente")
            # "Pedro Fuente"

            TextParser("en_US").remove_articles("John of the Hill")
            # "John Hill"
        """
        _article_removers = {
            'es': remove_spanish_articles,
            'en': remove_english_articles,
            'pt': remove_portuguese_articles,
            'fr': remove_french_articles,
            'de': remove_german_articles,
            'it': remove_italian_articles,
        }
        remover = _article_removers.get(self._language, remove_english_articles)
        return remover(text)

    # ------------------------------------------------------------------
    # Encoding / mojibake fix (locale-aware)
    # ------------------------------------------------------------------

    def fix_encoding(self, text: str, add_charset: str = '') -> Optional[str]:
        """
        Fix mojibake and encoding issues for the locale's language.

        Uses the per-language function which delegates internally to
        ``EncodingFixer`` for universal mojibake repair, plus any
        language-specific legacy substitutions (e.g. §→º, ¥→Ñ).

        For a direct, non-dispatched call use ``fix_mojibake()`` instead.

        Args:
            text: Text with potential encoding problems.
            add_charset: Kept for backward compatibility (no effect).

        Returns:
            Cleaned text.

        Example:
            parser = TextParser("es_ES")
            parser.fix_encoding("Ã¡rbol")  # "árbol"
        """
        _encoding_fixers = {
            'es': fix_spanish_conversion_fails,
            'en': fix_english_conversion_fails,
            'pt': fix_portuguese_conversion_fails,
            'fr': fix_french_conversion_fails,
            'de': fix_german_conversion_fails,
            'it': fix_italian_conversion_fails,
        }
        fixer = _encoding_fixers.get(self._language, fix_english_conversion_fails)
        return fixer(text, add_charset)

    def fix_mojibake(self, text: str, normalize_quotes: bool = False) -> Optional[str]:
        """
        Repair mojibake (garbled text from encoding mismatches).

        Uses the general-purpose ``EncodingFixer`` which:
          • Covers all encoding pairs (CP1252, Latin-1, ISO-8859-15,
            CP850, CP437), not just the locale's language.
          • Handles double-encoded UTF-8.
          • Is non-destructive: fixes encoding without stripping valid
            characters through a charset allow-list.
          • Uses a programmatic mojibake map that covers every character
            in the Latin Supplement and Extended-A ranges.

        Args:
            text: Potentially garbled text.  None returns None.
            normalize_quotes: If True, also convert typographic
                characters (smart quotes, em-dash, ellipsis) to ASCII.

        Returns:
            Repaired text.

        Example:
            TextParser("es_ES").fix_mojibake("Ã¡rbol")       # "árbol"
            TextParser("fr_FR").fix_mojibake("FranÃ§ois")    # "François"
            TextParser("de_DE").fix_mojibake("MÃ¼ller")      # "Müller"
        """
        return self._encoding_fixer.fix(text, normalize_quotes=normalize_quotes)

    def detect_encoding(self, text: str) -> Dict[str, Any]:
        """
        Analyse text for encoding issues and return a diagnostic report.

        Useful for auditing data quality or choosing a repair strategy.

        Args:
            text: Text to analyse.

        Returns:
            Dict with keys: has_mojibake, likely_pair, sequences_found,
            score_original, score_fixed.

        Example:
            TextParser("es_ES").detect_encoding("espaÃ±ol")
            # {'has_mojibake': True, 'likely_pair': ('cp1252','utf-8'), ...}
        """
        return self._encoding_fixer.detect(text)

    @property
    def encoding_fixer(self) -> EncodingFixer:
        """Direct access to the underlying EncodingFixer instance."""
        return self._encoding_fixer

    # ------------------------------------------------------------------
    # Phonetic reduction (locale-aware)
    # ------------------------------------------------------------------

    def reduce_phonetic(self, text: str, strength: int = 1) -> Optional[str]:
        """
        Apply phonetic reduction for fuzzy matching using locale rules.

        Args:
            text: Input text.
            strength: Aggressiveness level (0-3).
                0: Only remove accents.
                1: Basic phonetics (silent H, digraphs, homophones).
                2: Intermediate (sibilant unification, consonant clusters).
                3: Aggressive (international normalization).

        Returns:
            Phonetically reduced text.

        Example:
            TextParser("es_ES").reduce_phonetic("José García", 1)
            # "JOSE JARSIA"

            TextParser("en_US").reduce_phonetic("Knight", 1)
            # "NIGT"
        """
        _phonetic_reducers = {
            'es': reduce_letters_spanish,
            'en': reduce_letters_english,
            'pt': reduce_letters_portuguese,
            'fr': reduce_letters_french,
            'de': reduce_letters_german,
            'it': reduce_letters_italian,
        }
        reducer = _phonetic_reducers.get(self._language, reduce_letters_english)
        return reducer(text, strength)

    def raw_string(self, text: str, accuracy: int = 1) -> Optional[str]:
        """
        Full pipeline: encoding fix + phonetic reduction for locale.

        Combines fix_encoding and reduce_phonetic into a single call,
        suitable for preparing text for fuzzy comparison.

        Args:
            text: Input text.
            accuracy: Phonetic reduction level (0-3).

        Returns:
            Processed text ready for fuzzy comparison.

        Example:
            TextParser("es_ES").raw_string("José de la Peña", 2)
            # "JOSE PENA"

            TextParser("en_US").raw_string("Joseph of the Hill", 2)
            # "JOSEPH HILL"
        """
        _raw_string_funcs = {
            'es': raw_string_spanish,
            'en': raw_string_english,
            'pt': raw_string_portuguese,
            'fr': raw_string_french,
            'de': raw_string_german,
            'it': raw_string_italian,
        }
        func = _raw_string_funcs.get(self._language, raw_string_english)
        return func(text, accuracy)

    # ------------------------------------------------------------------
    # Text extraction (locale-enhanced)
    # ------------------------------------------------------------------

    def extract_phones(self, text: str) -> Optional[List[str]]:
        """
        Extract phone numbers from text.

        Uses the locale's phone_min_digits to filter results appropriate
        for the country (e.g. 9 digits for Spain, 10 for US/Mexico).

        Args:
            text: Input text.

        Returns:
            List of phone number strings (digits only), or None.
        """
        phones = self._extractor.extract_phones(text)
        if not phones or not self.profile:
            return phones
        min_digits = self.profile.phone_min_digits
        filtered = [p for p in phones if len(p) >= min_digits]
        return filtered if filtered else None

    def extract_postal_codes(self, text: str) -> Optional[List[str]]:
        """
        Extract postal codes from text using locale-aware digit count.

        For locales with specific postal code lengths (e.g. 5 for Spain,
        4 for Argentina/Portugal), only codes of the correct length
        are returned.

        Args:
            text: Input text.

        Returns:
            List of postal code strings, or None.
        """
        if text is None:
            return None
        if not self.profile or self.profile.postal_code_digits == 0:
            return self._extractor.extract_postal_codes(text)

        digits = self.profile.postal_code_digits
        pattern = re.compile(r'\b\d{' + str(digits) + r'}\b')
        codes = pattern.findall(str(text))
        return codes if codes else None

    def extract_ids(self, text: str, doc_type: Optional[str] = None) -> Optional[List[str]]:
        """
        Extract ID document numbers from text using locale-specific patterns.

        Args:
            text: Input text.
            doc_type: Specific document type (e.g. 'NIE', 'CIF', 'EIN').
                     None uses the primary document pattern.

        Returns:
            List of matched ID strings, or None.

        Example:
            TextParser("es_ES").extract_ids("NIF 12345678A y NIE X1234567L")
            # ['12345678A']

            TextParser("es_ES").extract_ids("NIE X1234567L", doc_type="NIE")
            # ['X1234567L']

            TextParser("en_US").extract_ids("SSN 123-45-6789")
            # ['123-45-6789']
        """
        if text is None or not self.profile:
            return None

        if doc_type and doc_type.upper() in self.profile.extra_id_documents:
            pattern = self.profile.extra_id_documents[doc_type.upper()]
        else:
            pattern = self.profile.id_regex

        matches = re.findall(pattern, text)
        return matches if matches else None

    def extract_emails(self, text: str) -> Optional[List[str]]:
        """Extract email addresses from text."""
        return self._extractor.extract_emails(text)

    def extract_urls(self, text: str) -> Optional[List[str]]:
        """Extract URLs from text."""
        return self._extractor.extract_urls(text)

    def extract_dates(self, text: str) -> Optional[List[str]]:
        """Extract date strings from text."""
        return self._extractor.extract_dates(text)

    def extract_ibans(self, text: str) -> Optional[List[str]]:
        """Extract IBAN codes from text."""
        return self._extractor.extract_ibans(text)

    def extract_credit_cards(self, text: str) -> Optional[List[str]]:
        """Extract credit card numbers from text."""
        return self._extractor.extract_credit_cards(text)

    def extract_currency(self, text: str) -> Optional[List[str]]:
        """Extract currency amounts from text."""
        return self._extractor.extract_currency(text)

    def extract_hashtags(self, text: str) -> Optional[List[str]]:
        """Extract hashtags from text."""
        return self._extractor.extract_hashtags(text)

    def extract_mentions(self, text: str) -> Optional[List[str]]:
        """Extract @mentions from text."""
        return self._extractor.extract_mentions(text)

    def extract_ip_addresses(self, text: str) -> Optional[List[str]]:
        """Extract IPv4 addresses from text."""
        return self._extractor.extract_ip_addresses(text)

    def extract_numeric(self, text: str) -> Optional[List[str]]:
        """Extract numeric values from text."""
        return self._extractor.extract_numeric(text)

    def extract_percentages(self, text: str) -> Optional[List[str]]:
        """Extract percentage values from text."""
        return self._extractor.extract_percentages(text)

    def tokenize(self, text: str) -> Optional[List[str]]:
        """Tokenize text into a list of words."""
        return self._extractor.tokenize(text)

    # ------------------------------------------------------------------
    # ID validation (locale-aware)
    # ------------------------------------------------------------------

    def validate_id(self, id_string: str, doc_type: Optional[str] = None) -> Any:
        """
        Validate an ID document number using locale-specific rules.

        Dispatches to the appropriate country validator based on the
        current locale. Supports check-digit verification for:
        Spain (DNI/NIE/CIF), US (SSN), Brazil (CPF/CNPJ),
        Mexico (CURP), Chile (RUT), Argentina (CUIL), UK (NINO),
        Portugal (NIF), Italy (Codice Fiscale), Netherlands (BSN),
        and 28 EU countries via european_nif().

        Args:
            id_string: The ID number to validate.
            doc_type: Specific document type ('DNI', 'NIE', 'CIF').
                     Only used for Spanish locales.

        Returns:
            Validated ID string if valid, None if invalid.

        Example:
            TextParser("es_ES").validate_id("12345678Z")     # "12345678Z"
            TextParser("en_US").validate_id("123-45-6789")   # "123-45-6789"
            TextParser("pt_BR").validate_id("123.456.789-09") # "123.456.789-09"
            TextParser("es_CL").validate_id("12.345.678-5")  # "12.345.678-5"
        """
        if not id_string or not self.profile:
            return None

        # Determine country code from locale (e.g. "es_ES" → "ES")
        country_code = self.profile.code.split('_')[1] if '_' in self.profile.code else self.profile.code

        # Spanish locales (es_ES): full NIF validation with doc_type support
        if self.profile.code == 'es_ES':
            if doc_type:
                try:
                    if validate_spanish_nif(doc_type.upper(), id_string):
                        return id_string.strip().upper()
                except (TypeError, ValueError):
                    return None
                return None
            return nif_parse(id_string)

        # All other locales: dispatch via country code
        if validate_id_document(id_string, country_code):
            return id_string
        return None

    def pad_id(self, id_string: str) -> Optional[str]:
        """
        Pad an incomplete Spanish NIF with leading zeros.

        Args:
            id_string: Incomplete ID number.

        Returns:
            Padded ID string.

        Example:
            TextParser("es_ES").pad_id("123456Z")
            # "00123456Z"
        """
        return nif_padding(id_string)

    def calculate_id_letter(self, numeric_part: str) -> str:
        """
        Calculate and append the control letter for a Spanish DNI/NIE.

        Args:
            numeric_part: The numeric part of the DNI/NIE.

        Returns:
            Full DNI/NIE with control letter.

        Example:
            TextParser("es_ES").calculate_id_letter("12345678")
            # "12345678Z"
        """
        return nif_letter(numeric_part)

    # ------------------------------------------------------------------
    # Name parsing (locale-aware)
    # ------------------------------------------------------------------

    def parse_name(self, name: str) -> Optional[str]:
        """
        Rearrange a name from "Last, First" to "First Last" format,
        following the locale's name order convention.

        For locales with 'last_first' name_order (e.g. es_AR), this assumes
        the input is already in the correct order. For 'first_last' locales,
        rearranges comma-separated names.

        Args:
            name: Name string, potentially in "Last, First" format.

        Returns:
            Rearranged name, or None if format is invalid.

        Example:
            TextParser("es_ES").parse_name("García López, José")
            # "José García López"
        """
        from .names_parser import arrange_fullname
        return arrange_fullname(name)

    def parse_company(self, company_name: str, legal_forms: Optional[list] = None) -> Optional[tuple]:
        """
        Parse a company name extracting the legal form.

        Only available for Spanish locales (es_*) which have legal form
        detection. For other locales, returns the company name as-is.

        Args:
            company_name: Company name string.
            legal_forms: List of legal form abbreviations to detect.
                        If None, uses a default Spanish set.

        Returns:
            Tuple (company_name, legal_form) or None.

        Example:
            TextParser("es_ES").parse_company("EMPRESA ABC, S.L.")
            # ('EMPRESA ABC', 'SL')
        """
        if not self.profile or not self.profile.has_legal_forms:
            return (company_name, None) if company_name else None

        if legal_forms is None:
            legal_forms = [
                'SCCIL', 'SCCL', 'CORP', 'LTD', 'INC', 'LLC',
                'SAL', 'SAU', 'SLU', 'SRL', 'SAC', 'SCA', 'SLL',
                'SCOOP', 'SRLL', 'SLP', 'SAD',
                'CO', 'LC', 'LP', 'AG', 'NV',
                'SA', 'SL', 'SC', 'RL', 'CB', 'FC', 'S',
            ]

        from .names_parser import parse_company as _parse_company
        return _parse_company(company_name, legal_forms)

    def format_company(
        self,
        company_name: str,
        company_type: Optional[str],
        fmt: str = 'dots',
    ) -> Optional[str]:
        """
        Format a company name with its legal form.

        Args:
            company_name: Clean company name.
            company_type: Legal form abbreviation (e.g. 'SL', 'SA').
            fmt: Format style — 'brackets', 'dots', or 'comma&dots'.

        Returns:
            Formatted company name.

        Example:
            TextParser("es_ES").format_company("EMPRESA ABC", "SL", "dots")
            # "EMPRESA ABC S.L."
        """
        from .names_parser import format_companyname
        return format_companyname(company_name, company_type, fmt)

    # ------------------------------------------------------------------
    # Language normalizer customization
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Custom parsing functions
    # ------------------------------------------------------------------

    def register_custom(
        self,
        name: str,
        func: Callable[[str], str],
    ) -> None:
        """
        Register a custom parsing/transformation function.

        The callable must accept a string and return a transformed string.

        Args:
            name: Unique name for the custom function.
            func: Callable with signature ``(str) -> str``.

        Raises:
            TypeError: If *func* is not callable.

        Example:
            def remove_html(text: str) -> str:
                import re
                return re.sub(r'<[^>]+>', '', text)

            parser = TextParser("es_ES")
            parser.register_custom("strip_html", remove_html)
            clean = parser.run_custom("strip_html", "<b>Hola</b> mundo")
            # "Hola mundo"
        """
        if not callable(func):
            raise TypeError(f"func must be callable, got {type(func).__name__}")
        if not hasattr(self, '_custom_functions'):
            self._custom_functions: Dict[str, Callable[[str], str]] = {}
        self._custom_functions[name] = func

    def unregister_custom(self, name: str) -> None:
        """Remove a registered custom parsing function."""
        if hasattr(self, '_custom_functions'):
            self._custom_functions.pop(name, None)

    def run_custom(self, name: str, text: str) -> str:
        """
        Execute a registered custom parsing function.

        Args:
            name: Name of the registered function.
            text: Input text to transform.

        Returns:
            str: Transformed text.

        Raises:
            ValueError: If *name* is not registered.
        """
        funcs = getattr(self, '_custom_functions', {})
        if name not in funcs:
            raise ValueError(
                f"Custom function '{name}' not registered. "
                f"Registered: {list(funcs.keys())}"
            )
        return funcs[name](text)

    def list_custom(self) -> Dict[str, str]:
        """
        List registered custom parsing functions.

        Returns:
            Dict mapping name to the callable's qualified name.
        """
        funcs = getattr(self, '_custom_functions', {})
        return {
            name: getattr(fn, '__qualname__', repr(fn))
            for name, fn in funcs.items()
        }

    # ------------------------------------------------------------------
    # Language normalizer customization
    # ------------------------------------------------------------------

    def register_abbreviation(self, pattern: str, expansion: str) -> None:
        """
        Register a custom abbreviation expansion for the current locale.

        Args:
            pattern: Regex pattern to match (e.g. r'\\bDept\\.\\b').
            expansion: Full form (e.g. 'Department').

        Example:
            parser = TextParser("es_ES")
            parser.register_abbreviation(r'\\bC/\\b', 'Calle')
            parser.normalize("C/ Mayor 5")
            # "calle mayor 5"
        """
        self._lang_normalizer.register_abbreviation(self._language, pattern, expansion)

    def register_rule(self, rule_func, name: Optional[str] = None) -> None:
        """
        Register a custom normalization rule for the current locale.

        Args:
            rule_func: Callable that takes and returns a string.
            name: Optional name for the rule.

        Example:
            parser = TextParser("es_ES")
            parser.register_rule(lambda t: t.replace("s.l.", "sociedad limitada"))
        """
        self._lang_normalizer.register_rule(self._language, rule_func, name)

    # ------------------------------------------------------------------
    # Direct access to sub-components
    # ------------------------------------------------------------------

    @property
    def extractor(self) -> TextExtractor:
        """Direct access to the underlying TextExtractor instance."""
        return self._extractor

    @property
    def language_normalizer(self) -> LanguageNormalizer:
        """Direct access to the underlying LanguageNormalizer instance."""
        return self._lang_normalizer
