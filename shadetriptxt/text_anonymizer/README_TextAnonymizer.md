# Text Anonymizer

**Personal Identificable Information detection & data anonymization** — detect and anonymize Personally Identifiable Information in text and tabular data. Locale-aware (12 countries), with multiple anonymization strategies.

`TextAnonymizer` is the **central hub** for all anonymization techniques in shadetriptxt. It wraps both internal shadetriptxt modules and external libraries, so you can manage every anonymization task from a single entry point:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TextAnonymizer                                │
│                   (punto único de anonimización)                     │
│                                                                      │
│   ┌─────────────────── Módulos internos ──────────────────────┐     │
│   │                                                            │     │
│   │  TextDummy ─── generación datos falsos (replace,          │     │
│   │                 pseudonymize, id_document, iban...)        │     │
│   │                                                            │     │
│   │  TextParser ── normalización, extracción, mask_text       │     │
│   │                                                            │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│   ┌─────────────────── Librerías externas ────────────────────┐     │
│   │                                                            │     │
│   │  spaCy ────── NER: nombres, ubicaciones, organizaciones   │     │
│   │  NLTK ─────── NER fallback                                │     │
│   │  python-anonymity ─ k-anonymity, l-diversity, t-closeness │     │
│   │  pycanon ──── métricas de privacidad                      │     │
│   │                                                            │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│   ┌─────────────────── Técnicas propias ──────────────────────┐     │
│   │                                                            │     │
│   │  mask, redact, hash, generalize, suppress                 │     │
│   │  Regex PII detection (15 tipos, 12 locales)               │     │
│   │  Per-type strategy dispatch                               │     │
│   │  Pseudonymization cache                                   │     │
│   │                                                            │     │
│   └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

This architecture means you **don't need to import TextDummy or TextParser directly** for anonymization workflows — `TextAnonymizer` delegates to them internally.

## Quick Start

```python
from shadetriptxt.text_anonymizer import anonymize_text, detect_pii, anonymize_dict

# Anonymize free text
result = anonymize_text("Contactar a Juan García, DNI 12345678Z, email juan@test.com")
print(result.anonymized)
# → "Contactar a Juan García, DNI [ID_DOCUMENT], email [EMAIL]"

# Detect PII entities
entities = detect_pii("SSN: 123-45-6789, phone (555) 123-4567", locale="en_US")
for e in entities:
    print(f"  {e.pii_type.value}: {e.text}")

# Anonymize a dictionary record
record = {"name": "María López", "email": "maria@test.com", "age": 30}
anon = anonymize_dict(record, strategy="mask")
# → {"name": "M**** L****", "email": "m****@****.***", "age": 30}
```

## Installation & Dependencies

The base `TextAnonymizer` (regex detection + all 7 strategies) works with the core shadetriptxt install — no extra packages needed.

For NLP detection and DataFrame anonymization, install the optional group:

```bash
pip install shadetriptxt[anonymizer]
```

| Package | Version | Purpose | Required? |
|---------|---------|---------|-----------|
| `shadetriptxt.text_dummy` | — | Locale-aware fake data for `replace` and `pseudonymize` strategies | **Yes** (internal) |
| `shadetriptxt.text_parser` | — | Text normalization, extraction, masking (`mask_text`) | **Yes** (internal) |
| `spacy` | ≥ 3.5.0 | NER detection of names, locations, organizations in free text | No — only with `use_spacy=True` |
| `nltk` | ≥ 3.8.0 | NER fallback when spaCy is not available | No — only with `use_nltk=True` |
| `python-anonymity` | ≥ 0.0.1 | k-anonymity, l-diversity, t-closeness on DataFrames | No — only for `anonymize_dataframe()` |
| `pycanon` | ≥ 1.0.0 | Privacy metric measurement (k, l, t verification) | No — only for `measure_privacy()` |
| `pandas` | ≥ 1.5.0 | DataFrame operations | No — only for DataFrame functions |

All optional dependencies use **lazy loading**: they are imported only when their specific functionality is invoked. If a dependency is missing, an `ImportError` is raised with clear installation instructions.

**spaCy models** must be downloaded separately for each locale:

```bash
python -m spacy download es_core_news_sm   # Spanish
python -m spacy download en_core_web_sm    # English
python -m spacy download pt_core_news_sm   # Portuguese
python -m spacy download fr_core_news_sm   # French
python -m spacy download de_core_news_sm   # German
python -m spacy download it_core_news_sm   # Italian
```

## Features

| Feature                      | Description                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| **Central Hub**        | Wraps TextDummy, TextParser, and external libraries from a single API              |
| **PII Detection**      | Regex patterns (universal + locale-specific)                                       |
| **NLP Detection**      | spaCy NER and NLTK NER (lazy-loaded)                                               |
| **7 Strategies**       | redact, mask, replace, hash, generalize, pseudonymize, suppress                    |
| **12 Locales**         | es_ES, es_MX, es_AR, es_CO, es_CL, en_US, en_GB, pt_BR, pt_PT, fr_FR, de_DE, it_IT |
| **Text Anonymization** | Free-text PII detection and replacement                                            |
| **Dict/Records**       | Auto-detect PII fields by name                                                     |
| **DataFrame**          | Column-level anonymization and k-anonymity                                         |
| **Privacy Metrics**    | k-anonymity, l-diversity, t-closeness (pycanon)                                    |
| **Custom Patterns**    | Register your own regex patterns                                                   |
| **Per-type Strategy**  | Different strategy per PII type                                                    |

## PII Types Detected

| PiiType          | Examples                                           | Detection                              |
| ---------------- | -------------------------------------------------- | -------------------------------------- |
| `NAME`         | Juan García, John Smith                           | spaCy/NLTK NER                         |
| `EMAIL`        | user@domain.com                                    | Regex (universal)                      |
| `PHONE`        | +34 612 345 678, (555) 123-4567                    | Regex (locale-specific)                |
| `ID_DOCUMENT`  | DNI 12345678Z, SSN 123-45-6789, CPF 123.456.789-09 | Regex (locale-specific)                |
| `CREDIT_CARD`  | 4111 1111 1111 1111                                | Regex (Visa/MC/Amex/Discover prefixes) |
| `IBAN`         | ES91 2100 0418 4502 0005 1332                      | Regex (universal)                      |
| `IP_ADDRESS`   | 192.168.1.100                                      | Regex (universal)                      |
| `URL`          | https://example.com                                | Regex (universal)                      |
| `DATE`         | 15/03/1990, 2024-01-15                             | Regex (universal)                      |
| `CURRENCY`     | €1.234,56 / $100.00                               | Regex (universal)                      |
| `LOCATION`     | Madrid, New York                                   | spaCy/NLTK NER                         |
| `ORGANIZATION` | Acme Corp                                          | spaCy/NLTK NER                         |
| `CUSTOM`       | (user-defined patterns)                            | Regex (custom)                         |

## Anonymization Strategies

### REDACT

Replace PII with a type label.

```python
result = anonymize_text("Email: juan@test.com", strategy="redact")
# → "Email: [EMAIL]"
```

### MASK

Partially hide characters while preserving structure.

```python
result = anonymize_text("Email: juan@test.com", strategy="mask")
# → "Email: j***@****.***"
```

### HASH

Replace with a truncated SHA-256 hash.

```python
result = anonymize_text("DNI: 12345678Z", strategy="hash")
# → "DNI: 1c9f96328944"
```

### REPLACE

Replace with realistic locale-aware fake data (powered by TextDummy).

```python
result = anonymize_text("Email: juan@test.com", strategy="replace")
# → "Email: maria.gomez@example.org"
```

### PSEUDONYMIZE

Consistent replacement — same input always produces the same output.

```python
anon = TextAnonymizer(strategy="pseudonymize", seed=42)
r = anon.anonymize_text("juan@test.com y juan@test.com")
# Both instances get the same replacement
```

### GENERALIZE

Reduce precision while preserving utility.

```python
result = anonymize_text("Nacido el 15/03/1990", strategy="generalize")
# → "Nacido el 1990"
```

### SUPPRESS

Remove PII completely.

```python
result = anonymize_text("Email: juan@test.com fin", strategy="suppress")
# → "Email:  fin"
```

## Detection Engines

### Regex (default, always available)

```python
anon = TextAnonymizer(locale="es_ES")
entities = anon.detect_pii(text, use_regex=True)
```

### spaCy NER (lazy-loaded)

Requires a spaCy model installed for the locale:

```bash
python -m spacy download es_core_news_sm  # Spanish
python -m spacy download en_core_web_sm   # English
```

```python
entities = anon.detect_pii(text, use_spacy=True)
```

### NLTK NER (lazy-loaded)

Downloads required NLTK resources automatically on first use:

```python
entities = anon.detect_pii(text, use_nltk=True)
```

### Combined

```python
entities = anon.detect_pii(text, use_regex=True, use_spacy=True, use_nltk=True)
```

## Per-Type Strategies

```python
anon = TextAnonymizer(strategy="redact")
anon.set_strategy("mask", pii_type="EMAIL")
anon.set_strategy("replace", pii_type="NAME")
# Emails get masked, names get replaced, everything else is redacted
```

## Custom Patterns

```python
anon = TextAnonymizer()
anon.add_pattern("employee_id", r"EMP-\d{4}")
entities = anon.detect_pii("Empleado EMP-1234 en oficina")
# Detects EMP-1234 as PiiType.CUSTOM
```

## Dictionary & Records

### Auto-detect fields by name

```python
record = {"name": "Juan", "email": "juan@test.com", "age": 30}
result = anonymize_dict(record, strategy="redact")
# → {"name": "[NAME]", "email": "[EMAIL]", "age": 30}
```

### Explicit field types

```python
result = anonymize_dict(
    {"codigo": "12345678Z"},
    field_types={"codigo": PiiType.ID_DOCUMENT},
)
```

### Field whitelist (`fields`)

By default, all fields matching the auto-detection map are anonymized. Use `fields` to restrict anonymization to **only** the specified fields — everything else is left untouched:

```python
record = {"nombre": "Juan", "email": "juan@test.com", "telefono": "+34 612 345 678", "salario": 45000}

# Without fields: nombre, email, and telefono are all anonymized
result = anonymize_dict(record, strategy="redact")
# → {"nombre": "[NAME]", "email": "[EMAIL]", "telefono": "[PHONE]", "salario": 45000}

# With fields: only email and telefono are anonymized
result = anonymize_dict(record, strategy="redact", fields=["email", "telefono"])
# → {"nombre": "Juan", "email": "[EMAIL]", "telefono": "[PHONE]", "salario": 45000}
```

Combine with `field_types` for non-standard field names:

```python
result = anon.anonymize_dict(
    {"codigo_empleado": "12345678Z", "nombre": "Ana", "notas": "texto libre"},
    fields=["codigo_empleado"],
    field_types={"codigo_empleado": PiiType.ID_DOCUMENT},
)
# → {"codigo_empleado": "[ID_DOCUMENT]", "nombre": "Ana", "notas": "texto libre"}
```

Works the same way on `anonymize_records` and `anonymize_columns`:

```python
# Records
anon.anonymize_records(records, fields=["email", "telefono"])

# DataFrame
anon.anonymize_columns(df, columns=["email", "telefono"])
```

### Batch records

```python
records = [
    {"name": "Ana", "email": "ana@test.com"},
    {"name": "Pedro", "email": "pedro@test.com"},
]
anon = TextAnonymizer(strategy="mask")
results = anon.anonymize_records(records)
```

**Auto-detected field names** (and Spanish aliases):

| Field names                                              | PII Type     |
| -------------------------------------------------------- | ------------ |
| name, nombre, full_name, first_name, last_name, apellido | NAME         |
| email, correo, mail                                      | EMAIL        |
| phone, telefono, mobile, tel                             | PHONE        |
| address, direccion, street, postcode, zip                | ADDRESS      |
| dni, nif, ssn, passport, curp, cpf                       | ID_DOCUMENT  |
| credit_card, tarjeta, card_number                        | CREDIT_CARD  |
| iban, bban                                               | IBAN         |
| ip, ip_address                                           | IP_ADDRESS   |
| url, website, web                                        | URL          |
| date_of_birth, dob, birthdate, fecha_nacimiento          | DATE         |
| company, empresa, organization                           | ORGANIZATION |
| city, ciudad, state, country, pais                       | LOCATION     |

## DataFrame Anonymization

### Column-level (auto-detect)

```python
import pandas as pd
from shadetriptxt.text_anonymizer import TextAnonymizer

df = pd.DataFrame({
    "name": ["Juan", "María"],
    "email": ["juan@test.com", "maria@test.com"],
    "salary": [30000, 45000],
})

anon = TextAnonymizer(strategy="mask")
df_anon = anon.anonymize_columns(df)
```

### k-Anonymity (python-anonymity)

```python
df_anon = anon.anonymize_dataframe(
    df,
    identifiers=["name", "email"],       # → suppressed
    quasi_identifiers=["age", "city"],    # → generalized
    k=2,
)
```

### l-Diversity

```python
df_anon = anon.apply_l_diversity(
    df,
    sensitive_attrs=["salary"],
    quasi_identifiers=["age", "city"],
    l=2,
    identifiers=["name"],
)
```

### t-Closeness

```python
df_anon = anon.apply_t_closeness(
    df,
    sensitive_attrs=["salary"],
    quasi_identifiers=["age", "city"],
    t=0.2,
    identifiers=["name"],
)
```

## Privacy Metrics (pycanon)

```python
from shadetriptxt.text_anonymizer import measure_privacy

report = measure_privacy(
    df,
    quasi_identifiers=["age", "city"],
    sensitive_attrs=["salary"],
)
print(f"k-anonymity:  {report.k_anonymity}")
print(f"l-diversity:  {report.l_diversity}")
print(f"t-closeness:  {report.t_closeness:.4f}")
```

## Locale Support

| Locale | Country        | ID Documents    | Phone Pattern     | spaCy Model     |
| ------ | -------------- | --------------- | ----------------- | --------------- |
| es_ES  | Spain          | DNI/NIF, NIE    | +34 6xx xxx xxx   | es_core_news_sm |
| es_MX  | Mexico         | CURP, RFC       | +52 xx xxxx xxxx  | es_core_news_sm |
| es_AR  | Argentina      | DNI, CUIL       | +54 11 xxxx xxxx  | es_core_news_sm |
| es_CO  | Colombia       | Cédula         | +57 3xx xxx xxxx  | es_core_news_sm |
| es_CL  | Chile          | RUT             | +56 9 xxxx xxxx   | es_core_news_sm |
| en_US  | United States  | SSN, EIN        | +1 (xxx) xxx-xxxx | en_core_web_sm  |
| en_GB  | United Kingdom | NINO            | +44 xx xxxx xxxx  | en_core_web_sm  |
| pt_BR  | Brazil         | CPF, CNPJ       | +55 xx xxxxx-xxxx | pt_core_news_sm |
| pt_PT  | Portugal       | NIF             | +351 xxx xxx xxx  | pt_core_news_sm |
| fr_FR  | France         | NIR             | +33 x xx xx xx xx | fr_core_news_sm |
| de_DE  | Germany        | Personalausweis | +49 xx xxxxxxxx   | de_core_news_sm |
| it_IT  | Italy          | Codice Fiscale  | +39 xx xxxxxxxx   | it_core_news_sm |

## Lazy Loading

External libraries and internal modules are only loaded when their features are used:

| Module / Library             | Loaded when                                                                 |
| ---------------------------- | --------------------------------------------------------------------------- |
| **TextDummy**          | Strategy `replace` or `pseudonymize`                                    |
| **TextParser**         | Text normalization or `mask_text` via TextAnonymizer                      |
| **spacy**              | `use_spacy=True` in detect/anonymize                                      |
| **nltk**               | `use_nltk=True` in detect/anonymize                                       |
| **python-anonymity**   | `anonymize_dataframe()`, `apply_l_diversity()`, `apply_t_closeness()` |
| **pycanon**            | `measure_privacy()`                                                       |
| **pandas**             | `anonymize_columns()`                                                     |

## API Reference

### TextAnonymizer class

```python
anon = TextAnonymizer(locale="es_ES", strategy="redact", seed=None)
```

| Method                               | Description                                  |
| ------------------------------------ | -------------------------------------------- |
| `detect_pii(text, ...)`            | Detect PII entities in text                  |
| `anonymize_text(text, ...)`        | Detect and anonymize PII in text             |
| `anonymize_dict(record, ...)`      | Anonymize dictionary values                  |
| `anonymize_records(records, ...)`  | Anonymize list of dicts                      |
| `anonymize_batch(texts, ...)`      | Anonymize list of strings                    |
| `anonymize_columns(df, ...)`       | Anonymize DataFrame columns                  |
| `anonymize_dataframe(df, ...)`     | Apply k-anonymity (python-anonymity)         |
| `apply_l_diversity(df, ...)`       | Apply l-diversity                            |
| `apply_t_closeness(df, ...)`       | Apply t-closeness                            |
| `measure_privacy(df, ...)`         | Measure privacy metrics (pycanon)            |
| `summary(result)`                  | Get anonymization statistics                 |
| `set_strategy(strategy, pii_type)` | Set strategy (global or per-type)            |
| `add_pattern(name, pattern)`       | Register custom regex                        |
| `reset_pseudonyms()`               | Clear pseudonymization cache                 |
| `reset()`                          | Reset all state                              |

**Key parameters for dict/records/columns methods:**

| Parameter | Available in | Purpose |
|-----------|-------------|---------|
| `field_types` / `column_types` | `anonymize_dict`, `anonymize_records`, `anonymize_columns` | Override auto-detection with explicit PII types |
| `fields` / `columns` | `anonymize_dict`, `anonymize_records`, `anonymize_columns` | Whitelist: only anonymize these fields/columns |
| `strategy` | All methods | Override the default strategy for this call |

### Convenience functions

```python
from shadetriptxt.text_anonymizer import (
    anonymize_text,       # Quick text anonymization
    detect_pii,           # Quick PII detection
    anonymize_dict,       # Quick dict anonymization
    anonymize_dataframe,  # Quick k-anonymity
    measure_privacy,      # Quick privacy metrics
    get_anonymizer,       # Get cached instance
)
```

## Examples

All examples are in the `examples/` folder, organized by theme:

| File                      | Theme                    | Description                                                              | Guide sections |
| ------------------------- | ------------------------ | ------------------------------------------------------------------------ | -------------- |
| `text_strategies.py`    | Text Anonymization       | PII detection, all 7 strategies, per-type dispatch, custom patterns      | 3.1–3.7, 5.2  |
| `dict_records.py`       | Records & Dictionaries   | Auto-detect fields, explicit types, field whitelist, batch, pseudonymize | 5.3            |
| `dataframe_privacy.py`  | DataFrame & Privacy      | Column anonymization, k-anonymity, l-diversity, t-closeness, metrics     | 3.8, 5.4      |
| `multi_locale.py`       | Multi-locale             | 8-locale PII detection, fake data generation by country                  | 5.9            |
| `full_pipeline.py`      | Full Pipeline            | Normalize -> validate -> anonymize, mojibake repair, ID validation       | 5.5, 5.7      |
| `test_anonymizer.py`    | Tests                    | Full test suite (54 assertions)                                          | —              |

## Dependencies

**Internal (shadetriptxt — always available):**

- `TextDummy` — Locale-aware fake data generation for replace/pseudonymize strategies
- `TextParser` — Text normalization, extraction, masking

**External (lazy-loaded):**

- `spacy` — NLP-based NER detection
- `nltk` — NER fallback detection
- `python-anonymity` — k-anonymity / l-diversity / t-closeness on DataFrames
- `pycanon` — Privacy metric measurement
- `pandas` — DataFrame operations
