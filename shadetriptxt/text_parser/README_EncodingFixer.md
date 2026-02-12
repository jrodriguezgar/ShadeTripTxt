# EncodingFixer — Universal Mojibake Detection and Repair

## Overview

`EncodingFixer` solves the most common text data-quality problem: **mojibake** — garbled text produced when a file encoded in one codepage is opened or imported with a different one.

```
                  original encoding              opened as
UTF-8 file       ─────────────────────►    Latin-1 / CP1252 / CP850
     á  (0xC3 0xA1)                             Ã¡
     ñ  (0xC3 0xB1)                             Ã±
     ü  (0xC3 0xBC)                             Ã¼
     ß  (0xC3 0x9F)                             ÃŸ
     ç  (0xC3 0xA7)                             Ã§
     œ  (0xC5 0x93)                             Å"
```

`EncodingFixer` reverses this process automatically, recovering the original characters without destroying the surrounding clean text.

## Covered Scenarios

| Scenario | Garbled example | Result |
|----------|----------------|--------|
| UTF-8 opened as CP1252 | `Ã¡rbol` | `árbol` |
| UTF-8 opened as Latin-1 | `Ã±` | `ñ` |
| UTF-8 opened as ISO-8859-15 | `Ã¼ller` | `üller` |
| UTF-8 opened as CP850 (DOS) | Box-drawing characters | Original text |
| CP1252 "smart" characters (0x80-0x9F) | `l\x92homme` | `l'homme` |
| Double-encoded UTF-8 | `ÃƒÂ¡rbol` | `árbol` |
| Stray BOM (Byte Order Mark) | `ï»¿Hello` | `Hello` |
| Residual C0/C1 control characters | `\x00`, `\x1b`, `\x8d` | (removed) |

## Quick Start

### `EncodingFixer` Class

```python
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer

fixer = EncodingFixer()

# Standard mojibake repair
fixer.fix("Ã¡rbol")                    # "árbol"
fixer.fix("espaÃ±ol")                  # "español"
fixer.fix("FranÃ§ois")                 # "François"
fixer.fix("MÃ¼ller StraÃŸe")          # "Müller Straße"
fixer.fix("JoÃ£o da Silva")            # "João da Silva"
fixer.fix("cittÃ\xa0")                 # "città"

# Windows "smart" characters (curly quotes, etc.)
fixer.fix("l\x92homme")                # "l'homme"
fixer.fix("\x93Bonjour\x94")           # "\u201cBonjour\u201d"
fixer.fix("\x80100")                    # "€100"

# Double encoding
fixer.fix("ÃƒÂ¡rbol")                  # "árbol"

# BOM removal
fixer.fix("ï»¿Hello")                  # "Hello"
fixer.fix("\ufeffHello")                # "Hello"
```

### Language Hint

The `language` parameter improves ambiguous-case resolution by adding a scoring bonus for characters expected in that language:

```python
fixer_es = EncodingFixer(language='es')
fixer_es.fix("espaÃ±ol")               # "español"

fixer_de = EncodingFixer(language='de')
fixer_de.fix("MÃ¼ller")                # "Müller"
```

### Typographic Quote Normalisation

With `normalize_quotes=True`, in addition to repairing mojibake, curly quotes, em-dashes, and typographic ellipses are converted to their ASCII equivalents:

```python
fixer = EncodingFixer()

# Without normalisation: typographic characters are preserved
fixer.fix("l\x92homme")                           # "l\u2019homme" (curly quote)

# With normalisation: typographic → ASCII
fixer.fix("l\x92homme", normalize_quotes=True)    # "l'homme" (straight apostrophe)
fixer.fix("\u201cHola\u201d", normalize_quotes=True)  # '"Hola"'
```

Typographic map:

| Character | Unicode | Replacement |
|-----------|---------|-------------|
| `'` `'` | U+2018, U+2019 | `'` |
| `"` `"` | U+201C, U+201D | `"` |
| `‚` `„` | U+201A, U+201E | `'` `"` |
| `–` `—` | U+2013, U+2014 | `-` |
| `…` | U+2026 | `...` |
| `«` `»` | U+00AB, U+00BB | `"` |
| `` ` `` `´` | U+0060, U+00B4 | `'` |

### Convenience Function

```python
from shadetriptxt.text_parser.encoding_fixer import fix_encoding

# Equivalent to EncodingFixer(language).fix(text, ...)
fix_encoding("Ã¡rbol")                             # "árbol"
fix_encoding("espaÃ±ol", language='es')             # "español"
fix_encoding("l\x92homme", normalize_quotes=True)   # "l'homme"
```

## Detection and Diagnostics

### `has_mojibake(text)` — Quick Detection

Checks whether the text contains known mojibake sequences. Uses a pre-compiled regex — O(n):

```python
fixer = EncodingFixer()
fixer.has_mojibake("Hello world")       # False
fixer.has_mojibake("Ã¡rbol")           # True
fixer.has_mojibake("árbol")            # False
```

### `detect(text)` — Diagnostic Report

Analyses the text and returns a full report with the likely encoding pair, sequences found, and quality scores:

```python
fixer = EncodingFixer(language='es')
report = fixer.detect("espaÃ±ol")

# {
#   'has_mojibake': True,
#   'likely_pair': ('cp1252', 'utf-8'),
#   'sequences_found': ['Ã±'],
#   'score_original': 1.812,
#   'score_fixed': 2.0
# }
```

| Field | Type | Description |
|-------|------|-------------|
| `has_mojibake` | bool | Whether mojibake was detected |
| `likely_pair` | tuple \| None | Most likely `(wrong_encoding, actual_encoding)` pair |
| `sequences_found` | list[str] | Mojibake sequences found (max 20) |
| `score_original` | float | Quality score of the original text |
| `score_fixed` | float | Quality score after repair |

## TextParser Integration

`EncodingFixer` is integrated into the `TextParser` class in the `text_parser` module:

```python
from shadetriptxt.text_parser.text_parser import TextParser

parser = TextParser("es_ES")

# General repair (non-destructive, all codepages)
parser.fix_mojibake("espaÃ±ol")                    # "español"
parser.fix_mojibake("FranÃ§ois")                   # "François"
parser.fix_mojibake("MÃ¼ller StraÃŸe")             # "Müller Straße"

# Diagnostics
parser.detect_encoding("espaÃ±ol")
# {'has_mojibake': True, 'likely_pair': ('cp1252', 'utf-8'), ...}

# Direct access to the EncodingFixer
parser.encoding_fixer.has_mojibake("Ã¡rbol")       # True

# fix_encoding() (per-language, with charset filter) is still available
parser.fix_encoding("Ã¡rbol")                       # "árbol"
```

### `fix_mojibake` vs `fix_encoding`

| Aspect | `fix_mojibake()` | `fix_encoding()` |
|--------|------------------|-------------------|
| Engine | `EncodingFixer` (general) | `fix_XX_conversion_fails` (per-language) |
| Codepages | CP1252, Latin-1, ISO-8859-15, CP850, CP437 | Latin-1 → UTF-8 only |
| Double encoding | ✓ Detects and repairs | ✗ Not supported |
| Valid characters | **Leaves them untouched** | Filters by allowed charset (may lose chars) |
| Pattern map | ~200 (auto-generated) | ~15-20 (manual) |
| Diagnostics | ✓ `detect()`, `has_mojibake()` | ✗ Not available |
| Recommended for | Safe general-purpose repair | Strict cleanup with controlled charset |

## Repair Pipeline

The `fix()` method applies a 5-step pipeline:

```
Garbled text
    │
    ▼
┌─────────────────────────────────────────┐
│ Step 1: Pattern replacement             │  Known mojibake sequences →
│         (partial mojibake)              │  correct characters
└────────────────┬────────────────────────┘
                 │
    ▼ mojibake remaining?
┌─────────────────────────────────────────┐
│ Step 2: Full re-decode                  │  text.encode(wrong_codepage)
│         (5 encoding pairs)              │  .decode('utf-8')
└────────────────┬────────────────────────┘
                 │
    ▼ mojibake remaining?
┌─────────────────────────────────────────┐
│ Step 3: Double encoding                 │  Second pattern pass for text
│         (second pass)                   │  garbled twice
└────────────────┬────────────────────────┘
                 │
    ▼ (if normalize_quotes=True)
┌─────────────────────────────────────────┐
│ Step 4: Typographic normalisation       │  Curly quotes → straight,
│         (optional)                      │  em-dash → hyphen, etc.
└────────────────┬────────────────────────┘
                 │
    ▼
┌─────────────────────────────────────────┐
│ Step 5: Control character cleanup       │  Removes residual C0/C1
│                                         │  (preserves \t \n \r)
└────────────────┬────────────────────────┘
                 │
    ▼
Repaired text
```

## Internal Architecture

### Mojibake Map (auto-generated)

Unlike the `fix_XX_conversion_fails` functions which define ~15 manual replacements per language, `EncodingFixer` generates its map programmatically from the Unicode/codepage tables. This guarantees full coverage:

| Layer | Range | Coverage | Example |
|-------|-------|----------|---------|
| **1 — CP1252 gap** | U+0080–U+009F | Windows "smart" characters stored as C1 bytes | `\x92` → `'` (curly quote) |
| **2 — Latin Supplement** | U+0080–U+00FF | **All** accented letters, ñ, ü, ß, ç, etc. — auto-generated for CP1252 and Latin-1 | `Ã¡` → `á`, `Ã±` → `ñ` |
| **3 — Multi-byte** | Typographic + Latin Extended-A | Smart quotes, dashes, €, œ, Œ, Š, ž... — generated for CP1252 and Latin-1 | `â€"` → `—`, `Å"` → `œ` |

Keys are sorted by descending length to prevent partial-match collisions (a 3-character sequence like `â€™` must be replaced before its 1-character component is processed).

### Scoring System

To choose between ambiguous decoding candidates, each text receives a normalised quality score:

| Unicode Category | Score |
|------------------|-------|
| Letter (Lu, Ll, Lt, Lm, Lo) | +2.0 |
| Digit (Nd) | +2.0 |
| Space (Zs) | +0.5 |
| Punctuation (P*) | +1.0 |
| Symbol (S*) | +0.5 |
| Control (C*) | −5.0 |
| Private use / unassigned (Co, Cn) | −5.0 |
| Expected language character | +0.5 (bonus) |

The candidate with the highest score / length wins.

### Expected Characters per Language

| Language | Bonus characters |
|----------|-----------------|
| Spanish (`es`) | á é í ó ú ñ Á É Í Ó Ú Ñ ü Ü ¿ ¡ |
| English (`en`) | _(none)_ |
| Portuguese (`pt`) | á é í ó ú à â ê ô ã õ ç Á É Í Ó Ú À Â Ê Ô Ã Õ Ç |
| French (`fr`) | à â ä æ ç é è ê ë î ï ô ö ù û ü ÿ œ (+ uppercase) |
| German (`de`) | ä ö ü Ä Ö Ü ß |
| Italian (`it`) | à è é ì í ò ó ù ú À È É Ì Í Ò Ó Ù Ú |

## Supported Encoding Pairs

| # | Misread as | Actual encoding | Typical use case |
|---|-----------|-----------------|-------------------|
| 1 | Windows-1252 | UTF-8 | Most common — web/Excel/CSV files |
| 2 | Latin-1 (ISO-8859-1) | UTF-8 | Legacy Unix/Linux systems |
| 3 | Latin-9 (ISO-8859-15) | UTF-8 | Like Latin-1 but with €, œ, Ž |
| 4 | CP850 (DOS OEM West) | UTF-8 | CMD/Windows terminal files |
| 5 | CP437 (DOS US) | UTF-8 | DOS/mainframe legacy files |

## API Reference

### `EncodingFixer` Class

```python
EncodingFixer(language=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | str \| None | `None` | Language hint for scoring (`'es'`, `'en'`, `'pt'`, `'fr'`, `'de'`, `'it'`) |

#### Methods

| Method | Description |
|--------|-------------|
| `fix(text, normalize_quotes=False)` | Repair mojibake in text |
| `has_mojibake(text)` | Quick mojibake detection (pre-compiled regex) |
| `detect(text)` | Full diagnostic report |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `language` | str \| None | Current language hint (read/write) |

### `fix_encoding()` Function

```python
fix_encoding(text, language=None, normalize_quotes=False)
```

Module-level shortcut — equivalent to `EncodingFixer(language).fix(text, normalize_quotes)`.

## Performance

- **Pattern map**: generated once on first instantiation and shared across all instances (class-level cache)
- **Detection regex**: pre-compiled, O(n)
- **Repair**: O(n × k) where k ≈ 200 patterns
- **Re-decode**: O(n × m) where m = 5 encoding pairs
- **Memory**: ~200 entries in the shared map (~50 KB)

## Related Documentation

| Document | Description |
|----------|-------------|
| [TextParser README](README.md) | Main module documentation — architecture, quick start, class reference |
| [Technical Reference](README_TextParser_Technical_Reference.md) | Complete API reference for all `text_parser` functions |

## Dependencies

- Python standard library (`re`, `unicodedata`, `typing`)
- No external dependencies

## License

Part of the `shadetriptxt` library by DatamanEdge.
