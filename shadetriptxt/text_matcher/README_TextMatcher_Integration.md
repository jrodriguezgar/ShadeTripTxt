# TextMatcher + TextParser — Integration Guide

## Overview

`TextMatcher` and `TextParser` are complementary modules in shadetriptxt that work together to provide a full data-quality pipeline:

| Module | Purpose |
|--------|---------|
| **TextParser** | *Prepare* text — locale-aware normalization, encoding repair, phonetic reduction, article removal, ID validation, content extraction |
| **TextMatcher** | *Compare* text — locale-aware abbreviation resolution, similarity scoring, name matching, deduplication, fuzzy search |

`TextMatcher` depends on `TextParser` internally (it calls `text_normalizer.normalize_text` for all its preprocessing). This guide shows how to combine both modules explicitly for advanced workflows.

---

## How They Connect

### Internal dependency

`TextMatcher.normalize_text()` delegates general text normalization to `text_parser.text_normalizer.normalize_text()`:

```
TextMatcher.normalize_text(text, for_names=False, ...)
    └── text_parser.text_normalizer.normalize_text(text, ...)
            ├── remove_parentheses_content
            ├── strip_quotes
            ├── remove_accents (unicodedata NFD)
            ├── lowercase / uppercase
            ├── remove_punctuation
            └── normalize_whitespace
```

For name-specific normalization (`for_names=True`), `TextMatcher` uses its own regex that keeps letters, accents, spaces, hyphens, and apostrophes.

### What each module owns

```
TextParser handles:                      TextMatcher handles:
─────────────────                        ──────────────────
✓ Locale-aware normalization             ✓ Word similarity (Levenshtein, Jaro-Winkler, Metaphone)
✓ Language-specific abbreviation         ✓ Name comparison (single word + full name)
  expansion (Avda. → Avenida)            ✓ Locale-aware nickname dictionary (6 languages)
✓ Article/particle removal              ✓ Word alignment for multi-word names
  (de, la, the, of)                      ✓ Duplicate detection with blocking
✓ Phonetic reduction per language        ✓ Best match / top-K search
✓ Encoding/mojibake repair              ✓ Batch comparison with parallelization
✓ ID document validation (28 countries)  ✓ Phrase comparison (Sørensen-Dice)
✓ Content extraction (emails, phones,   ✓ Text/code diff (difflib)
  URLs, IBANs, credit cards, …)         ✓ Character-level analysis (Jaccard)
✓ Company name parsing                  ✓ LCS pattern detection
```

**Abbreviation scope difference:**
- `TextParser` expands *title and address* abbreviations (Sr.→Señor, St.→Street, Dr.→Doktor)
- `TextMatcher` resolves *name nicknames* (Paco→Francisco, Bob→Robert, Fritz→Friedrich)

---

## Pipelines

### Pipeline 1 — Clean then Compare (most common)

Use `TextParser` to normalize, then `TextMatcher` to compare. Both share the same locale:

```python
from shadetriptxt.text_parser.text_parser import TextParser
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig

parser  = TextParser("es_ES")
matcher = TextMatcher(config=MatcherConfig.lenient(), locale="es_ES")

# Step 1: Clean with TextParser (locale-aware)
name_a = parser.normalize("  José  Fco.  de la García-López  ")
name_b = parser.normalize("  Jose Francisco Garcia Lopez  ")
# name_a → "jose fco garcia lopez"
# name_b → "jose francisco garcia lopez"

# Step 2: Compare with TextMatcher
is_match, metrics = matcher.compare_name_bytokens(name_a, name_b)
print(is_match)  # True — "Fco" matches "Francisco" via abbreviation dict
```

### Pipeline 2 — Encoding Fix → Normalize → Compare

Handle dirty data from legacy systems:

```python
parser  = TextParser("es_ES")
matcher = TextMatcher(locale="es_ES")

# Raw data with mojibake
raw_name = "JosÃ© GarcÃ\xada"

# Step 1: Fix encoding
fixed = parser.fix_encoding(raw_name)   # "José García"

# Step 2: Normalize
clean = parser.normalize(fixed)          # "jose garcia"

# Step 3: Compare
is_match, _ = matcher.compare_names(clean, "jose garcia")
print(is_match)  # True
```

### Pipeline 3 — Phonetic Reduction for Fuzzy Matching

When text has heavy misspellings or transliteration issues:

```python
parser  = TextParser("es_ES")
matcher = TextMatcher(locale="es_ES")

# Step 1: Phonetic reduction with TextParser
raw_a = parser.raw_string("González Fernández", accuracy=2)  # "JONSALES FERNANDES"
raw_b = parser.raw_string("Gonzales Fernandes", accuracy=2)  # "JONSALES FERNANDES"

# Step 2: Compare phonetically reduced strings
is_match, metrics = matcher.compare_names(raw_a, raw_b)
print(is_match)  # True — phonetic forms are identical
```

### Pipeline 4 — Article Removal + Name Matching

Articles and particles can cause false negatives:

```python
parser  = TextParser("es_ES")
matcher = TextMatcher(locale="es_ES")

name1 = "Pedro de la Fuente Martínez"
name2 = "Pedro Fuente Martinez"

# Without article removal — may get partial match issues
is_match, _ = matcher.compare_name_bytokens(name1, name2)
# "de" and "la" are extra tokens that may cause mismatch

# With article removal first
clean1 = parser.remove_articles(name1)   # "Pedro Fuente Martínez"
clean2 = parser.remove_articles(name2)   # "Pedro Fuente Martinez"
is_match, _ = matcher.compare_name_bytokens(clean1, clean2)
print(is_match)  # True
```

### Pipeline 5 — ID Validation + Entity Matching

Combine document validation with name matching for identity resolution:

```python
parser  = TextParser("es_ES")
matcher = TextMatcher(locale="es_ES")

# Database record
db_nif  = "12345678Z"
db_name = "Juan García López"

# Incoming request
incoming_nif  = "12345678z"
incoming_name = "Juan Fco García"

# Step 1: Validate IDs with TextParser
valid_db  = parser.validate_id(db_nif)        # "12345678Z"
valid_inc = parser.validate_id(incoming_nif)   # "12345678Z"

# Step 2: If IDs match exactly, confirmed identity
if valid_db and valid_inc and valid_db == valid_inc:
    print("ID match confirmed")

# Step 3: Cross-check name as secondary signal
is_name_match, _ = matcher.compare_name_bytokens(db_name, incoming_name)
print(f"Name also matches: {is_name_match}")   # True
```

### Pipeline 6 — Batch Deduplication with Preprocessing

Full-scale deduplication pipeline:

```python
parser  = TextParser("es_ES")
matcher = TextMatcher(config=MatcherConfig.lenient(), locale="es_ES")

# Raw records from a legacy database
raw_records = [
    "JosÃ© GarcÃ\xada LÃ³pez",
    "Jose Garcia Lopez",
    "JOSE DE LA GARCIA LOPEZ",
    "María Fernández",
    "maria fernandez",
]

# Step 1: Clean all records with TextParser
cleaned = []
for record in raw_records:
    fixed   = parser.fix_encoding(record)
    no_arts = parser.remove_articles(fixed)
    normed  = parser.normalize(no_arts)
    cleaned.append(normed)

# Step 2: Detect duplicates with TextMatcher
duplicates = matcher.detect_duplicates(cleaned, threshold=0.85)
for name1, name2, score in duplicates:
    print(f"Duplicate: '{name1}' ≈ '{name2}' ({score:.0%})")
```

---

## `MatcherConfig` Normalization Flags

`TextMatcher.normalize_text()` passes these `MatcherConfig` flags to `text_normalizer.normalize_text()`:

| MatcherConfig flag | text_normalizer parameter | Default | Effect |
|--------------------|---------------------------|---------|--------|
| `normalize_punctuation` | `remove_punctuation` | `True` | Remove `,` `;` `:` `!` `?` etc. |
| `normalize_whitespace` | `normalize_whitespace` | `True` | Collapse multiple spaces |
| `remove_accents` | `remove_accents` | `False` | Strip diacritical marks (é→e) |
| `normalize_parentheses` | `remove_parentheses_content` | `False` | Remove `(content)` |

These only apply when `for_names=False`. For `for_names=True`, `TextMatcher` uses its own regex.

---

## When to Use Which

| Situation | Use |
|-----------|-----|
| Compare two words/names | `TextMatcher.compare_names()` (handles normalization internally) |
| Compare two full names with multiple words | `TextMatcher.compare_name_bytokens()` |
| Data from legacy/broken encodings | `TextParser.fix_encoding()` or `fix_mojibake()` **before** matching |
| Names with articles (de, la, von, di) | `TextParser.remove_articles()` **before** matching |
| Heavy misspellings / transliterations | `TextParser.reduce_phonetic()` **before** matching |
| Locale-specific abbreviation expansion | `TextParser.normalize()` **before** matching |
| ID document validation | `TextParser.validate_id()` — standalone, no matcher needed |
| Extract emails, phones, IBANs from text | `TextParser.extract_*()` — standalone |
| Fuzzy search across a list | `TextMatcher.compare_lists()` or `find_best_match()` |
| Large-scale deduplication | `TextParser` preprocessing → `TextMatcher.detect_duplicates()` |
| Code/text diff analysis | `TextMatcher.compare_text_detailed()` — standalone |

---

## Supported Locales

Both modules share the same 12 locale codes:

| Code | Country | Language |
|------|---------|----------|
| `es_ES` | Spain | Spanish |
| `es_MX` | Mexico | Spanish |
| `es_AR` | Argentina | Spanish |
| `es_CO` | Colombia | Spanish |
| `es_CL` | Chile | Spanish |
| `en_US` | United States | English |
| `en_GB` | United Kingdom | English |
| `pt_BR` | Brazil | Portuguese |
| `pt_PT` | Portugal | Portuguese |
| `fr_FR` | France | French |
| `de_DE` | Germany | German |
| `it_IT` | Italy | Italian |

`TextParser` uses locales for language-specific phonetics, article removal, abbreviation expansion, ID validation patterns, phone digit counts, postal code lengths, and date formats.

`TextMatcher` uses locales to select the appropriate name abbreviation/nickname dictionary (e.g., Paco→Francisco for Spanish, Bob→Robert for English, Fritz→Friedrich for German). When `locale=None`, Spanish is used by default for backward compatibility.

**Best practice:** Pass the same locale to both modules to ensure consistent language-specific behavior across the pipeline:

```python
locale = "en_US"
parser  = TextParser(locale)
matcher = TextMatcher(locale=locale)
```

---

## Related Documents

| Topic | Document |
|-------|----------|
| TextMatcher API reference | [text_matcher/README.md](README.md) |
| TextParser API reference | [text_parser/README.md](../text_parser/README.md) |
| `MatcherConfig` presets and flags | [text_matcher/README.md](README.md#configuration) |
| Normalization engine (text_parser) | [text_parser/README_Normalization.md](../text_parser/README_Normalization.md) |
| Normalization config (text_matcher) | [README_Normalization.md](README_Normalization.md) |
