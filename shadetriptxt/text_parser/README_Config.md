# TextParser — Configuration Module

Configuration management for text parsing, normalization, extraction, and locale-aware processing.

## Overview

The `config.py` module provides a unified configuration manager with multi-source priority resolution:

```
Arguments > Environment Variables > Config File > Defaults
```

## Quick Usage

```python
from shadetriptxt.text_parser.config import Config, load_config, create_sample_config

# Quick setup with defaults
config = load_config(filepath='textparser_config.json')

# Access values
locale = config.get('locale')                    # -> 'es_ES'
strength = config.get('strength', type=int)       # -> 1

# Dictionary-style access
config['locale'] = 'en_US'
print(config['locale'])

# Create a sample config file
create_sample_config('textparser_config.json')
```

## Default Values

| Key | Default | Description |
|-----|---------|-------------|
| `locale` | `es_ES` | Processing locale |
| `strength` | `1` | Phonetic reduction strength (0-3) |
| `keep_case` | `false` | Preserve case during normalization |
| `keep_punctuation` | `false` | Preserve punctuation |
| `keep_accents` | `false` | Preserve accents |
| `remove_parentheses` | `false` | Remove parenthesized content |
| `aggressive` | `false` | Aggressive preparation mode |
| `normalize_quotes` | `false` | Convert typographic quotes |
| `encoding` | `utf-8` | File encoding |
| `mask_char` | `*` | Masking character |
| `keep_first` | `1` | Characters to keep at mask start |
| `keep_last` | `1` | Characters to keep at mask end |

## Environment Variables

All settings can be overridden via environment variables with the `TEXTPARSER_` prefix:

```bash
# Simple keys
export TEXTPARSER_LOCALE=en_US
export TEXTPARSER_STRENGTH=2
export TEXTPARSER_KEEP_CASE=true

# Nested keys (double underscore)
export TEXTPARSER_PARSER__LOCALE=pt_BR
```

## Configuration File

Auto-discovered filenames (searched in current directory):

1. `textparser_config.json`
2. `textparser_config.yaml` / `textparser_config.yml`
3. `textparser_config.toml`
4. `config.json` / `config.yaml` / `config.yml` / `config.toml`

**Sample JSON config:**

```json
{
  "parser": {
    "locale": "es_ES",
    "strength": 1,
    "aggressive": false
  },
  "normalize": {
    "keep_case": false,
    "keep_punctuation": false,
    "keep_accents": false,
    "remove_parentheses": false
  },
  "encoding": {
    "normalize_quotes": false
  },
  "mask": {
    "char": "*",
    "keep_first": 1,
    "keep_last": 1
  },
  "batch": {
    "encoding": "utf-8",
    "operation": "normalize"
  }
}
```

## Schema Validation

```python
from shadetriptxt.text_parser.config import Config, ConfigSchema

schema = ConfigSchema()
schema.add_field('locale', type=str, required=True,
                 choices=['es_ES', 'en_US', 'en_GB', 'pt_BR', 'pt_PT',
                          'fr_FR', 'de_DE', 'it_IT', 'es_MX', 'es_AR',
                          'es_CO', 'es_CL'])
schema.add_field('strength', type=int, min_value=0, max_value=3)

config = Config(schema=schema)
config.load_file('config.json')
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
