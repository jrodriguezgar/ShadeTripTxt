# TextDummy — Configuration Module

Configuration management for locale-aware fake data generation (65+ data types, 12 locales).

## Overview

The `config.py` module provides a unified configuration manager with multi-source priority resolution:

```
Arguments > Environment Variables > Config File > Defaults
```

## Quick Usage

```python
from shadetriptxt.text_dummy.config import Config, load_config, create_sample_config

# Quick setup with defaults
config = load_config(filepath='textdummy_config.json')

# Access values
locale = config.get('locale')              # -> 'es_ES'
count = config.get('count', type=int)       # -> 10

# Dictionary-style access
config['locale'] = 'en_US'
print(config['locale'])

# Create a sample config file
create_sample_config('textdummy_config.json')
```

## Default Values

| Key | Default | Description |
|-----|---------|-------------|
| `locale` | `es_ES` | Generation locale |
| `count` | `10` | Number of items to generate |
| `delimiter` | `,` | CSV delimiter for batch mode |
| `encoding` | `utf-8` | File encoding |
| `number_type` | `integer` | Number type (`integer` / `float`) |
| `digits` | `6` | Significant digits |
| `decimals` | `2` | Decimal places for floats |
| `key_length` | `8` | Key length |
| `key_type` | `alphanumeric` | Key type |

## Environment Variables

All settings can be overridden via environment variables with the `TEXTDUMMY_` prefix:

```bash
# Simple keys
export TEXTDUMMY_LOCALE=en_US
export TEXTDUMMY_COUNT=50

# Nested keys (double underscore)
export TEXTDUMMY_GENERATOR__LOCALE=pt_BR
```

## Configuration File

Auto-discovered filenames (searched in current directory):

1. `textdummy_config.json`
2. `textdummy_config.yaml` / `textdummy_config.yml`
3. `textdummy_config.toml`
4. `config.json` / `config.yaml` / `config.yml` / `config.toml`

**Sample JSON config:**

```json
{
  "generator": {
    "locale": "es_ES",
    "count": 10
  },
  "batch": {
    "delimiter": ",",
    "encoding": "utf-8"
  },
  "number": {
    "type": "integer",
    "digits": 6,
    "decimals": 2,
    "currency": false
  },
  "date": {
    "start": "1970-01-01",
    "end": null,
    "pattern": null
  },
  "key": {
    "length": 8,
    "type": "alphanumeric",
    "prefix": "",
    "separator": "",
    "segment_length": 0
  }
}
```

## Schema Validation

```python
from shadetriptxt.text_dummy.config import Config, ConfigSchema

schema = ConfigSchema()
schema.add_field('locale', type=str, required=True,
                 choices=['es_ES', 'en_US', 'en_GB', 'pt_BR', 'pt_PT',
                          'fr_FR', 'de_DE', 'it_IT', 'es_MX', 'es_AR',
                          'es_CO', 'es_CL'])
schema.add_field('count', type=int, min_value=1, max_value=1000000)

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
