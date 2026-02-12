# TextMatcher — Configuration Module

Configuration management for fuzzy text comparison, name matching, deduplication, and diff analysis.

## Overview

The `config.py` module provides a unified configuration manager with multi-source priority resolution:

```
Arguments > Environment Variables > Config File > Defaults
```

## Quick Usage

```python
from shadetriptxt.text_matcher.config import Config, load_config, create_sample_config

# Quick setup with defaults
config = load_config(filepath='textmatcher_config.json')

# Access values
locale = config.get('locale')                              # -> 'es_ES'
threshold = config.get('levenshtein_threshold', type=float) # -> 0.85

# Dictionary-style access
config['preset'] = 'lenient'
print(config['preset'])

# Create a sample config file
create_sample_config('textmatcher_config.json')
```

## Default Values

| Key | Default | Description |
|-----|---------|-------------|
| `locale` | `es_ES` | Abbreviation locale |
| `preset` | `default` | Config preset (`strict`/`default`/`lenient`/`fuzzy`) |
| `levenshtein_threshold` | `0.85` | Levenshtein similarity threshold |
| `jaro_winkler_threshold` | `0.9` | Jaro-Winkler similarity threshold |
| `metaphone_required` | `true` | Require phonetic match |
| `ignore_case` | `true` | Case-insensitive comparison |
| `normalize_whitespace` | `true` | Normalize whitespace |
| `normalize_punctuation` | `true` | Normalize punctuation |
| `normalize_parentheses` | `false` | Remove parenthesized content |
| `remove_accents` | `false` | Strip accents before comparison |
| `debug_mode` | `false` | Enable debug output |
| `enable_cache` | `true` | Enable LRU cache for comparisons |
| `cache_size` | `1024` | Cache size (entries) |
| `threshold` | `0.85` | Default comparison threshold |
| `use_blocking` | `true` | Enable blocking for deduplication |
| `parallel` | `false` | Enable parallel processing |

## Environment Variables

All settings can be overridden via environment variables with the `TEXTMATCHER_` prefix:

```bash
# Simple keys
export TEXTMATCHER_LOCALE=en_US
export TEXTMATCHER_PRESET=lenient
export TEXTMATCHER_LEVENSHTEIN_THRESHOLD=0.75

# Nested keys (double underscore)
export TEXTMATCHER_MATCHER__LOCALE=pt_BR
export TEXTMATCHER_PERFORMANCE__CACHE_SIZE=2048
```

## Configuration File

Auto-discovered filenames (searched in current directory):

1. `textmatcher_config.json`
2. `textmatcher_config.yaml` / `textmatcher_config.yml`
3. `textmatcher_config.toml`
4. `config.json` / `config.yaml` / `config.yml` / `config.toml`

**Sample JSON config:**

```json
{
  "matcher": {
    "locale": "es_ES",
    "preset": "default",
    "levenshtein_threshold": 0.85,
    "jaro_winkler_threshold": 0.9,
    "metaphone_required": true
  },
  "normalization": {
    "ignore_case": true,
    "normalize_whitespace": true,
    "normalize_punctuation": true,
    "normalize_parentheses": false,
    "remove_accents": false
  },
  "performance": {
    "enable_cache": true,
    "cache_size": 1024,
    "use_blocking": true,
    "parallel": false
  },
  "comparison": {
    "threshold": 0.85,
    "debug_mode": false
  }
}
```

## Schema Validation

```python
from shadetriptxt.text_matcher.config import Config, ConfigSchema

schema = ConfigSchema()
schema.add_field('locale', type=str, required=True,
                 choices=['es_ES', 'en_US', 'en_GB', 'pt_BR', 'pt_PT',
                          'fr_FR', 'de_DE', 'it_IT', 'es_MX', 'es_AR',
                          'es_CO', 'es_CL'])
schema.add_field('levenshtein_threshold', type=float, min_value=0.0, max_value=1.0)
schema.add_field('jaro_winkler_threshold', type=float, min_value=0.0, max_value=1.0)

config = Config(schema=schema)
config.load_file('textmatcher_config.json')
is_valid, errors = config.validate(raise_on_error=False)
```

## Public API

| Class/Function | Description |
|----------------|-------------|
| `Config` | Configuration manager with priority resolution |
| `ConfigSchema` | Schema definition and validation |
| `ConfigValue` | Value wrapper with source metadata |
| `ConfigSource` | Enum: `DEFAULT`, `FILE`, `ENVIRONMENT`, `ARGUMENT` |
| `ConfigFormat` | Enum: `JSON`, `YAML`, `TOML` |
| `load_config()` | Convenience function — creates pre-configured `Config` |
| `create_sample_config()` | Generate a sample JSON config file |

## Config Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `.get(key, default, type)` | `Any` | Get value with priority resolution |
| `.set(key, value)` | `Config` | Set value (highest priority) |
| `.require(key)` | `Any` | Get value or raise `ValueError` |
| `.all()` | `dict` | Get all resolved values |
| `.load_file(path)` | `Config` | Load from JSON/YAML/TOML |
| `.load_env(prefix)` | `Config` | Load from environment variables |
| `.load_args(args)` | `Config` | Load from argparse namespace |
| `.validate()` | `(bool, list)` | Validate against schema |
| `.copy()` | `Config` | Deep copy |
