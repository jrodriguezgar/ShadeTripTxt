# TextMatcher — Normalization Config

> How to configure `MatcherConfig` normalization flags for text comparison and deduplication.
>
> For details on **what each normalization step does** (punctuation rules, accent stripping logic, whitespace handling), see the normalization engine reference: [text_parser/README_Normalization.md](../text_parser/README_Normalization.md).

---

## Quick Start

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig

# Option 1: Use defaults (punctuation normalization only)
matcher = TextMatcher()

# Option 2: Enable full normalization
config = MatcherConfig(
    normalize_punctuation=True,    # Remove punctuation
    normalize_parentheses=True,    # Remove (content)
    remove_accents=True            # José → Jose
)
matcher = TextMatcher(config=config)
```

---

## Configuration Flags

These `MatcherConfig` flags are passed to `text_parser.text_normalizer.normalize_text()` internally when `for_names=False`:

| MatcherConfig Flag | text_normalizer Parameter | Default | Effect |
|--------------------|---------------------------|---------|--------|
| `normalize_punctuation` | `remove_punctuation` | ✅ True | Remove `. , ; : ! ? ¡ ¿` |
| `normalize_whitespace` | `normalize_whitespace` | ✅ True | Collapse multiple spaces |
| `normalize_parentheses` | `remove_parentheses_content` | ❌ False | Remove `(content)` |
| `remove_accents` | `remove_accents` | ❌ False | Strip diacritical marks (é→e) |

For name-specific normalization (`for_names=True`), `TextMatcher` uses its own regex that keeps letters (all Latin scripts), spaces, hyphens, and apostrophes — `text_normalizer` is not used.

---

## Common Scenarios

### Scenario 1: Name Matching (International)

```python
# Enable accent removal for international names
config = MatcherConfig(
    normalize_punctuation=True,
    remove_accents=True
)
matcher = TextMatcher(config=config, locale='de_DE')

# Single-word names — use compare_names:
matcher.compare_names("François", "Francois")            # ✓ Match
matcher.compare_names("Müller", "Muller")                # ✓ Match

# Multi-word names — use compare_name_bytokens:
matcher.compare_name_bytokens("José García", "Jose Garcia")  # ✓ Match
matcher.compare_name_bytokens("Fritz Müller", "Friedrich Muller")  # ✓ Match
```

### Scenario 2: Company Name Matching

```python
# Remove parentheses for company names
config = MatcherConfig(
    normalize_punctuation=True,
    normalize_parentheses=True
)
matcher = TextMatcher(config=config)

# Single-word comparisons:
matcher.compare_names("Apple", "Apple")                  # ✓ Match

# Multi-word comparisons:
matcher.compare_name_bytokens("Apple Inc.", "Apple Inc")         # ✓ Match
matcher.compare_name_bytokens("Company (USA)", "Company USA")    # ✓ Match
matcher.compare_name_bytokens("Test, LLC", "Test LLC")           # ✓ Match
```

### Scenario 3: Duplicate Detection in Messy Data

```python
# Enable all normalization for messy datasets
config = MatcherConfig(
    normalize_punctuation=True,
    normalize_parentheses=True,
    remove_accents=True
)
matcher = TextMatcher(config=config)

items = [
    "José  García",
    "Jose Garcia",      # Duplicate: accents + spaces
    "Test, Inc.",
    "Test Inc",         # Duplicate: punctuation
    "Company (2024)",
    "Company 2024"      # Duplicate: parentheses
]

duplicates = matcher.detect_duplicates(items, threshold=0.95)
# Returns all 3 duplicate pairs
```

### Scenario 4: Exact Matching (No Normalization)

```python
# Disable normalization when format matters
config = MatcherConfig(
    normalize_punctuation=False,
    normalize_parentheses=False,
    remove_accents=False
)
matcher = TextMatcher(config=config)

# These require exact match:
matcher.compare_names("José", "Jose")       # Depends on phonetic similarity
```

---

## Presets

`MatcherConfig` provides factory methods with ready-made normalization settings:

| Preset | Punctuation | Whitespace | Accents | Parentheses | Use Case |
|--------|:-----------:|:----------:|:-------:|:-----------:|----------|
| `MatcherConfig()` | ✅ | ✅ | ❌ | ❌ | General purpose |
| `.strict()` | ✅ | ✅ | ❌ | ❌ | Legal / financial data |
| `.lenient()` | ✅ | ✅ | ✅ | ❌ | User-input name matching |
| `.fuzzy()` | ✅ | ✅ | ✅ | ✅ | Messy datasets, deduplication |

```python
config = MatcherConfig.lenient()     # accent removal enabled
config = MatcherConfig.fuzzy()       # all normalization enabled
```

---

## Performance Tips

### For Small Datasets (< 1,000 items)
```python
# Defaults are fine
matcher = TextMatcher()
```

### For Medium Datasets (1,000 - 10,000 items)
```python
# Enable caching
matcher = TextMatcher(enable_cache=True, cache_size=5000)
```

### For Large Datasets (> 10,000 items)
```python
# Enable caching + blocking
matcher = TextMatcher(enable_cache=True, cache_size=10000)
duplicates = matcher.detect_duplicates(
    items,
    use_blocking=True,      # 100x faster for large lists
    parallel=True           # Use multiple CPU cores
)
```

---

## Common Mistakes

### ❌ Mistake 1: Over-normalization
```python
# Don't remove accents if they're semantically important
config = MatcherConfig(remove_accents=True)
matcher = TextMatcher(config=config)

# Problem: "resume" and "résumé" now match (different meanings!)
```

### ❌ Mistake 2: Under-normalization
```python
# Don't disable punctuation normalization for user data
config = MatcherConfig(normalize_punctuation=False)
matcher = TextMatcher(config=config)

# Problem: "John Smith" and "John Smith," don't match
```

### ✅ Best Practice
```python
# Start with defaults, add features as needed
config = MatcherConfig(
    normalize_punctuation=True,     # Almost always needed
    normalize_parentheses=False,    # Enable if needed
    remove_accents=False            # Enable if needed
)
```

---

## Testing Your Configuration

```python
matcher = TextMatcher(config=MatcherConfig(remove_accents=True))

# Test single-word names
test_pairs = [
    ("José", "Jose"),                         # Accents
    ("François", "Francois"),                 # Accents
    ("Müller", "Muller"),                     # Accents
]

for str1, str2 in test_pairs:
    is_match, metrics = matcher.compare_names(str1, str2)
    print(f"'{str1}' vs '{str2}': {is_match}")

# Test multi-word names
test_fullnames = [
    ("Test  String", "Test String"),          # Multiple spaces
    ("José García", "Jose Garcia"),           # Accents
    ("Company (USA)", "Company USA"),         # Parentheses
]

for str1, str2 in test_fullnames:
    is_match, metrics = matcher.compare_name_bytokens(str1, str2)
    print(f"'{str1}' vs '{str2}': {is_match}")
```

---

## API Reference

### Methods That Use Normalization

- ✅ `compare_names(name1, name2, config=...)` — single-word comparison
- ✅ `compare_name_bytokens(name1, name2, ...)` — multi-word full name comparison
- ✅ `find_best_match(target, candidates, ...)`
- ✅ `compare_lists(target, candidates, config=...)`
- ✅ `batch_compare(pairs, config=...)`
- ✅ `detect_duplicates(items, config=...)`

### Configuration Precedence

```python
# Method-level config overrides instance config
matcher = TextMatcher(config=default_config)

# Use different config for specific comparison
is_match, metrics = matcher.compare_names(
    name1,
    name2,
    config=special_config    # Overrides default_config
)
```

### Inspecting Normalized Output

```python
matcher = TextMatcher()

# Name normalization (uses TextMatcher's own regex)
matcher.normalize_text("José María O'Connor-Smith", for_names=True)
# "JOSÉ MARÍA O'CONNOR-SMITH"

# General text normalization (delegates to text_normalizer)
matcher.normalize_text("  John   Smith,  Inc.  ")
# "JOHN SMITH INC"
```

---

## FAQ

**Q: Are normalized results cached?**
A: Yes, if caching is enabled (`enable_cache=True`). Normalized strings are used as cache keys.

**Q: Does normalization change the original strings?**
A: No. Normalization only affects the internal comparison — original strings are never modified.

**Q: What's the difference between `TextMatcher.normalize_text()` and `text_normalizer.normalize_text()`?**
A: `TextMatcher.normalize_text()` adds a name-specific mode (`for_names=True`) that preserves accents, hyphens, and apostrophes. For general text (`for_names=False`), it delegates to `text_normalizer.normalize_text()`.

**Q: Does this work with `are_words_equivalent()`?**
A: No. Normalization is only applied inside TextMatcher methods. Preprocess strings with `text_normalizer.normalize_text()` before passing them to `are_words_equivalent()`.

---

## Related Documents

| Topic | Document |
|-------|----------|
| Normalization engine reference | [text_parser/README_Normalization.md](../text_parser/README_Normalization.md) |
| TextMatcher API reference | [README.md](README.md) |
| TextMatcher + TextParser integration | [README_TextMatcher_Integration.md](README_TextMatcher_Integration.md) |
