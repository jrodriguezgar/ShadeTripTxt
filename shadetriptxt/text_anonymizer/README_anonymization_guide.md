# Anonymization Techniques & Data Protection Guide with shadetriptxt

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Anonymization Fundamentals](#2-anonymization-fundamentals)
  - [2.1 What is anonymization?](#21-what-is-anonymization)
  - [2.2 Regulatory framework](#22-regulatory-framework)
  - [2.3 Types of personal data (PII)](#23-types-of-personal-data-pii)
- [3. Anonymization Techniques](#3-anonymization-techniques)
  - [3.1 Masking](#31-masking)
  - [3.2 Redaction (Redact)](#32-redaction-redact)
  - [3.3 Replacement with realistic data (Replace)](#33-replacement-with-realistic-data-replace)
  - [3.4 Pseudonymization (Pseudonymize)](#34-pseudonymization-pseudonymize)
  - [3.5 Hashing](#35-hashing)
  - [3.6 Generalization (Generalize)](#36-generalization-generalize)
  - [3.7 Suppression (Suppress)](#37-suppression-suppress)
  - [3.8 k-Anonymity, l-Diversity and t-Closeness](#38-k-anonymity-l-diversity-and-t-closeness)
- [4. shadetriptxt Tools](#4-shadetriptxt-tools)
  - [4.1 External dependencies](#41-external-dependencies)
- [5. Use Cases](#5-use-cases)
  - [5.1 Generate test data for development and testing](#51-generate-test-data-for-development-and-testing)
  - [5.2 Mask sensitive data in free text](#52-mask-sensitive-data-in-free-text)
  - [5.3 Anonymize records and dictionaries](#53-anonymize-records-and-dictionaries)
  - [5.4 Anonymize DataFrames with k-Anonymity](#54-anonymize-dataframes-with-k-anonymity)
  - [5.5 Normalize and clean text before anonymizing](#55-normalize-and-clean-text-before-anonymizing)
  - [5.6 Detect anonymized duplicates with TextMatcher](#56-detect-anonymized-duplicates-with-textmatcher)
  - [5.7 Full pipeline: detection, validation and anonymization](#57-full-pipeline-detection-validation-and-anonymization)
  - [5.8 Generate complete development environments](#58-generate-complete-development-environments)
  - [5.9 Multi-language anonymization](#59-multi-language-anonymization)
- [6. Strategy Comparison](#6-strategy-comparison)
- [7. Best Practices](#7-best-practices)

---

## 1. Introduction

Protecting personal data is a critical requirement in any enterprise data pipeline. Whether to comply with regulations such as GDPR, to build safe test environments, or to share data across teams without exposing sensitive information, having the right techniques and tools is essential.

**shadetriptxt** provides a complete ecosystem for these scenarios. The central module is **TextAnonymizer**, which acts as a single entry point for all anonymization techniques, internally delegating to the other modules:

| Module                  | Role in anonymization                                                                        |
| ------------------------ | --------------------------------------------------------------------------------------------- |
| **TextAnonymizer** | **Central hub**: PII detection, 7 built-in strategies, and wrapper of the other modules  |
| **TextDummy**      | Internal delegate: generates fake data for the `replace` and `pseudonymize` strategies       |
| **TextParser**     | Internal delegate: normalization, extraction and `mask_text` for data preparation             |
| **TextMatcher**    | Complementary: record deduplication before/after anonymization                                |

> **💡 You don't need to import TextDummy or TextParser directly** for anonymization workflows — `TextAnonymizer` instantiates and uses them internally.

---

## 2. Anonymization Fundamentals

### 2.1 What is anonymization?

**Anonymization** is the process of transforming personal data so that the individual it refers to can no longer be identified, either directly or indirectly. Unlike **pseudonymization**, which allows re-identification with additional information, true anonymization is irreversible.

```
┌──────────────────┐     Anonymization     ┌──────────────────┐
│  Original data    │ ───────────────────► │  Anonymous data    │
│  "Juan García"   │                       │  "[NAME]"         │
│  "12345678Z"     │                       │  "[ID_DOCUMENT]"  │
│  "juan@mail.com" │                       │  "[EMAIL]"        │
└──────────────────┘                       └──────────────────┘
```

### 2.2 Regulatory framework

The two main data protection regulations are **GDPR** (European Union) and **CCPA** (California, USA). Both require minimizing the use of personal data and providing anonymization or deletion mechanisms.

shadetriptxt facilitates technical compliance with these regulations through **12 locales** with country-specific PII patterns — the same locales used across `TextAnonymizer`, `TextDummy` and `TextParser`:

| Regulation               | Locales covered by shadetriptxt                                     |
| -------------------------- | ---------------------------------------------------------------- |
| **GDPR** (EU)        | `es_ES`, `fr_FR`, `de_DE`, `it_IT`, `pt_PT`, `en_GB` |
| **CCPA** (USA)       | `en_US`                                                        |
| **LGPD** (Brazil)    | `pt_BR`                                                        |
| Other local regulations    | `es_MX`, `es_AR`, `es_CO`, `es_CL`                       |

### 2.3 Types of personal data (PII)

shadetriptxt detects and anonymizes the following PII types:

| PII Type         | Examples                                           | Detection           |
| ---------------- | -------------------------------------------------- | ------------------- |
| `NAME`         | Juan García, John Smith                           | spaCy / NLTK NER    |
| `EMAIL`        | user@domain.com                                    | Universal regex     |
| `PHONE`        | +34 612 345 678, (555) 123-4567                    | Locale-specific regex |
| `ID_DOCUMENT`  | DNI 12345678Z, SSN 123-45-6789, CPF 123.456.789-09 | Locale-specific regex |
| `CREDIT_CARD`  | 4111 1111 1111 1111                                | Universal regex     |
| `IBAN`         | ES91 2100 0418 4502 0005 1332                      | Universal regex     |
| `IP_ADDRESS`   | 192.168.1.100, 2001:0db8::1                        | Universal regex     |
| `URL`          | https://example.com                                | Universal regex     |
| `DATE`         | 15/03/1990, 2024-01-15                             | Universal regex     |
| `CURRENCY`     | €1,234.56 / $100.00                               | Universal regex     |
| `LOCATION`     | Madrid, New York                                   | spaCy / NLTK NER    |
| `ORGANIZATION` | Acme Corp                                          | spaCy / NLTK NER    |
| `CUSTOM`       | User-defined patterns                              | Custom regex        |

---

## 3. Anonymization Techniques

### 3.1 Masking

Partially hides characters in the data while keeping the structure visible. Useful for audits where you need to verify the format without revealing the content.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale="es_ES", strategy="mask")
result = anon.anonymize_text("Email: juan.garcia@empresa.com, DNI: 12345678Z")
print(result.anonymized)
# → "Email: j***.g*****@*******.***,  DNI: 1*******Z"
```

**Also available at field level with TextParser:**

```python
from shadetriptxt.text_parser.text_normalizer import mask_text

# Mask a DNI
mask_text("12345678Z", keep_first=2, keep_last=1)
# → "12******Z"

# Mask an email preserving its structure
mask_text("juan.garcia@gmail.com", keep_first=1, keep_last=4, keep_chars="@.")
# → "j***.g*****@g****.com"

# Mask a credit card number
mask_text("4111111111111111", keep_first=4, keep_last=4)
# → "4111********1111"
```

### 3.2 Redaction (Redact)

Replaces PII with a label indicating the data type. This is the safest strategy — it completely removes the original data.

```python
from shadetriptxt.text_anonymizer import anonymize_text

result = anonymize_text(
    "Juan García, DNI 12345678Z, email juan@test.com",
    strategy="redact",
    locale="es_ES"
)
print(result.anonymized)
# → "Juan García, DNI [ID_DOCUMENT], email [EMAIL]"
```

### 3.3 Replacement with realistic data (Replace)

Replaces PII with realistic fake data generated internally by `TextDummy`. The generator uses the same locale configured in `TextAnonymizer`, producing names, emails, phone numbers and identity documents consistent with the country. Ideal for creating test datasets that maintain visual coherence.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale="es_ES", strategy="replace", seed=42)
result = anon.anonymize_text("Email: juan@empresa.com, teléfono +34 612 345 678")
print(result.anonymized)
# → "Email: maria.gomez@example.org, teléfono +34 698 234 567"
```

### 3.4 Pseudonymization (Pseudonymize)

**Consistent** replacement: the same input always produces the same output. Allows maintaining relationships between records without revealing identities.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

anon = TextAnonymizer(locale="es_ES", strategy="pseudonymize", seed=42)

# Same email → same replacement
r1 = anon.anonymize_text("Contact juan@test.com")
r2 = anon.anonymize_text("Forward to juan@test.com and pedro@test.com")
# "juan@test.com" will have the same replacement in both calls
```

### 3.5 Hashing

Replaces PII with a truncated SHA-256 hash. Irreversible and deterministic — useful for auditing and traceability without exposure.

```python
from shadetriptxt.text_anonymizer import anonymize_text

result = anonymize_text("DNI: 12345678Z", strategy="hash", locale="es_ES")
print(result.anonymized)
# → "DNI: 1c9f96328944"
```

### 3.6 Generalization (Generalize)

Reduces data precision while maintaining statistical utility. Transforms specific values into broader ranges or categories.

```python
from shadetriptxt.text_anonymizer import anonymize_text

# Dates → year only
result = anonymize_text("Born on 15/03/1990", strategy="generalize")
print(result.anonymized)
# → "Born on 1990"

# Emails → domain only
result = anonymize_text("Email: juan@empresa.com", strategy="generalize")
print(result.anonymized)
# → "Email: ***@empresa.com"
```

### 3.7 Suppression (Suppress)

Completely removes PII from the text, leaving an empty space.

```python
from shadetriptxt.text_anonymizer import anonymize_text

result = anonymize_text("Contact: juan@test.com, end", strategy="suppress")
print(result.anonymized)
# → "Contact: , end"
```

### 3.8 k-Anonymity, l-Diversity and t-Closeness

These three techniques protect tabular data (tables, DataFrames). Unlike the previous strategies that operate on individual text or fields, these work on the **entire dataset** to prevent re-identification by cross-referencing columns.

To understand them, you need to classify table columns into three categories:

| Category                       | Meaning                                                        | Example                      |
| ------------------------------- | -------------------------------------------------------------- | ----------------------------- |
| **Direct identifier**     | Identifies a person on its own                                 | Name, email, DNI              |
| **Quasi-identifier**      | Doesn't identify alone, but combined with others it can        | Age, city, zip code           |
| **Sensitive attribute**   | The data we want to protect                                    | Salary, medical diagnosis     |

#### k-Anonymity

The idea is simple: **each person must "hide" among at least *k-1* other people** with the same quasi-identifiers. If someone knows the person is 30 years old and lives in Madrid, they should find at least *k* matching rows, making it impossible to know which one is the real person.

```
Original table (k=1, no anonymity):
┌────────┬──────┬───────────┬─────────┐
│ Name   │ Age  │ City      │ Salary  │
├────────┼──────┼───────────┼─────────┤
│ Juan   │  25  │ Madrid    │ 30,000  │  ← Only one with 25+Madrid → identifiable
│ María  │  30  │ Madrid    │ 45,000  │
│ Pedro  │  28  │ Barcelona │ 28,000  │  ← Only one with 28+Barcelona → identifiable
│ Ana    │  30  │ Barcelona │ 50,000  │
└────────┴──────┴───────────┴─────────┘

After applying k-Anonymity (k=2):
┌──────────┬───────┬───────────┬─────────┐
│ Name     │ Age   │ City      │ Salary  │
├──────────┼───────┼───────────┼─────────┤
│ [SUPPR]  │ 25-30 │ Madrid    │ 30,000  │  ┐ Same group: 2 people
│ [SUPPR]  │ 25-30 │ Madrid    │ 45,000  │  ┘ → cannot distinguish
│ [SUPPR]  │ 25-30 │ Barcelona │ 28,000  │  ┐ Same group: 2 people
│ [SUPPR]  │ 25-30 │ Barcelona │ 50,000  │  ┘ → cannot distinguish
└──────────┴───────┴───────────┴─────────┘
```

- **Direct identifiers** (name) are removed.
- **Quasi-identifiers** (age) are generalized (25 → "25-30") until each combination has at least *k* rows.

#### l-Diversity

k-Anonymity has a weakness: if all members of a group have the **same sensitive value**, the attacker can deduce it. l-Diversity solves this by requiring each group to have at least *l* distinct values for the sensitive attribute.

```
Problem with k-Anonymity alone:
┌───────┬───────────┬─────────────┐
│ Age   │ City      │ Diagnosis   │
├───────┼───────────┼─────────────┤
│ 25-30 │ Madrid    │ Flu         │  ┐ Same group, SAME diagnosis
│ 25-30 │ Madrid    │ Flu         │  ┘ → If you know age+city, you know they have flu
└───────┴───────────┴─────────────┘

With l-Diversity (l=2):
┌───────┬───────────┬─────────────┐
│ Age   │ City      │ Diagnosis   │
├───────┼───────────┼─────────────┤
│ 25-30 │ Madrid    │ Flu         │  ┐ 2 distinct diagnoses
│ 25-30 │ Madrid    │ Allergy     │  ┘ → Cannot deduce which one
└───────┴───────────┴─────────────┘
```

#### t-Closeness

l-Diversity also has a gap: if a group has values very different from the global distribution, information can be inferred. t-Closeness requires that the **distribution of the sensitive attribute within each group be similar to the global distribution**, with a maximum difference of *t*.

```
Global salary distribution:   30K(33%), 45K(33%), 50K(33%)

Group "25-30, Madrid":
  With t-Closeness: salaries = 30K, 45K   → distribution similar to global ✓
  Without t-Closeness: salaries = 50K, 50K   → very different distribution ✗
                       (can deduce both earn 50K)
```

The smaller *t* is (from 0.0 to 1.0), the stricter the protection.

#### shadetriptxt Example

```python
import pandas as pd
from shadetriptxt.text_anonymizer import TextAnonymizer

df = pd.DataFrame({
    "nombre": ["Juan", "María", "Pedro", "Ana", "Luis", "Carmen"],
    "edad": [25, 30, 25, 30, 25, 30],
    "ciudad": ["Madrid", "Madrid", "Barcelona", "Barcelona", "Madrid", "Barcelona"],
    "salario": [30000, 45000, 28000, 50000, 32000, 47000],
})

anon = TextAnonymizer(locale="es_ES")

# k-Anonymity: "nombre" is suppressed, "edad"/"ciudad" are generalized
df_kanon = anon.anonymize_dataframe(
    df,
    identifiers=["nombre"],                      # → removed
    quasi_identifiers=["edad", "ciudad"],         # → generalized
    k=2,
)

# l-Diversity: also ensures diversity in "salario"
df_ldiv = anon.apply_l_diversity(
    df,
    sensitive_attrs=["salario"],
    quasi_identifiers=["edad", "ciudad"],
    l=2,
    identifiers=["nombre"],
)

# t-Closeness: the distribution of "salario" in each group
# differs no more than t=0.2 from the global distribution
df_tclose = anon.apply_t_closeness(
    df,
    sensitive_attrs=["salario"],
    quasi_identifiers=["edad", "ciudad"],
    t=0.2,
    identifiers=["nombre"],
)

# Measure privacy metrics on the result
report = anon.measure_privacy(
    df_kanon,
    quasi_identifiers=["edad", "ciudad"],
    sensitive_attrs=["salario"],
)
print(f"k-anonymity: {report.k_anonymity}")    # ≥ 2
print(f"l-diversity: {report.l_diversity}")     # ≥ 2
print(f"t-closeness: {report.t_closeness:.4f}") # ≤ 0.2
```

#### Which one to use?

| Scenario                                       | Recommended technique                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------------------------- |
| Demographics, simple surveys                    | **k-Anonymity** is sufficient                                                   |
| Medical data, salaries, sensitive information   | **l-Diversity** (protects against value inference)                              |
| Financial data, research, publication           | **t-Closeness** (strictest, protects against distribution inference)            |

The three techniques are cumulative: t-Closeness implies l-Diversity, which in turn implies k-Anonymity.

---

## 4. shadetriptxt Tools

`TextAnonymizer` is the **single point of anonymization**. It integrates all techniques — built-in, internal modules, and external libraries — under a single API:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TextAnonymizer                                │
│                  (single point of anonymization)                     │
│                                                                      │
│   ┌─────────────────── Built-in techniques ───────────────────┐     │
│   │  mask · redact · hash · generalize · suppress             │     │
│   │  Regex PII detection (15 types, 12 locales)               │     │
│   │  Per-type strategy dispatch                               │     │
│   │  Pseudonymization cache                                   │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│   ┌─────────────────── Internal modules ──────────────────────┐     │
│   │                                                            │     │
│   │  TextDummy ─── fake data generation (replace,             │     │
│   │                 pseudonymize, id_document, iban...)        │     │
│   │                                                            │     │
│   │  TextParser ── normalization, extraction, mask_text        │     │
│   │                                                            │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│   ┌─────────────────── External libraries ────────────────────┐     │
│   │                                                            │     │
│   │  spaCy ────── NER: names, locations, organizations        │     │
│   │  NLTK ─────── NER fallback                                │     │
│   │  python-anonymity ─ k-anonymity, l-diversity, t-closeness │     │
│   │  pycanon ──── privacy metrics                             │     │
│   │                                                            │     │
│   └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  TextMatcher (complementary)                                         │
│  Deduplicate records before/after anonymization                      │
└──────────────────────────────────────────────────────────────────────┘
```

### What does each layer provide?

| Layer | Component | Techniques covered |
|------|-----------|-------------------|
| **Built-in** | TextAnonymizer | `mask`, `redact`, `hash`, `generalize`, `suppress`, regex detection, per-type dispatch |
| **Internal** | TextDummy (lazy) | `replace`, `pseudonymize` — generates fake names, emails, IDs, IBANs, phones with the correct locale |
| **Internal** | TextParser (lazy) | Pre-anonymization normalization, configurable `mask_text`, PII extraction, document validation |
| **External** | spaCy / NLTK | NER detection of names, addresses, organizations in free text |
| **External** | python-anonymity | k-anonymity, l-diversity, t-closeness on DataFrames |
| **External** | pycanon | Privacy metric measurement (post-anonymization verification) |

> **Design principle**: Everything is managed from `TextAnonymizer`. When you use `strategy="replace"`, it internally creates a `TextDummy` instance with the same locale and seed. When you need to normalize text, `TextParser` is available as a complementary tool. External libraries are only imported when you invoke their specific functionality.

### 4.1 External dependencies

shadetriptxt uses **lazy loading** for all heavy dependencies: they are only imported when the functionality that needs them is invoked. This allows you to install only what you need.

**Internal modules** (always available — `TextAnonymizer` instantiates them automatically):

| Module | Used when | Purpose |
|--------|-----------|---------|
| `TextDummy` | Strategy `replace` or `pseudonymize` | Generates realistic locale-aware fake data (names, emails, IDs, IBANs, phones...) |
| `TextParser` | Pre-anonymization normalization | Text cleanup, PII extraction, `mask_text`, document validation |

**Required dependencies** (always installed with `pip install shadetriptxt`):

| Package | Purpose |
|---------|---------|
| `faker` | Underlying fake data generation engine (used by `TextDummy`, which in turn is used by `TextAnonymizer`) |
| `email-validator` | Email address validation |
| `flashtext` | Fast keyword processing (FlashText algorithm) |

**Optional dependencies** — installed on demand based on the features you need:

```bash
# For NLP-based PII detection (names, addresses, organizations in free text)
pip install shadetriptxt[anonymizer]

# For all features
pip install shadetriptxt[full]
```

| Package | Group | Used in | Purpose |
|---------|-------|---------|---------|
| `spacy` (≥ 3.5.0) | `anonymizer` | `TextAnonymizer` with `use_spacy=True` | NLP entity detection (names, locations, organizations) |
| `nltk` (≥ 3.8.0) | `anonymizer` | `TextAnonymizer` with `use_nltk=True` | NER fallback when spaCy is not available |
| `python-anonymity` (≥ 0.0.1) | `anonymizer` | `anonymize_dataframe()`, `k_anonymity()`, `l_diversity()`, `t_closeness()` | Statistical anonymization on DataFrames |
| `pycanon` (≥ 1.0.0) | `anonymizer` | `measure_privacy()` | Privacy metric measurement (k, l, t) |
| `pandas` (≥ 1.5.0) | `anonymizer` | All DataFrame functions | Tabular operations |
| `formulite` | `full` | `TextMatcher` | String similarity algorithms |

> **💡 Note**: If you try to use a feature whose dependency is not installed, shadetriptxt raises an `ImportError` with clear installation instructions. No guesswork needed.

---

## 5. Use Cases

### 5.1 Generate test data for development and testing

**Problem**: You need to populate a development database with realistic data without using real production data.

**Solution**: Use `TextDummy` to generate synthetic data with coherent structure per locale.

```python
from pydantic import BaseModel
from typing import Annotated, Optional
from shadetriptxt.text_dummy.text_dummy import TextDummy, DummyField

# Define the data model
class Empleado(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    telefono: str
    dni: str
    departamento: str
    cargo: str
    salario: float
    fecha_nacimiento: str
    ciudad: str
    codigo_postal: str
    iban: str
    activo: bool

# Generate data for Spain
gen = TextDummy("es_ES")

# A single employee
empleado = gen.fill_model(Empleado)
print(empleado)
# Empleado(id=1, nombre='María', apellido='García', email='maria@ejemplo.com', ...)

# Batch of 100 employees
empleados = gen.fill_model_batch(Empleado, count=100)

# As a list of dictionaries (ideal for database inserts)
registros = gen.to_records(Empleado, count=1000)

# As columnar format (ideal for DataFrames)
import pandas as pd
df = pd.DataFrame(gen.to_columns(Empleado, count=1000))
print(df.head())
```

**With custom fields using DummyField:**

```python
class Producto(BaseModel):
    codigo: Annotated[str, DummyField("unique_key", prefix="PRD-", length=6, key_type="hex")]
    nombre: Annotated[str, DummyField("product_name")]
    referencia: Annotated[str, DummyField("product_sku")]
    precio: float
    categoria: Annotated[str, DummyField("product_category")]
    ean: Annotated[str, DummyField("ean13")]

gen = TextDummy("es_ES")
productos = gen.fill_model_batch(Producto, count=50)
```

**Custom generators for domain-specific data:**

```python
import random

gen = TextDummy("es_ES")

# Register business-specific data types
gen.register_custom("nivel_acceso", ["Básico", "Intermedio", "Avanzado", "Admin"])
gen.register_custom("codigo_centro", lambda: f"CTR-{random.randint(100, 999)}")
gen.register_custom("turno", ["Mañana", "Tarde", "Noche", "Rotativo"])

# Use them via DummyField in models
class Trabajador(BaseModel):
    nombre: str
    nivel: Annotated[str, DummyField("nivel_acceso")]     # Custom
    centro: Annotated[str, DummyField("codigo_centro")]   # Custom
    turno: Annotated[str, DummyField("turno")]            # Custom
```

### 5.2 Mask sensitive data in free text

**Problem**: You have logs, emails or documents containing personal data and need to hide them before sharing with development or support teams.

**Solution**: Use `TextAnonymizer` to automatically detect and anonymize PII.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer, Strategy, PiiType

# Text with multiple PII types
texto = (
    "El cliente Juan García López con DNI 12345678Z vive en "
    "Calle Mayor 15, Madrid 28001. Su email es juan.garcia@empresa.com "
    "y su teléfono es +34 612 345 678. Nacido el 15/03/1990. "
    "IP de acceso: 192.168.1.100. Visita https://www.ejemplo.com"
)

# Basic strategy: redact everything
anon = TextAnonymizer(locale="es_ES", strategy="redact")
result = anon.anonymize_text(texto)
print(result.anonymized)

# Mixed strategies by PII type
anon = TextAnonymizer(locale="es_ES", strategy="redact")
anon.set_strategy("mask", pii_type=PiiType.EMAIL)           # Emails: mask
anon.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)     # DNIs: hash
anon.set_strategy("suppress", pii_type=PiiType.IP_ADDRESS)  # IPs: remove

result = anon.anonymize_text(texto)
print(result.anonymized)

# View summary of what was anonymized
summary = anon.summary(result)
print(f"Entities detected: {summary['total_entities']}")
print(f"By type: {summary['by_type']}")
```

**Granular masking with `mask_text`:**

```python
from shadetriptxt.text_parser.text_normalizer import mask_text

# Specific masking cases
datos = {
    "dni": "12345678Z",
    "email": "juan.garcia@empresa.com",
    "telefono": "+34 612 345 678",
    "iban": "ES9121000418450200051332",
    "tarjeta": "4111111111111111",
}

for campo, valor in datos.items():
    if campo == "email":
        masked = mask_text(valor, keep_first=1, keep_last=4, keep_chars="@.")
    elif campo == "tarjeta":
        masked = mask_text(valor, keep_first=4, keep_last=4)
    elif campo == "iban":
        masked = mask_text(valor, keep_first=4, keep_last=4)
    else:
        masked = mask_text(valor, keep_first=2, keep_last=1)
    print(f"  {campo}: {valor} → {masked}")
```

### 5.3 Anonymize records and dictionaries

**Problem**: You have records (dictionaries or lists) with customer data and need to anonymize them while preserving the structure.

**Solution**: `TextAnonymizer` automatically detects which fields contain PII based on field names.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer, anonymize_dict, PiiType

# Field names are auto-detected
registro = {
    "nombre": "María López García",
    "email": "maria.lopez@empresa.com",
    "telefono": "+34 698 123 456",
    "dni": "87654321X",
    "direccion": "Calle Gran Vía 42, Madrid",
    "fecha_nacimiento": "22/07/1988",
    "salario": 45000,               # Not PII — left untouched
    "departamento": "Marketing",     # Not PII — left untouched
}

# Quick anonymization with convenience function
anonimizado = anonymize_dict(registro, strategy="mask", locale="es_ES")
print(anonimizado)
# nombre: "M**** L**** G*****"
# email:  "m****@*******.***"
# dni:    "8*******X"
# ...but salario and departamento remain intact

# Batch records
registros = [
    {"nombre": "Ana García", "email": "ana@test.com", "edad": 25},
    {"nombre": "Pedro Ruiz", "email": "pedro@test.com", "edad": 30},
    {"nombre": "Luis Fernández", "email": "luis@test.com", "edad": 28},
]

anon = TextAnonymizer(locale="es_ES", strategy="pseudonymize", seed=42)
anonimizados = anon.anonymize_records(registros)
# Pseudonymization is consistent: if "Ana García" appears in another
# record, it will get the same replacement
```

**Fields with non-standard names — explicit mapping:**

```python
registro_custom = {
    "codigo_empleado": "EMP-1234",
    "nombre_completo": "Carlos Martínez",
    "correo_personal": "carlos@gmail.com",
    "num_seguridad_social": "12345678Z",
}

anonimizado = anon.anonymize_dict(
    registro_custom,
    field_types={
        "codigo_empleado": PiiType.ID_DOCUMENT,
        "nombre_completo": PiiType.NAME,
        "correo_personal": PiiType.EMAIL,
        "num_seguridad_social": PiiType.ID_DOCUMENT,
    }
)
```

**Field whitelist — anonymize only the fields you specify (`fields`):**

By default, all fields matching auto-detection are anonymized. With the `fields` parameter you can restrict anonymization to **only** the specified fields — the rest are left untouched:

```python
registro = {
    "nombre": "Juan García",
    "email": "juan@test.com",
    "telefono": "+34 612 345 678",
    "salario": 45000,
    "departamento": "Marketing",
}

# Without fields → auto-detection anonymizes nombre, email, telefono
resultado = anon.anonymize_dict(registro, strategy="redact")
# → {"nombre": "[NAME]", "email": "[EMAIL]", "telefono": "[PHONE]",
#    "salario": 45000, "departamento": "Marketing"}

# With fields → only email and telefono are anonymized
resultado = anon.anonymize_dict(registro, strategy="redact", fields=["email", "telefono"])
# → {"nombre": "Juan García", "email": "[EMAIL]", "telefono": "[PHONE]",
#    "salario": 45000, "departamento": "Marketing"}
```

Can be combined with `field_types` for non-standard field names:

```python
resultado = anon.anonymize_dict(
    {"codigo": "12345678Z", "nombre": "Ana", "notas": "texto"},
    fields=["codigo"],                                 # Only this field
    field_types={"codigo": PiiType.ID_DOCUMENT},       # Specify PII type
)
# → {"codigo": "[ID_DOCUMENT]", "nombre": "Ana", "notas": "texto"}
```

Works the same on batches and DataFrames:

```python
# Record batches
anon.anonymize_records(registros, fields=["email", "telefono"])

# DataFrames (parameter is called 'columns')
anon.anonymize_columns(df, columns=["email", "telefono"])
```

### 5.4 Anonymize DataFrames with k-Anonymity

**Problem**: You need to publish or share a tabular dataset ensuring no individual can be re-identified by the combination of their attributes.

**Solution**: Apply k-anonymity, l-diversity or t-closeness with `TextAnonymizer`.

```python
import pandas as pd
from shadetriptxt.text_anonymizer import TextAnonymizer

# Sample dataset
df = pd.DataFrame({
    "nombre": ["Juan García", "María López", "Pedro Ruiz",
               "Ana Martín", "Luis Sánchez", "Carmen Torres"],
    "email": ["juan@mail.com", "maria@mail.com", "pedro@mail.com",
              "ana@mail.com", "luis@mail.com", "carmen@mail.com"],
    "edad": [25, 30, 25, 30, 25, 30],
    "ciudad": ["Madrid", "Madrid", "Barcelona", "Barcelona", "Madrid", "Barcelona"],
    "salario": [30000, 45000, 28000, 50000, 32000, 47000],
})

anon = TextAnonymizer(locale="es_ES")

# 1. Anonymize columns by name (auto-detection)
df_masked = anon.anonymize_columns(df, strategy="mask")
# "nombre" and "email" are masked; "edad", "ciudad" and "salario" are not

# 2. k-Anonymity (requires python-anonymity)
df_kanon = anon.anonymize_dataframe(
    df,
    identifiers=["nombre", "email"],        # Removed
    quasi_identifiers=["edad", "ciudad"],   # Generalized
    k=2,                                     # At least 2 people per group
)

# 3. l-Diversity
df_ldiv = anon.apply_l_diversity(
    df,
    sensitive_attrs=["salario"],
    quasi_identifiers=["edad", "ciudad"],
    l=2,
    identifiers=["nombre", "email"],
)

# 4. Measure privacy metrics
report = anon.measure_privacy(
    df_kanon,
    quasi_identifiers=["edad", "ciudad"],
    sensitive_attrs=["salario"],
)
print(f"k = {report.k_anonymity}")
print(f"l = {report.l_diversity}")
print(f"t = {report.t_closeness:.4f}")
```

### 5.5 Normalize and clean text before anonymizing

**Problem**: Input data has inconsistencies (extra spaces, accents, abbreviations, mojibake) that hinder correct PII detection.

**Solution**: Use `TextParser` to normalize and prepare text before passing it to the anonymizer.

```python
from shadetriptxt.text_parser.text_parser import TextParser
from shadetriptxt.text_parser.text_normalizer import normalize_text, mask_text
from shadetriptxt.text_anonymizer import TextAnonymizer

# 1. Normalize text
parser = TextParser("es_ES")

texto_sucio = "  José   García-López  (CEO)   EMPRESA S.L.  "
limpio = parser.normalize(texto_sucio)
print(limpio)  # "jose garcia lopez empresa sl"

# 2. Expand abbreviations
texto_abreviado = "C/ Mayor, 15 - Esc. 3ª - 1º Dcha."
expandido = parser.expand_abbreviations(texto_abreviado)
print(expandido)  # "Calle Mayor, 15 - Escalera 3ª - 1º Derecha"

# 3. Extract PII for later anonymization
parser = TextParser("es_ES")
texto = "Llamar al +34 612 345 678 o escribir a juan@test.com"

telefonos = parser.extract_phones(texto)
emails = parser.extract_emails(texto)
print(f"Phones: {telefonos}")
print(f"Emails: {emails}")

# 4. Fix mojibake before anonymizing
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer

fixer = EncodingFixer(language="es")
texto_roto = "JosÃ© GarcÃ­a â€" informaciÃ³n"
texto_reparado = fixer.fix(texto_roto)
print(texto_reparado)  # "José García — información"

# Now anonymize with clean data
anon = TextAnonymizer(locale="es_ES", strategy="redact")
result = anon.anonymize_text(texto_reparado)
```

### 5.6 Detect anonymized duplicates with TextMatcher

**Problem**: After anonymizing data, you need to verify there are no duplicate records, or you need to deduplicate before anonymizing to maintain consistency.

**Solution**: Use `TextMatcher` with flexible configurations to handle name and data variations.

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig

# Lenient configuration for names (common variations)
config = MatcherConfig.lenient()
matcher = TextMatcher(config=config)

# Compare names with variations
resultado = matcher.compare_names("García", "Garcia")
print(f"Match: {resultado.is_match}, Score: {resultado.score:.2f}")
# → Match: True

# Compare full names token by token
resultado = matcher.compare_name_bytokens("Juan García López", "García López, Juan")
print(f"Match: {resultado.is_match}, Score: {resultado.score:.2f}")

# Detect duplicates in a list
nombres = [
    "Juan García López",
    "María López García",
    "Juan Garcia Lopez",     # Duplicate (no accents)
    "García López, Juan",    # Duplicate (reordered)
    "María López",           # Possible partial duplicate
]

duplicados = matcher.detect_duplicates(nombres)
for grupo in duplicados:
    print(f"  Group: {grupo}")
```

**Find the best match in a catalog:**

```python
# Before anonymizing, unify records
catalogo = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"]
resultado = matcher.find_best_match("Madrit", catalogo)  # typo
print(f"Best match: {resultado}")  # → "Madrid"
```

### 5.7 Full pipeline: detection, validation and anonymization

**Problem**: You need an end-to-end pipeline that detects, validates and anonymizes personal data systematically.

**Why is validation necessary?** Anonymization relies on detecting known patterns (DNI format, email structure, phone prefixes, etc.). If input data doesn't match those patterns — for example, a DNI with spaces, an uppercase email with extra characters, or a phone without an international prefix — the detection engine doesn't recognize them and, therefore, **doesn't anonymize them**. Validating before anonymizing ensures every sensitive datum fits the expected pattern and gets processed correctly.

```
Raw data                → Detected?  → Anonymized?
────────────────────────────────────────────────────────
"12345678Z"             →     ✔      →     ✔         (valid DNI pattern)
"12 345 678 Z"          →     ✘      →     ✘         (spaces break the pattern)
"juan@test.com"         →     ✔      →     ✔         (valid email)
"  JUAN @ TEST . COM "  →     ✘      →     ✘         (spaces and broken format)

Solution: normalize and validate FIRST → all data fits → complete anonymization.
```

**Solution**: Combine the four shadetriptxt modules in an integrated pipeline: normalize → validate → anonymize → replace.

```python
from shadetriptxt.text_parser.text_parser import TextParser
from shadetriptxt.text_parser.text_normalizer import normalize_text
from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType
from shadetriptxt.text_dummy.text_dummy import TextDummy

# ── Step 1: Normalize input ──
# Remove extra spaces and standardize format so detection
# patterns work correctly.
parser = TextParser("es_ES")
texto_raw = "  Juan   García  López, DNI:12 345 678Z, email: JUAN @ TEST.COM  "
texto_limpio = parser.normalize(texto_raw, remove_accents=False)
# Result: "Juan García López, DNI:12345678Z, email: juan@test.com"

# ── Step 2: Validate that PII matches expected patterns ──
# Without this step, malformatted data would escape anonymization.
emails = parser.extract_emails(texto_limpio)      # Extracts only valid emails
telefonos = parser.extract_phones(texto_limpio)    # Extracts only valid phones
dni_valido = parser.nif_parse("12345678Z")         # Validates DNI structure

if not dni_valido:
    print("⚠ Invalid DNI: cannot anonymize reliably")

# ── Step 3: Anonymize with mixed strategies ──
# Now that data is normalized and validated, detection is reliable.
anon = TextAnonymizer(locale="es_ES", strategy="redact", seed=42)
anon.set_strategy("mask", pii_type=PiiType.EMAIL)
anon.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)
anon.set_strategy("pseudonymize", pii_type=PiiType.NAME)

result = anon.anonymize_text(texto_limpio)
print(f"Anonymized: {result.anonymized}")
print(f"Entities detected: {len(result.entities)}")
print(f"Replacement map: {result.replacements}")

# ── Step 4: Generate alternative replacement data ──
gen = TextDummy("es_ES")
print(f"Fake name:  {gen.name()}")
print(f"Fake email: {gen.email()}")
print(f"Fake DNI:   {gen.id_document()}")
```

### 5.8 Generate complete development environments

**Problem**: You need to create a complete development database with multiple related tables and coherent data.

**Solution**: Use `TextDummy` with Pydantic models, custom generators and `autoincrement`.

```python
from pydantic import BaseModel
from typing import Annotated, Optional, List
from shadetriptxt.text_dummy.text_dummy import TextDummy, DummyField

# ── Data models ──
class Cliente(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    telefono: str
    dni: str
    ciudad: str
    codigo_postal: str
    fecha_alta: Annotated[str, DummyField("random_date", start="2020-01-01")]

class Pedido(BaseModel):
    id: Annotated[str, DummyField("autoincrement", start=1000, prefix="PED-", zfill=6)]
    id_cliente: Annotated[int, DummyField("random_number", min_val=1, max_val=100)]
    producto: Annotated[str, DummyField("product_name")]
    cantidad: Annotated[int, DummyField("random_number", min_val=1, max_val=20)]
    precio: float
    estado: Annotated[str, DummyField("order_status")]
    fecha: Annotated[str, DummyField("random_date", start="2024-01-01")]
    tracking: Annotated[str, DummyField("tracking_number")]
    factura: Annotated[str, DummyField("invoice_number")]

# ── Bulk generation ──
gen = TextDummy("es_ES")

# 100 customers
clientes = gen.to_records(Cliente, count=100)

# 500 orders
pedidos = gen.to_records(Pedido, count=500)

# Create DataFrames
import pandas as pd
df_clientes = pd.DataFrame(clientes)
df_pedidos = pd.DataFrame(pedidos)

print(f"Customers: {len(df_clientes)} records")
print(df_clientes.head())
print(f"\nOrders: {len(df_pedidos)} records")
print(df_pedidos.head())
```

### 5.9 Multi-language anonymization

**Problem**: Your organization operates in multiple countries and you need to detect and anonymize PII in multiple languages, each with its own document, phone and address formats.

**Solution**: shadetriptxt supports 12 locales with country-specific patterns.

```python
from shadetriptxt.text_anonymizer import TextAnonymizer

# Texts with PII from different countries
textos = {
    "es_ES": "Cliente: Juan García, DNI 12345678Z, tel +34 612 345 678",
    "en_US": "Customer: John Smith, SSN 123-45-6789, phone (555) 123-4567",
    "pt_BR": "Cliente: João Silva, CPF 123.456.789-09, tel +55 11 91234-5678",
    "fr_FR": "Client: Jean Dupont, NIR 1 85 05 78 006 084 36, tél +33 6 12 34 56 78",
    "de_DE": "Kunde: Hans Müller, tel +49 30 12345678",
    "it_IT": "Cliente: Marco Rossi, CF RSSMRC85M10H501Z, tel +39 06 12345678",
}

for locale, texto in textos.items():
    anon = TextAnonymizer(locale=locale, strategy="redact")
    result = anon.anonymize_text(texto)
    print(f"\n[{locale}]")
    print(f"  Original:    {texto}")
    print(f"  Anonymized:  {result.anonymized}")
    for e in result.entities:
        print(f"    → {e.pii_type.value}: '{e.text}'")
```

**Generate fake data by country:**

```python
from shadetriptxt.text_dummy.text_dummy import TextDummy

locales = ["es_ES", "en_US", "pt_BR", "fr_FR", "de_DE", "it_IT"]

for locale in locales:
    gen = TextDummy(locale)
    info = gen.locale_info()
    print(f"\n[{locale}] {info['country']} ({info['language']})")
    print(f"  Name:        {gen.name()}")
    print(f"  Email:       {gen.email()}")
    print(f"  Phone:       {gen.phone()}")
    print(f"  ID Document: {gen.id_document()} ({info['id_document']})")
    print(f"  Price:       {gen.price()}")
    print(f"  IBAN:        {gen.iban()}")
    print(f"  Date:        {gen.date()}")
```

---

## 6. Strategy Comparison

| Strategy             | Reversible | Preserves format | Consistent | Statistical utility | Ideal use case                                     |
| ---------------------- | :--------: | :--------------: | :---------: | :-------------------: | -------------------------------------------------- |
| **Redact**       |     No     |        No        |     Yes    |          No          | Logs, legal documents                              |
| **Mask**         |     No     |       Yes       |     No     |          No          | Audits, format verification                        |
| **Replace**      |     No     |       Yes       |     No     |       Partial        | Demos, test environments                           |
| **Pseudonymize** |    Yes*   |       Yes       |     Yes    |       Partial        | Longitudinal analysis, record relationships        |
| **Hash**         |     No     |        No        |     Yes    |          No          | Traceability, technical auditing                   |
| **Generalize**   |     No     |      Partial    |     Yes    |          Yes         | Statistical analysis, reporting                    |
| **Suppress**     |     No     |        No        |     Yes    |          No          | Total removal, maximum privacy                     |

*\* Pseudonymize is reversible only if the internal mapping is preserved.*

### When to use each strategy?

```
Do you need to maintain statistical utility?
├── Yes → GENERALIZE or k-ANONYMITY
│
├── Do you need to maintain relationships between records?
│   ├── Yes → PSEUDONYMIZE
│   └── No → Do you need visually realistic data?
│       ├── Yes → REPLACE
│       └── No → Do you need to see the original format?
│           ├── Yes → MASK
│           └── No → REDACT or SUPPRESS
│
└── Is it for technical auditing?
    ├── Yes → HASH
    └── No → REDACT
```

---

## 7. Best Practices

### Development and testing

1. **Never use real data in development environments**.
   Production data contains real PII. A leak in a development environment — which typically has fewer access controls — can result in a data breach with legal consequences. Use `TextDummy.fill_model()` to generate synthetic data that maintains the structure and data types without exposing anyone.

   ```python
   # ✅ Correct: synthetic data that looks real
   gen = TextDummy("es_ES", seed=42)
   cliente_test = gen.fill_model(Cliente)

   # ❌ Wrong: copy a production table to the test environment
   ```
2. **Generate data with the correct locale**.
   A Spanish DNI (`12345678Z`) does not have the same format as a Portuguese NIF (`123456789`) or an American SSN (`123-45-6789`). If you generate data with the wrong locale, your tests won't cover the system's real validations. Always configure the locale that matches your users' country.

   ```python
   gen_es = TextDummy("es_ES")   # DNI: 12345678Z, phone: +34 6XX XXX XXX
   gen_us = TextDummy("en_US")   # SSN: 123-45-6789, phone: +1 (XXX) XXX-XXXX
   gen_br = TextDummy("pt_BR")   # CPF: XXX.XXX.XXX-XX, phone: +55 XX XXXXX-XXXX
   ```
3. **Use `seed` for reproducible data**.
   Without a fixed seed, each test run generates different random data. If a test fails, you can't reproduce it exactly. With a fixed seed, the generator always produces the same data, enabling deterministic debugging and cross-run comparisons.

   ```python
   gen = TextDummy("es_ES", seed=42)
   print(gen.name())  # Always generates the same name → reproducible test
   ```

### Anonymization

4. **Combine regex + NLP detection for maximum coverage**.
   Regular expressions are fast and precise for structured data (DNI, email, phone, IBAN), but they don't detect proper names or addresses in free text. NLP models (spaCy, NLTK) recognize entities by semantic context, but may fail with technical formats. Combining both methods covers both structured patterns and natural language entities.

   ```python
   anon = TextAnonymizer(
       locale="es_ES",
       use_regex=True,    # Detects DNI, email, phone, IBAN...
       use_spacy=True     # Detects names, addresses, organizations...
   )
   ```
5. **Use different strategies per PII type**.
   Not all sensitive data carries the same risk. A name can be pseudonymized (replaced with a fictitious one) to maintain readability, while a credit card number should be masked or suppressed entirely. Assigning the appropriate strategy to each PII type balances privacy and data utility.

   ```python
   anon.set_strategy("pseudonymize", pii_type=PiiType.NAME)         # Readable
   anon.set_strategy("mask", pii_type=PiiType.EMAIL)                 # j***@***.com
   anon.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)           # Irreversible
   anon.set_strategy("suppress", pii_type=PiiType.CREDIT_CARD)       # Removed
   ```
6. **Always normalize before anonymizing**.
   As explained in use case 5.7, anonymization depends on pattern detection. If data contains extra spaces, inconsistent capitalization, or junk characters, detection patterns fail and PII passes through unanonymized. `TextParser.normalize()` ensures data is in a clean, uniform format before processing.
7. **Validate identity documents before anonymizing**.
   If you hash or mask an invalid DNI (e.g., `99999999X` with an incorrect check letter), you're anonymizing garbage: the result looks protected but the original data wasn't real. Validating with `nif_parse()` or `european_nif()` detects invented or erroneous data before processing. **Don't waste resources on bad data.** Anonymization consumes compute time (especially cryptographic hashing and NLP-based pseudonymization). If a significant percentage of records contains fake DNIs, malformed emails, or incorrectly formatted phone numbers, you're running an expensive pipeline on worthless data. Validating first lets you filter or correct those records, focusing resources only on real data that needs protection.

   ```python
   from shadetriptxt.text_parser.text_parser import TextParser

   parser = TextParser("es_ES")
   registros = ["12345678Z", "99999999X", "X1234567L", "INVALIDO"]

   for doc in registros:
       valido = parser.nif_parse(doc)
       if valido:
           # Only anonymize valid documents → resource savings
           print(f"✔ {doc} → proceed to anonymize")
       else:
           print(f"✘ {doc} → discard or correct before anonymizing")
   ```

### Data pipeline

8. **Deduplicate before anonymizing**.
   If the same person appears 3 times with name variations ("Juan García", "J. García López", "GARCIA, Juan"), anonymization will generate 3 different pseudonyms for the same person. By deduplicating first with `TextMatcher.detect_duplicates()`, you unify records and ensure each real identity maps to a single anonymized value, avoiding inconsistencies.
9. **Measure privacy metrics after processing**.
   Anonymizing does not automatically guarantee privacy. An anonymized dataset can still be vulnerable to re-identification attacks if quasi-identifiers (age, zip code, gender) are too specific. Use `measure_privacy()` to verify the result meets adequate k-anonymity, l-diversity, or t-closeness thresholds.

   ```python
   metrics = anon.measure_privacy(df_anonimizado, quasi_identifiers=["edad", "cp", "genero"])
   print(f"k = {metrics['k_anonymity']}")  # Target: k ≥ 5
   ```
10. **Register custom patterns for domain-specific PII**.
    Default patterns cover universal PII (DNI, email, phone), but every organization has its own sensitive data: policy numbers, employee codes, medical identifiers, etc. Use `add_pattern()` so the detection engine recognizes and anonymizes them automatically.

    ```python
    # Detect medical record numbers: HC-XXXXXXX
    anon.add_pattern(
        name="medical_record",
        pattern=r"HC-\d{7}",
        pii_type="MEDICAL_ID"
    )
    ```

### Security

11. **Never log real data**.
    Log files typically have looser permissions, are rotated with less control, and are often shared in support tickets. If a log contains a real DNI, email, or name, it's a silent data breach. Use `TextDummy` to generate example data in logs, documentation, and error messages.
12. **Don't hardcode PII in tests**.
    An `assert result.name == "Juan García López"` with a real name in source code means PII is compromised in every repository clone for life (even if deleted later, it remains in Git history). Always generate test data with `TextDummy`.
13. **Pseudonymization is not anonymization**.
    Pseudonymization replaces real data with aliases, but if you keep the mapping table (`"Juan García" → "Carlos Ruiz"`), the data is still personal and reversible under GDPR. For data to be truly anonymous, it must be **irreversible**: nobody, not even you, can recover the original. If you need irreversibility, use `hash` or `suppress`.

    ```
    Pseudonymization (reversible):       Anonymization (irreversible):
    ┌─────────────┐   mapping  ┌──────┐  ┌─────────────┐   hash    ┌──────────────┐
    │ Juan García │ ────────► │Carlos│  │ Juan García │ ────────► │ a3f2b9c1...  │
    └─────────────┘  (exists) └──────┘  └─────────────┘  (no      └──────────────┘
                     ▲ can be                  way back)
                     │ reversed
    ```
14. **Document the techniques applied to each field**.
    In an audit or access request (ARCO/DSAR), you need to demonstrate what treatment was applied to each piece of data: which fields were masked, which were hashed, which were suppressed. Without this documentation, you cannot prove regulatory compliance.

    `AnonymizationResult` already returns the information needed to build this record:

    - `entities` → each `DetectedEntity` includes the PII type (`pii_type`), original text, position, detection source (`regex`/`spacy`/`nltk`), and confidence level.
    - `replacements` → mapping of each original value to its anonymized version.
    - The strategy applied to each type can be queried from the `TextAnonymizer` instance.

    ```python
    from datetime import datetime
    from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType, Strategy

    anon = TextAnonymizer(locale="es_ES", strategy="redact")
    anon.set_strategy("mask", pii_type=PiiType.EMAIL)
    anon.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)
    anon.set_strategy("pseudonymize", pii_type=PiiType.NAME)

    result = anon.anonymize_text("Juan García, DNI 12345678Z, email juan@test.com")

    # ── Build audit log ──
    audit_log = {
        "timestamp": datetime.now().isoformat(),
        "locale": anon.locale,
        "default_strategy": anon.strategy.value,
        "fields": [
            {
                "original": ent.text,
                "pii_type": ent.pii_type.value,
                "strategy": anon._strategy_for(ent.pii_type).value,
                "replacement": result.replacements.get(ent.text),
                "detection_source": ent.source,
                "confidence": ent.confidence,
            }
            for ent in result.entities
        ],
    }
    # audit_log:
    # {
    #   "timestamp": "2026-02-12T10:30:00",
    #   "locale": "es_ES",
    #   "default_strategy": "redact",
    #   "fields": [
    #     {"original": "Juan García", "pii_type": "NAME",
    #      "strategy": "pseudonymize", "replacement": "Carlos Ruiz", ...},
    #     {"original": "12345678Z", "pii_type": "ID_DOCUMENT",
    #      "strategy": "hash", "replacement": "a3f2b9c1...", ...},
    #     {"original": "juan@test.com", "pii_type": "EMAIL",
    #      "strategy": "mask", "replacement": "j***@***.com", ...},
    #   ]
    # }
    ```

---

## Examples

All code examples referenced in this guide are available in `shadetriptxt/text_anonymizer/examples/`, organized by theme:

| File                      | Theme                    | Guide sections covered                                                   |
| ------------------------- | ------------------------ | ------------------------------------------------------------------------ |
| `text_strategies.py`    | Text Anonymization       | 3.1–3.7 Techniques, 5.2 Mask sensitive data in free text                |
| `dict_records.py`       | Records & Dictionaries   | 5.3 Anonymize records and dictionaries (incl. field whitelist)           |
| `dataframe_privacy.py`  | DataFrame & Privacy      | 3.8 k-Anonymity/l-Diversity/t-Closeness, 5.4 DataFrame anonymization    |
| `multi_locale.py`       | Multi-locale             | 5.9 Multi-language anonymization + fake data by country                  |
| `full_pipeline.py`      | Full Pipeline            | 5.5 Normalize, 5.7 Detection -> validation -> anonymize                 |
| `test_anonymizer.py`    | Tests                    | Full test suite (54 assertions)                                          |

Run any example directly:

```bash
cd shadetriptxt/text_anonymizer/examples
python text_strategies.py
python dict_records.py
python dataframe_privacy.py
python multi_locale.py
python full_pipeline.py
python test_anonymizer.py
```

---

## References

| Resource                                                                    | Description                                         |
| -------------------------------------------------------------------------- | ---------------------------------------------------- |
| [README TextAnonymizer](./README_TextAnonymizer.md) | Full TextAnonymizer module reference               |
| [README TextDummy](../text_dummy/README.md)          | Fake data generator reference (60+ types)           |
| [GDPR — Official text](https://gdpr-info.eu/)                                | General Data Protection Regulation (EU)              |
| [AEPD — Anonymization guide](https://www.aepd.es/)                           | Spanish Data Protection Agency                       |
| [ICO — Anonymisation guidance](https://ico.org.uk/)                          | Information Commissioner's Office (UK)               |

---

*Document generated for the shadetriptxt project — DatamanEdge (MIT License)*
