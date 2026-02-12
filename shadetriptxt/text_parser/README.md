# TextParser - Locale-Aware Text Extraction, Normalization & Parsing

## Overview

`text_parser` is a comprehensive, locale-configurable text processing toolkit that provides extraction, normalization, and parsing capabilities for structured and unstructured text. It handles everything from extracting phone numbers and emails to validating national ID documents, normalizing text for comparison, and applying language-specific phonetic transformations — all adapted to the configured country/language.

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Features](#features)
- [Supported Locales](#supported-locales)
- [Core Architecture: The Tiered Design](#core-architecture-the-tiered-design)
- [Module Structure](#module-structure)
- [Quick Start](#quick-start)
  - [TextParser — Unified Locale-Aware API](#textparser--unified-locale-aware-api)
  - [Direct Module Access (without locale)](#direct-module-access-without-locale)
- [Class Reference](#class-reference)
  - [TextParser (Locale-Aware)](#textparser-locale-aware)
  - [TextExtractor](#textextractor)
  - [Text Normalizer Functions](#text-normalizer-functions)
  - [ID Card Parser Functions](#id-card-parser-functions-idcard_parser)
  - [Names Parser Functions](#names-parser-functions)
  - [LanguageNormalizer](#languagenormalizer)
  - [EncodingFixer (Universal Mojibake Repair)](#encodingfixer-universal-mojibake-repair)
  - [Phonetic Reduction (all languages)](#phonetic-reduction-all-languages)
- [Use Cases](#use-cases)
- [Performance](#performance)
- [Related Documentation](#related-documentation)
- [Dependencies](#dependencies)

---

## Problem Statement

Real-world text data often contains formatting inconsistencies that interfere with accurate comparison, deduplication, and identity resolution. These inconsistencies silently break exact-match logic, inflate duplicate counts, and degrade search quality. Here are the most common categories — each one addressed by a specific capability in `text_parser`:

### 1. Accents, Case & Whitespace Variance

The same entity appears written in subtly different ways across systems:

```
"José  García-López"   vs   "jose garcia lopez"   vs   "JOSE   GARCIA  LOPEZ"
```

Extra spaces, inconsistent casing, accented vs unaccented characters, and hyphens vs spaces all cause false negatives in naive string comparison.

**→ Solved by** [`normalize_text()`](#text-normalizer-functions) / [`TextParser.normalize()`](#textparser-locale-aware) — configurable pipeline that collapses whitespace, removes punctuation, strips accents, and normalises case in a single pass.

### 2. Name Format Inconsistencies

Person names arrive in different ordering conventions depending on the source:

```
"García López, José"   vs   "José García López"   vs   "GARCIA LOPEZ JOSE"
```

Some systems store surname-first with comma separator; others use natural order. Abbreviations add another layer:

```
"Ma. P. García"   vs   "María Pilar García"
"Fco. Javier"     vs   "Francisco Javier"
"J. M. Smith"     vs   "John Michael Smith"
```

**→ Solved by** [`arrange_fullname()`](#names-parser-functions) for comma-reordering, [`LanguageNormalizer`](#languagenormalizer) for abbreviation expansion (six languages), and [`format_name()`](#names-parser-functions) for character-level cleanup.

### 3. Encoding Corruption (Mojibake)

Data migrated between databases, exported to CSV, or ingested from legacy systems frequently shows garbled characters when codepages are mismatched:

```
"Ã¡rbol"         → should be "árbol"
"espaÃ±ol"       → should be "español"
"FranÃ§ois"      → should be "François"
"MÃ¼ller StraÃŸe" → should be "Müller Straße"
```

These mojibake sequences make records unmatchable — `"García"` ≠ `"GarcÃ­a"` — and they propagate silently through ETL pipelines.

**→ Solved by** [`EncodingFixer`](#encodingfixer-universal-mojibake-repair) — universal, non-destructive mojibake detection and repair across five encoding pairs (CP1252, Latin-1, Latin-9, CP850, CP437 → UTF-8), including double-encoded text.

### 4. Phonetic Variation Across Languages

Names that sound the same are spelled differently depending on locale, transliteration, or simple typos:

```
"García"   vs   "Garsia"    (Spanish C → S)
"Ximénez"  vs   "Jimenez"   (Spanish X → J)
"Knight"   vs   "Nigt"      (English silent K)
"Müller"   vs   "Mueller"   (German umlaut expansion)
"Gnocchi"  vs   "Nioci"     (Italian GN → NI)
```

Standard string comparison fails completely here; phonetic reduction maps these to equivalent forms.

**→ Solved by** per-language [phonetic reducers](#phonetic-reduction-all-languages) (`reduce_letters_spanish`, `reduce_letters_english`, etc.) with progressive strength levels (0–3), and `raw_string_XX()` pipelines that combine article removal + phonetic reduction.

### 5. Unstructured ID & Contact Extraction

Phone numbers, emails, NIFs, and IBANs are embedded in free-text fields with inconsistent formatting:

```
"Llamar al +34 91-303-20-60 o al 600.606.060"
"NIF: B-84.761.857 / Email: juan.garcia@empresa.com"
"IBAN ES91 2100 0418 4502 0005 1332"
```

There is no single regex that handles all variations — separators, prefixes, grouping, and surrounding context differ per source.

**→ Solved by** [`TextExtractor`](#textextractor) — 25+ extraction methods for phones, emails, IBANs, credit cards, postal codes, URLs, IPs, dates, currencies, and more, with configurable separators.

### 6. ID Document Validation

Identification numbers arrive with missing digits, wrong control letters, or ambiguous format:

```
"123456Z"       → should be "00123456Z" (missing leading zeros)
"B1404500I"     → invalid CIF (wrong control character)
"X1234567L"     → valid NIE? needs algorithmic check
```

Accepting invalid IDs into a system corrupts downstream matching and regulatory reporting.

**→ Solved by** [`nif_parse()`](#id-card-parser-functions-idcard_parser) for Spanish DNI/NIE/CIF validation, `nif_padding()` for zero-fill, `nif_letter()` for control-letter calculation, and [`european_nif()`](#id-card-parser-functions-idcard_parser) for 28 European countries.

### 7. Company Name Ambiguity

The same company appears with different legal form notations, abbreviations, and orderings:

```
"SERVICIOS CARREFOUR, S.A."   vs   "SERVICIOS CARREFOUR SA"   vs   "SERVICIOS CARREFOUR (SA)"
"Sociedad Limitada"           vs   "SL"   vs   "S.L."   vs   "S.L.U."
```

Without normalising legal forms, deduplication algorithms treat each variation as a distinct entity.

**→ Solved by** [`parse_company()`](#names-parser-functions) to separate name from legal form, and [`format_companyname()`](#names-parser-functions) to emit a canonical representation (`dots`, `brackets`, or `comma&dots`).

---

> **In summary**, `text_parser` provides a single, locale-aware toolkit that addresses all of these inconsistencies — so that two records referring to the same person, company, or document converge to the same normalised form before any comparison logic runs.

---

## Features

### Core Capabilities

- **Locale-Aware Processing**: Single `TextParser` class that routes all operations through the correct language/country rules
- **Content Extraction**: Extract phones, emails, URLs, IBANs, credit cards, dates, IPs, and 20+ content types from raw text
- **Text Normalization**: Clean and standardize text for comparison (whitespace, punctuation, accents, special characters)
- **ID Validation**: Validation of national ID documents (DNI, SSN, CPF, NIF...) for 12 locales and 28 European countries
- **Name Parsing**: Parse and format person names and company names with legal form detection
- **Language Normalization**: Language-aware text preprocessing with abbreviation expansion and custom rules
- **Phonetic Reduction**: Progressive phonetic transformations for fuzzy matching in Spanish, English, Portuguese, French, German, and Italian
- **Encoding Recovery**: Universal mojibake detection and repair — fixes garbled text caused by codepage mismatches (UTF-8/Latin-1/CP1252/CP850), double encoding, and stray control characters

## Supported Locales

| Code      | Country        | Language   | ID Document         | Postal Code | Phone Prefix |
| --------- | -------------- | ---------- | ------------------- | ----------- | ------------ |
| `es_ES` | Spain          | Spanish    | DNI/NIF + NIE + CIF | 5 digits    | +34          |
| `es_MX` | Mexico         | Spanish    | CURP + RFC          | 5 digits    | +52          |
| `es_AR` | Argentina      | Spanish    | DNI + CUIL          | 4 digits    | +54          |
| `es_CO` | Colombia       | Spanish    | Cédula             | 6 digits    | +57          |
| `es_CL` | Chile          | Spanish    | RUT                 | 7 digits    | +56          |
| `en_US` | United States  | English    | SSN + EIN           | 5 digits    | +1           |
| `en_GB` | United Kingdom | English    | NINO                | —          | +44          |
| `pt_BR` | Brazil         | Portuguese | CPF + CNPJ          | 8 digits    | +55          |
| `pt_PT` | Portugal       | Portuguese | NIF                 | 4 digits    | +351         |
| `fr_FR` | France         | French     | INSEE/NIR           | 5 digits    | +33          |
| `de_DE` | Germany        | German     | Personalausweis     | 5 digits    | +49          |
| `it_IT` | Italy          | Italian    | Codice Fiscale      | 5 digits    | +39          |

## Core Architecture: The Tiered Design

The library is built on a tiered architecture that balances ease of use with granular control. You can interact with the toolkit at four different levels:

### 1. The Orchestrator: `TextParser` (High-Level Class)

This is the **primary entry point** for most applications. It is a **locale-aware** facade that coordinates all underlying modules. When you initialize it with a locale (e.g., `es_ES`), it automatically selects the correct phonetic reducers, loads country-specific regexes (DNI vs. SSN), and standardizes transformation rules.

### 2. The Functional Engines: `TextExtractor` & `EncodingFixer` (Utility Classes)

These classes handle heavy-duty, complex tasks that require persistent configuration:

- **`TextExtractor`**: Pulls 25+ structured data types (Emails, IBANs, URLs) out of unstructured text with configurable separators.
- **`EncodingFixer`**: A universal engine that detects and repairs garbled text (mojibake) across multiple codepage pairs.

### 3. The Logic Blocks: Standalone Modules & Phonetic Reducers

Every module exposes its core logic as **pure, stateless functions** (e.g., `nif_parse()`, `reduce_letters_spanish()`). This level allows for high performance with minimal overhead and granular control over atomic operations.

### 4. The Foundation: `shadetriptxt.utils` (Internal Utilities)

The library's performance is driven by its internal utility layer, which provides a consistent foundation for all higher-level components:

| Module                 | Purpose                                                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `string_ops`         | Centralized string operations — accent removal, whitespace normalization, character-level cleaning       |
| `similarity_engines` | Core similarity algorithms — Levenshtein, Jaro-Winkler, Sørensen-Dice, Ratcliff-Obershelp               |
| `string_similarity`  | High-level OOP wrapper —`WordSimilarity` class, `are_words_equivalent()`, `calculate_similarity()` |

## Module Structure

The library follows a layered architecture where a unified facade (`TextParser`) coordinates specialized sub-engines.

### How Modules Relate

The `TextParser` class acts as the central orchestrator. When you initialize it with a locale (e.g., `es_ES`), it automatically configures and routes calls to the appropriate specialized sub-modules based on the language and country rules.

```
User Code
  │
  ▼
TextParser (Orchestrator)                          ← locale-aware facade
  │
  ├── TextExtractor ··················· Regex-based extraction (25+ types)
  │
  ├── TextNormalizer ·················· Whitespace, punctuation, accents
  │
  ├── NamesParser ····················· Person & company name formatting
  │
  ├── IDCardParser ···················· ID document validation
  │     ├── ES: DNI / NIE / CIF
  │     ├── US: SSN
  │     ├── BR: CPF / CNPJ
  │     ├── MX: CURP
  │     ├── CL: RUT
  │     ├── AR: CUIL
  │     ├── IT: Codice Fiscale
  │     ├── PT: NIF
  │     ├── GB: NINO
  │     ├── NL: BSN
  │     └── 28 EU countries (format validation)
  │
  ├── EncodingFixer ··················· Universal mojibake repair
  │
  └── LanguageNormalizer ·············· Abbreviation expansion
        ├── spanish_parser
        ├── english_parser
        ├── portuguese_parser
        ├── french_parser
        ├── german_parser
        └── italian_parser
```

### Component Breakdown

| Module                     | Category           | Responsibility                                                      |
| :------------------------- | :----------------- | :------------------------------------------------------------------ |
| `text_parser.py`         | Orchestration      | Unified, locale-aware API — routes operations to all sub-modules   |
| `text_extract.py`        | Functional Engine  | Regex-based content extraction (25+ types: phones, emails, IBANs…) |
| `text_normalizer.py`     | Functional Engine  | Whitespace, punctuation, and accent normalization pipeline          |
| `idcard_parser.py`       | Functional Engine  | ID document validation — 12 locales + 28 EU countries              |
| `encoding_fixer.py`      | Functional Engine  | Universal mojibake detection and repair (5 codepage pairs)          |
| `names_parser.py`        | Parsing & Identity | Person/company name formatting and legal-form detection             |
| `language_normalizer.py` | Parsing & Identity | Language-aware abbreviation expansion (6 languages)                 |
| `spanish_parser.py`      | Linguistic Engine  | Spanish article removal + phonetic reduction (Level 0-3)            |
| `english_parser.py`      | Linguistic Engine  | English article removal + phonetic reduction (Level 0-3)            |
| `portuguese_parser.py`   | Linguistic Engine  | Portuguese article removal + phonetic reduction (Level 0-3)         |
| `french_parser.py`       | Linguistic Engine  | French article removal + phonetic reduction (Level 0-3)             |
| `german_parser.py`       | Linguistic Engine  | German article removal + phonetic reduction (Level 0-3)             |
| `italian_parser.py`      | Linguistic Engine  | Italian article removal + phonetic reduction (Level 0-3)            |

---

## Quick Start

### TextParser — Unified Locale-Aware API

```python
from shadetriptxt.text_parser.text_parser import TextParser

# --- Spanish (Spain) — default locale ---
parser = TextParser("es_ES")

parser.normalize("Ma. P. García-López")         # "maria pilar garcia lopez"
parser.extract_phones("+34 91 303 20 60")        # ['34913032060']
parser.extract_ids("NIF 12345678A")              # ['12345678A']
parser.validate_id("12345678Z")                  # "12345678Z"
parser.remove_articles("Pedro de la Fuente")     # "Pedro Fuente"
parser.reduce_phonetic("García", 1)              # "JARSIA"
parser.parse_name("García López, José")          # "José García López"
parser.parse_company("EMPRESA ABC, S.L.")        # ('EMPRESA ABC', 'SL')

# --- Encoding recovery (any locale) ---
parser.fix_mojibake("Ã¡rbol")                   # "árbol"
parser.fix_mojibake("FranÃ§ois")                # "François"
parser.fix_mojibake("MÃ¼ller StraÃŸe")          # "Müller Straße"
parser.detect_encoding("espaÃ±ol")              # {'has_mojibake': True, ...}

# --- US English ---
parser_us = TextParser("en_US")

parser_us.normalize("123 Main St. Apt. 4B")      # "123 main street apartment 4b"
parser_us.extract_ids("SSN 123-45-6789")          # ['123-45-6789']
parser_us.remove_articles("John of the Hill")     # "John Hill"
parser_us.reduce_phonetic("Knight", 1)            # "NIGT"

# --- Brazil ---
parser_br = TextParser("pt_BR")

parser_br.extract_ids("CPF 123.456.789-09")       # ['123.456.789-09']
parser_br.extract_postal_codes("CEP 01310-100")    # Results based on 8-digit format

# --- France ---
parser_fr = TextParser("fr_FR")

parser_fr.remove_articles("Jean de la Fontaine")     # "Jean Fontaine"
parser_fr.reduce_phonetic("François", 1)              # "FRANCOAS"

# --- Germany ---
parser_de = TextParser("de_DE")

parser_de.reduce_phonetic("Müller Straße", 1)         # "MUELLER STRASSE"

# --- Italy ---
parser_it = TextParser("it_IT")

parser_it.remove_articles("Giovanni della Rovere")    # "Giovanni Rovere"
parser_it.reduce_phonetic("Chiara Gnocchi", 1)        # "CIARA NIOCI"

# --- Locale info ---
parser.locale_info()
# {"locale": "es_ES", "country": "Spain", "language": "es",
#  "phone_prefix": "+34", "postal_code_digits": 5,
#  "id_document": "DNI/NIF", "extra_documents": ["NIE", "CIF"], ...}

TextParser.supported_locales()
# {"es_ES": "Spain", "en_US": "United States", "pt_BR": "Brazil", ...}
```

### Direct Module Access (without locale)

Individual modules can still be used directly without the `TextParser` class:

#### Text Extraction

```python
from shadetriptxt.text_parser.text_extract import TextExtractor

extractor = TextExtractor()

# Extract phone numbers
phones = extractor.extract_phones("Call me at +34-91-303-20-60 or 600606060")
# Returns: ['34913032060', '600606060']

# Extract emails
emails = extractor.extract_emails("Contact support@example.com or sales@company.org")
# Returns: ['support@example.com', 'sales@company.org']

# Extract URLs
urls = extractor.extract_urls("Visit https://www.example.com for info")
# Returns: ['https://www.example.com']

# Extract IBANs
ibans = extractor.extract_ibans("Account IBAN ES9121000418450200051332")
# Returns: ['ES9121000418450200051332']
```

#### Text Normalization

```python
from shadetriptxt.text_parser.text_normalizer import normalize_text, prepare_for_comparison

# Basic normalization
text = normalize_text("  John   Smith,  Inc.  ")
# Returns: "john smith inc"

# With accent removal
text = normalize_text("José García", remove_accents=True)
# Returns: "jose garcia"

# Remove parentheses content
text = normalize_text("Microsoft (MSFT)", remove_parentheses_content=True)
# Returns: "microsoft"

# Convenience function for comparison
text = prepare_for_comparison("José García (CEO)", aggressive=True)
# Returns: "jose garcia ceo"
```

#### ID Card Validation

```python
from shadetriptxt.text_parser.idcard_parser import (
    validate_id_document, nif_parse, european_nif, nif_padding,
    is_valid_ssn, is_valid_cpf, is_valid_codice_fiscale,
)

# --- Unified dispatcher (any country) ---
validate_id_document("12345678Z", "ES")              # True  (Spanish DNI)
validate_id_document("123-45-6789", "US")             # True  (US SSN)
validate_id_document("123.456.789-09", "BR")          # True  (Brazilian CPF)
validate_id_document("RSSMRA85M01H501Z", "IT")        # True  (Italian Codice Fiscale)
validate_id_document("12.345.678-5", "CL")            # True  (Chilean RUT)
validate_id_document("20-12345678-9", "AR")           # True  (Argentine CUIL)

# --- Spanish NIF (DNI/NIE/CIF) ---
nif_parse("12345678Z")                                # "12345678Z" (valid DNI)
nif_parse("B84761857")                                # "B84761857" (valid CIF)

# --- European NIF (28 countries) ---
european_nif("DE123456789", False)                    # ('NIF', 'GERMANY', 'DE', '123456789')

# --- Individual validators ---
is_valid_ssn("123-45-6789")                           # True
is_valid_cpf("123.456.789-09")                        # True
is_valid_codice_fiscale("RSSMRA85M01H501Z")           # True

# --- Pad incomplete NIFs with leading zeros ---
nif_padding("123456Z")                                # "00123456Z"
```

#### Name Parsing

```python
from shadetriptxt.text_parser.names_parser import arrange_fullname, parse_company, format_companyname

# Rearrange "Last, First" to "First Last"
name = arrange_fullname("García López, José")
# Returns: "José García López"

# Parse company name and legal form
result = parse_company("SERVICIOS FROS. CARREFOUR, S.A.", legal_forms)
# Returns: ('SERVICIOS FROS CARREFOUR', 'SA')

# Format company name with legal form
formatted = format_companyname("EMPRESA ABC", "SL", "dots")
# Returns: "EMPRESA ABC S.L."
```

#### Language-Specific Processing

```python
from shadetriptxt.text_parser.language_normalizer import LanguageNormalizer

# Spanish normalization
normalizer = LanguageNormalizer(language='es')
text = normalizer.normalize("José García-López")
# Returns: "jose garcia lopez"

# Abbreviation expansion
text = normalizer.normalize("Ma. P. García")
# Returns: "maria pilar garcia"

# English normalization
normalizer_en = LanguageNormalizer(language='en')
text = normalizer_en.normalize("123 Main St. Apt. 4B")
# Returns: "123 main street apartment 4b"

# Portuguese normalization
normalizer_pt = LanguageNormalizer(language='pt')
text = normalizer_pt.normalize("Av. Paulista, Dr. Silva")
# Returns: "avenida paulista doutor silva"

# French normalization
normalizer_fr = LanguageNormalizer(language='fr')
text = normalizer_fr.normalize("M. Dupont, Bd. Haussmann")
# Returns: "monsieur dupont boulevard haussmann"

# German normalization
normalizer_de = LanguageNormalizer(language='de')
text = normalizer_de.normalize("Hr. Müller, Str. 5")
# Returns: "herr mueller strasse 5"

# Italian normalization
normalizer_it = LanguageNormalizer(language='it')
text = normalizer_it.normalize("Sig. Rossi, V. Garibaldi")
# Returns: "signore rossi via garibaldi"
```

#### Encoding Recovery (Mojibake Repair)

```python
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer, fix_encoding

# --- Basic usage ---
fixer = EncodingFixer()
fixer.fix("Ã¡rbol")                     # "árbol"
fixer.fix("espaÃ±ol")                   # "español"
fixer.fix("FranÃ§ois")                  # "François"
fixer.fix("MÃ¼ller StraÃŸe")           # "Müller Straße"
fixer.fix("JoÃ£o da Silva")             # "João da Silva"
fixer.fix("cittÃ\xa0")                  # "città"

# --- CP1252 smart characters (0x80-0x9F) ---
fixer.fix("l\x92homme")                 # "l'homme"  (0x92 → right quote)
fixer.fix("\x80100")                     # "€100"     (0x80 → euro sign)

# --- Double-encoded UTF-8 ---
fixer.fix("ÃƒÂ¡rbol")                   # "árbol"

# --- BOM removal ---
fixer.fix("ï»¿Hello")                   # "Hello"

# --- With language hint (improves scoring on ambiguous text) ---
fixer_es = EncodingFixer(language='es')
fixer_es.fix("espaÃ±ol")                # "español"

# --- Detection / diagnostics ---
fixer.has_mojibake("Hello world")        # False
fixer.has_mojibake("Ã¡rbol")            # True

report = fixer.detect("espaÃ±ol")
# {'has_mojibake': True,
#  'likely_pair': ('cp1252', 'utf-8'),
#  'sequences_found': ['Ã±'],
#  'score_original': 1.812,
#  'score_fixed': 2.0}

# --- Typographic normalisation ---
fixer.fix("l\u2019homme", normalize_quotes=True)   # "l'homme" (straight ')

# --- Module-level convenience function ---
result = fix_encoding("Ã¡rbol", language='es')       # "árbol"
```

#### Phonetic Reduction

```python
from shadetriptxt.text_parser.spanish_parser import reduce_letters_spanish, raw_string_spanish
from shadetriptxt.text_parser.english_parser import reduce_letters_english
from shadetriptxt.text_parser.portuguese_parser import reduce_letters_portuguese
from shadetriptxt.text_parser.french_parser import reduce_letters_french
from shadetriptxt.text_parser.german_parser import reduce_letters_german
from shadetriptxt.text_parser.italian_parser import reduce_letters_italian

# Spanish phonetic reduction (level 1: basic)
text = reduce_letters_spanish("José García", 1)
# Returns: "JOSE JARSIA"

# Spanish phonetic reduction (level 2: intermediate)
text = reduce_letters_spanish("Ximénez", 2)
# Returns: "SIMENES"

# Full Spanish text preparation for fuzzy comparison
text = raw_string_spanish("José de la Peña", 2)
# Returns: "JOSE PENA"

# English phonetic reduction
text = reduce_letters_english("Joseph Garcia", 1)
# Returns: "JOSEPH GARSIA"

# Portuguese phonetic reduction
text = reduce_letters_portuguese("Gonçalves", 2)
# Returns: "GONSALVES"

# French phonetic reduction
text = reduce_letters_french("François", 1)
# Returns: "FRANCOAS"

# German phonetic reduction (umlauts expanded)
text = reduce_letters_german("Müller Straße", 1)
# Returns: "MUELLER STRASSE"

# Italian phonetic reduction
text = reduce_letters_italian("Chiara Gnocchi", 1)
# Returns: "CIARA NIOCI"
```

---

## Class Reference

### TextParser (Locale-Aware)

Unified locale-configurable class that wraps all `text_parser` modules, routing operations through the correct language/country rules.

#### Constructor

```python
TextParser(locale="es_ES")
```

**Parameters:**

- `locale` (str): Locale code (e.g., `"es_ES"`, `"en_US"`, `"pt_BR"`). Defaults to `"es_ES"`. Use `TextParser.supported_locales()` to list available codes.

#### Properties

| Property                | Type                    | Description                                    |
| ----------------------- | ----------------------- | ---------------------------------------------- |
| `profile`             | `ParserLocaleProfile` | Current locale profile with all metadata       |
| `extractor`           | `TextExtractor`       | Direct access to the underlying extractor      |
| `language_normalizer` | `LanguageNormalizer`  | Direct access to the underlying normalizer     |
| `encoding_fixer`      | `EncodingFixer`       | Direct access to the underlying encoding fixer |

#### Methods — Normalization & Comparison

| Method                                             | Description                                                        |
| -------------------------------------------------- | ------------------------------------------------------------------ |
| `normalize(text, **kwargs)`                      | Language-aware text normalization                                  |
| `mask(text, **kwargs)`                           | Mask sensitive text (keep parts visible)                           |
| `prepare_for_comparison(text, aggressive=False)` | Normalize text for comparison                                      |
| `remove_articles(text)`                          | Remove articles/prepositions for the locale's language             |
| `fix_encoding(text)`                             | Fix mojibake/encoding issues (per-language, with charset filter)   |
| `fix_mojibake(text, normalize_quotes)`           | **General** mojibake repair (non-destructive, all codepages) |
| `detect_encoding(text)`                          | Diagnostic report on encoding issues                               |
| `reduce_phonetic(text, strength=1)`              | Phonetic reduction for the locale's language                       |
| `raw_string(text, accuracy=1)`                   | Full pipeline: clean + phonetic reduction                          |

#### Methods — Extraction

| Method                         | Description                                         |
| ------------------------------ | --------------------------------------------------- |
| `extract_phones(text)`       | Extract phone numbers (locale-aware min digits)     |
| `extract_postal_codes(text)` | Extract postal codes (locale-aware digit count)     |
| `extract_ids(text)`          | Extract ID documents matching the locale's patterns |
| `extract_emails(text)`       | Extract email addresses                             |
| `extract_urls(text)`         | Extract HTTP/HTTPS URLs                             |
| `extract_ibans(text)`        | Extract IBAN codes                                  |
| `extract_credit_cards(text)` | Extract credit card numbers                         |
| `extract_dates(text)`        | Extract dates                                       |
| `extract_currency(text)`     | Extract currency amounts                            |
| `extract_hashtags(text)`     | Extract hashtags                                    |
| `extract_mentions(text)`     | Extract @mentions                                   |
| `extract_ip_addresses(text)` | Extract IPv4 addresses                              |
| `extract_numeric(text)`      | Extract numeric values                              |
| `extract_percentages(text)`  | Extract percentage values                           |
| `tokenize(text)`             | Tokenize text into words                            |

#### Methods — ID Validation

| Method                             | Description                                  |
| ---------------------------------- | -------------------------------------------- |
| `validate_id(id_string)`         | Validate an ID document for the locale       |
| `pad_id(id_string)`              | Pad incomplete ID with leading zeros         |
| `calculate_id_letter(id_string)` | Calculate control letter for the locale's ID |

#### Methods — Name & Company Parsing

| Method                                              | Description                             |
| --------------------------------------------------- | --------------------------------------- |
| `parse_name(name)`                                | Rearrange "Last, First" → "First Last" |
| `parse_company(company_string, legal_forms=None)` | Parse company name and legal form       |
| `format_company(name, legal_form, fmt="dots")`    | Format company with legal form          |

#### Methods — Extensibility & Info

| Method                                        | Description                                                    |
| --------------------------------------------- | -------------------------------------------------------------- |
| `register_custom(name, func)`               | Register a custom `(str) -> str` parsing function              |
| `unregister_custom(name)`                   | Remove a registered custom parsing function                    |
| `run_custom(name, text)`                    | Execute a registered custom parsing function                   |
| `list_custom()`                             | List registered custom parsing functions                       |
| `register_abbreviation(pattern, expansion)` | Register custom abbreviation for current language              |
| `register_rule(rule_func, name=None)`       | Register custom normalization rule                             |
| `locale_info()`                             | Return a dict with all locale metadata                         |
| `supported_locales()`                       | **(static method)** Return dict of all supported locales |

```python
import re

parser = TextParser("es_ES")
parser.register_custom("strip_html", lambda t: re.sub(r"<[^>]+>", "", t))
clean = parser.run_custom("strip_html", "<b>Hola</b> mundo")
# "Hola mundo"
```

#### ParserLocaleProfile Fields

| Field                   | Type           | Description                                  |
| ----------------------- | -------------- | -------------------------------------------- |
| `code`                | str            | Locale code (e.g.,`"es_ES"`)               |
| `country`             | str            | Country name                                 |
| `language`            | str            | ISO 639-1 language code                      |
| `postal_code_digits`  | int            | Expected postal code digit count             |
| `phone_prefix`        | str            | International phone prefix                   |
| `phone_min_digits`    | int            | Minimum digits to consider a phone number    |
| `id_document_name`    | str            | Primary ID document name                     |
| `id_regex`            | str            | Regex pattern for the primary ID document    |
| `name_order`          | str            | `"first_last"` or `"last_first"`         |
| `has_legal_forms`     | bool           | Whether legal forms are supported            |
| `date_format`         | str            | Typical date format                          |
| `decimal_separator`   | str            | Decimal separator                            |
| `thousands_separator` | str            | Thousands separator                          |
| `extra_id_documents`  | Dict[str, str] | Additional ID document types (name → regex) |

---

### TextExtractor

Extracts various content types from text strings using regex-based pattern matching.

#### Constructor

```python
TextExtractor(separators=None)
```

**Parameters:**

- `separators` (str, list, or `'all'`, optional): Configurable separators
  - `str`: Use that string as separators
  - `list`: Join the list into a string
  - `'all'`: Comprehensive set of separators
  - `None`: Default separators (`" \t\n\r\f\v-()."`)

#### Methods

| Category                 | Method                                | Description                               |
| ------------------------ | ------------------------------------- | ----------------------------------------- |
| **Generic**        | `extract_from_parentheses(text)`    | Text enclosed in parentheses              |
|                          | `tokenize(text)`                    | Split text into tokens                    |
|                          | `extract_phones(text)`              | Phone numbers (≥5 digits)                |
|                          | `extract_emails(text)`              | Email addresses                           |
|                          | `extract_mentions(text)`            | @mentions                                 |
| **Financial**      | `extract_currency(text)`            | Currency amounts ($, €, £, ¥)          |
|                          | `extract_credit_cards(text)`        | 16-digit credit card numbers              |
|                          | `extract_ibans(text)`               | IBAN codes                                |
|                          | `extract_swift_bic(text)`           | SWIFT/BIC codes                           |
| **Identifiers**    | `extract_postal_codes(text)`        | 4-5 digit postal codes                    |
|                          | `extract_custom_ids(text)`          | Uppercase letters + digits (e.g., REF456) |
|                          | `extract_patient_ids(text)`         | Patient IDs (PAT-XXXXX)                   |
|                          | `extract_nif(text)`                 | Spanish NIF numbers                       |
|                          | `extract_social_security(text)`     | SSN format (XXX-XX-XXXX)                  |
| **Technical**      | `extract_ip_addresses(text)`        | IPv4 addresses                            |
|                          | `extract_checksums(text)`           | Hex checksums (MD5, SHA)                  |
|                          | `extract_cve_ids(text)`             | CVE identifiers                           |
|                          | `extract_version_numbers(text)`     | Version strings (X.Y.Z)                   |
|                          | `extract_patent_numbers(text)`      | Patent numbers                            |
|                          | `extract_isbns(text)`               | ISBN-10 and ISBN-13                       |
| **Text Structure** | `extract_urls(text)`                | HTTP/HTTPS URLs                           |
|                          | `extract_hashtags(text)`            | #hashtags                                 |
|                          | `extract_quotations(text)`          | Quoted strings                            |
|                          | `extract_paragraphs(text)`          | Paragraphs (split by double newline)      |
|                          | `extract_classification_tags(text)` | Tags in [brackets]                        |
| **Numeric**        | `extract_numeric(text)`             | Numeric values                            |
|                          | `extract_numeric_units(text)`       | Numbers with units (10kg, 5m)             |
|                          | `extract_percentages(text)`         | Percentage values                         |
|                          | `extract_dates(text)`               | Dates (DD/MM/YYYY, etc.)                  |
|                          | `extract_times(text)`               | Times (HH:MM, with optional AM/PM)        |
| **Security**       | `extract_passwords(text)`           | Potential password strings                |

All methods return `list[str]` if matches are found, or `None` if no matches / input is `None`.

---

### Text Normalizer Functions

Standalone functions for text preprocessing and data masking.

| Function                                     | Description                                   | Example                                  |
| -------------------------------------------- | --------------------------------------------- | ---------------------------------------- |
| `normalize_text(text, ...)`                | Main normalization with configurable steps    | `"  John, Inc.  "` → `"john inc"`   |
| `mask_text(text, ...)`                     | Mask sensitive text with custom visible parts | `"12345678Z"` → `"12******Z"`       |
| `normalize_whitespace(text)`               | Collapse multiple spaces                      | `"John    Smith"` → `"John Smith"`  |
| `remove_punctuation_marks(text)`           | Remove punctuation marks                      | `"Hello, world!"` → `"Hello world"` |
| `remove_special_characters(text)`          | Keep only alphanumeric                        | `"Test@#123"` → `"Test 123"`        |
| `remove_parentheses_and_content(text)`     | Remove parenthesized content                  | `"A (B)"` → `"A"`                   |
| `strip_quotes(text)`                       | Remove quotation marks                        | `'"Hello"'` → `"Hello"`             |
| `prepare_for_comparison(text, aggressive)` | Convenience wrapper with presets              | See below                                |

#### `mask_text()` Parameters

| Parameter      | Type | Default  | Description                               |
| -------------- | ---- | -------- | ----------------------------------------- |
| `text`       | str  | —       | Text to mask                              |
| `keep_first` | int  | `1`    | Number of characters to keep at the start |
| `keep_last`  | int  | `1`    | Number of characters to keep at the end   |
| `mask_char`  | str  | `"*"`  | Character used for masking                |
| `keep_chars` | str  | `None` | Characters to never mask (e.g.,`"@."`)  |

#### `normalize_text()` Parameters

| Parameter                      | Type | Default   | Description                   |
| ------------------------------ | ---- | --------- | ----------------------------- |
| `text`                       | str  | —        | Text to normalize             |
| `lowercase`                  | bool | `True`  | Convert to lowercase          |
| `remove_punctuation`         | bool | `True`  | Remove punctuation marks      |
| `normalize_whitespace`       | bool | `True`  | Collapse multiple spaces      |
| `remove_accents`             | bool | `False` | Remove diacritical marks      |
| `remove_parentheses_content` | bool | `False` | Remove text in parentheses    |
| `strip_quotes`               | bool | `True`  | Remove quotation marks        |
| `preserve_alphanumeric_only` | bool | `False` | Keep only letters and numbers |

---

### ID Card Parser Functions (`idcard_parser`)

Validation of identification documents for 12 locales, with check-digit verification where applicable.

#### Spanish ID Functions

| Function                                      | Description                                        |
| --------------------------------------------- | -------------------------------------------------- |
| `nif_parse(nif)`                            | Validate any Spanish NIF format (DNI/NIE/CIF)      |
| `nif_padding(p_nif)`                        | Pad incomplete NIF with leading zeros              |
| `nif_letter(p_dni)`                         | Calculate and append DNI/NIE control letter        |
| `is_valid_dni(dni_value)`                   | Validate Spanish DNI format and control letter     |
| `is_valid_nie(nie_value)`                   | Validate Spanish NIE format and control letter     |
| `is_valid_cif(cif_value)`                   | Validate Spanish CIF format and control character  |
| `validate_spanish_nif(nif_type, nif_value)` | Dispatcher: validate by type ('DNI', 'NIE', 'CIF') |
| `european_nif(p_iparse, p_find_letter)`     | Parse and validate European NIFs (28 countries)    |

#### International ID Functions

| Function                         | Country     | Document               |    Check-digit    |
| -------------------------------- | ----------- | ---------------------- | :----------------: |
| `is_valid_ssn(ssn)`            | US          | Social Security Number |    Format rules    |
| `is_valid_cpf(cpf)`            | Brazil      | CPF (Individuals)      |     Modulo-11     |
| `is_valid_cnpj(cnpj)`          | Brazil      | CNPJ (Companies)       | Weighted modulo-11 |
| `is_valid_curp(curp)`          | Mexico      | CURP                   |   Format + regex   |
| `is_valid_rut(rut)`            | Chile       | RUT                    |     Modulo-11     |
| `is_valid_cuil(cuil)`          | Argentina   | CUIL/CUIT              | Weighted checksum |
| `is_valid_nino(nino)`          | UK          | National Insurance No. |    Prefix rules    |
| `is_valid_portuguese_nif(nif)` | Portugal    | NIF                    |     Modulo-11     |
| `is_valid_bsn(bsn)`            | Netherlands | BSN                    |      11-test      |
| `is_valid_codice_fiscale(cf)`  | Italy       | Codice Fiscale         | Odd/even algorithm |

#### Unified Dispatcher

| Function                                       | Description                                        |
| ---------------------------------------------- | -------------------------------------------------- |
| `validate_id_document(id_str, country_code)` | Route to the correct validator by ISO country code |

#### Supported Countries (via `validate_id_document`)

**With check-digit verification**: ES, US, BR, MX, CL, AR, GB, PT, NL, IT.

**With format validation (regex)**: DE, FR, EL, AT, BE, BG, HR, CY, CZ, DK, EE, FI, HU, IE, LV, LT, LU, MT, PL, RO, SK, SI, SE.

---

### Names Parser Functions

Parsing and formatting person and company names.

| Function                                                       | Description                                   |
| -------------------------------------------------------------- | --------------------------------------------- |
| `arrange_fullname(input_name)`                               | Rearrange "Last, First" → "First Last"       |
| `format_name(input_string, add_charset, format_type, upper)` | Clean and format a name string                |
| `parse_company(input_string, legal_forms)`                   | Extract company name and legal form           |
| `format_companyname(company_name, company_type, format)`     | Format company with legal form style          |
| `get_companyname(company_name, company_type)`                | Extract clean company name without legal form |
| `get_companytype(input_string)`                              | Extract legal form from company name          |
| `isformat_company(input_string)`                             | Check if string matches a company format      |

#### Company Legal Form Formats

The `format_companyname` function supports three formatting styles:

| Format           | Example               |
| ---------------- | --------------------- |
| `'brackets'`   | `EMPRESA ABC (SL)`  |
| `'dots'`       | `EMPRESA ABC S.L.`  |
| `'comma&dots'` | `EMPRESA ABC, S.L.` |

---

### LanguageNormalizer

Language-aware text normalization with extensible rules.

#### Constructor

```python
LanguageNormalizer(language='es', case_sensitive=False, remove_accents=True)
```

#### Methods

| Method                                                  | Description                                 |
| ------------------------------------------------------- | ------------------------------------------- |
| `normalize(text, language=None)`                      | Normalize text with language-specific rules |
| `register_rule(language, rule_func, name=None)`       | Add custom normalization rule               |
| `register_abbreviation(language, pattern, expansion)` | Add custom abbreviation                     |
| `get_supported_languages()`                           | List supported language codes               |
| `clear_rules(language=None)`                          | Clear custom rules                          |

#### Built-in Abbreviations

**Spanish**: `Ma.` → María, `Ma. P.` → María Pilar, `J. M.` → José María, `Sr.` → Señor, `Dra.` → Doctora, etc.

**English**: `St.` → Street, `Ave.` → Avenue, `Blvd.` → Boulevard, `Apt.` → Apartment, etc.

**Portuguese**: `Sr.` → Senhor, `Sra.` → Senhora, `Dr.` → Doutor, `Av.` → Avenida, `R.` → Rua, etc.

**French**: `M.` → Monsieur, `Mme.` → Madame, `Mlle.` → Mademoiselle, `Av.` → Avenue, `Bd.` → Boulevard, `Sté.` → Société, etc.

**German**: `Hr.` → Herr, `Fr.` → Frau, `Dr.` → Doktor, `Str.` → Straße, `Nr.` → Nummer, `GmbH` → Gesellschaft mit beschränkter Haftung, etc.

**Italian**: `Sig.` → Signore, `Sig.ra` → Signora, `Dott.` → Dottore, `Avv.` → Avvocato, `V.` → Via, `P.za` → Piazza, etc.

---

### EncodingFixer (Universal Mojibake Repair)

Language-independent encoding recovery. Detects and repairs garbled text (mojibake) caused by codepage mismatches.

#### Constructor

```python
EncodingFixer(language=None)
```

**Parameters:**

- `language` (str, optional): Language hint (`'es'`, `'en'`, `'pt'`, `'fr'`, `'de'`, `'it'`). Improves scoring when choosing between ambiguous decodings.

#### Supported Encoding Pairs

Recovery is attempted for the most common Western-European codepage mismatches:

| # | Misread as            | Actual encoding | Typical symptom                              |
| - | --------------------- | --------------- | -------------------------------------------- |
| 1 | Windows-1252          | UTF-8           | `Ã¡`, `Ã±`, `Ã¼`, `ÃŸ`       |
| 2 | Latin-1 (ISO-8859-1)  | UTF-8           | Same visual but with C1 control chars        |
| 3 | Latin-9 (ISO-8859-15) | UTF-8           | Like Latin-1 but with `€`, `œ`, `Ž` |
| 4 | CP850 (DOS OEM)       | UTF-8           | Different garbled characters                 |
| 5 | CP437 (DOS US)        | UTF-8           | Box-drawing characters instead of accents    |

#### Pipeline

The `fix()` method applies a 5-step recovery pipeline:

| Step | Strategy                      | What it fixes                                                                   |
| ---- | ----------------------------- | ------------------------------------------------------------------------------- |
| 1    | **Pattern replacement** | Known mojibake sequences → correct chars (handles partial mojibake)            |
| 2    | **Full re-decode**      | Re-encode with candidate codepage, decode as UTF-8 (handles fully garbled text) |
| 3    | **Double-encoding**     | Second pattern pass for text garbled twice                                      |
| 4    | **Quote normalisation** | Optional: curly quotes → straight, em-dash → hyphen                           |
| 5    | **Control cleanup**     | Remove stray C0/C1 control characters                                           |

#### Methods

| Method                                | Description                                                        |
| ------------------------------------- | ------------------------------------------------------------------ |
| `fix(text, normalize_quotes=False)` | Repair mojibake in text                                            |
| `has_mojibake(text)`                | Check if text contains mojibake patterns                           |
| `detect(text)`                      | Diagnostic report (encoding pair, sequences found, quality scores) |

#### How It Works (vs per-language functions)

The per-language `fix_XX_conversion_fails` functions use a **manual** map of ~15 mojibake patterns plus a charset allow-list that **strips** unrecognised characters. `EncodingFixer` instead:

1. **Generates the map programmatically** from the Unicode / codepage tables — covering **every** character in the Latin Supplement (U+0080-U+00FF), Latin Extended-A, and common typographic range automatically.
2. **Tries multiple encoding pairs**, not just `latin-1 → utf-8`.
3. **Handles double-encoded** UTF-8 (the file went through the garbling twice).
4. **Is non-destructive** — fixes only the garbled bytes, never strips valid characters.
5. **Works across all languages** with a single code path.

---

### Phonetic Reduction (all languages)

Progressive phonetic transformation levels for fuzzy matching. Each language has its own `reduce_letters_XX`, `remove_XX_articles`, `fix_XX_conversion_fails`, and `raw_string_XX` functions.

#### Reduction Levels

| Level | Description         | Spanish                     | English                        | Portuguese                      | French                        | German                       | Italian                  |
| ----- | ------------------- | --------------------------- | ------------------------------ | ------------------------------- | ----------------------------- | ---------------------------- | ------------------------ |
| 0     | Only remove accents | `José` → `Jose`       | `café` → `cafe`          | `João` → `Joao`           | `François` → `Francois` | `Müller` → `Muller`    | `Città` → `Citta`  |
| 1     | Basic phonetics     | `García` → `JARSIA`   | `Knight` → `NIGT`         | `Silva` → `SILVA`          | `Philippe` → `FILIPE`    | `Straße` → `STRASSE`   | `Gnocchi` → `NIOCI` |
| 2     | Intermediate        | `Ximénez` → `SIMENES` | `Psychology` → `SYSOLOGY` | `Gonçalves` → `GONSALVES` | `François` → `FRENSOAS` | `Schneider` → `SNEIDER` | `Chiara` → `CIARA`  |
| 3     | Aggressive          | `Ñoño` → `NONO`      | `William` → `VILLIAM`     | Full international              | Full international            | `Knecht` → `NECT`       | Full international       |

#### Helper Functions per Language

| Language             | Remove articles                      | Fix encoding                              | Phonetic reduction                            | Raw string                                |
| -------------------- | ------------------------------------ | ----------------------------------------- | --------------------------------------------- | ----------------------------------------- |
| **Spanish**    | `remove_spanish_articles(text)`    | `fix_spanish_conversion_fails(text)`    | `reduce_letters_spanish(text, strength)`    | `raw_string_spanish(text, accuracy)`    |
| **English**    | `remove_english_articles(text)`    | `fix_english_conversion_fails(text)`    | `reduce_letters_english(text, strength)`    | `raw_string_english(text, accuracy)`    |
| **Portuguese** | `remove_portuguese_articles(text)` | `fix_portuguese_conversion_fails(text)` | `reduce_letters_portuguese(text, strength)` | `raw_string_portuguese(text, accuracy)` |
| **French**     | `remove_french_articles(text)`     | `fix_french_conversion_fails(text)`     | `reduce_letters_french(text, strength)`     | `raw_string_french(text, accuracy)`     |
| **German**     | `remove_german_articles(text)`     | `fix_german_conversion_fails(text)`     | `reduce_letters_german(text, strength)`     | `raw_string_german(text, accuracy)`     |
| **Italian**    | `remove_italian_articles(text)`    | `fix_italian_conversion_fails(text)`    | `reduce_letters_italian(text, strength)`    | `raw_string_italian(text, accuracy)`    |

French and Italian also handle elided articles (`l'`, `d'`, `dell'`, etc.) in article removal.

---

### Standalone Utility

```python
from shadetriptxt.text_parser.text_extract import get_string_between

result = get_string_between("El texto 'entre comillas' es importante.", "'")
# Returns: "entre comillas"
```

---

## Use Cases

### 1. Data Cleansing Pipeline

```python
from shadetriptxt.text_parser.text_extract import TextExtractor
from shadetriptxt.text_parser.text_normalizer import normalize_text

extractor = TextExtractor()

raw = "Contact: Juan García (+34) 91-303-20-60, email: juan.garcia@empresa.com"

phones = extractor.extract_phones(raw)       # ['34913032060']
emails = extractor.extract_emails(raw)       # ['juan.garcia@empresa.com']
clean  = normalize_text(raw, remove_accents=True)  # "contact juan garcia +34 91-303-20-60 email juan.garcia@empresa.com"
```

### 2. Identity Resolution

```python
from shadetriptxt.text_parser.names_parser import arrange_fullname, parse_company
from shadetriptxt.text_parser.idcard_parser import nif_parse, european_nif

# Standardize name formats
name = arrange_fullname("García López, José")   # "José García López"

# Validate identification
nif = nif_parse("B84761857")                     # "B84761857" (valid CIF)
eu  = european_nif("DE123456789", False)         # ('NIF', 'GERMANY', 'DE', '123456789')
```

### 3. Fuzzy Name Matching Preparation

```python
from shadetriptxt.text_parser.spanish_parser import raw_string_spanish
from shadetriptxt.text_parser.language_normalizer import LanguageNormalizer

# Prepare strings for fuzzy comparison
a = raw_string_spanish("José María García-López", 2)
b = raw_string_spanish("Jose Maria Garsia Lopes", 2)
# Both produce similar phonetic representations for accurate matching
```

### 4. Custom Language Rules

```python
from shadetriptxt.text_parser.language_normalizer import LanguageNormalizer

normalizer = LanguageNormalizer(language='es')

# Add business suffix normalization
def normalize_business(text):
    return text.replace("s.l.", "sociedad limitada")

normalizer.register_rule('es', normalize_business)
normalizer.register_abbreviation('es', r'\bC/\b', 'Calle')

result = normalizer.normalize("Empresa C/ Mayor, S.L.")
# Returns: "empresa calle mayor sociedad limitada"
```

### 5. Encoding Recovery (Data Migration)

```python
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer

fixer = EncodingFixer(language='es')

# CSV exported from a legacy database with CP1252 → UTF-8 mismatch
records = [
    "GarcÃ­a LÃ³pez, JosÃ©",
    "SeÃ±or MuÃ±oz",
    "NiÃ±o de la CrÃºz",
]

clean = [fixer.fix(r) for r in records]
# ['García López, José', 'Señor Muñoz', 'Niño de la Crúz']

# Detect before fixing — useful for auditing incoming data
report = fixer.detect("GarcÃ­a")
# {'has_mojibake': True, 'likely_pair': ('cp1252', 'utf-8'), ...}
```

### 6. International ID Validation

```python
from shadetriptxt.text_parser.idcard_parser import validate_id_document

# Validate IDs from different countries in a single pipeline
incoming = [
    ("12345678Z", "ES"),   # Spanish DNI
    ("123-45-6789", "US"), # US SSN
    ("123.456.789-09", "BR"),  # Brazilian CPF
    ("RSSMRA85M01H501Z", "IT"),  # Italian Codice Fiscale
    ("12.345.678-5", "CL"),  # Chilean RUT
]

for id_str, country in incoming:
    result = validate_id_document(id_str, country)
    print(f"{country}: {id_str} → {'Valid' if result else 'Invalid'}")
```

### 7. Multi-Locale Processing

```python
from shadetriptxt.text_parser.text_parser import TextParser

# Process international records, each with its own locale
locales = {
    "es_ES": "Llamar a Fco. García al +34 91 303 20 60. DNI: 12345678Z",
    "en_US": "Contact J. Smith at 123 Main St. SSN: 123-45-6789",
    "pt_BR": "Sr. Silva, Av. Paulista 1000. CPF: 123.456.789-09",
    "de_DE": "Hr. Müller, Str. 5. Tel: +49 30 1234567",
}

for locale, text in locales.items():
    parser = TextParser(locale)
    print(f"[{locale}] Normalized: {parser.normalize(text)}")
    print(f"[{locale}] Phones:     {parser.extract_phones(text)}")
    print(f"[{locale}] IDs:        {parser.extract_ids(text)}")
```

### 8. PII Extraction for Compliance Auditing

```python
from shadetriptxt.text_parser.text_extract import TextExtractor
from shadetriptxt.text_parser.text_normalizer import mask_text

extractor = TextExtractor()

document = """
Paciente: Juan García (PAT-12345)
DNI: 12345678Z
Email: juan.garcia@hospital.com
Tel: +34 600 606 060
IBAN: ES91 2100 0418 4502 0005 1332
"""

# Detect all PII in unstructured text
phones = extractor.extract_phones(document)        # ['+34600606060']
emails = extractor.extract_emails(document)        # ['juan.garcia@hospital.com']
ibans  = extractor.extract_ibans(document)         # ['ES9121000418450200051332']
nifs   = extractor.extract_nif(document)           # ['12345678Z']
pids   = extractor.extract_patient_ids(document)   # ['PAT-12345']

# Mask sensitive values for logging
for email in emails:
    print(mask_text(email, keep_first=2, keep_last=4, keep_chars="@."))
    # "ju*********..com"
```

## Performance

All extraction and normalization functions are **O(n)** in the length of the input string. Regex patterns in `TextExtractor` are pre-compiled for efficiency.

## Example Scripts

Runnable scripts in `examples/`:

| Script                            | Description                                                                   |
| --------------------------------- | ----------------------------------------------------------------------------- |
| `example_normalization.py`        | Text normalization pipeline and its integration with `TextMatcher`             |
| `example_custom_transforms.py`    | Register and run user-defined text transforms (`register_custom`, `run_custom`) |
| `example_config.py`               | Configuration module: defaults, env vars, schema validation, sample file       |

## Related Documentation

| Document                                                    | Description                                                                         |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [Technical Reference](README_TextParser_Technical_Reference.md) | Complete API reference — all functions, parameters, returns, and cost              |
| [EncodingFixer](README_EncodingFixer.md)                       | In-depth guide to mojibake detection and repair (pipeline, scoring, encoding pairs) |
| [Normalization Reference](README_Normalization.md)             | Normalization engine reference — what gets normalized, pipeline order, parameters  |
| [TextMatcher Integration](README_TextMatcher_Integration.md)   | Cross-reference to normalization integration with `TextMatcher`                   |
| [TextMatcher](../text_matcher/README.md)                       | Fuzzy text comparison, deduplication, and name matching                             |
| [TextAnonymizer](../text_anonymizer/README_TextAnonymizer.md)  | PII detection and anonymization (uses `text_parser` for extraction)               |
| [TextDummy](../text_dummy/README.md)                           | Fake data generation (shares locale profiles with `text_parser`)                  |

## Dependencies

- Python standard library (`re`, `unicodedata`, `typing`)
- Internal utilities:
  - `shadetriptxt.utils.string_ops` — accent removal, character cleaning (used by `names_parser`, `text_extract`)
  - `shadetriptxt.utils.similarity_engines` — core similarity algorithms (used indirectly via `string_similarity`)
  - `shadetriptxt.utils.string_similarity` — high-level similarity API (`WordSimilarity`, `are_words_equivalent`)

## License

Part of the `shadetriptxt` library by DatamanEdge.
