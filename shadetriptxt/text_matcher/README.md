# TextMatcher - High-Level Text Comparison Utilities

## Overview

`TextMatcher` is a production-ready text comparison framework built on top of `WordSimilarity`. It provides enterprise-grade matching capabilities for real-world scenarios including identity resolution, duplicate detection, and fuzzy search with support for multiple similarity algorithms.

## Features

### Core Capabilities
- **Word Comparison**: `are_words_equivalent` with multiple similarity metrics
- **Name Comparison**: `compare_names` — Specialized single word/name comparison with abbreviation handling
- **Full Name Matching**: `compare_name_bytokens` — Multi-word name comparison for complete names
- **Phrase Comparison**: `compare_phrases` — Sørensen-Dice based phrase/sentence comparison
- **Character Comparison**: `same_chars` / `same_chars_similarity` — Character-level analysis
- **Text Comparison**: `compare_text_detailed` — difflib-based diff analysis
- **Best Match Finding**: `find_best_match` — Find optimal match from candidate list
- **Top-K Search**: `compare_lists` — Ranked multi-match with threshold filtering
- **Batch Processing**: `batch_compare` — Efficiently compare multiple pairs with optional parallelization
- **Duplicate Detection**: `detect_duplicates` — Built-in deduplication with blocking strategy
- **Phonetic Duplicates**: `find_phonetic_duplicates` — MRA/Metaphone-based name grouping
- **Pattern Analysis**: `find_common_patterns` — LCS-based common pattern detection
- **Locale-Aware Abbreviations**: Per-language nickname/abbreviation dictionaries for 6 languages

### Advanced Features

#### Automatic Preprocessing
- All comparison methods automatically normalize text before comparing (whitespace, punctuation, case, accents)
- Configurable via `MatcherConfig` flags — no manual preprocessing required
- Format-agnostic: "José  García" matches "Jose Garcia" transparently

#### Performance Optimizations
- **Intelligent Caching**: LRU-style caching eliminates redundant comparisons
- **Parallel Processing**: Multi-core support for batch operations
- **Blocking Strategy**: Reduces comparisons for large-scale deduplication
- **Parameter Validation**: Clear error messages for invalid inputs
- **Unified Configuration**: `MatcherConfig` with preset configurations

## Installation

```bash
pip install shadetriptxt
```

For full similarity algorithm support:

```bash
pip install shadetriptxt[full]
```

## Quick Start

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher
from shadetriptxt.utils.string_similarity import are_words_equivalent

# Create a matcher instance (defaults to Spanish abbreviations)
matcher = TextMatcher()

# Create a matcher with English abbreviations
matcher_en = TextMatcher(locale='en_US')

# Basic word comparison using are_words_equivalent
is_match, metrics = are_words_equivalent("Smith", "Smyth")
print(f"Match: {is_match}")  # True
print(f"Levenshtein ratio: {metrics['levenshtein_ratio']:.4f}")  # 0.8333

# Single name/word comparison
is_match, metrics = matcher.compare_names("José", "Jose")
print(f"Match: {is_match}")  # True

# Full name comparison (multiple words)
is_match, metrics = matcher.compare_name_bytokens("José García López", "Jose Garcia Lopez")
print(f"Match: {is_match}")  # True

# English nickname resolution
is_match, metrics = matcher_en.compare_name_bytokens("Bill Smith", "William Smith")
print(f"Match: {is_match}")  # True
```

## Class Reference

### TextMatcher

#### Constructor

```python
TextMatcher(
    config: Optional[MatcherConfig] = None,
    locale: Optional[str] = None,
    enable_cache: bool = True,
    cache_size: int = 1024
)
```

**Parameters:**
- `config` (Optional[MatcherConfig]): Configuration object for default settings. If `None`, uses `MatcherConfig.default()`
- `locale` (Optional[str]): Locale code for language-specific abbreviation handling (e.g. `'es_ES'`, `'en_US'`). Also accepts bare language codes (`'es'`, `'en'`, etc.). If `None`, defaults to `'es'` (Spanish) for backward compatibility. See [Supported Locales](#supported-locales).
- `enable_cache` (bool): Enable LRU cache for comparison results. Default: `True`
- `cache_size` (int): Maximum number of cached comparisons. Default: `1024`

**Example:**
```python
# Spanish (default)
matcher = TextMatcher()

# English name matching
matcher = TextMatcher(locale='en_US')

# Portuguese with lenient config
matcher = TextMatcher(config=MatcherConfig.lenient(), locale='pt_BR')
```

---

#### Methods

##### `are_words_equivalent(word1, word2, levenshtein_threshold=0.85, jaro_winkler_threshold=0.9, metaphone_required=True)`

**Note:** This function is imported from `shadetriptxt.utils.string_similarity` module.

Determines if two words are effectively the same based on multiple similarity metrics.

**Parameters:**
- `word1` (str): The first word to compare
- `word2` (str): The second word to compare
- `levenshtein_threshold` (float): Minimum Levenshtein ratio (0.0-1.0). Default: `0.85`
- `jaro_winkler_threshold` (float): Minimum Jaro-Winkler score (0.0-1.0). Default: `0.9`
- `metaphone_required` (bool): Whether phonetic similarity is required. Default: `True`

**Returns:**
- `Tuple[bool, Dict[str, Any]]`: (is_match, detailed_metrics)

**Example:**
```python
from shadetriptxt.utils.string_similarity import are_words_equivalent

# Handle typographical errors
is_match, metrics = are_words_equivalent("conocimiento", "conosimiento")
# Returns: (True, {'metaphone_match': True, 'levenshtein_ratio': 0.92, ...})

# Completely different words
is_match, metrics = are_words_equivalent("casa", "perro")
# Returns: (False, {'metaphone_match': False, 'levenshtein_ratio': 0.22, ...})
```

---

##### `compare_names(name1, name2, strict=False, config=None)`

Compares two single names/words considering common variations and nicknames. Uses lenient thresholds suitable for name matching.

**Parameters:**
- `name1` (str): The first name to compare
- `name2` (str): The second name to compare
- `strict` (bool): Whether to require phonetic matching. Default: `False`
- `config` (Optional[MatcherConfig]): Configuration for comparison. Default: `None`

**Returns:**
- `Tuple[bool, Dict[str, Any]]`: (is_match, detailed_metrics)

**Example:**
```python
matcher = TextMatcher()

# Common name variants
is_match, metrics = matcher.compare_names("José", "Jose")
# Returns: (True, {...})

# Different names
is_match, metrics = matcher.compare_names("Juan", "Pedro")
# Returns: (False, {...})

# Strict matching
is_match, metrics = matcher.compare_names("Michael", "Mikhail", strict=True)
```

---

##### `compare_name_bytokens(name1, name2, threshold=0.9, keep_order=True, normalize_names=True, fuzzy_align=False)`

Advanced multi-word name comparison with abbreviation handling and word alignment. This method tokenizes full names and compares them word by word using `compare_names`.

**Parameters:**
- `name1` (str): The first full name to compare
- `name2` (str): The second full name to compare
- `threshold` (float): Similarity threshold (0.0-1.0). Default: `0.9`
- `keep_order` (bool): Whether to preserve word order. Default: `True`
- `normalize_names` (bool): Whether to normalize names. Default: `True`
- `fuzzy_align` (bool): Use fuzzy matching for word alignment (e.g., ROBERT ≈ ROBERTO). Default: `False`

**Returns:**
- `Tuple[bool, Dict[str, Any]]`: (is_match, detailed_metrics with alignment info)

**Matching Rules:**
- **Rule #1**: If both names have the same word count, all words must match
- **Rule #2**: If word counts differ and both have >2 words, the difference must equal the number of non-matching words

**Example:**
```python
matcher = TextMatcher()

# Exact match with different order
is_match, metrics = matcher.compare_name_bytokens(
    "Fernando Marcos", 
    "Marcos Fernando",
    keep_order=False
)
# Returns: (True, {...})

# Subset match (rule #2)
is_match, metrics = matcher.compare_name_bytokens(
    "Fernando Marcos",
    "Jose Fernando Marcos Bernabé"
)
# Returns: (True, {...})

# Abbreviation handling
is_match, metrics = matcher.compare_name_bytokens(
    "Juan Francisco Dieguez",
    "Juan Fco Dieguez"
)
# Returns: (True, {...})
```

---

##### `compare_tokens(name1, name2, keep_order=True, require_same_len=False)`

Token-based comparison with configurable position and length rules.

**Token Difference Validation:**
- If number of tokens < 4: all tokens must match (0 difference allowed)
- If number of tokens ≥ 4: at most 1 non-matching token allowed

**Parameters:**
- `name1` (str): First tokenized string
- `name2` (str): Second tokenized string
- `keep_order` (bool): Whether tokens must maintain relative positions. Default: `True`
- `require_same_len` (bool): Whether both lists must have the same number of tokens. Default: `False`

**Returns:**
- `bool`: `True` if tokens match according to the criteria

**Example:**
```python
matcher = TextMatcher()

# Same tokens, same order
matcher.compare_tokens("Juan Perez", "Juan Perez")  # True

# 1 difference with ≥4 tokens — allowed
matcher.compare_tokens(
    "Juan Carlos Maria Perez",
    "Juan Carlos Maria Garcia"
)  # True

# 1 difference with <4 tokens — not allowed
matcher.compare_tokens("Juan Perez", "Juan Garcia")  # False
```

---

##### `compare_phrases(phrase1, phrase2, threshold=0.8)`

Compare two phrases using Sørensen-Dice coefficient.

**Parameters:**
- `phrase1` (str): The first phrase to compare
- `phrase2` (str): The second phrase to compare
- `threshold` (float): Minimum similarity score (0.0-1.0). Default: `0.8`

**Returns:**
- `Tuple[bool, Dict[str, Any]]`: (is_match, metrics) where metrics includes `similarity`, `score`, `common_words`, `unique_to_phrase1`, `unique_to_phrase2`

**Example:**
```python
matcher = TextMatcher()

is_match, metrics = matcher.compare_phrases(
    "Premium leather wallet with card slots",
    "Leather wallet premium with slots for cards"
)
print(f"Common words: {metrics['common_words']}")
```

---

##### `compare_text(text1, text2)`

Quick text comparison using token-based and subsequence algorithms (Sørensen-Dice + Ratcliff-Obershelp).

**Parameters:**
- `text1` (str): The first text to compare
- `text2` (str): The second text to compare

**Returns:**
- `Dict[str, Any]`: Dictionary with `sorensen_dice`, `ratcliff_obershelp`, `exact_match`

**Example:**
```python
matcher = TextMatcher()
metrics = matcher.compare_text("this is a test", "this is test")
print(metrics)
# {'sorensen_dice': 0.86, 'ratcliff_obershelp': 0.89, 'exact_match': False}
```

---

##### `compare_text_detailed(text1, text2, case_sensitive=False, show_diff=True, context_lines=3)`

Comprehensive text comparison using `difflib.SequenceMatcher` with detailed diff analysis.

**Parameters:**
- `text1` (str): The first text to compare (often the "original")
- `text2` (str): The second text to compare (often the "modified")
- `case_sensitive` (bool): Whether comparison should be case-sensitive. Default: `False`
- `show_diff` (bool): Whether to generate unified diff output. Default: `True`
- `context_lines` (int): Number of context lines to show in diff. Default: `3`

**Returns:**
- `Dict[str, Any]`: Dictionary with `ratio`, `score`, `matching_blocks`, `opcodes`, `diff`, `lines_added`, `lines_removed`, `lines_changed`, `total_lines_text1`, `total_lines_text2`

**Example:**
```python
matcher = TextMatcher()

result = matcher.compare_text_detailed(
    "The quick brown fox jumps over the lazy dog.",
    "The fast brown fox runs over the sleepy dog."
)
print(f"Similarity: {result['score']:.1f}%")
print(f"Lines changed: {result['lines_changed']}")
print(result['diff'])
```

---

##### `same_chars(str1, str2)`

Compares if two strings contain the same characters with the same frequency (ignoring case, accents, and spaces).

**Parameters:**
- `str1` (str): The first string
- `str2` (str): The second string

**Returns:**
- `bool`: `True` if both strings contain the same characters with the same frequency

**Example:**
```python
matcher = TextMatcher()
matcher.same_chars("amor", "roma")        # True
matcher.same_chars("José María", "Maria Jose")  # True
matcher.same_chars("hello", "world")      # False
```

---

##### `same_chars_similarity(str1, str2)`

Character similarity using Jaccard index (gradual score instead of boolean).

**Parameters:**
- `str1` (str): The first string
- `str2` (str): The second string

**Returns:**
- `Dict[str, float]`: Dictionary with `distance`, `similarity` (0.0-1.0), `score` (0.0-100.0)

**Example:**
```python
matcher = TextMatcher()
result = matcher.same_chars_similarity("José", "Jose")
# Returns: {'distance': 0.0, 'similarity': 1.0, 'score': 100.0}
```

---

##### `similarity_percentage(p_str1, p_str2)` *(static)*

Calculates a similarity score between two strings (0.0-100.0) using exact match, substring match, or character alignment.

**Parameters:**
- `p_str1` (str): The first string
- `p_str2` (str): The second string

**Returns:**
- `float`: Similarity score between 0.0 and 100.0

**Example:**
```python
TextMatcher.similarity_percentage("hello", "hello")  # 100.0
TextMatcher.similarity_percentage("hel", "hello")    # 60.0
```

---

##### `find_best_match(target, candidates, threshold=0.85)`

Finds the best matching string from a list of candidates.

**Parameters:**
- `target` (str): The string to match against
- `candidates` (List[str]): List of candidate strings to compare
- `threshold` (float): Minimum similarity threshold (0.0-1.0). Default: `0.85`

**Returns:**
- `Tuple[Optional[str], float, Dict[str, Any]]`: (best_match, score, metrics). Returns `(None, 0.0, {})` if no match meets threshold.

**Example:**
```python
matcher = TextMatcher()

candidates = ["Smith", "Smyth", "Jones", "Johnson"]
best, score, metrics = matcher.find_best_match("Smithe", candidates)
# Returns: ("Smith", 0.92, {...})

# No match case
best, score, metrics = matcher.find_best_match("Garcia", candidates)
# Returns: (None, 0.0, {})
```

---

##### `compare_lists(target, candidates, top_k=None, threshold=None, config=None)`

Compare target against multiple candidates, returning top K matches ranked by score.

**Parameters:**
- `target` (str): The string to match against
- `candidates` (List[str]): List of candidate strings
- `top_k` (Optional[int]): Maximum number of results to return. Default: `None` (all)
- `threshold` (Optional[float]): Minimum similarity threshold. Default: uses config threshold
- `config` (Optional[MatcherConfig]): Configuration for comparison. Default: `None`

**Returns:**
- `List[Tuple[str, float, Dict[str, Any]]]`: List of (candidate, score, metrics) sorted by score descending

**Example:**
```python
matcher = TextMatcher()

candidates = ["Smith", "Smyth", "Jones", "Johnson", "Smithson"]

# Get top 3 matches
results = matcher.compare_lists("Smithe", candidates, top_k=3)
for candidate, score, metrics in results:
    print(f"{candidate}: {score:.4f}")
```

---

##### `detect_duplicates(items, threshold=0.85, use_blocking=True, parallel=False, max_workers=None, config=None)`

Detect duplicate strings in a list based on similarity threshold.

**Parameters:**
- `items` (List[str]): List of strings to check for duplicates
- `threshold` (float): Minimum similarity threshold. Default: `0.85`
- `use_blocking` (bool): Use blocking to reduce comparisons (for lists ≥100 items). Default: `True`
- `parallel` (bool): Enable parallel processing. Default: `False`
- `max_workers` (Optional[int]): Number of parallel workers. Default: `None`
- `config` (Optional[MatcherConfig]): Configuration for comparison. Default: `None`

**Returns:**
- `List[Tuple[str, str, float]]`: List of tuples containing duplicate pairs and their similarity score

**Example:**
```python
matcher = TextMatcher()

items = ["apple", "aple", "banana", "bananna", "orange"]
duplicates = matcher.detect_duplicates(items, threshold=0.8)
# Returns: [("apple", "aple", 0.91), ("banana", "bananna", 0.92)]
```

---

##### `find_phonetic_duplicates(names, threshold=0.8, use_mra=True)`

Find groups of phonetically similar names using Match Rating Approach (MRA) or Metaphone.

**Parameters:**
- `names` (List[str]): List of names to analyze
- `threshold` (float): Minimum similarity score (0.0-1.0). Default: `0.8`
- `use_mra` (bool): If `True`, uses MRA; if `False`, uses Metaphone. Default: `True`

**Returns:**
- `List[List[str]]`: List of groups of phonetically similar names

**Example:**
```python
matcher = TextMatcher()

names = ["Smith", "Smyth", "Schmidt", "Johnson", "Jonson"]
duplicates = matcher.find_phonetic_duplicates(names, threshold=0.75)
# Returns: [['Smith', 'Smyth', 'Schmidt'], ['Johnson', 'Jonson']]
```

---

##### `find_common_patterns(text1, text2, min_length=3)`

Find common patterns between two texts using Longest Common Subsequence (LCS).

**Parameters:**
- `text1` (str): The first text
- `text2` (str): The second text
- `min_length` (int): Minimum length of common subsequence. Default: `3`

**Returns:**
- `Dict[str, Any]`: Dictionary with `lcs_length`, `lcs_ratio`, `similarity`, `score`, `has_significant_overlap`

**Example:**
```python
matcher = TextMatcher()

result = matcher.find_common_patterns(
    "The quick brown fox jumps",
    "The fast brown dog runs"
)
print(f"Similarity: {result['score']:.1f}%")
print(f"Significant overlap: {result['has_significant_overlap']}")
```

---

##### `compare_with_abbreviation(w1, w2, threshold_val)`

Compare two words with special logic for abbreviations, using the locale-specific name abbreviation dictionary configured at construction time.

**Parameters:**
- `w1` (str): The first word
- `w2` (str): The second word
- `threshold_val` (float): Similarity threshold (0.0-1.0)

**Returns:**
- `float`: Similarity score (0.0-1.0)

**Example:**
```python
# Spanish abbreviations (default)
matcher_es = TextMatcher()
score = matcher_es.compare_with_abbreviation("Fco", "Francisco", 0.9)  # 1.0
score = matcher_es.compare_with_abbreviation("J", "Juan", 0.9)        # 1.0

# English abbreviations
matcher_en = TextMatcher(locale='en_US')
score = matcher_en.compare_with_abbreviation("Bob", "Robert", 0.9)     # 1.0
score = matcher_en.compare_with_abbreviation("Bill", "William", 0.9)   # 1.0

# German abbreviations
matcher_de = TextMatcher(locale='de_DE')
score = matcher_de.compare_with_abbreviation("Fritz", "Friedrich", 0.9) # 1.0
```

---

##### `batch_compare(pairs, config=None, parallel=False, max_workers=None, **kwargs)`

Performs batch comparison of multiple word pairs.

**Parameters:**
- `pairs` (List[Tuple[str, str]]): List of (word1, word2) tuples to compare
- `config` (Optional[MatcherConfig]): Configuration for comparison. Default: `None`
- `parallel` (bool): Enable parallel processing (recommended for >100 pairs). Default: `False`
- `max_workers` (Optional[int]): Number of parallel workers. Default: `None`
- `**kwargs`: Additional arguments passed to `are_words_equivalent` (override config settings)

**Returns:**
- `List[Tuple[bool, Dict[str, Any]]]`: List of (is_match, metrics) tuples

**Example:**
```python
matcher = TextMatcher()

pairs = [
    ("programacion", "programación"),
    ("telefono", "telefno")
]

results = matcher.batch_compare(pairs)
for (word1, word2), (is_match, metrics) in zip(pairs, results):
    if is_match:
        print(f"'{word1}' ≈ '{word2}' (ratio: {metrics['levenshtein_ratio']:.2f})")
```

---

##### `get_cache_stats()`

Get cache performance statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with `enabled`, `size`, `max_size`, `hits`, `misses`, `total_requests`, `hit_rate`

**Example:**
```python
stats = matcher.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['size']}/{stats['max_size']}")
```

---

##### `clear_cache()`

Clear the comparison cache and reset statistics.

---

## Use Cases

### 1. Identity Resolution

Match incoming records against a database with potential typos or variations:

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher

matcher = TextMatcher()

# Database records
database = [
    ("001", "Juan Francisco Dieguez"),
    ("002", "Maria Garcia Lopez")
]

# Incoming record with variation
incoming = "Juan Fco Dieguez"

# Find best match using full name comparison
for record_id, db_name in database:
    is_match, metrics = matcher.compare_name_bytokens(incoming, db_name)
    
    if is_match:
        print(f"Matched: [{record_id}] {db_name}")
        print(f"Rule applied: {metrics.get('rule_applied')}")
```

### 2. Deduplication

Identify and merge duplicate records:

```python
from shadetriptxt.utils.string_similarity import are_words_equivalent
from shadetriptxt.text_matcher.text_matcher import TextMatcher

matcher = TextMatcher()

records = [
    "programacion",
    "programación",
    "desarrollo",
    "desarollo"
]

# Compare all pairs using are_words_equivalent
for i, record1 in enumerate(records):
    for record2 in records[i+1:]:
        is_match, metrics = are_words_equivalent(record1, record2)
        if is_match:
            print(f"Duplicate found: '{record1}' and '{record2}'")
            print(f"  Levenshtein: {metrics['levenshtein_ratio']:.2f}")

# Or use batch_compare for efficiency
pairs = [(records[i], records[j]) 
         for i in range(len(records)) 
         for j in range(i+1, len(records))]
results = matcher.batch_compare(pairs, levenshtein_threshold=0.85)

for (r1, r2), (is_match, metrics) in zip(pairs, results):
    if is_match:
        print(f"Duplicate: '{r1}' ≈ '{r2}'")
```

### 3. Fuzzy Search / Autocomplete

Find the best match from a list of options:

```python
matcher = TextMatcher()

products = ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8"]
search_query = "iphone 15"

best, score, _ = matcher.find_best_match(
    search_query,
    products,
    threshold=0.60  # Lower threshold for partial matches
)

if best:
    print(f"Found: {best} (score: {score:.2f})")
```

### 4. Top-K Fuzzy Search

Get multiple ranked results:

```python
matcher = TextMatcher(config=MatcherConfig.fuzzy())

products = ["iPhone 15 Pro Max", "Samsung Galaxy S24 Ultra", "Google Pixel 8 Pro"]
results = matcher.compare_lists("iphone 15 pro", products, top_k=3, threshold=0.50)

for product, score, _ in results:
    print(f"{product} (relevance: {score:.2%})")
```

## Configuration

### MatcherConfig

`MatcherConfig` is an immutable dataclass that controls **how TextMatcher decides if two strings match**. It has two groups of attributes:

#### 1. Comparison Thresholds — *"How similar is similar enough?"*

These three parameters set the bar for what counts as a positive match. All similarity methods (`compare_names`, `compare_name_bytokens`, `find_best_match`, etc.) use them internally.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `levenshtein_threshold` | float | `0.85` | Minimum edit-distance ratio (0.0–1.0). Higher = more strict. |
| `jaro_winkler_threshold` | float | `0.9` | Minimum Jaro-Winkler score (0.0–1.0). Favors strings that share a common prefix. |
| `metaphone_required` | bool | `True` | If `True`, both words must also sound alike (phonetic match). If `False`, edit-distance alone can produce a match. |

**How they interact:** A pair of words is considered equivalent when:
- Levenshtein ratio ≥ `levenshtein_threshold` **AND**
- Jaro-Winkler score ≥ `jaro_winkler_threshold` **AND**
- (if `metaphone_required`) Metaphone codes match

Setting `metaphone_required=False` makes matching purely distance-based, which catches more typos but may produce false positives between phonetically different words.

#### 2. Preprocessing Flags — *"What to clean before comparing?"*

These flags control the automatic text normalization applied **before** any similarity calculation. They only affect the `for_names=False` path of the internal `normalize_text()` method.

| Flag | Type | Default | Effect |
| --- | --- | --- | --- |
| `ignore_case` | bool | `True` | Convert to common case before comparing |
| `normalize_whitespace` | bool | `True` | Collapse `"  hello   world  "` → `"hello world"` |
| `normalize_punctuation` | bool | `True` | Remove `,` `;` `:` `!` `?` `"` etc. |
| `normalize_parentheses` | bool | `False` | Remove parenthesized content: `"Test (Beta)"` → `"Test"` |
| `remove_accents` | bool | `False` | Strip diacritics: `"José"` → `"Jose"`, `"Müller"` → `"Muller"` |

#### 3. Debug

| Flag | Type | Default | Effect |
| --- | --- | --- | --- |
| `debug_mode` | bool | `False` | Adds detailed explanation fields to the metrics dictionary returned by comparison methods |

---

### Presets

Four factory methods create pre-tuned configurations for common scenarios:

```
                  strict()     default()    lenient()    fuzzy()
                  ─────────    ─────────    ─────────    ─────────
levenshtein       0.95         0.85         0.75         0.65
jaro_winkler      0.95         0.90         0.80         0.70
metaphone_req     True         True         False        False
─────────────────────────────────────────────────────────────────
Best for:         Legal/       General      Names,       Autocomplete,
                  financial    purpose      user input   search box
```

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig

# Use a preset directly
matcher = TextMatcher(config=MatcherConfig.strict())

# Or store and inspect
config = MatcherConfig.lenient()
print(config.to_dict())
# {'levenshtein_threshold': 0.75, 'jaro_winkler_threshold': 0.8,
#  'metaphone_required': False, 'ignore_case': True, ...}
```

---

### Choosing the Right Preset

#### `MatcherConfig.strict()` — Legal/Financial Data

Use when false positives are costly (compliance, deduplication in official records).

```python
matcher = TextMatcher(config=MatcherConfig.strict(), locale="es_ES")

# Only matches very close strings
matcher.compare_names("García", "Garcia")    # True  — accent difference only
matcher.compare_names("García", "Garsia")    # False — too many changes at 0.95
```

#### `MatcherConfig.default()` — General Purpose

Balanced trade-off. Good starting point.

```python
matcher = TextMatcher(config=MatcherConfig.default(), locale="es_ES")

matcher.compare_names("García", "Garsia")    # True  — close enough at 0.85
matcher.compare_names("García", "Gomez")     # False — totally different
```

#### `MatcherConfig.lenient()` — Names and User Input

Tolerates typos and informal variations. Disables phonetic requirement so purely visual similarity is enough.

```python
matcher = TextMatcher(config=MatcherConfig.lenient(), locale="en_US")

matcher.compare_names("Michael", "Mikhail")  # True  — low threshold + no metaphone
matcher.compare_names("Smith", "Smyth")      # True

# Full name matching
matcher.compare_name_bytokens(
    "Bill Johnson", "William Johnson"
)  # True — "Bill" resolved via en_US nickname dictionary
```

#### `MatcherConfig.fuzzy()` — Search / Autocomplete

Very permissive. Use for "did you mean?" suggestions, not for asserting identity.

```python
matcher = TextMatcher(config=MatcherConfig.fuzzy(), locale="es_ES")

candidates = ["iPhone 15 Pro Max", "Samsung Galaxy S24", "Google Pixel 8"]
results = matcher.compare_lists("iphone pro", candidates, top_k=3, threshold=0.50)
for product, score, _ in results:
    print(f"{product} ({score:.0%})")
```

---

### Custom Comparison Functions

Register your own comparison callables. Each must accept two strings and
return `(is_match: bool, metrics: dict)`.

```python
import difflib

def seq_ratio(a: str, b: str) -> tuple[bool, dict]:
    ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return ratio >= 0.8, {"ratio": round(ratio, 4)}

matcher.register_custom("seq_ratio", seq_ratio)

ok, info = matcher.run_custom("seq_ratio", "García López", "Garcia Lopez")
# ok=True, info={'ratio': 0.8333}
```

| Method                              | Description                                    |
| ----------------------------------- | ---------------------------------------------- |
| `register_custom(name, func)`     | Register a `(str, str) -> (bool, dict)` callable |
| `unregister_custom(name)`         | Remove a registered comparator                 |
| `run_custom(name, text1, text2)`  | Execute a registered comparator                |
| `list_custom()`                   | List registered comparators                    |

---

### Custom Configuration

Combine any thresholds and flags for specific use cases:

```python
# Company name matching: remove parentheses, ignore accents
config = MatcherConfig(
    levenshtein_threshold=0.80,
    jaro_winkler_threshold=0.85,
    metaphone_required=False,
    normalize_parentheses=True,
    remove_accents=True,
)
matcher = TextMatcher(config=config)

matcher.compare_name_bytokens(
    "Société Générale (France)", "Societe Generale"
)  # True — parentheses removed + accents stripped + 0.80 threshold met
```

```python
# Debug mode: see why a comparison matched or failed
config = MatcherConfig(debug_mode=True)
matcher = TextMatcher(config=config, locale="es_ES")

is_match, metrics = matcher.compare_names("José", "Jose")
print(metrics)
# Includes detailed explanation fields showing each algorithm's score
# and which thresholds were met or missed
```

---

### Overriding Config Per Call

Some methods accept a `config` parameter that overrides the instance config for that single call:

```python
# Instance uses default (strict comparisons)
matcher = TextMatcher(config=MatcherConfig.strict(), locale="es_ES")

# But for this specific call, use lenient settings
is_match, metrics = matcher.compare_names(
    "Migel", "Miguel",
    config=MatcherConfig.lenient()
)
# Uses lenient thresholds only for this comparison
```

Methods that accept a per-call `config`:
- `compare_names(config=...)`
- `compare_lists(config=...)`
- `batch_compare(config=...)`
- `detect_duplicates(config=...)`

---

### Validation

`MatcherConfig` validates thresholds at construction time:

```python
# Raises ValueError — thresholds must be between 0.0 and 1.0
MatcherConfig(levenshtein_threshold=1.5)   # ValueError
MatcherConfig(jaro_winkler_threshold=-0.1) # ValueError
```

### Supported Locales

The `locale` parameter controls which name abbreviation/nickname dictionary is used for methods like `compare_with_abbreviation()`, `compare_name_bytokens()`, and `_align_lists()`.

| Code | Language | Nicknames Examples |
| --- | --- | --- |
| `es_ES`, `es_MX`, `es_AR`, `es_CO`, `es_CL` | Spanish | Paco→Francisco, Pepe→José, Nacho→Ignacio |
| `en_US`, `en_GB` | English | Bill→William, Bob→Robert, Mike→Michael |
| `pt_BR`, `pt_PT` | Portuguese | Zé→José, Chico→Francisco, Dudu→Eduardo |
| `fr_FR` | French | JP→Jean-Pierre, Nico→Nicolas, Manu→Emmanuel |
| `de_DE` | German | Fritz→Friedrich, Sepp→Josef, Hans→Johannes |
| `it_IT` | Italian | Beppe→Giuseppe, Sandro→Alessandro, Gianni→Giovanni |

All locales also include single-letter initial expansions (e.g., `J` → common names starting with J in that language).

Bare language codes (`'es'`, `'en'`, `'pt'`, `'fr'`, `'de'`, `'it'`) are also accepted.

When `locale=None` (default), Spanish abbreviations are used for backward compatibility.

## Performance Considerations

### Computational Complexity

| Method | Complexity |
| --- | --- |
| `are_words_equivalent` | O(n×m) where n, m are word lengths |
| `compare_names` | O(n×m) where n, m are name lengths |
| `compare_name_bytokens` | O(n×m×w) where w is number of word pairs |
| `find_best_match` | O(k×n×m) where k is number of candidates |
| `compare_lists` | O(k×n×m) + O(k log k) for sorting |
| `batch_compare` | O(k×n×m) where k is number of pairs |
| `detect_duplicates` | O(n²×m) without blocking, O(n×k×m) with blocking |
| `find_phonetic_duplicates` | O(n²) pairwise comparison |
| `compare_phrases` | O(n+m) words |
| `same_chars` | O(n+m) characters |
| `compare_text_detailed` | O(n×m) characters |
| `find_common_patterns` | O(n×m) characters |

### Optimization Tips

1. **Enable Caching**: For repeated comparisons
   ```python
   matcher = TextMatcher(enable_cache=True, cache_size=10000)
   ```

2. **Use Blocking**: For large-scale deduplication
   ```python
   duplicates = matcher.detect_duplicates(items, use_blocking=True)
   ```

3. **Enable Parallelization**: For large batches
   ```python
   results = matcher.batch_compare(pairs, parallel=True, max_workers=8)
   ```

4. **Monitor Performance**: Check cache effectiveness
   ```python
   stats = matcher.get_cache_stats()
   print(f"Hit rate: {stats['hit_rate']:.2%}")
   ```

## Examples

### Basic Name Comparison

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig

matcher = TextMatcher()

# Single name comparison
is_match, metrics = matcher.compare_names("José", "Jose")
print(f"Match: {is_match}")  # True

# Full name comparison
is_match, metrics = matcher.compare_name_bytokens("John Smith", "Jon Smith")
print(f"Match: {is_match}, Rule: {metrics.get('rule_applied')}")
```

### Real-World Workflow

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig

# 1. Build a matcher for your domain
matcher = TextMatcher(config=MatcherConfig.lenient(), locale="es_ES")

# 2. Check a single pair of names — returns (bool, dict)
is_match, metrics = matcher.compare_names("Josema", "José María")
print(f"Match: {is_match}, Score: {metrics.get('levenshtein_ratio', 0):.2f}")

# 3. Find duplicates in a customer list
customers = ["García López, Antonio", "Garcia Lopez Antonio",
             "Martínez Ruiz, Pedro", "Martinez Ruiz Pedro"]
for n1, n2, score in matcher.detect_duplicates(customers, threshold=0.80):
    print(f"  Duplicate: '{n1}' ↔ '{n2}' ({score:.0%})")

# 4. Switch config on the fly for one strict comparison
is_match, _ = matcher.compare_names(
    "María", "Marta", config=MatcherConfig.strict()
)
print(f"Strict match: {is_match}")  # False — too different at 0.95
```

### Duplicate Detection

```python
matcher = TextMatcher()

names = ["John Smith", "Jon Smith", "Jane Doe", "Bob Johnson"]
duplicates = matcher.detect_duplicates(names, threshold=0.8)
for name1, name2, score in duplicates:
    print(f"'{name1}' matches '{name2}' with score {score:.2f}")
```

### Batch Comparison

```python
matcher = TextMatcher()

pairs = [("John", "Jon"), ("Smith", "Smyth"), ("Jane", "Jayne")]
results = matcher.batch_compare(pairs)
for (text1, text2), (is_match, metrics) in zip(pairs, results):
    if is_match:
        print(f"'{text1}' ≈ '{text2}' (ratio: {metrics['levenshtein_ratio']:.2f})")
```

### Finding Best Match

```python
matcher = TextMatcher()

candidates = ["Jon Smith", "John Smyth", "Jane Smith"]
best_match, score, metrics = matcher.find_best_match("John Smith", candidates)
if best_match:
    print(f"Best match: '{best_match}' with score {score:.2f}")
```

### Example Scripts

Runnable scripts in `examples/`:

| Script                                | Description                                                         |
| ------------------------------------- | ------------------------------------------------------------------- |
| `example_name_comparison.py`          | Single-word and multi-word name comparison (`compare_names`, `compare_name_bytokens`) |
| `example_fuzzy_search.py`             | Best-match lookup, ranked results, and vocabulary correction (`find_best_match`, `compare_lists`) |
| `example_batch_and_duplicates.py`     | Bulk pair evaluation and duplicate detection (`batch_compare`, `detect_duplicates`) |
| `example_config_presets.py`           | Effect of `MatcherConfig` presets on matching strictness             |
| `example_identity_resolution.py`      | Real-world name validation against a reference database              |
| `example_text_and_code_diff.py`       | Text and source-code diff (`compare_text_detailed`, `compare_code_blocks`) |
| `example_custom_comparators.py`       | Register and run user-defined comparison functions (`register_custom`, `run_custom`) |
| `example_cli.py`                      | CLI programmatic API (`run_api`, output utilities, CI mode)          |

## Dependencies

### Internal

- `shadetriptxt.utils.string_similarity`: `WordSimilarity` class and `are_words_equivalent` function
- `shadetriptxt.utils.string_similarity`: Similarity algorithm implementations (Levenshtein, Jaro-Winkler, MRA, etc.)
- `shadetriptxt.utils.string_ops`: Low-level text utilities (`flat_vowels`, `normalize_spaces`)
- `shadetriptxt.text_parser.text_normalizer`: Text preprocessing pipeline (used internally for automatic normalization)

### External (optional)

- `formulite` (via `pip install shadetriptxt[full]`): Advanced string similarity algorithms

## Contributing

When adding new features to TextMatcher:

1. Follow the existing API patterns
2. Include comprehensive docstrings (Description, Args, Returns, Raises, Example, Cost)
3. Add corresponding test cases
4. Update this README with new examples

## License

Part of the `shadetriptxt` library by DatamanEdge.
