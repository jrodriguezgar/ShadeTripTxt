# Anonymization Parameters & Strategy Reference

Complete reference for all `TextAnonymizer` parameters, PII types, detection engines, and anonymization strategies with descriptions and examples.

---

## Table of Contents

- [1. Constructor Parameters](#1-constructor-parameters)
- [2. PII Types](#2-pii-types)
- [3. Detection Parameters](#3-detection-parameters)
- [4. Anonymization Strategies](#4-anonymization-strategies)
  - [4.1 Redact](#41-redact)
  - [4.2 Mask](#42-mask)
  - [4.3 Replace](#43-replace)
  - [4.4 Pseudonymize](#44-pseudonymize)
  - [4.5 Hash](#45-hash)
  - [4.6 Generalize](#46-generalize)
  - [4.7 Suppress](#47-suppress)
- [5. Per-Type Strategy Configuration](#5-per-type-strategy-configuration)
- [6. Custom Patterns](#6-custom-patterns)
- [7. Text Anonymization Parameters](#7-text-anonymization-parameters)
- [8. Dictionary & Record Parameters](#8-dictionary--record-parameters)
- [9. DataFrame Parameters](#9-dataframe-parameters)
- [10. Privacy Metric Parameters](#10-privacy-metric-parameters)
- [11. Supported Locales](#11-supported-locales)
- [12. Strategy Comparison Matrix](#12-strategy-comparison-matrix)
- [13. Configuration File Parameters](#13-configuration-file-parameters)

---

## 1. Constructor Parameters

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale, strategy, seed)
```

| Parameter  | Type              | Default     | Description |
|------------|-------------------|-------------|-------------|
| `locale`   | `str`             | `"es_ES"`   | Language/country code that determines locale-specific PII patterns (ID documents, phone numbers, postcodes) and the spaCy/NLTK models used for NER. See [Supported Locales](#11-supported-locales). |
| `strategy` | `str \| Strategy` | `"redact"`  | Default anonymization strategy applied to all detected PII. Can be overridden per PII type with `set_strategy()` or per call with the `strategy` parameter. One of: `mask`, `replace`, `hash`, `redact`, `generalize`, `pseudonymize`, `suppress`. |
| `seed`     | `int \| None`     | `None`      | Random seed for reproducible replacements. When set, `replace` and `pseudonymize` strategies generate the same fake data across runs. Essential for deterministic testing. |

**Examples:**

```python
# Spanish locale, default redact strategy
anon = TextAnonymizer()

# English (US) locale, mask strategy, reproducible output
anon = TextAnonymizer(locale="en_US", strategy="mask", seed=42)

# Brazilian Portuguese, replace with fake data
anon = TextAnonymizer(locale="pt_BR", strategy="replace")
```

---

## 2. PII Types

The `PiiType` enum defines all categories of Personally Identifiable Information that can be detected and anonymized.

| PiiType          | Value            | Description                                        | Detection Method          |
|------------------|------------------|----------------------------------------------------|---------------------------|
| `NAME`           | `"NAME"`         | Person names (first, last, full)                  | spaCy / NLTK NER          |
| `EMAIL`          | `"EMAIL"`        | Email addresses                                    | Universal regex            |
| `PHONE`          | `"PHONE"`        | Phone numbers (with/without country code)          | Locale-specific regex      |
| `ADDRESS`        | `"ADDRESS"`      | Postal addresses and postcodes                     | Locale-specific regex      |
| `ID_DOCUMENT`    | `"ID_DOCUMENT"`  | National ID documents (DNI, SSN, CPF, NIF, etc.)  | Locale-specific regex      |
| `CREDIT_CARD`    | `"CREDIT_CARD"`  | Credit/debit card numbers (Visa, MC, Amex, etc.)  | Universal regex            |
| `IBAN`           | `"IBAN"`         | International Bank Account Numbers                 | Universal regex            |
| `IP_ADDRESS`     | `"IP_ADDRESS"`   | IPv4 and IPv6 addresses                            | Universal regex            |
| `DATE`           | `"DATE"`         | Dates in common formats (dd/mm/yyyy, yyyy-mm-dd)  | Universal regex            |
| `URL`            | `"URL"`          | HTTP/HTTPS URLs and www addresses                  | Universal regex            |
| `ORGANIZATION`   | `"ORGANIZATION"` | Company and organization names                     | spaCy / NLTK NER          |
| `LOCATION`       | `"LOCATION"`     | Cities, countries, geographic locations            | spaCy / NLTK NER          |
| `NUMBER`         | `"NUMBER"`       | Cardinal numbers (detected via NER)                | spaCy NER                  |
| `CURRENCY`       | `"CURRENCY"`     | Monetary amounts with currency symbols/codes       | Universal regex            |
| `CUSTOM`         | `"CUSTOM"`       | User-defined patterns registered via `add_pattern()` | Custom regex |

**Usage in code:**

```python
from shadetriptxt.text_anonymizer import PiiType

# Reference PII types by enum or string
anon.set_strategy("mask", pii_type=PiiType.EMAIL)
anon.set_strategy("mask", pii_type="EMAIL")  # equivalent
```

### Custom PII Categories

The `CUSTOM` type is a catch-all for user-defined patterns registered via `add_pattern()`. Use it to detect domain-specific sensitive data that the built-in types don't cover — employee codes, medical record numbers, internal project IDs, policy numbers, etc.

Custom patterns are **always detected via regex** with a default confidence of 0.70, and they are subject to the same anonymization strategies as any built-in PII type.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale="es_ES", strategy="redact")

# Register custom patterns — all detected as PiiType.CUSTOM
anon.add_pattern("employee_id", r"EMP-\d{4}")
anon.add_pattern("medical_record", r"HC-\d{7}")
anon.add_pattern("policy_number", r"POL-[A-Z]{2}-\d{6}")
anon.add_pattern("project_code", r"PRJ-[A-Z]{4}-\d{2}")
anon.add_pattern("license_plate", r"\b\d{4}[A-Z]{3}\b")

text = "Employee EMP-1234 with policy POL-ES-001234 and record HC-0012345"
result = anon.anonymize_text(text)
print(result.anonymized)
# → "Employee [CUSTOM] with policy [CUSTOM] and record [CUSTOM]"

# Each detection includes the matched text and source
for entity in result.entities:
    print(f"  {entity.pii_type.value}: '{entity.text}' (confidence: {entity.confidence})")
    # → CUSTOM: 'EMP-1234' (confidence: 0.70)
    # → CUSTOM: 'POL-ES-001234' (confidence: 0.70)
    # → CUSTOM: 'HC-0012345' (confidence: 0.70)
```

**Applying specific strategies to custom patterns:**

Since all custom patterns share the `PiiType.CUSTOM` type, you can set a strategy for all of them at once:

```python
# All custom patterns will be hashed
anon.set_strategy("hash", pii_type="CUSTOM")

result = anon.anonymize_text("EMP-1234 policy POL-ES-001234")
print(result.anonymized)
# → "a3f2b9c10de4 policy 7b1c4e8f9a02"
```

**Combining custom patterns with built-in detection:**

Custom patterns are evaluated alongside built-in regex, spaCy, and NLTK detections. If a custom pattern overlaps with a built-in detection, the one with the highest confidence is kept (built-in detections typically have higher confidence than custom ones).

```python
anon = TextAnonymizer(locale="es_ES", strategy="redact")
anon.add_pattern("internal_code", r"INT-\d{6}")

# Built-in detections (email, DNI) + custom (internal code)
text = "Contact juan@test.com, DNI 12345678Z, code INT-001234"
result = anon.anonymize_text(text)
print(result.anonymized)
# → "Contact [EMAIL], DNI [ID_DOCUMENT], code [CUSTOM]"
```

---

## 3. Detection Parameters

### `detect_pii()` Parameters

```python
entities = anon.detect_pii(text, use_regex, use_spacy, use_nltk, min_confidence, pii_types)
```

| Parameter        | Type                           | Default  | Description |
|------------------|--------------------------------|----------|-------------|
| `text`           | `str`                          | Required | Input text to scan for PII entities. |
| `use_regex`      | `bool`                         | `True`   | Enable regex-based detection. Fast, always available, no external dependencies. Detects structured PII (emails, phones, IDs, credit cards, IBANs, IPs, URLs, dates, currency). |
| `use_spacy`      | `bool`                         | `False`  | Enable spaCy NER detection. Requires the locale-specific spaCy model to be installed. Detects names, organizations, locations, dates, and monetary amounts from natural language context. |
| `use_nltk`       | `bool`                         | `False`  | Enable NLTK NER detection. Downloads required NLTK resources automatically on first use. Serves as a fallback NER engine for names, organizations, and locations. |
| `min_confidence`  | `float`                       | `0.0`    | Minimum confidence threshold (0.0–1.0). Entities below this score are filtered out. Regex detections typically have 0.60–0.90 confidence; spaCy has ~0.75; NLTK has ~0.65. |
| `pii_types`      | `Sequence[str \| PiiType] \| None` | `None` | Restrict detection to only these PII types. `None` means detect all types. |

**Confidence levels by source:**

| Source   | Typical Confidence | Best For |
|----------|-------------------|----------|
| Regex (universal patterns) | 0.90 | Email, credit card, IBAN, IP, URL, date, currency |
| Regex (locale ID documents) | 0.85 | DNI, SSN, CPF, NIF, CURP, etc. |
| Regex (locale phones) | 0.80 | Phone numbers with country-specific formats |
| spaCy NER | 0.75 | Names, organizations, locations |
| Regex (custom patterns) | 0.70 | User-defined patterns |
| NLTK NER | 0.65 | Names, organizations, locations (fallback) |
| Regex (postcodes) | 0.60 | Postal codes |

**Examples:**

```python
# Regex only (default — fast, no external dependencies)
entities = anon.detect_pii("DNI: 12345678Z, email: juan@test.com")

# Combined detection (maximum coverage)
entities = anon.detect_pii(
    "Juan García works at Acme Corp, DNI 12345678Z",
    use_regex=True,
    use_spacy=True,
    use_nltk=True,
)

# Only high-confidence detections
entities = anon.detect_pii(text, min_confidence=0.80)

# Only detect emails and phones
entities = anon.detect_pii(text, pii_types=["EMAIL", "PHONE"])
entities = anon.detect_pii(text, pii_types=[PiiType.EMAIL, PiiType.PHONE])
```

### `DetectedEntity` Result Fields

Each detected entity is returned as a `DetectedEntity` dataclass:

| Field        | Type       | Description |
|--------------|------------|-------------|
| `text`       | `str`      | The matched PII text (e.g., `"12345678Z"`). |
| `pii_type`   | `PiiType`  | Category of PII detected (e.g., `PiiType.ID_DOCUMENT`). |
| `start`      | `int`      | Start position (character index) in the original text. |
| `end`        | `int`      | End position (character index) in the original text. |
| `confidence` | `float`    | Detection confidence score (0.0–1.0). |
| `source`     | `str`      | Detection engine used: `"regex"`, `"spacy"`, or `"nltk"`. |

---

## 4. Anonymization Strategies

Each strategy transforms detected PII in a different way, balancing privacy, data utility, and readability.

### 4.1 Redact

**Replaces PII with a type label.** The safest strategy — completely removes the original data and replaces it with a tag indicating what type of information was there.

| Property          | Value |
|-------------------|-------|
| Reversible        | No |
| Preserves format  | No |
| Deterministic     | Yes |
| Statistical utility | No |
| Best for          | Logs, legal documents, audit trails, maximum privacy |

**Behavior:**

All PII types are replaced with `[TYPE]` (e.g., `[EMAIL]`, `[NAME]`, `[ID_DOCUMENT]`).

**Examples:**

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale="es_ES", strategy="redact")

# Email
result = anon.anonymize_text("Contact: juan@empresa.com")
print(result.anonymized)
# → "Contact: [EMAIL]"

# ID Document
result = anon.anonymize_text("DNI: 12345678Z")
print(result.anonymized)
# → "DNI: [ID_DOCUMENT]"

# Phone
result = anon.anonymize_text("Call +34 612 345 678")
print(result.anonymized)
# → "Call [PHONE]"

# Multiple PII types
result = anon.anonymize_text("DNI 12345678Z, email juan@test.com, IP 192.168.1.1")
print(result.anonymized)
# → "DNI [ID_DOCUMENT], email [EMAIL], IP [IP_ADDRESS]"
```

---

### 4.2 Mask

**Partially hides characters while preserving the data structure.** Shows enough of the original to verify format without revealing the full content.

| Property          | Value |
|-------------------|-------|
| Reversible        | No |
| Preserves format  | Yes |
| Deterministic     | No |
| Statistical utility | No |
| Best for          | Audits, format verification, customer-facing displays |

**Behavior by PII type:**

| PII Type      | Masking Rule | Example |
|---------------|-------------|---------|
| `EMAIL`       | Keep first char of local part, mask domain, replace TLD with `***` | `juan@empresa.com` → `j***@*******.***` |
| `PHONE`       | Keep last 4 digits, mask the rest | `+34 612 345 678` → `*******5678` |
| `CREDIT_CARD` | Keep last 4 digits, mask the rest | `4111111111111111` → `************1111` |
| `NAME`        | Keep first char of each word, mask the rest | `Juan García` → `J*** G*****` |
| Other types   | Keep first and last char, mask middle | `12345678Z` → `1*******Z` |

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="mask")

# Email masking
result = anon.anonymize_text("Email: juan.garcia@empresa.com")
print(result.anonymized)
# → "Email: j***.g*****@*******.***"

# Phone masking (last 4 digits visible)
result = anon.anonymize_text("Phone: +34 612 345 678")
print(result.anonymized)
# → "Phone: *******5678"

# Credit card masking
result = anon.anonymize_text("Card: 4111 1111 1111 1111")
print(result.anonymized)
# → "Card: ************1111"

# Name masking
result = anon.anonymize_text("Name: Juan García López")
# (detected via spaCy NER — requires use_spacy=True)
```

---

### 4.3 Replace

**Replaces PII with realistic locale-aware fake data.** The anonymizer generates names, emails, phones, IDs, and other data types consistent with the configured locale.

| Property          | Value |
|-------------------|-------|
| Reversible        | No |
| Preserves format  | Yes |
| Deterministic     | No (random each time unless `seed` is set) |
| Statistical utility | Partial |
| Best for          | Demos, test environments, data sharing, presentations |

**Replacement generated by PII type:**

| PII Type        | Replacement Output |
|-----------------|-------------------|
| `NAME`          | Realistic full name (locale-aware) |
| `EMAIL`         | Realistic email address |
| `PHONE`         | Phone number with correct country format |
| `ADDRESS`       | Full street address |
| `ORGANIZATION`  | Company name |
| `LOCATION`      | City name |
| `URL`           | URL |
| `DATE`          | Date string |
| `CREDIT_CARD`   | Valid-format credit card number |
| `IBAN`          | IBAN with correct country prefix |
| `ID_DOCUMENT`   | National ID with correct locale format (DNI, SSN, CPF...) |
| `CURRENCY`      | Price with locale currency symbol |
| Other types     | Random word |

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="replace", seed=42)

# Email → realistic fake email
result = anon.anonymize_text("Contact: juan@empresa.com")
print(result.anonymized)
# → "Contact: maria.gomez@example.org"

# ID Document → locale-specific fake ID
result = anon.anonymize_text("DNI: 12345678Z")
print(result.anonymized)
# → "DNI: 98765432W"

# Phone → locale-specific fake phone
result = anon.anonymize_text("Call +34 612 345 678")
print(result.anonymized)
# → "Call +34 698 234 567"

# Different locale generates different format
anon_us = TextAnonymizer(locale="en_US", strategy="replace", seed=42)
result = anon_us.anonymize_text("SSN: 123-45-6789, phone (555) 123-4567")
print(result.anonymized)
# → SSN and phone replaced with US-format fakes
```

---

### 4.4 Pseudonymize

**Consistent replacement — the same input always produces the same output.** Maintains an internal cache mapping each original value to its replacement, so repeated occurrences across multiple calls get the same fake value. Essential for preserving referential integrity across records.

| Property          | Value |
|-------------------|-------|
| Reversible        | Yes (if internal mapping is retained) |
| Preserves format  | Yes |
| Deterministic     | Yes (same input → same output within the same session) |
| Statistical utility | Partial |
| Best for          | Longitudinal analysis, record relationships, linked datasets |

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="pseudonymize", seed=42)

# Same email → same replacement every time
r1 = anon.anonymize_text("Contact juan@test.com about project A")
r2 = anon.anonymize_text("Forward to juan@test.com and pedro@test.com")

# In both results, "juan@test.com" gets the SAME replacement
# "pedro@test.com" gets a different replacement
print(r1.anonymized)
print(r2.anonymized)

# Clear the cache to generate new mappings
anon.reset_pseudonyms()

# After reset, "juan@test.com" would get a NEW replacement
r3 = anon.anonymize_text("Contact juan@test.com again")
```

**Use case — preserving relationships:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="pseudonymize", seed=42)

records = [
    {"name": "Juan García", "email": "juan@test.com", "manager": "Ana López"},
    {"name": "Pedro Ruiz", "email": "pedro@test.com", "manager": "Ana López"},
    {"name": "Ana López", "email": "ana@test.com", "manager": "Director"},
]

results = anon.anonymize_records(records)
# "Ana López" gets the same replacement in all three records,
# preserving the manager relationship
```

---

### 4.5 Hash

**Replaces PII with a truncated SHA-256 hash.** Irreversible and deterministic — the same input always produces the same hash, enabling traceability without revealing the original value.

| Property          | Value |
|-------------------|-------|
| Reversible        | No |
| Preserves format  | No |
| Deterministic     | Yes |
| Statistical utility | No |
| Best for          | Traceability, technical auditing, deduplication verification |

**Behavior:**

The original value is SHA-256 hashed and truncated to 12 hexadecimal characters by default.

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="hash")

# ID Document
result = anon.anonymize_text("DNI: 12345678Z")
print(result.anonymized)
# → "DNI: 1c9f96328944"

# Email
result = anon.anonymize_text("Email: juan@test.com")
print(result.anonymized)
# → "Email: 5a8dd3ad0756"

# Same input always produces the same hash
result1 = anon.anonymize_text("DNI: 12345678Z")
result2 = anon.anonymize_text("DNI: 12345678Z")
# Both produce the same hash value for "12345678Z"
```

---

### 4.6 Generalize

**Reduces data precision while preserving statistical utility.** Converts specific values into broader categories or ranges, maintaining analytical value without exposing individual data points.

| Property          | Value |
|-------------------|-------|
| Reversible        | No |
| Preserves format  | Partial |
| Deterministic     | Yes |
| Statistical utility | Yes |
| Best for          | Statistical analysis, reporting, data aggregation |

**Behavior by PII type:**

| PII Type           | Generalization Rule | Example |
|--------------------|---------------------|---------|
| `DATE`             | Extract year only | `15/03/1990` → `1990` |
| `NUMBER`           | Round to decade range | `34` → `30-39` |
| `ADDRESS`/`LOCATION` | Keep first part (before comma) | `Calle Mayor 15, Madrid` → `Calle Mayor 15` |
| `EMAIL`            | Replace local part with `***`, keep domain | `juan@empresa.com` → `***@empresa.com` |
| Other types        | Keep first 2 and last 2 chars, ellipsis in middle | `12345678Z` → `12...8Z` |

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="generalize")

# Date → year only
result = anon.anonymize_text("Born on 15/03/1990")
print(result.anonymized)
# → "Born on 1990"

# Email → domain preserved
result = anon.anonymize_text("Email: juan@empresa.com")
print(result.anonymized)
# → "Email: ***@empresa.com"

# IBAN → partial visibility
result = anon.anonymize_text("IBAN: ES9121000418450200051332")
print(result.anonymized)
# → "IBAN: ES...32"
```

---

### 4.7 Suppress

**Removes PII completely from the text.** Replaces matched entities with an empty string, leaving no trace of the original data.

| Property          | Value |
|-------------------|-------|
| Reversible        | No |
| Preserves format  | No |
| Deterministic     | Yes |
| Statistical utility | No |
| Best for          | Maximum privacy, data minimization, GDPR erasure requests |

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="suppress")

# Email → empty
result = anon.anonymize_text("Contact: juan@test.com for info")
print(result.anonymized)
# → "Contact:  for info"

# Phone → empty
result = anon.anonymize_text("Call +34 612 345 678 today")
print(result.anonymized)
# → "Call  today"

# Multiple PII — all removed
result = anon.anonymize_text("DNI 12345678Z, email juan@test.com")
print(result.anonymized)
# → "DNI , email "
```

---

## 5. Per-Type Strategy Configuration

You can apply different strategies to different PII types using `set_strategy()`. Types without an override use the instance default strategy.

```python
anon.set_strategy(strategy, pii_type=None)
```

| Parameter  | Type              | Default  | Description |
|------------|-------------------|----------|-------------|
| `strategy` | `str \| Strategy` | Required | The strategy to apply. |
| `pii_type` | `str \| PiiType \| None` | `None` | If provided, set strategy only for this PII type. If `None`, set the global default. |

**Returns:** `self` (supports method chaining).

**Example — mixed strategies:**

```python
from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType

anon = TextAnonymizer(locale="es_ES", strategy="redact")  # default: redact

# Per-type overrides
anon.set_strategy("mask", pii_type=PiiType.EMAIL)          # Emails → j***@***.***
anon.set_strategy("mask", pii_type=PiiType.PHONE)          # Phones → ****5678
anon.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)    # DNIs → a3f2b9c1...
anon.set_strategy("replace", pii_type=PiiType.NAME)        # Names → fake name
anon.set_strategy("suppress", pii_type=PiiType.IP_ADDRESS) # IPs → removed
anon.set_strategy("generalize", pii_type=PiiType.DATE)     # Dates → year only

# Everything else (IBAN, CREDIT_CARD, URL, etc.) uses the default: redact

text = (
    "Juan García, DNI 12345678Z, email juan@test.com, "
    "phone +34 612 345 678, born 15/03/1990, IP 192.168.1.1"
)
result = anon.anonymize_text(text)
print(result.anonymized)
# Name → replaced with fake, DNI → hashed, email → masked,
# phone → masked, date → year only, IP → removed
```

**Method chaining:**

```python
anon = (
    TextAnonymizer(locale="en_US", strategy="redact")
    .set_strategy("mask", pii_type="EMAIL")
    .set_strategy("hash", pii_type="ID_DOCUMENT")
    .set_strategy("suppress", pii_type="IP_ADDRESS")
)
```

---

## 6. Custom Patterns

Register custom regex patterns to detect domain-specific PII that the built-in patterns don't cover.

```python
anon.add_pattern(name, pattern, pii_type="CUSTOM")
```

| Parameter  | Type              | Default        | Description |
|------------|-------------------|----------------|-------------|
| `name`     | `str`             | Required       | Identifier for the pattern (e.g., `"employee_id"`). |
| `pattern`  | `str`             | Required       | Regex pattern string. |
| `pii_type` | `str \| PiiType`  | `PiiType.CUSTOM` | PII type to associate with matches. |

**Returns:** `self` (supports method chaining).

**Examples:**

```python
anon = TextAnonymizer(locale="es_ES", strategy="redact")

# Detect employee IDs (EMP-XXXX)
anon.add_pattern("employee_id", r"EMP-\d{4}")

# Detect medical record numbers (HC-XXXXXXX)
anon.add_pattern("medical_record", r"HC-\d{7}")

# Detect internal project codes (PRJ-XXXX-XX)
anon.add_pattern("project_code", r"PRJ-[A-Z]{4}-\d{2}")

text = "Employee EMP-1234 working on PRJ-ACME-01, record HC-0012345"
result = anon.anonymize_text(text)
print(result.anonymized)
# → "Employee [CUSTOM] working on [CUSTOM], record [CUSTOM]"

# Check what was detected
for entity in result.entities:
    print(f"  {entity.pii_type.value}: '{entity.text}' (confidence: {entity.confidence})")
```

---

## 7. Text Anonymization Parameters

### `anonymize_text()`

```python
result = anon.anonymize_text(text, strategy, use_regex, use_spacy, use_nltk, pii_types, min_confidence)
```

| Parameter        | Type                           | Default       | Description |
|------------------|--------------------------------|---------------|-------------|
| `text`           | `str`                          | Required      | Input text to anonymize. |
| `strategy`       | `str \| Strategy \| None`      | `None`        | Override the instance default strategy for this call only. `None` uses the instance default. |
| `use_regex`      | `bool`                         | `True`        | Enable regex-based detection. |
| `use_spacy`      | `bool`                         | `False`       | Enable spaCy NER detection. |
| `use_nltk`       | `bool`                         | `False`       | Enable NLTK NER detection. |
| `pii_types`      | `Sequence[str \| PiiType] \| None` | `None`    | Only anonymize these PII types. `None` = all. |
| `min_confidence`  | `float`                       | `0.0`         | Minimum confidence threshold. |

**Returns:** `AnonymizationResult` with fields:

| Field          | Type                    | Description |
|----------------|-------------------------|-------------|
| `original`     | `str`                   | The original input text. |
| `anonymized`   | `str`                   | The anonymized output text. |
| `entities`     | `List[DetectedEntity]`  | All PII entities detected. |
| `replacements` | `Dict[str, str]`        | Mapping of original values to their anonymized versions. |

**Examples:**

```python
# Basic usage
result = anon.anonymize_text("DNI: 12345678Z, email: juan@test.com")

# Override strategy for this call
result = anon.anonymize_text("DNI: 12345678Z", strategy="hash")

# Only anonymize emails and phones
result = anon.anonymize_text(text, pii_types=["EMAIL", "PHONE"])

# Use all detection engines
result = anon.anonymize_text(text, use_regex=True, use_spacy=True, use_nltk=True)
```

### `anonymize_batch()`

Anonymize multiple texts at once.

```python
results = anon.anonymize_batch(texts, strategy, use_regex, use_spacy, use_nltk)
```

| Parameter    | Type                      | Default  | Description |
|--------------|---------------------------|----------|-------------|
| `texts`      | `Sequence[str]`           | Required | List of input texts. |
| `strategy`   | `str \| Strategy \| None` | `None`   | Override default strategy. |
| `use_regex`  | `bool`                    | `True`   | Enable regex detection. |
| `use_spacy`  | `bool`                    | `False`  | Enable spaCy detection. |
| `use_nltk`   | `bool`                    | `False`  | Enable NLTK detection. |

**Returns:** `List[AnonymizationResult]`

---

## 8. Dictionary & Record Parameters

### `anonymize_dict()`

Anonymize values in a dictionary. Field names are automatically matched to PII types using a built-in mapping (see table below).

```python
result = anon.anonymize_dict(record, field_types, strategy, fields)
```

| Parameter     | Type                                  | Default  | Description |
|---------------|---------------------------------------|----------|-------------|
| `record`      | `Dict[str, Any]`                      | Required | Dictionary with field names and values. |
| `field_types` | `Dict[str, str \| PiiType] \| None`   | `None`   | Explicit mapping `{field_name: PiiType}` to override auto-detection. |
| `strategy`    | `str \| Strategy \| None`             | `None`   | Override default strategy. |
| `fields`      | `Sequence[str] \| None`               | `None`   | Whitelist: only anonymize these fields. All other fields are left untouched, even if auto-detected. |

**Returns:** `Dict[str, Any]` — new dictionary with anonymized values.

### `anonymize_records()`

Anonymize a list of dictionaries. Same parameters as `anonymize_dict()` plus:

| Parameter     | Type                       | Default  | Description |
|---------------|----------------------------|----------|-------------|
| `records`     | `Sequence[Dict[str, Any]]` | Required | List of dictionaries. |

**Returns:** `List[Dict[str, Any]]`

**Auto-detected field names:**

| Field Names (case-insensitive)                                          | PII Type       |
|-------------------------------------------------------------------------|----------------|
| `name`, `nombre`, `full_name`, `fullname`, `first_name`, `firstname`, `last_name`, `lastname`, `surname`, `apellido` | `NAME` |
| `email`, `correo`, `mail`, `email_address`                              | `EMAIL`        |
| `phone`, `telefono`, `phone_number`, `mobile`, `telephone`, `tel`       | `PHONE`        |
| `address`, `direccion`, `street`, `street_address`                      | `ADDRESS`      |
| `postcode`, `zip_code`, `zip`, `codigo_postal`                          | `ADDRESS`      |
| `dni`, `nif`, `ssn`, `id_document`, `document`, `documento`, `passport`, `pasaporte`, `curp`, `rfc`, `cpf`, `cnpj` | `ID_DOCUMENT` |
| `credit_card`, `tarjeta`, `card_number`                                 | `CREDIT_CARD`  |
| `iban`, `bban`                                                          | `IBAN`         |
| `ip`, `ip_address`                                                      | `IP_ADDRESS`   |
| `url`, `website`, `web`                                                 | `URL`          |
| `date_of_birth`, `dob`, `birth_date`, `birthdate`, `fecha_nacimiento`   | `DATE`         |
| `company`, `empresa`, `organization`                                    | `ORGANIZATION` |
| `city`, `ciudad`, `state`, `provincia`, `country`, `pais`               | `LOCATION`     |

**Examples:**

```python
from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType

anon = TextAnonymizer(locale="es_ES", strategy="mask")

# Auto-detect by field name
record = {"nombre": "Juan García", "email": "juan@test.com", "salary": 45000}
result = anon.anonymize_dict(record)
# → {"nombre": "J*** G*****", "email": "j***@****.***", "salary": 45000}

# Explicit field types for non-standard names
result = anon.anonymize_dict(
    {"codigo": "12345678Z", "correo_personal": "juan@test.com"},
    field_types={"codigo": PiiType.ID_DOCUMENT, "correo_personal": PiiType.EMAIL},
)

# Whitelist: only anonymize specific fields
result = anon.anonymize_dict(
    {"nombre": "Juan", "email": "juan@test.com", "telefono": "+34 612 345 678"},
    fields=["email", "telefono"],  # "nombre" is NOT anonymized
)
# → {"nombre": "Juan", "email": "j***@****.***", "telefono": "****5678"}
```

---

## 9. DataFrame Parameters

### `anonymize_columns()`

Anonymize specific columns of a DataFrame using auto-detection by column name.

```python
df_anon = anon.anonymize_columns(df, column_types, strategy, columns)
```

| Parameter      | Type                                  | Default  | Description |
|----------------|---------------------------------------|----------|-------------|
| `df`           | `pandas.DataFrame`                    | Required | Input DataFrame. |
| `column_types` | `Dict[str, str \| PiiType] \| None`   | `None`   | Explicit mapping `{column_name: PiiType}`. |
| `strategy`     | `str \| Strategy \| None`             | `None`   | Override default strategy. |
| `columns`      | `Sequence[str] \| None`               | `None`   | Whitelist: only anonymize these columns. |

**Returns:** New `DataFrame` with anonymized columns.

### `anonymize_dataframe()` (k-Anonymity)

Apply k-anonymity generalization using the `python-anonymity` library.

```python
df_anon = anon.anonymize_dataframe(df, identifiers, quasi_identifiers, k, supp_threshold, hierarchies, method)
```

| Parameter            | Type                      | Default      | Description |
|----------------------|---------------------------|--------------|-------------|
| `df`                 | `pandas.DataFrame`        | Required     | Input DataFrame. |
| `identifiers`        | `Sequence[str]`           | Required     | Direct identifier columns (suppressed/removed). |
| `quasi_identifiers`  | `Sequence[str]`           | Required     | Quasi-identifier columns (generalized). |
| `k`                  | `int`                     | `2`          | Desired k-anonymity level. Each combination of quasi-identifiers must have at least `k` rows. |
| `supp_threshold`     | `int`                     | `0`          | Maximum number of rows that can be suppressed to achieve k-anonymity. |
| `hierarchies`        | `Dict[str, Any] \| None`  | `None`       | Generalization hierarchies `{column: {value: generalized_value}}`. |
| `method`             | `str`                     | `"datafly"`  | Algorithm: `"datafly"` or `"incognito"`. |

**Returns:** Anonymized `DataFrame`.

### `apply_l_diversity()`

Apply l-diversity to ensure sensitive attribute diversity within each equivalence class.

```python
df_anon = anon.apply_l_diversity(df, sensitive_attrs, quasi_identifiers, l, identifiers, k, supp_threshold, hierarchies, k_method)
```

| Parameter            | Type                      | Default      | Description |
|----------------------|---------------------------|--------------|-------------|
| `df`                 | `pandas.DataFrame`        | Required     | Input DataFrame. |
| `sensitive_attrs`    | `Sequence[str]`           | Required     | Sensitive attribute columns. |
| `quasi_identifiers`  | `Sequence[str]`           | Required     | Quasi-identifier columns. |
| `l`                  | `int`                     | `2`          | Desired l-diversity level. Each group must have at least `l` distinct values for each sensitive attribute. |
| `identifiers`        | `Sequence[str] \| None`   | `None`       | Direct identifier columns. |
| `k`                  | `int`                     | `2`          | k-anonymity level to apply first. |
| `supp_threshold`     | `int`                     | `0`          | Maximum rows to suppress. |
| `hierarchies`        | `Dict[str, Any] \| None`  | `None`       | Generalization hierarchies. |
| `k_method`           | `str`                     | `"datafly"`  | k-anonymity algorithm. |

### `apply_t_closeness()`

Apply t-closeness to ensure the distribution of sensitive attributes within each group is similar to the global distribution.

```python
df_anon = anon.apply_t_closeness(df, sensitive_attrs, quasi_identifiers, t, identifiers, supp_threshold, hierarchies, k_method)
```

| Parameter            | Type                      | Default      | Description |
|----------------------|---------------------------|--------------|-------------|
| `df`                 | `pandas.DataFrame`        | Required     | Input DataFrame. |
| `sensitive_attrs`    | `Sequence[str]`           | Required     | Sensitive attribute columns. |
| `quasi_identifiers`  | `Sequence[str]`           | Required     | Quasi-identifier columns. |
| `t`                  | `float`                   | `0.2`        | t-closeness threshold (0.0–1.0). Smaller values are stricter. |
| `identifiers`        | `Sequence[str] \| None`   | `None`       | Direct identifier columns. |
| `supp_threshold`     | `int`                     | `0`          | Maximum rows to suppress. |
| `hierarchies`        | `Dict[str, Any] \| None`  | `None`       | Generalization hierarchies. |
| `k_method`           | `str`                     | `"datafly"`  | k-anonymity algorithm. |

**DataFrame example — full pipeline:**

```python
import pandas as pd
from shadetriptxt.text_anonymizer import TextAnonymizer

df = pd.DataFrame({
    "nombre": ["Juan", "María", "Pedro", "Ana", "Luis", "Carmen"],
    "email": ["juan@m.com", "maria@m.com", "pedro@m.com",
              "ana@m.com", "luis@m.com", "carmen@m.com"],
    "edad": [25, 30, 25, 30, 25, 30],
    "ciudad": ["Madrid", "Madrid", "Barcelona", "Barcelona", "Madrid", "Barcelona"],
    "salario": [30000, 45000, 28000, 50000, 32000, 47000],
})

anon = TextAnonymizer(locale="es_ES")

# Step 1: Column-level anonymization
df_masked = anon.anonymize_columns(df, strategy="mask")

# Step 2: k-Anonymity
df_kanon = anon.anonymize_dataframe(
    df, identifiers=["nombre", "email"],
    quasi_identifiers=["edad", "ciudad"], k=2,
)

# Step 3: l-Diversity
df_ldiv = anon.apply_l_diversity(
    df, sensitive_attrs=["salario"],
    quasi_identifiers=["edad", "ciudad"], l=2,
    identifiers=["nombre", "email"],
)

# Step 4: t-Closeness
df_tclose = anon.apply_t_closeness(
    df, sensitive_attrs=["salario"],
    quasi_identifiers=["edad", "ciudad"], t=0.2,
    identifiers=["nombre", "email"],
)
```

---

## 10. Privacy Metric Parameters

### `measure_privacy()`

Measure k-anonymity, l-diversity, and t-closeness on a DataFrame using `pycanon`.

```python
report = anon.measure_privacy(df, quasi_identifiers, sensitive_attrs)
```

| Parameter           | Type                      | Default  | Description |
|---------------------|---------------------------|----------|-------------|
| `df`                | `pandas.DataFrame`        | Required | DataFrame to evaluate. |
| `quasi_identifiers` | `Sequence[str]`           | Required | Quasi-identifier column names. |
| `sensitive_attrs`   | `Sequence[str] \| None`   | `None`   | Sensitive attribute column names. Required for l-diversity and t-closeness. |

**Returns:** `PrivacyReport` with fields:

| Field          | Type             | Description |
|----------------|------------------|-------------|
| `k_anonymity`  | `int \| None`    | Achieved k-anonymity level. |
| `l_diversity`  | `int \| None`    | Achieved l-diversity level (requires `sensitive_attrs`). |
| `t_closeness`  | `float \| None`  | Achieved t-closeness value (requires `sensitive_attrs`). |
| `details`      | `Dict[str, Any]` | Additional info: quasi-identifiers, sensitive attrs, row count. |

**Example:**

```python
report = anon.measure_privacy(
    df_anonymized,
    quasi_identifiers=["edad", "ciudad"],
    sensitive_attrs=["salario"],
)
print(f"k-anonymity:  {report.k_anonymity}")     # Target: ≥ 2
print(f"l-diversity:  {report.l_diversity}")      # Target: ≥ 2
print(f"t-closeness:  {report.t_closeness:.4f}")  # Target: ≤ 0.2
```

---

## 11. Supported Locales

| Locale   | Country        | Language   | ID Documents       | Phone Format          | spaCy Model       |
|----------|----------------|------------|--------------------|-----------------------|-------------------|
| `es_ES`  | Spain          | Spanish    | DNI/NIF, NIE       | `+34 6xx xxx xxx`     | `es_core_news_sm` |
| `es_MX`  | Mexico         | Spanish    | CURP, RFC          | `+52 xx xxxx xxxx`    | `es_core_news_sm` |
| `es_AR`  | Argentina      | Spanish    | DNI, CUIL          | `+54 11 xxxx xxxx`    | `es_core_news_sm` |
| `es_CO`  | Colombia       | Spanish    | Cédula             | `+57 3xx xxx xxxx`    | `es_core_news_sm` |
| `es_CL`  | Chile          | Spanish    | RUT                | `+56 9 xxxx xxxx`     | `es_core_news_sm` |
| `en_US`  | United States  | English    | SSN, EIN           | `+1 (xxx) xxx-xxxx`   | `en_core_web_sm`  |
| `en_GB`  | United Kingdom | English    | NINO               | `+44 xx xxxx xxxx`    | `en_core_web_sm`  |
| `pt_BR`  | Brazil         | Portuguese | CPF, CNPJ          | `+55 xx xxxxx-xxxx`   | `pt_core_news_sm` |
| `pt_PT`  | Portugal       | Portuguese | NIF                | `+351 xxx xxx xxx`    | `pt_core_news_sm` |
| `fr_FR`  | France         | French     | NIR                | `+33 x xx xx xx xx`   | `fr_core_news_sm` |
| `de_DE`  | Germany        | German     | Personalausweis    | `+49 xx xxxxxxxx`     | `de_core_news_sm` |
| `it_IT`  | Italy          | Italian    | Codice Fiscale     | `+39 xx xxxxxxxx`     | `it_core_news_sm` |

---

## 12. Strategy Comparison Matrix

| Strategy           | Reversible | Format | Deterministic | Utility | Best Use Case |
|--------------------|:----------:|:------:|:-------------:|:-------:|---------------|
| **Redact**         | No         | No     | Yes           | None    | Logs, legal docs, max privacy |
| **Mask**           | No         | Yes    | No            | None    | Audits, format checks |
| **Replace**        | No         | Yes    | No*           | Partial | Demos, test data |
| **Pseudonymize**   | Yes**      | Yes    | Yes           | Partial | Record linkage, longitudinal analysis |
| **Hash**           | No         | No     | Yes           | None    | Traceability, technical audits |
| **Generalize**     | No         | Partial| Yes           | Yes     | Statistics, reporting |
| **Suppress**       | No         | No     | Yes           | None    | Data minimization, GDPR erasure |

*\* Deterministic when `seed` is set.*
*\*\* Only if the internal `_pseudo_map` cache is preserved.*

### Decision Tree

```
Need statistical utility?
├── Yes → GENERALIZE or k-ANONYMITY / l-DIVERSITY / t-CLOSENESS
│
├── Need consistent record relationships?
│   ├── Yes → PSEUDONYMIZE
│   └── No → Need visually realistic data?
│       ├── Yes → REPLACE
│       └── No → Need to see original format?
│           ├── Yes → MASK
│           └── No → REDACT or SUPPRESS
│
└── Need traceability / deduplication?
    └── Yes → HASH
```

---

## 13. Configuration File Parameters

Configuration can be loaded from JSON, YAML, or TOML files using the `Config` class.

### File Structure (JSON)

```json
{
  "anonymizer": {
    "locale": "es_ES",
    "strategy": "redact",
    "seed": null
  },
  "detection": {
    "use_regex": true,
    "use_spacy": false,
    "use_nltk": false,
    "min_confidence": 0.0,
    "pii_types": null
  },
  "strategies": {
    "hash_length": 12
  },
  "type_overrides": {
    "EMAIL": "mask",
    "PHONE": "mask",
    "ID_DOCUMENT": "hash",
    "NAME": "pseudonymize"
  }
}
```

### Environment Variables

All configuration keys can be set via environment variables with the `ANONYMIZER_` prefix:

| Environment Variable               | Config Key                  | Example |
|------------------------------------|-----------------------------|---------|
| `ANONYMIZER_LOCALE`                | `locale`                    | `es_ES` |
| `ANONYMIZER_STRATEGY`              | `strategy`                  | `mask` |
| `ANONYMIZER_SEED`                  | `seed`                      | `42` |
| `ANONYMIZER_DETECTION__USE_REGEX`  | `detection.use_regex`       | `true` |
| `ANONYMIZER_DETECTION__USE_SPACY`  | `detection.use_spacy`       | `false` |
| `ANONYMIZER_DETECTION__MIN_CONFIDENCE` | `detection.min_confidence` | `0.5` |

Double underscores (`__`) in variable names map to dots (`.`) in config keys.

### Priority Order

1. **Command-line arguments** (highest)
2. **Environment variables** (`ANONYMIZER_*`)
3. **Configuration files** (JSON/YAML/TOML)
4. **Default values** (lowest)

### Loading Configuration

```python
from shadetriptxt.text_anonymizer.config import Config, load_config, create_sample_config

# Quick load with defaults
config = load_config(filepath="anonymizer_config.json")

# Access values
locale = config.get("locale")                                    # "es_ES"
confidence = config.get("detection.min_confidence", type=float)  # 0.0

# Create and configure TextAnonymizer from config
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(
    locale=config.get("locale", "es_ES"),
    strategy=config.get("strategy", "redact"),
    seed=config.get("seed", type=int),
)

# Generate a sample config file
create_sample_config("anonymizer_config.json")
```

---

*Document generated for the shadetriptxt project — DatamanEdge (MIT License)*
