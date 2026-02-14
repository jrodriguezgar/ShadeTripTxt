# TextAnonymizer — Configuration Module

Configuration management for PII detection & anonymization (7 strategies, 12 locales).

## Overview

The `config.py` module provides a unified configuration manager with multi-source priority resolution:

```
Arguments > Environment Variables > Config File > Defaults
```

## Quick Usage

```python
from shadetriptxt.text_anonymizer.config import Config, load_config, create_sample_config

# Quick setup with defaults
config = load_config(filepath='anonymizer_config.json')

# Access values
locale = config.get('locale')              # -> 'es_ES'
strategy = config.get('strategy')          # -> 'redact'

# Dictionary-style access
config['locale'] = 'en_US'
print(config['locale'])

# Create a sample config file
create_sample_config('anonymizer_config.json')
```

## Default Values

| Key | Default | Description |
|-----|---------|-------------|
| `locale` | `es_ES` | Anonymization locale |
| `strategy` | `redact` | Default strategy (`mask`, `replace`, `hash`, `redact`, `generalize`, `pseudonymize`, `suppress`) |
| `seed` | `None` | Random seed for reproducible output |
| `mask_char` | `*` | Single character used by the built-in mask logic |
| `detection.use_regex` | `True` | Enable regex PII detection |
| `detection.use_spacy` | `False` | Enable spaCy NER detection |
| `detection.use_nltk` | `False` | Enable NLTK NER detection |
| `detection.min_confidence` | `0.0` | Minimum confidence threshold (0.0–1.0) |
| `hash_length` | `12` | Truncated SHA-256 hash length |

## Environment Variables

All settings can be overridden via environment variables with the `ANONYMIZER_` prefix:

```bash
# Simple keys
export ANONYMIZER_LOCALE=en_US
export ANONYMIZER_STRATEGY=mask

# Nested keys (double underscore)
export ANONYMIZER_DETECTION__USE_SPACY=true
export ANONYMIZER_DETECTION__MIN_CONFIDENCE=0.5
```

## Configuration File

Auto-discovered filenames (searched in current directory):

1. `anonymizer_config.json`
2. `anonymizer_config.yaml` / `anonymizer_config.yml`
3. `anonymizer_config.toml`
4. `config.json` / `config.yaml` / `config.yml` / `config.toml`

**Sample JSON config:**

```json
{
  "anonymizer": {
    "locale": "es_ES",
    "strategy": "redact",
    "seed": null,
    "mask_char": "*"
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
    "PHONE": "mask"
  }
}
```

**Sample TOML config:**

```toml
[anonymizer]
locale = "es_ES"
strategy = "redact"
mask_char = "*"

[detection]
use_regex = true
use_spacy = false
use_nltk = false
min_confidence = 0.0

[strategies]
hash_length = 12

[type_overrides]
EMAIL = "mask"
PHONE = "mask"
```

## Schema Validation

```python
from shadetriptxt.text_anonymizer.config import Config, ConfigSchema

schema = ConfigSchema()
schema.add_field('locale', type=str, required=True,
                 choices=['es_ES', 'en_US', 'en_GB', 'pt_BR', 'pt_PT',
                          'fr_FR', 'de_DE', 'it_IT', 'es_MX', 'es_AR',
                          'es_CO', 'es_CL'])
schema.add_field('strategy', type=str, required=True,
                 choices=['mask', 'replace', 'hash', 'redact',
                          'generalize', 'pseudonymize', 'suppress'])
schema.add_field('detection.min_confidence', type=float,
                 min_value=0.0, max_value=1.0)

config = Config(schema=schema)
config.load_file('anonymizer_config.json')
is_valid, errors = config.validate(raise_on_error=False)
```

## Integration with TextAnonymizer

```python
from shadetriptxt.text_anonymizer.config import load_config
from shadetriptxt.text_anonymizer import TextAnonymizer

config = load_config(filepath='anonymizer_config.json')

anon = TextAnonymizer(
    locale=config.get('locale', 'es_ES'),
    strategy=config.get('strategy', 'redact'),
    seed=config.get('seed', type=int),
    mask_char=config.get('mask_char', '*'),
)

# Apply per-type overrides from config
type_overrides = {
    k.replace('type_overrides.', ''): v
    for k, v in config.all().items()
    if k.startswith('type_overrides.')
}
for pii_type, strategy in type_overrides.items():
    anon.set_strategy(strategy, pii_type=pii_type)

# Use detection settings from config
result = anon.anonymize_text(
    "DNI: 12345678Z, email: juan@test.com",
    use_regex=config.get('detection.use_regex', True),
    use_spacy=config.get('detection.use_spacy', False),
    min_confidence=config.get('detection.min_confidence', 0.0, type=float),
)
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
