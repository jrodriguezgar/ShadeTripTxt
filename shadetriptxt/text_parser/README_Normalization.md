# Text Normalization — Quick Reference

> How `text_normalizer.py` transforms text before comparison, deduplication, or storage.

---

## Overview

The normalization engine lives in `text_parser.text_normalizer` and provides a configurable pipeline that cleans text in a single pass. It is used directly by `TextParser.normalize()` and indirectly by `TextMatcher.normalize_text()` (which delegates general text normalization here).

```
TextParser.normalize(text, ...)
    └── LanguageNormalizer.normalize()   ← abbreviation expansion
         └── normalize_text()            ← this module

TextMatcher.normalize_text(text, for_names=False, ...)
    └── normalize_text()                 ← this module (when for_names=False)
```

---

## Quick Start

```python
from shadetriptxt.text_parser.text_normalizer import normalize_text, prepare_for_comparison

# Default: lowercase + remove punctuation + normalize whitespace + strip quotes
normalize_text("  John   Smith,  Inc.  ")
# "john smith inc"

# With accents removal
normalize_text("José García", remove_accents=True)
# "jose garcia"

# Remove parentheses content
normalize_text("Microsoft (MSFT)", remove_parentheses_content=True)
# "microsoft"

# Convenience wrapper — standard mode
prepare_for_comparison("  John   Smith,  Inc.  ")
# "john smith inc"

# Convenience wrapper — aggressive mode
prepare_for_comparison("José García (CEO)", aggressive=True)
# "jose garcia ceo"
```

### Via TextParser (locale-aware)

```python
from shadetriptxt.text_parser.text_parser import TextParser

parser = TextParser("es_ES")
parser.normalize("Ma. P. García-López")   # "maria pilar garcia lopez"
#                ↑ abbreviation expansion + normalization
```

`TextParser.normalize()` adds **language-specific abbreviation expansion** (via `LanguageNormalizer`) before calling the normalization pipeline.

---

## Parameters

| Parameter | Default | Effect | Example |
|-----------|---------|--------|---------|
| `lowercase` | `True` | Convert to lowercase | `"ABC"` → `"abc"` |
| `remove_punctuation` | `True` | Remove punctuation marks | `"Hello, World!"` → `"Hello World"` |
| `normalize_whitespace` | `True` | Collapse multiple spaces, trim | `"  a   b  "` → `"a b"` |
| `remove_accents` | `False` | Strip diacritical marks | `"José García"` → `"Jose Garcia"` |
| `remove_parentheses_content` | `False` | Remove `(text)`, `[text]`, `{text}` | `"Test (Beta)"` → `"Test"` |
| `strip_quotes` | `True` | Remove quotation marks | `'"Hello"'` → `"Hello"` |
| `preserve_alphanumeric_only` | `False` | Keep only letters, numbers, spaces | `"Product-123!"` → `"Product123"` |

---

## What Gets Normalized

### Punctuation (`remove_punctuation=True`)
- **Removed**: `. , ; : ! ? ¡ ¿`
- **Preserved**: Hyphens and apostrophes between word characters
- **Example**: `"Hello, World!"` → `"Hello World"`

### Parentheses (`remove_parentheses_content=True`)
- **Removed**: `( )` and all content inside, also `[ ]` and `{ }`
- **Example**: `"Test (Beta Version)"` → `"Test"`

### Accents (`remove_accents=True`)
- **Removed**: All diacritical marks (Unicode NFD decomposition)
- **Examples**:
  - `"José"` → `"Jose"`
  - `"François"` → `"Francois"`
  - `"Müller"` → `"Muller"`
  - `"Søren"` → `"Soren"`

### Quotes (`strip_quotes=True`)
- **Removed**: `"` `'` `"` `"` `'` `'` (straight and typographic)

### Whitespace (always recommended)
- **Collapsed**: Multiple spaces, tabs, newlines → single space
- **Trimmed**: Leading/trailing whitespace removed
- **Example**: `"  Hello    World  "` → `"Hello World"`

### Alphanumeric Only (`preserve_alphanumeric_only=True`)
- **Keeps**: Letters (a-z, A-Z), digits (0-9), spaces
- **Removes**: All other characters
- **Example**: `"Product-123 (New!)"` → `"Product123 New"`

---

## Pipeline Order

The normalization steps execute in this fixed order:

1. Remove parentheses content *(if enabled)*
2. Strip quotes *(if enabled)*
3. Remove accents *(if enabled)*
4. Lowercase *(if enabled)*
5. Remove punctuation *(if enabled)*
6. Preserve alphanumeric only *(if enabled)*
7. Normalize whitespace *(if enabled — always last)*

---

## Available Functions

| Function | Purpose |
|----------|---------|
| `normalize_text()` | Main pipeline — all steps configurable |
| `prepare_for_comparison()` | Convenience wrapper: standard or aggressive mode |
| `normalize_whitespace()` | Collapse spaces only |
| `remove_punctuation_marks()` | Remove `. , ; : ! ? ¡ ¿` (optional hyphen preservation) |
| `remove_special_characters()` | Keep only alphanumeric |
| `remove_parentheses_and_content()` | Remove `(…)`, `[…]`, `{…}` |
| `strip_quotes()` | Remove quotation marks |
| `mask_text()` | Mask sensitive text (e.g. `"12345678Z"` → `"12******Z"`) |

---

## Common Patterns

### Pattern 1: Basic Cleanup for Storage

```python
from shadetriptxt.text_parser.text_normalizer import normalize_text

# Defaults are sufficient — lowercase + punctuation removal + whitespace
clean = normalize_text("  John   Smith,  Inc.  ")
# "john smith inc"
```

### Pattern 2: International Name Normalization

```python
# Enable accent removal for cross-locale name comparison
clean = normalize_text("José François Müller", remove_accents=True)
# "jose francois muller"
```

### Pattern 3: Aggressive Cleanup for Deduplication

```python
from shadetriptxt.text_parser.text_normalizer import prepare_for_comparison

# Aggressive mode: accents + parentheses + alphanumeric only
clean = prepare_for_comparison("ACME Corp. (NYSE: ACME) — €10B", aggressive=True)
# "acme corp nyse acme 10b"
```

### Pattern 4: Partial Normalization

```python
# Keep punctuation but fix whitespace and case
clean = normalize_text("  JOHN   SMITH,  INC.  ", remove_punctuation=False)
# "john   smith,  inc."  → only lowercase + whitespace
```

### Pattern 5: Data Masking

```python
from shadetriptxt.text_parser.text_normalizer import mask_text

mask_text("12345678Z", keep_first=2, keep_last=1)
# "12******Z"

mask_text("juan.garcia@gmail.com", keep_first=1, keep_last=4, keep_chars="@.")
# "j***.g*****@g****.com"
```

---

## Integration with TextMatcher

`TextMatcher.normalize_text()` delegates to this module when `for_names=False`. The `MatcherConfig` flags map directly:

| MatcherConfig flag | normalize_text parameter | Default |
|--------------------|--------------------------|---------|
| `normalize_punctuation` | `remove_punctuation` | `True` |
| `normalize_whitespace` | `normalize_whitespace` | `True` |
| `remove_accents` | `remove_accents` | `False` |
| `normalize_parentheses` | `remove_parentheses_content` | `False` |

For name-specific normalization (`for_names=True`), `TextMatcher` uses its own regex instead of this module. See [TextMatcher — Normalization Config](../text_matcher/README_Normalization.md) for matching-specific configuration.

---

## FAQ

**Q: Does normalization change the original strings?**
A: No. All functions return a new string — the original is never modified.

**Q: What's the performance impact?**
A: Negligible for typical strings (< 0.1ms per string). All functions are O(n).

**Q: Can I use `normalize_text()` directly without TextParser?**
A: Yes. It's a standalone function with no locale dependency:
```python
from shadetriptxt.text_parser.text_normalizer import normalize_text
result = normalize_text("José García", remove_accents=True)
```

**Q: When should I use TextParser.normalize() instead?**
A: When you need language-aware abbreviation expansion (e.g. `Ma.` → `María`, `St.` → `Street`). `TextParser.normalize()` adds `LanguageNormalizer` before calling `normalize_text()`.

---

## Related Documents

| Topic | Document |
|-------|----------|
| TextParser API reference | [README.md](README.md) |
| TextParser technical reference | [README_TextParser_Technical_Reference.md](README_TextParser_Technical_Reference.md) |
| Encoding repair | [README_EncodingFixer.md](README_EncodingFixer.md) |
| TextMatcher normalization config | [text_matcher/README_Normalization.md](../text_matcher/README_Normalization.md) |
| TextMatcher + TextParser integration | [text_matcher/README_TextMatcher_Integration.md](../text_matcher/README_TextMatcher_Integration.md) |
