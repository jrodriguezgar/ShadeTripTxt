# shadetriptxt

> A Python library for text validation, data cleaning, fuzzy matching, fake data generation, and PII detection & anonymization across 12 locales.

![Version](https://img.shields.io/badge/version-0.0.1-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## What's Inside

### 🔍 TextMatcher — Enterprise Fuzzy Matching

Production-ready text comparison for **identity resolution, deduplication, and fuzzy search**. Compare names, phrases, and full texts using 6 algorithms (Levenshtein, Jaro-Winkler, Metaphone, MRA, LCS, Sørensen-Dice) with automatic algorithm selection, intelligent caching, and parallel batch processing. Handles abbreviations, accents, and word reordering transparently across 6 languages. → [Full docs](shadetriptxt/text_matcher/README.md)

### 🧹 TextParser — Locale-Aware Text Processing

Comprehensive extraction, normalization, and parsing toolkit that solves the messy reality of text data: **inconsistent casing, accents, name orderings, encoding corruption, and format variations**. Includes 25+ regex extractors (phones, emails, IBANs, dates, IPs…), ID validation for 28 countries, phonetic reduction for 6 languages, abbreviation expansion, and universal mojibake repair — all configurable per locale. → [Full docs](shadetriptxt/text_parser/README.md)

### 🎭 TextDummy — Fake Data Generation

Generate **realistic, locale-aware synthetic data** for testing and development. 60+ data types across 12 locales — from personal data and IDs to financial info, vehicles, and products. Auto-fill Pydantic models, generate batches, register custom types, and export as records or DataFrame-ready columns. Reproducible output with seed support. → [Full docs](shadetriptxt/text_dummy/README.md)

### 🔒 TextAnonymizer — PII Detection & Anonymization

Detect and anonymize Personally Identifiable Information with a **single entry point**. Combines regex detection (15 PII types, 12 locales), spaCy NER, and NLTK as detection engines. Apply 7 strategies per PII type (redact, mask, replace, hash, generalize, pseudonymize, suppress). Includes DataFrame anonymization with **k-anonymity, l-diversity, and t-closeness** privacy metrics. → [Full docs](shadetriptxt/text_anonymizer/README_TextAnonymizer.md)

## Why shadetriptxt?

- **All-in-one text toolkit** — matching, parsing, anonymization, and fake data in a single library. No need to glue together dozens of packages.
- **12 locales, 6 languages** — first-class support for Spanish, English, Portuguese, French, German, and Italian with locale-specific ID validation, phonetic reduction, and abbreviation expansion.
- **Multi-algorithm fuzzy matching** — Levenshtein, Jaro-Winkler, Metaphone, MRA, LCS, and Sørensen-Dice with automatic algorithm selection based on your use case.
- **GDPR-ready anonymization** — 7 strategies (redact, mask, replace, hash, generalize, pseudonymize, suppress) with k-anonymity, l-diversity, and t-closeness metrics built in.
- **28-country ID validation** — Spanish DNI/NIE/CIF, European NIFs, US SSN, Brazilian CPF, and more — all in one module.
- **60+ fake data types** — generate realistic locale-aware data with Pydantic model auto-filling, batch generation, and custom type registration.
- **Zero config** — works out of the box. No config files, no environment variables, no setup ceremony.
- **Mojibake repair** — automatic detection and fix of encoding corruption (`Ã¡rbol` → `árbol`).
- **Lightweight core** — only 2 runtime dependencies (`flashtext`, `faker`). Heavy NLP libraries (spaCy, NLTK) are optional.

## Table of Contents

- [What's Inside](#whats-inside)
- [Why shadetriptxt?](#why-shadetriptxt)
- [Modules](#modules)
- [Usage](#usage)
- [CLI](#cli)
- [Configuration](#configuration)
- [License](#license)
- [Contact](#contact)
- [Dependencies](#dependencies)

## Modules

| Module              | Description                                                                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text_matcher`    | Fuzzy text comparison, best-match finding, duplicate detection. See[TextMatcher docs](shadetriptxt/text_matcher/README.md)                                    |
| `text_parser`     | Text normalization, name parsing, NIF/DNI validation (28 countries), encoding repair. See[TextParser docs](shadetriptxt/text_parser/README.md)                |
| `text_dummy`      | Locale-aware fake data generation (60+ data types, 12 locales, Pydantic model filling). See[TextDummy docs](shadetriptxt/text_dummy/README.md)                |
| `text_anonymizer` | PII detection & anonymization with 7 strategies (regex, spaCy, NLTK engines). See[TextAnonymizer docs](shadetriptxt/text_anonymizer/README_TextAnonymizer.md) |

## Usage

### Locale-Aware Parsing

```python
from shadetriptxt.text_parser.text_parser import TextParser

parser = TextParser("es_ES")
parser.normalize("Ma. P. García")      # "maria pilar garcia"
parser.extract_ids("DNI 12345678Z")    # ['12345678Z']
```

### Text Matching

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher

matcher = TextMatcher()

# Single name comparison
is_match, metrics = matcher.compare_names("José García", "Jose Garcia")

# Multi-word name comparison with token alignment
is_match, metrics = matcher.compare_name_bytokens(
    "Juan García López", "Garcia Lopez Juan", keep_order=False
)

# Find best match from candidates
best, score, metrics = matcher.find_best_match("Smithe", ["Smith", "Jones", "Smyth"])

# Duplicate detection
duplicates = matcher.detect_duplicates(["apple", "aple", "banana", "bananna"], threshold=0.8)
```

### ID Validation (Spanish / US / Brazil)

```python
from shadetriptxt.text_parser.idcard_parser import nif_parse, is_valid_cpf, is_valid_ssn

# Spanish DNI
nif_parse("12345678Z")    # "12345678Z"

# Brazil CPF
is_valid_cpf("123.456.789-09")  # True

# US SSN
is_valid_ssn("123-45-6789")     # True
```

### Fake Data Generation

```python
from shadetriptxt.text_dummy.text_dummy import TextDummy

# Spanish data (default)
gen = TextDummy("es_ES")
gen.name()              # "María García López"
gen.id_document()       # "45678123P"
gen.iban()              # "ES9121000418450200051332"
gen.product_name()      # "Premium Keyboard"

# US data
gen_us = TextDummy("en_US")
gen_us.id_document()    # "456-78-1234"
gen_us.credit_card_number()

# Batch generation
gen.generate_batch("email", count=5)

# Custom types
gen.register_custom_type("priority", ["Low", "Medium", "High", "Critical"])
gen.generate_batch("priority", count=10)

# Pydantic model auto-filling
from pydantic import BaseModel
from typing import Annotated
from shadetriptxt.text_dummy.text_dummy import DummyField

class Employee(BaseModel):
    code: Annotated[str, DummyField("uuid4")]
    name: str
    email: str

employee = gen.fill_model(Employee)
batch = gen.fill_model_batch(Employee, count=100)
```

### Text Extraction

```python
from shadetriptxt.text_parser.text_extract import TextExtractor

extractor = TextExtractor()
extractor.extract_emails("Contact us at info@example.com or sales@example.com")
extractor.extract_phones("Call +34 612 345 678")
```

### Encoding Repair

```python
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer

fixer = EncodingFixer(language="es")
fixer.fix("Ã¡rbol")           # "árbol"
fixer.detect("espaÃ±ol")      # Encoding diagnostics
```

### PII Anonymization

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale="es_ES", strategy="pseudonymize", seed=42)
result = anon.anonymize_text("DNI: 12345678Z, email: juan@test.com")
# result.anonymized, result.entities, result.replacements

# Per-type strategy
anon.set_strategy("mask", pii_type="EMAIL")
anon.set_strategy("hash", pii_type="ID_DOCUMENT")

# Detection with multiple engines
entities = anon.detect_pii(text, use_regex=True, use_spacy=True, use_nltk=True)
```

## CLI

Each module includes a CLI interface via `python -m`:

```bash
python -m shadetriptxt.text_parser.cli --help
python -m shadetriptxt.text_matcher.cli --help
python -m shadetriptxt.text_dummy.cli --help
python -m shadetriptxt.text_anonymizer.cli --help
```

See individual CLI docs: [TextParser CLI](shadetriptxt/text_parser/README_CLI.md) · [TextMatcher CLI](shadetriptxt/text_matcher/README_CLI.md) · [TextDummy CLI](shadetriptxt/text_dummy/README_CLI.md) · [TextAnonymizer CLI](shadetriptxt/text_anonymizer/README_CLI.md)

## Configuration

shadetriptxt works out of the box with no configuration files required. Module behavior is controlled through constructor parameters and method arguments:

| Parameter    | Module                                            | Description                                                                              | Default                     |
| ------------ | ------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------- |
| `locale`   | `TextParser`, `TextDummy`, `TextAnonymizer` | ISO locale code (e.g.`es_ES`, `en_US`)                                               | `es_ES`                   |
| `config`   | `TextMatcher`                                   | `MatcherConfig` with preset profiles (`.strict()`, `.lenient()`, `.fuzzy()`)     | `MatcherConfig.default()` |
| `strategy` | `TextAnonymizer`                                | Anonymization strategy (redact, mask, replace, hash, generalize, pseudonymize, suppress) | `redact`                  |
| `seed`     | `TextAnonymizer`                                | Reproducible pseudonymization seed                                                       | `None`                    |
| `language` | `EncodingFixer`, `LanguageNormalizer`         | ISO 639-1 language code                                                                  | `None`                    |

## License

MIT © 2025 DatamanEdge. See [LICENSE](LICENSE).

## Contact

- **Author**: [DatamanEdge](https://github.com/DatamanEdge)
- **Email**: [jrodriguezga@outlook.com](mailto:jrodriguezga@outlook.com)
- **LinkedIn**: [Javier Rodríguez](https://es.linkedin.com/in/javier-rodriguez-ga)

## Dependencies

### Core

| Package                                                       | Min Version | Description          |
| ------------------------------------------------------------- | ----------- | -------------------- |
| [`flashtext`](https://pypi.org/project/flashtext/)             | 2.7         | Keyword processing   |
| [`faker`](https://pypi.org/project/Faker/)                     | 20.0.0      | Fake data generation |

### Optional (`pip install ".[anonymizer]"`)

| Package                                                         | Min Version | Description              |
| --------------------------------------------------------------- | ----------- | ------------------------ |
| [`spacy`](https://pypi.org/project/spacy/)                       | 3.5.0       | NLP-based PII detection  |
| [`nltk`](https://pypi.org/project/nltk/)                         | 3.8.0       | Named entity recognition |
| [`pandas`](https://pypi.org/project/pandas/)                     | 1.5.0       | DataFrame anonymization  |
| [`python-anonymity`](https://pypi.org/project/python-anonymity/) | 0.0.1       | k-anonymity, l-diversity |
| [`pycanon`](https://pypi.org/project/pycanon/)                   | 1.0.0       | Privacy metrics          |
