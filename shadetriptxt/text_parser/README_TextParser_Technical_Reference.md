# shadetriptxt — TextParser Module: Technical Reference

> Complete API reference for `shadetriptxt.text_parser` — locale-aware text extraction, normalization, ID validation, name parsing, encoding recovery, and phonetic reduction.

---

## Module Structure

| File | Purpose |
|------|---------|
| `text_parser.py` | `TextParser` class — unified locale-aware facade |
| `text_extract.py` | `TextExtractor` class — regex-based content extraction (25+ types) |
| `text_normalizer.py` | Standalone text normalization and masking functions |
| `idcard_parser.py` | ID document validation — 12 locales + 28 EU countries |
| `names_parser.py` | Person and company name parsing and formatting |
| `language_normalizer.py` | `LanguageNormalizer` class — abbreviation expansion (6 languages) |
| `encoding_fixer.py` | `EncodingFixer` class — universal mojibake detection and repair |
| `spanish_parser.py` | Spanish article removal and phonetic reduction |
| `english_parser.py` | English article removal and phonetic reduction |
| `portuguese_parser.py` | Portuguese article removal and phonetic reduction |
| `french_parser.py` | French article removal and phonetic reduction |
| `german_parser.py` | German article removal and phonetic reduction |
| `italian_parser.py` | Italian article removal and phonetic reduction |

---

## Table of Contents

- [TextParser (Orchestrator)](#textparser-orchestrator)
- [TextExtractor](#textextractor)
- [Text Normalizer Functions](#text-normalizer-functions)
- [ID Card Parser Functions](#id-card-parser-functions)
- [Names Parser Functions](#names-parser-functions)
- [LanguageNormalizer](#languagenormalizer)
- [EncodingFixer](#encodingfixer)
- [Phonetic Reducers (per language)](#phonetic-reducers-per-language)
- [Function Index](#function-index)

---

## TextParser (Orchestrator)

```python
from shadetriptxt.text_parser.text_parser import TextParser
```

### `TextParser()`

Locale-configurable class that routes all text operations through the correct language/country rules.

**Parameters:**
- `locale` (str): Language/country code. Default: `"es_ES"`. Supported: `es_ES`, `es_MX`, `es_AR`, `es_CO`, `es_CL`, `en_US`, `en_GB`, `pt_BR`, `pt_PT`, `fr_FR`, `de_DE`, `it_IT`.
- `separators` (str | list | `'all'` | None): Separators for `TextExtractor`.

**Example:**
```python
parser = TextParser("es_ES")
parser_us = TextParser("en_US")
```

---

### `TextParser.normalize()`

Normalize text using the locale's language rules — abbreviation expansion, character transformations, accent removal.

**Parameters:**
- `text` (str): Text to normalize.
- `lowercase` (bool): Convert to lowercase. Default: `True`.
- `remove_punctuation` (bool): Remove punctuation marks. Default: `True`.
- `remove_accents` (bool): Remove diacritical marks. Default: `True`.
- `remove_parentheses_content` (bool): Remove content in parentheses. Default: `False`.

**Returns:**
- `str`: Normalized text.

**Example:**
```python
from shadetriptxt.text_parser.text_parser import TextParser
parser = TextParser("es_ES")
parser.normalize("Ma. P. García-López")   # "maria pilar garcia lopez"
```

**Cost:** O(n)

---

### `TextParser.mask()`

Mask sensitive text while keeping parts visible.

**Parameters:**
- `text` (str): Text to mask.
- `keep_first` (int): Chars to keep at start. Default: `1`.
- `keep_last` (int): Chars to keep at end. Default: `1`.
- `mask_char` (str): Masking character. Default: `"*"`.
- `keep_chars` (str | None): Chars to never mask (e.g. `"@."`). Default: `None`.

**Returns:**
- `str`: Masked string.

**Example:**
```python
parser.mask("12345678Z", keep_first=2, keep_last=1)  # "12******Z"
```

**Cost:** O(n)

---

### `TextParser.prepare_for_comparison()`

Prepare text for comparison — combines encoding fix, article removal, and normalization.

**Parameters:**
- `text` (str): Text to prepare.
- `aggressive` (bool): If True, also applies phonetic reduction (level 1). Default: `False`.

**Returns:**
- `str`: Cleaned text.

**Example:**
```python
parser = TextParser("es_ES")
parser.prepare_for_comparison("José de la García")            # "jose garcia"
parser.prepare_for_comparison("José de la García", aggressive=True)  # "JOSE JARSIA"
```

**Cost:** O(n)

---

### `TextParser.remove_articles()`

Remove articles, prepositions, and conjunctions for the locale's language.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `str | None`: Cleaned text.

**Example:**
```python
TextParser("es_ES").remove_articles("Pedro de la Fuente")  # "Pedro Fuente"
TextParser("en_US").remove_articles("John of the Hill")    # "John Hill"
```

**Cost:** O(n)

---

### `TextParser.fix_encoding()`

Fix mojibake using the per-language function (legacy charset allow-list + `EncodingFixer`).

**Parameters:**
- `text` (str): Text with potential encoding problems.
- `add_charset` (str): Kept for backward compatibility (no effect). Default: `''`.

**Returns:**
- `str | None`: Cleaned text.

**Example:**
```python
TextParser("es_ES").fix_encoding("Ã¡rbol")  # "árbol"
```

**Cost:** O(n)

---

### `TextParser.fix_mojibake()`

Repair mojibake using the general-purpose `EncodingFixer` — all codepage pairs, double-encoding, non-destructive.

**Parameters:**
- `text` (str): Potentially garbled text. `None` returns `None`.
- `normalize_quotes` (bool): Convert typographic quotes to ASCII. Default: `False`.

**Returns:**
- `str | None`: Repaired text.

**Example:**
```python
TextParser("fr_FR").fix_mojibake("FranÃ§ois")  # "François"
```

**Cost:** O(n × k), k ≈ 200 patterns

---

### `TextParser.detect_encoding()`

Diagnostic report on encoding issues.

**Parameters:**
- `text` (str): Text to analyse.

**Returns:**
- `dict`: Keys: `has_mojibake`, `likely_pair`, `sequences_found`, `score_original`, `score_fixed`.

**Example:**
```python
TextParser("es_ES").detect_encoding("espaÃ±ol")
# {'has_mojibake': True, 'likely_pair': ('cp1252','utf-8'), ...}
```

**Cost:** O(n × m), m ≈ 5 encoding pairs

---

### `TextParser.reduce_phonetic()`

Apply phonetic reduction for fuzzy matching using locale rules.

**Parameters:**
- `text` (str): Input text.
- `strength` (int): Aggressiveness level 0–3. Default: `1`.

**Returns:**
- `str | None`: Phonetically reduced text.

**Example:**
```python
TextParser("es_ES").reduce_phonetic("José García", 1)  # "JOSE JARSIA"
TextParser("en_US").reduce_phonetic("Knight", 1)        # "NIGT"
```

**Cost:** O(n)

---

### `TextParser.raw_string()`

Full pipeline: encoding fix + article removal + phonetic reduction.

**Parameters:**
- `text` (str): Input text.
- `accuracy` (int): Phonetic reduction level 0–3. Default: `1`.

**Returns:**
- `str | None`: Processed text ready for fuzzy comparison.

**Example:**
```python
TextParser("es_ES").raw_string("José de la Peña", 2)  # "JOSE PENA"
```

**Cost:** O(n)

---

### `TextParser.extract_phones()`

Extract phone numbers. Uses locale's `phone_min_digits` to filter.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Phone numbers (digits only).

**Cost:** O(n)

---

### `TextParser.extract_postal_codes()`

Extract postal codes using locale-aware digit count.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Postal code strings.

**Cost:** O(n)

---

### `TextParser.extract_ids()`

Extract ID document numbers using locale-specific regex patterns.

**Parameters:**
- `text` (str): Input text.
- `doc_type` (str | None): Specific document type (e.g. `'NIE'`, `'CIF'`, `'EIN'`). Default: `None` (primary document).

**Returns:**
- `list[str] | None`: Matched ID strings.

**Example:**
```python
TextParser("es_ES").extract_ids("NIF 12345678A y NIE X1234567L")  # ['12345678A']
TextParser("en_US").extract_ids("SSN 123-45-6789")                # ['123-45-6789']
```

**Cost:** O(n)

---

### `TextParser.extract_emails()`

Extract email addresses.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Email addresses.

**Cost:** O(n)

---

### `TextParser.extract_urls()`

Extract HTTP/HTTPS URLs.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: URL strings.

**Cost:** O(n)

---

### `TextParser.extract_dates()`

Extract date strings (DD/MM/YYYY, MM-DD-YY, etc.).

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Date strings.

**Cost:** O(n)

---

### `TextParser.extract_ibans()`

Extract IBAN codes.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: IBAN strings.

**Cost:** O(n)

---

### `TextParser.extract_credit_cards()`

Extract 16-digit credit card numbers.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Credit card numbers.

**Cost:** O(n)

---

### `TextParser.extract_currency()`

Extract currency amounts ($, €, £, ¥).

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Currency strings.

**Cost:** O(n)

---

### `TextParser.extract_hashtags()`

Extract #hashtags.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Hashtag strings.

**Cost:** O(n)

---

### `TextParser.extract_mentions()`

Extract @mentions.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Mention strings.

**Cost:** O(n)

---

### `TextParser.extract_ip_addresses()`

Extract IPv4 addresses.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: IP address strings.

**Cost:** O(n)

---

### `TextParser.extract_numeric()`

Extract numeric values.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Numeric strings.

**Cost:** O(n)

---

### `TextParser.extract_percentages()`

Extract percentage values.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Percentage strings.

**Cost:** O(n)

---

### `TextParser.tokenize()`

Tokenize text into a list of words.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `list[str] | None`: Token list.

**Cost:** O(n)

---

### `TextParser.validate_id()`

Validate an ID document number using locale-specific rules with check-digit verification.

**Parameters:**
- `id_string` (str): The ID number to validate.
- `doc_type` (str | None): Specific document type (`'DNI'`, `'NIE'`, `'CIF'`). Only for `es_ES`. Default: `None`.

**Returns:**
- `str | None`: Validated ID string if valid, `None` if invalid.

**Example:**
```python
TextParser("es_ES").validate_id("12345678Z")       # "12345678Z"
TextParser("en_US").validate_id("123-45-6789")     # "123-45-6789"
TextParser("pt_BR").validate_id("123.456.789-09")  # "123.456.789-09"
```

**Cost:** O(n)

---

### `TextParser.pad_id()`

Pad an incomplete Spanish NIF with leading zeros.

**Parameters:**
- `id_string` (str): Incomplete ID number.

**Returns:**
- `str | None`: Padded ID string.

**Example:**
```python
TextParser("es_ES").pad_id("123456Z")  # "00123456Z"
```

**Cost:** O(n)

---

### `TextParser.calculate_id_letter()`

Calculate and append the control letter for a Spanish DNI/NIE.

**Parameters:**
- `numeric_part` (str): The numeric part of the DNI/NIE.

**Returns:**
- `str`: Full DNI/NIE with control letter.

**Example:**
```python
TextParser("es_ES").calculate_id_letter("12345678")  # "12345678Z"
```

**Cost:** O(1)

---

### `TextParser.parse_name()`

Rearrange a name from "Last, First" to "First Last".

**Parameters:**
- `name` (str): Name string in "Last, First" format.

**Returns:**
- `str | None`: Rearranged name.

**Example:**
```python
TextParser("es_ES").parse_name("García López, José")  # "José García López"
```

**Cost:** O(n)

---

### `TextParser.parse_company()`

Parse a company name and extract the legal form.

**Parameters:**
- `company_name` (str): Company name string.
- `legal_forms` (list | None): List of legal form abbreviations. Default: `None` (uses Spanish defaults).

**Returns:**
- `tuple | None`: `(company_name, legal_form)`.

**Example:**
```python
TextParser("es_ES").parse_company("EMPRESA ABC, S.L.")  # ('EMPRESA ABC', 'SL')
```

**Cost:** O(n × m)

---

### `TextParser.format_company()`

Format a company name with its legal form.

**Parameters:**
- `company_name` (str): Clean company name.
- `company_type` (str | None): Legal form abbreviation (e.g. `'SL'`, `'SA'`).
- `fmt` (str): Format style. Options: `'brackets'`, `'dots'`, `'comma&dots'`. Default: `'dots'`.

**Returns:**
- `str | None`: Formatted company name.

**Example:**
```python
TextParser("es_ES").format_company("EMPRESA ABC", "SL", "dots")  # "EMPRESA ABC S.L."
```

**Cost:** O(n)

---

### `TextParser.register_abbreviation()`

Register a custom abbreviation expansion for the current locale.

**Parameters:**
- `pattern` (str): Regex pattern to match.
- `expansion` (str): Full form expansion.

**Returns:**
- `None`

**Cost:** O(1)

---

### `TextParser.register_rule()`

Register a custom normalization rule for the current locale.

**Parameters:**
- `rule_func` (Callable[[str], str]): Function that takes and returns a string.
- `name` (str | None): Optional rule name. Default: `None`.

**Returns:**
- `None`

**Cost:** O(1)

---

### `TextParser.locale_info()`

Return information about the current locale.

**Parameters:** None.

**Returns:**
- `dict`: Keys: `locale`, `country`, `language`, `phone_prefix`, `postal_code_digits`, `id_document`, `extra_documents`, `name_order`, `date_format`, `decimal_separator`, `thousands_separator`.

**Cost:** O(1)

---

### `TextParser.supported_locales()`

*(static method)* Return all supported locale codes with country names.

**Parameters:** None.

**Returns:**
- `Dict[str, str]`: `{locale_code: country_name}`.

**Cost:** O(1)

---

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `profile` | `ParserLocaleProfile` | Current locale profile |
| `extractor` | `TextExtractor` | Direct access to underlying `TextExtractor` |
| `language_normalizer` | `LanguageNormalizer` | Direct access to underlying `LanguageNormalizer` |
| `encoding_fixer` | `EncodingFixer` | Direct access to underlying `EncodingFixer` |

---

## TextExtractor

```python
from shadetriptxt.text_parser.text_extract import TextExtractor
```

### `TextExtractor()`

Regex-based content extraction from text strings.

**Parameters:**
- `separators` (str | list | `'all'` | None): Configurable separators. Default: `" \t\n\r\f\v-()."`.

---

### Extraction Methods

All methods take `text (str)` and return `list[str] | None`.

| Method | Category | Description | Cost |
|--------|----------|-------------|------|
| `extract_from_parentheses(text)` | Generic | Text enclosed in parentheses | O(n) |
| `tokenize(text)` | Generic | Split text into tokens | O(n) |
| `extract_phones(text)` | Generic | Phone numbers (≥ 5 digits) | O(n) |
| `extract_emails(text)` | Generic | Email addresses | O(n) |
| `extract_mentions(text)` | Generic | @mentions | O(n) |
| `extract_currency(text)` | Financial | Currency amounts ($, €, £, ¥) | O(n) |
| `extract_credit_cards(text)` | Financial | 16-digit credit card numbers | O(n) |
| `extract_ibans(text)` | Financial | IBAN codes | O(n) |
| `extract_swift_bic(text)` | Financial | SWIFT/BIC codes (8 or 11 chars) | O(n) |
| `extract_postal_codes(text)` | Identifiers | 4-5 digit postal codes | O(n) |
| `extract_custom_ids(text)` | Identifiers | Uppercase letters + digits (e.g. REF456) | O(n) |
| `extract_patient_ids(text)` | Identifiers | Patient IDs (PAT-XXXXX) | O(n) |
| `extract_nif(text)` | Identifiers | Spanish NIF (8 digits + letter) | O(n) |
| `extract_social_security(text)` | Identifiers | SSN format (XXX-XX-XXXX) | O(n) |
| `extract_ip_addresses(text)` | Technical | IPv4 addresses | O(n) |
| `extract_checksums(text)` | Technical | Hex checksums (MD5, SHA) | O(n) |
| `extract_cve_ids(text)` | Technical | CVE identifiers (CVE-YYYY-NNNN) | O(n) |
| `extract_version_numbers(text)` | Technical | Version strings (X.Y.Z) | O(n) |
| `extract_patent_numbers(text)` | Technical | Patent numbers (US1234567A1) | O(n) |
| `extract_isbns(text)` | Technical | ISBN-10 and ISBN-13 | O(n) |
| `extract_urls(text)` | Text Structure | HTTP/HTTPS URLs | O(n) |
| `extract_hashtags(text)` | Text Structure | #hashtags | O(n) |
| `extract_quotations(text)` | Text Structure | Quoted strings | O(n) |
| `extract_paragraphs(text)` | Text Structure | Paragraphs (double newline) | O(n) |
| `extract_classification_tags(text)` | Text Structure | Tags in [brackets] | O(n) |
| `extract_numeric(text)` | Numeric | Numeric values | O(n) |
| `extract_numeric_units(text)` | Numeric | Numbers with units (10kg, 5m) | O(n) |
| `extract_percentages(text)` | Numeric | Percentage values | O(n) |
| `extract_dates(text)` | Numeric | Dates (DD/MM/YYYY, etc.) | O(n) |
| `extract_times(text)` | Numeric | Times (HH:MM, optional AM/PM) | O(n) |
| `extract_passwords(text)` | Security | Potential password strings | O(n) |

---

### `get_string_between()`

*(module-level function)*

Extract the substring between the first two occurrences of a delimiter.

**Parameters:**
- `text` (str): Input string.
- `delimiter` (str): Delimiter string.

**Returns:**
- `str`: Substring between delimiters, or `""` if not found.

**Example:**
```python
from shadetriptxt.text_parser.text_extract import get_string_between
get_string_between("El texto 'entre comillas' es importante.", "'")
# "entre comillas"
```

**Cost:** O(n)

---

## Text Normalizer Functions

```python
from shadetriptxt.text_parser.text_normalizer import (
    normalize_text, mask_text, normalize_whitespace,
    remove_punctuation_marks, remove_special_characters,
    remove_parentheses_and_content, strip_quotes,
    prepare_for_comparison,
)
```

### `normalize_text()`

Main normalization function with configurable steps.

**Parameters:**
- `text` (str): Text to normalize.
- `lowercase` (bool): Convert to lowercase. Default: `True`.
- `remove_punctuation` (bool): Remove punctuation marks. Default: `True`.
- `normalize_whitespace` (bool): Collapse multiple spaces. Default: `True`.
- `remove_accents` (bool): Remove diacritical marks. Default: `False`.
- `remove_parentheses_content` (bool): Remove text in parentheses. Default: `False`.
- `strip_quotes` (bool): Remove quotation marks. Default: `True`.
- `preserve_alphanumeric_only` (bool): Keep only letters and numbers. Default: `False`.

**Returns:**
- `str`: Normalized text.

**Raises:**
- `ValueError`: If text is not a string.

**Example:**
```python
from shadetriptxt.text_parser.text_normalizer import normalize_text
normalize_text("  John   Smith,  Inc.  ")            # "john smith inc"
normalize_text("José García", remove_accents=True)   # "jose garcia"
```

**Cost:** O(n)

---

### `mask_text()`

Mask text by replacing characters with a mask character.

**Parameters:**
- `text` (str): Text to mask.
- `keep_first` (int): Chars to keep at start. Default: `1`.
- `keep_last` (int): Chars to keep at end. Default: `1`.
- `mask_char` (str): Masking character. Default: `"*"`.
- `keep_chars` (str | None): Chars to never mask. Default: `None`.

**Returns:**
- `str`: Masked string.

**Example:**
```python
from shadetriptxt.text_parser.text_normalizer import mask_text
mask_text("12345678Z", keep_first=2, keep_last=1)                         # "12******Z"
mask_text("juan.garcia@gmail.com", keep_first=1, keep_last=4, keep_chars="@.")  # "j***.g*****@g****.com"
```

**Cost:** O(n)

---

### `normalize_whitespace()`

Collapse multiple spaces and trim.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `str`: Text with normalized whitespace.

**Cost:** O(n)

---

### `remove_punctuation_marks()`

Remove common punctuation marks (. , ; : ! ? ¡ ¿).

**Parameters:**
- `text` (str): Input text.
- `preserve_hyphens` (bool): Keep hyphens. Default: `True`.

**Returns:**
- `str`: Text without punctuation.

**Cost:** O(n)

---

### `remove_special_characters()`

Keep only alphanumeric characters.

**Parameters:**
- `text` (str): Input text.
- `keep_spaces` (bool): Preserve spaces. Default: `True`.
- `keep_hyphens` (bool): Preserve hyphens. Default: `False`.

**Returns:**
- `str`: Cleaned text.

**Cost:** O(n)

---

### `remove_parentheses_and_content()`

Remove parentheses, brackets, and braces along with their content.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `str`: Text without parenthesized content.

**Cost:** O(n)

---

### `strip_quotes()`

Remove all types of quotation marks.

**Parameters:**
- `text` (str): Input text.

**Returns:**
- `str`: Text without quotes.

**Cost:** O(n)

---

### `prepare_for_comparison()`

Convenience wrapper with standard/aggressive presets.

**Parameters:**
- `text` (str): Text to prepare.
- `aggressive` (bool): If True, also removes accents, parentheses, and non-alphanumeric. Default: `False`.

**Returns:**
- `str`: Normalized text.

**Cost:** O(n)

---

## ID Card Parser Functions

```python
from shadetriptxt.text_parser.idcard_parser import (
    nif_parse, nif_padding, nif_letter,
    is_valid_dni, is_valid_nie, is_valid_cif,
    validate_spanish_nif, european_nif,
    validate_id_document,
    is_valid_ssn, is_valid_cpf, is_valid_cnpj,
    is_valid_curp, is_valid_rut, is_valid_cuil,
    is_valid_nino, is_valid_portuguese_nif,
    is_valid_bsn, is_valid_codice_fiscale,
)
```

### Spanish ID Functions

---

### `nif_parse()`

Validate any Spanish NIF format (DNI/NIE/CIF) — with automatic zero-padding.

**Parameters:**
- `nif` (str): Identification number string.

**Returns:**
- `str | None`: Validated NIF (uppercase) if correct, `None` if invalid.

**Example:**
```python
from shadetriptxt.text_parser.idcard_parser import nif_parse
nif_parse("12345678Z")  # "12345678Z"
nif_parse("1234567L")   # "01234567L" (auto-padded)
nif_parse("invalid")    # None
```

**Cost:** O(n)

---

### `nif_padding()`

Pad an incomplete NIF/NIE/CIF with leading zeros.

**Parameters:**
- `p_nif` (str): Incomplete identification number.

**Returns:**
- `str | None`: Padded identification number, or `None` if input is invalid.

**Example:**
```python
from shadetriptxt.text_parser.idcard_parser import nif_padding
nif_padding("123456Z")  # "00123456Z"
nif_padding("X1234L")   # "X0001234L"
```

**Cost:** O(n)

---

### `nif_letter()`

Calculate and append the control letter to a DNI/NIE numeric part.

**Parameters:**
- `p_dni` (str): Numeric part (8 digits for DNI, or X/Y/Z + 7 digits for NIE).

**Returns:**
- `str`: Full DNI/NIE with the calculated control letter.

**Example:**
```python
from shadetriptxt.text_parser.idcard_parser import nif_letter
nif_letter("12345678")   # "12345678Z"
nif_letter("X1234567")   # "X1234567L"
```

**Cost:** O(1)

---

### `is_valid_dni()`

Validate a Spanish DNI format and control letter.

**Parameters:**
- `dni_value` (str): DNI string (e.g. `"12345678Z"`).

**Returns:**
- `bool`: `True` if valid.

**Raises:**
- `TypeError`: If input is not a string.

**Cost:** O(1)

---

### `is_valid_nie()`

Validate a Spanish NIE format and control letter.

**Parameters:**
- `nie_value` (str): NIE string (e.g. `"X1234567L"`).

**Returns:**
- `bool`: `True` if valid.

**Raises:**
- `TypeError`: If input is not a string.

**Cost:** O(1)

---

### `is_valid_cif()`

Validate a Spanish CIF format and control character.

**Parameters:**
- `cif_value` (str): CIF string (e.g. `"A12345678"`).

**Returns:**
- `bool`: `True` if valid.

**Raises:**
- `TypeError`: If input is not a string.

**Cost:** O(1)

---

### `validate_spanish_nif()`

Dispatcher: validate DNI, NIE, or CIF by type.

**Parameters:**
- `nif_type` (str): `'DNI'`, `'NIE'`, or `'CIF'`.
- `nif_value` (str): The NIF string.

**Returns:**
- `bool`: `True` if valid.

**Raises:**
- `TypeError`: If either argument is not a string.
- `ValueError`: If `nif_type` is not `'DNI'`, `'NIE'`, or `'CIF'`.

**Cost:** O(1)

---

### `european_nif()`

Parse and validate a European NIF (28 countries).

**Parameters:**
- `p_iparse` (str): Identifier string (with or without country code prefix).
- `p_find_letter` (bool): If True and Spanish NIF with 7–8 digits, compute and append control letter.

**Returns:**
- `tuple | None`: `(type, country, code, nif_value)` or `None`.

**Example:**
```python
from shadetriptxt.text_parser.idcard_parser import european_nif
european_nif("DE123456789", False)   # ('NIF', 'GERMANY', 'DE', '123456789')
european_nif("ESB84761857", False)   # ('CIF', 'SPAIN', 'ES', 'B84761857')
```

**Cost:** O(k), k = number of patterns for the country

---

### International ID Functions

---

### `is_valid_ssn()`

Validate a US Social Security Number.

**Parameters:**
- `ssn` (str): SSN string (e.g. `"123-45-6789"`).

**Returns:**
- `bool`: `True` if valid format.

**Cost:** O(1)

---

### `is_valid_cpf()`

Validate a Brazilian CPF using modulo-11 checksum.

**Parameters:**
- `cpf` (str): CPF string (e.g. `"123.456.789-09"`).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `is_valid_cnpj()`

Validate a Brazilian CNPJ using weighted modulo-11 checksum.

**Parameters:**
- `cnpj` (str): CNPJ string (e.g. `"12.345.678/0001-95"`).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `is_valid_curp()`

Validate a Mexican CURP (format + regex).

**Parameters:**
- `curp` (str): CURP string (18 characters, e.g. `"GARC850101HDFRRR09"`).

**Returns:**
- `bool`: `True` if valid format.

**Cost:** O(1)

---

### `is_valid_rut()`

Validate a Chilean RUT using modulo-11 algorithm.

**Parameters:**
- `rut` (str): RUT string (e.g. `"12.345.678-5"`).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(n)

---

### `is_valid_cuil()`

Validate an Argentine CUIL/CUIT using weighted checksum.

**Parameters:**
- `cuil` (str): CUIL string (e.g. `"20-12345678-9"`).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `is_valid_nino()`

Validate a UK National Insurance Number (prefix + format rules).

**Parameters:**
- `nino` (str): NINO string (e.g. `"AB123456C"`).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `is_valid_portuguese_nif()`

Validate a Portuguese NIF using modulo-11 check digit.

**Parameters:**
- `nif` (str): NIF string (9 digits).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `is_valid_bsn()`

Validate a Netherlands BSN using the 11-test.

**Parameters:**
- `bsn` (str): BSN string (9 digits).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `is_valid_codice_fiscale()`

Validate an Italian Codice Fiscale (format + odd/even positional algorithm).

**Parameters:**
- `cf` (str): Codice Fiscale string (16 characters, e.g. `"RSSMRA85M01H501Z"`).

**Returns:**
- `bool`: `True` if valid.

**Cost:** O(1)

---

### `validate_id_document()`

Unified dispatcher — route to the correct country validator.

**Parameters:**
- `id_str` (str): Identification string.
- `country_code` (str): ISO 3166-1 alpha-2 country code (e.g. `'US'`, `'BR'`, `'ES'`).

**Returns:**
- `bool`: `True` if valid.

**Example:**
```python
from shadetriptxt.text_parser.idcard_parser import validate_id_document
validate_id_document("12345678Z", "ES")              # True
validate_id_document("123-45-6789", "US")             # True
validate_id_document("123.456.789-09", "BR")          # True
validate_id_document("RSSMRA85M01H501Z", "IT")        # True
validate_id_document("12.345.678-5", "CL")            # True
validate_id_document("20-12345678-9", "AR")           # True
```

**Supported countries:**
- **Check-digit**: ES, US, BR, MX, CL, AR, GB, PT, NL, IT.
- **Format (regex)**: DE, FR, EL, AT, BE, BG, HR, CY, CZ, DK, EE, FI, HU, IE, LV, LT, LU, MT, PL, RO, SK, SI, SE.
- **Brazil**: Auto-detects CPF (11 digits) vs CNPJ (14 digits).
- **Argentina**: Auto-detects CUIL (11 digits) vs DNI (7–8 digits).
- **Colombia**: Cédula format validation (6–10 digits).

**Cost:** O(1)

---

## Names Parser Functions

```python
from shadetriptxt.text_parser.names_parser import (
    arrange_fullname, format_name, parse_company,
    format_companyname, get_companyname, get_companytype,
    isformat_company,
)
```

### `arrange_fullname()`

Rearrange "Last, First" → "First Last".

**Parameters:**
- `input_name` (str): Name string.

**Returns:**
- `str | None`: Rearranged name.

**Cost:** O(n)

---

### `format_name()`

Clean and format a name string with character normalization.

**Parameters:**
- `input_string` (str): Name string to format.
- `add_charset` (str): Additional characters to allow.
- `format_type` (str): `"PERSONA"` (letters only) or other (letters + digits).
- `upper` (bool): Convert to uppercase.

**Returns:**
- `str | None`: Formatted name.

**Cost:** O(n)

---

### `parse_company()`

Extract company name and legal form.

**Parameters:**
- `input_string` (str): Company name string.
- `legal_forms` (list): List of legal form abbreviations to detect.

**Returns:**
- `tuple | None`: `(company_name, legal_form)`.

**Example:**
```python
from shadetriptxt.text_parser.names_parser import parse_company
parse_company("SERVICIOS FROS. CARREFOUR, S.A.", legal_forms)
# ('SERVICIOS FROS CARREFOUR', 'SA')
```

**Cost:** O(n × m)

---

### `format_companyname()`

Format a company name with its legal form in a specific style.

**Parameters:**
- `company_name` (str): Clean company name.
- `company_type` (str | None): Legal form abbreviation.
- `format` (str): `'brackets'`, `'dots'`, or `'comma&dots'`.

**Returns:**
- `str | None`: Formatted company name.

**Cost:** O(n)

---

### `get_companyname()`

Extract clean company name without legal form suffix.

**Parameters:**
- `company_name` (str): Company name that may include a legal form.
- `company_type` (str): Known legal form.

**Returns:**
- `str | None`: Clean company name.

**Cost:** O(n)

---

### `get_companytype()`

Extract legal form from a company name.

**Parameters:**
- `input_string` (str): Company name string.

**Returns:**
- `str | None`: Legal form abbreviation (e.g. `'SL'`, `'SA'`).

**Cost:** O(n)

---

### `isformat_company()`

Check if a string matches a known company format (ends with a legal form).

**Parameters:**
- `input_string` (str): String to check.

**Returns:**
- `bool`: `True` if it ends with a known legal form.

**Cost:** O(n)

---

## LanguageNormalizer

```python
from shadetriptxt.text_parser.language_normalizer import LanguageNormalizer
```

### `LanguageNormalizer()`

Language-specific text normalization with extensible abbreviation rules.

**Parameters:**
- `language` (str): Default language code. Default: `'es'`. Supported: `es`, `en`, `pt`, `fr`, `de`, `it`.
- `case_sensitive` (bool): Preserve case. Default: `False`.
- `remove_accents` (bool): Remove diacritical marks. Default: `True`.

---

### `LanguageNormalizer.normalize()`

Normalize text with language-specific rules: abbreviation expansion → case → character transformations → accent removal → custom rules → whitespace.

**Parameters:**
- `text` (str): Text to normalize.
- `language` (str | None): Language code override. Default: `None` (uses instance language).

**Returns:**
- `str`: Normalized text.

**Raises:**
- `ValueError`: If text is empty.

**Example:**
```python
from shadetriptxt.text_parser.language_normalizer import LanguageNormalizer
normalizer = LanguageNormalizer(language='es')
normalizer.normalize("Ma. P. García-López")  # "maria pilar garcia lopez"

normalizer_de = LanguageNormalizer(language='de')
normalizer_de.normalize("Hr. Müller, Str. 5")  # "herr mueller strasse 5"
```

**Cost:** O(n × m), m = number of abbreviations

---

### `LanguageNormalizer.register_rule()`

Register a custom normalization rule. Applied after standard steps.

**Parameters:**
- `language` (str): Language code.
- `rule_func` (Callable[[str], str]): Normalization function.
- `name` (str | None): Optional rule name. Default: `None`.

**Returns:**
- `None`

**Raises:**
- `TypeError`: If `rule_func` is not callable.

**Cost:** O(1)

---

### `LanguageNormalizer.register_abbreviation()`

Register a custom abbreviation expansion.

**Parameters:**
- `language` (str): Language code.
- `pattern` (str): Regex pattern (e.g. `r'\bDept\.\b'`).
- `expansion` (str): Full form (e.g. `'Department'`).

**Returns:**
- `None`

**Cost:** O(1)

---

### `LanguageNormalizer.get_supported_languages()`

Return list of supported language codes.

**Returns:**
- `list[str]`: Language codes (e.g. `['es', 'en', 'pt', 'fr', 'de', 'it']`).

**Cost:** O(1)

---

### `LanguageNormalizer.clear_rules()`

Clear custom normalization rules.

**Parameters:**
- `language` (str | None): Language to clear. `None` clears all. Default: `None`.

**Returns:**
- `None`

**Cost:** O(1)

---

### Built-in Abbreviations by Language

| Language | Examples |
|----------|----------|
| **Spanish** | `Ma.` → María, `Ma. P.` → María Pilar, `J. M.` → José María, `Sr.` → Señor, `Dra.` → Doctora |
| **English** | `St.` → Street, `Ave.` → Avenue, `Blvd.` → Boulevard, `Apt.` → Apartment, `Rd.` → Road |
| **Portuguese** | `Sr.` → Senhor, `Dr.` → Doutor, `Av.` → Avenida, `R.` → Rua, `Pç.` → Praça |
| **French** | `M.` → Monsieur, `Mme.` → Madame, `Av.` → Avenue, `Bd.` → Boulevard, `Sté.` → Société |
| **German** | `Hr.` → Herr, `Fr.` → Frau, `Str.` → Straße, `Nr.` → Nummer, `GmbH` → Gesellschaft... |
| **Italian** | `Sig.` → Signore, `Dott.` → Dottore, `V.` → Via, `P.za` → Piazza, `Avv.` → Avvocato |

---

## EncodingFixer

```python
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer, fix_encoding
```

### `EncodingFixer()`

Universal mojibake detection and repair across 5 encoding pairs.

**Parameters:**
- `language` (str | None): Language hint for better scoring. Default: `None`. Supported: `'es'`, `'en'`, `'pt'`, `'fr'`, `'de'`, `'it'`.

---

### `EncodingFixer.fix()`

Repair mojibake using a 5-step pipeline: pattern replacement → full re-decode → double-encoding recovery → quote normalisation → control cleanup.

**Parameters:**
- `text` (str): Potentially garbled text. `None` → `None`.
- `normalize_quotes` (bool): Convert typographic quotes to ASCII. Default: `False`.

**Returns:**
- `str | None`: Repaired text.

**Example:**
```python
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer
fixer = EncodingFixer(language='es')
fixer.fix("Ã¡rbol")           # "árbol"
fixer.fix("FranÃ§ois")        # "François"
fixer.fix("MÃ¼ller StraÃŸe")  # "Müller Straße"
fixer.fix("l\x92homme")        # "l'homme"
```

**Cost:** O(n × k), k ≈ 200 patterns

---

### `EncodingFixer.has_mojibake()`

Check whether text contains mojibake sequences.

**Parameters:**
- `text` (str): Text to inspect.

**Returns:**
- `bool`: `True` if mojibake detected.

**Cost:** O(n)

---

### `EncodingFixer.detect()`

Diagnostic report on encoding issues.

**Parameters:**
- `text` (str): Text to analyse.

**Returns:**
- `dict`: `has_mojibake`, `likely_pair`, `sequences_found`, `score_original`, `score_fixed`.

**Cost:** O(n × m), m ≈ 5 encoding pairs

---

### `fix_encoding()`

*(module-level convenience function)*

**Parameters:**
- `text` (str): Potentially garbled text.
- `language` (str | None): Language hint. Default: `None`.
- `normalize_quotes` (bool): Convert typographic quotes. Default: `False`.

**Returns:**
- `str | None`: Repaired text.

**Cost:** O(n × k)

---

### Supported Encoding Pairs

| # | Misread as | Actual | Typical symptom |
|---|-----------|--------|-----------------|
| 1 | Windows-1252 | UTF-8 | `Ã¡`, `Ã±`, `Ã¼`, `ÃŸ` |
| 2 | Latin-1 (ISO-8859-1) | UTF-8 | Same visual, C1 control chars |
| 3 | Latin-9 (ISO-8859-15) | UTF-8 | Like Latin-1 with `€`, `œ`, `Ž` |
| 4 | CP850 (DOS OEM) | UTF-8 | Different garbled characters |
| 5 | CP437 (DOS US) | UTF-8 | Box-drawing chars instead of accents |

---

## Phonetic Reducers (per language)

Each language exposes four public functions with the same interface.

### Function Pattern

| Function | Parameters | Returns | Cost |
|----------|-----------|---------|------|
| `remove_XX_articles(input_string)` | `input_string (str)` | `str \| None` | O(n) |
| `fix_XX_conversion_fails(input_string, add_charset)` | `input_string (str)`, `add_charset (str)` Default: `''` | `str \| None` | O(n) |
| `reduce_letters_XX(input_string, strength)` | `input_string (str)`, `strength (int)` 0–3 | `str \| None` | O(n) |
| `raw_string_XX(input_string, accuracy)` | `input_string (str)`, `accuracy (int)` 0–3 | `str \| None` | O(n) |

Where `XX` is one of: `spanish`, `english`, `portuguese`, `french`, `german`, `italian`.

---

### Available Languages

| Import path | Language |
|-------------|----------|
| `shadetriptxt.text_parser.spanish_parser` | Spanish |
| `shadetriptxt.text_parser.english_parser` | English |
| `shadetriptxt.text_parser.portuguese_parser` | Portuguese |
| `shadetriptxt.text_parser.french_parser` | French |
| `shadetriptxt.text_parser.german_parser` | German |
| `shadetriptxt.text_parser.italian_parser` | Italian |

---

### Reduction Levels

| Level | Description | Spanish | English | German | Italian |
|-------|-------------|---------|---------|--------|---------|
| 0 | Remove accents only | `José` → `Jose` | `café` → `cafe` | `Müller` → `Muller` | `Città` → `Citta` |
| 1 | Basic phonetics | `García` → `JARSIA` | `Knight` → `NIGT` | `Straße` → `STRASSE` | `Gnocchi` → `NIOCI` |
| 2 | Intermediate | `Ximénez` → `SIMENES` | `Psychology` → `SYSOLOGY` | `Schneider` → `SNEIDER` | `Chiara` → `CIARA` |
| 3 | Aggressive | `Ñoño` → `NONO` | `William` → `VILLIAM` | `Knecht` → `NECT` | Full intl. |

---

### Example

```python
from shadetriptxt.text_parser.spanish_parser import reduce_letters_spanish, raw_string_spanish
from shadetriptxt.text_parser.german_parser import reduce_letters_german

reduce_letters_spanish("José García", 1)      # "JOSE JARSIA"
raw_string_spanish("José de la Peña", 2)      # "JOSE PENA"
reduce_letters_german("Müller Straße", 1)      # "MUELLER STRASSE"
```

---

## Function Index

Alphabetical list of all public functions across `text_parser`.

| Function | Module | Description |
|----------|--------|-------------|
| [`arrange_fullname()`](#arrange_fullname) | `names_parser` | Rearrange "Last, First" → "First Last" |
| [`european_nif()`](#european_nif) | `idcard_parser` | Validate European NIF (28 countries) |
| [`fix_encoding()`](#fix_encoding) | `encoding_fixer` | Module-level mojibake repair |
| [`fix_XX_conversion_fails()`](#function-pattern) | `*_parser` | Per-language encoding fix (6 languages) |
| [`format_companyname()`](#format_companyname) | `names_parser` | Format company with legal form style |
| [`format_name()`](#format_name) | `names_parser` | Clean and format a name string |
| [`get_companyname()`](#get_companyname) | `names_parser` | Extract clean company name |
| [`get_companytype()`](#get_companytype) | `names_parser` | Extract legal form from company name |
| [`get_string_between()`](#get_string_between) | `text_extract` | Extract substring between delimiters |
| [`is_valid_bsn()`](#is_valid_bsn) | `idcard_parser` | Validate Netherlands BSN |
| [`is_valid_cif()`](#is_valid_cif) | `idcard_parser` | Validate Spanish CIF |
| [`is_valid_cnpj()`](#is_valid_cnpj) | `idcard_parser` | Validate Brazilian CNPJ |
| [`is_valid_codice_fiscale()`](#is_valid_codice_fiscale) | `idcard_parser` | Validate Italian Codice Fiscale |
| [`is_valid_cpf()`](#is_valid_cpf) | `idcard_parser` | Validate Brazilian CPF |
| [`is_valid_cuil()`](#is_valid_cuil) | `idcard_parser` | Validate Argentine CUIL |
| [`is_valid_curp()`](#is_valid_curp) | `idcard_parser` | Validate Mexican CURP |
| [`is_valid_dni()`](#is_valid_dni) | `idcard_parser` | Validate Spanish DNI |
| [`is_valid_nie()`](#is_valid_nie) | `idcard_parser` | Validate Spanish NIE |
| [`is_valid_nino()`](#is_valid_nino) | `idcard_parser` | Validate UK NINO |
| [`is_valid_portuguese_nif()`](#is_valid_portuguese_nif) | `idcard_parser` | Validate Portuguese NIF |
| [`is_valid_rut()`](#is_valid_rut) | `idcard_parser` | Validate Chilean RUT |
| [`is_valid_ssn()`](#is_valid_ssn) | `idcard_parser` | Validate US SSN |
| [`isformat_company()`](#isformat_company) | `names_parser` | Check if string matches company format |
| [`mask_text()`](#mask_text) | `text_normalizer` | Mask sensitive text |
| [`nif_letter()`](#nif_letter) | `idcard_parser` | Calculate DNI/NIE control letter |
| [`nif_padding()`](#nif_padding) | `idcard_parser` | Pad incomplete NIF with zeros |
| [`nif_parse()`](#nif_parse) | `idcard_parser` | Validate Spanish NIF (DNI/NIE/CIF) |
| [`normalize_text()`](#normalize_text) | `text_normalizer` | Main text normalization |
| [`normalize_whitespace()`](#normalize_whitespace) | `text_normalizer` | Collapse multiple spaces |
| [`parse_company()`](#parse_company) | `names_parser` | Extract company name + legal form |
| [`prepare_for_comparison()`](#prepare_for_comparison) | `text_normalizer` | Convenience normalization wrapper |
| [`raw_string_XX()`](#function-pattern) | `*_parser` | Full pipeline: encoding fix + phonetic (6 langs) |
| [`reduce_letters_XX()`](#function-pattern) | `*_parser` | Phonetic reduction (6 languages, levels 0–3) |
| [`remove_parentheses_and_content()`](#remove_parentheses_and_content) | `text_normalizer` | Remove parenthesized content |
| [`remove_punctuation_marks()`](#remove_punctuation_marks) | `text_normalizer` | Remove punctuation |
| [`remove_special_characters()`](#remove_special_characters) | `text_normalizer` | Keep only alphanumeric |
| [`remove_XX_articles()`](#function-pattern) | `*_parser` | Article removal (6 languages) |
| [`strip_quotes()`](#strip_quotes) | `text_normalizer` | Remove quotation marks |
| [`validate_id_document()`](#validate_id_document) | `idcard_parser` | Unified ID validation dispatcher |
| [`validate_spanish_nif()`](#validate_spanish_nif) | `idcard_parser` | Validate by NIF type (DNI/NIE/CIF) |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [TextParser README](README.md) | Main module documentation — architecture, problem statement, quick start, use cases |
| [Normalization Reference](README_Normalization.md) | Normalization engine reference — what gets normalized, pipeline order, parameters |
| [EncodingFixer](README_EncodingFixer.md) | In-depth guide to mojibake detection and repair (pipeline, scoring, encoding pairs) |
| [TextMatcher Integration](README_TextMatcher_Integration.md) | Cross-reference to normalization integration with `TextMatcher` |

## License

Part of the `shadetriptxt` library by DatamanEdge.
