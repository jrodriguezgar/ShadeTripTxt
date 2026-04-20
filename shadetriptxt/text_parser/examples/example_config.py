"""
Example: Configuration Module
===============================
Demonstrates the TextParser Config class for managing settings.

Features:
    - Config()                — instantiate with defaults
    - load_env() / load_args()  — merge from environment / argparse
    - get() / require()       — safe and required access
    - ConfigSchema            — validation with types, ranges, and choices
    - create_sample_config()  — generate a sample JSON config file

Run: python -m shadetriptxt.text_parser.examples.example_config
"""

from shadetriptxt.text_parser.config import (
    Config,
    ConfigSchema,
    load_config,
    create_sample_config,
)


def example_basic_usage() -> None:
    """Instantiate Config with default values."""
    print("=" * 60)
    print("1. Basic Usage with Defaults")
    print("=" * 60)

    config = Config(defaults={
        "locale": "es_ES",
        "strength": 1,
        "keep_case": False,
        "keep_accents": False,
        "encoding": "utf-8",
    })

    print(f"  locale       = {config.get('locale')}")
    print(f"  strength     = {config.get('strength', type=int)}")
    print(f"  keep_case    = {config.get('keep_case')}")
    print(f"  keep_accents = {config.get('keep_accents')}")
    print(f"  encoding     = {config.get('encoding')}")
    print()


def example_fluent_api() -> None:
    """Method chaining with set()."""
    print("=" * 60)
    print("2. Method Chaining (Fluent API)")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES", "strength": 1})
    config.load_env(prefix="TEXTPARSER_")
    config.set("locale", "en_US").set("strength", 2)

    print(f"  locale   = {config['locale']}")
    print(f"  strength = {config['strength']}")
    print()


def example_dictionary_access() -> None:
    """Read, write, and membership via [] and 'in'."""
    print("=" * 60)
    print("3. Dictionary-Style Access")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES", "strength": 1})

    print(f"  config['locale']   = {config['locale']}")

    config["locale"] = "pt_BR"
    print(f"  config['locale']   = {config['locale']}  (updated)")

    print(f"  'locale' in config = {'locale' in config}")
    print(f"  'debug' in config  = {'debug' in config}")
    print()


def example_require() -> None:
    """require() raises ValueError when a key is missing."""
    print("=" * 60)
    print("4. Required Values")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES"})

    locale = config.require("locale")
    print(f"  locale = {locale}")

    try:
        config.require("missing_key", message="'missing_key' is required")
    except ValueError as e:
        print(f"  Error: {e}")
    print()


def example_schema_validation() -> None:
    """Validate configuration against a schema."""
    print("=" * 60)
    print("5. Schema Validation")
    print("=" * 60)

    schema = ConfigSchema()
    schema.add_field("locale", type=str, required=True,
                     choices=["es_ES", "en_US", "en_GB", "pt_BR", "pt_PT",
                              "fr_FR", "de_DE", "it_IT", "es_MX", "es_AR",
                              "es_CO", "es_CL"])
    schema.add_field("strength", type=int, min_value=0, max_value=3)

    # Valid
    config = Config(
        defaults={"locale": "es_ES", "strength": 1},
        schema=schema,
    )
    is_valid, errors = config.validate(raise_on_error=False)
    print(f"  Valid config: is_valid={is_valid}, errors={errors}")

    # Invalid
    config_bad = Config(
        defaults={"locale": "xx_XX", "strength": 5},
        schema=schema,
    )
    is_valid, errors = config_bad.validate(raise_on_error=False)
    print(f"  Bad config:   is_valid={is_valid}")
    for err in errors:
        print(f"    - {err}")
    print()


def example_load_config() -> None:
    """Convenience function load_config()."""
    print("=" * 60)
    print("6. load_config() Convenience")
    print("=" * 60)

    config = load_config(env_prefix="TEXTPARSER_")

    print("  Defaults:")
    for key, value in config.all().items():
        print(f"    {key:25s} = {value}")
    print()


def example_sample_config() -> None:
    """Generate and inspect a sample JSON config file."""
    print("=" * 60)
    print("7. Sample Config File")
    print("=" * 60)

    import json
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp())
    filepath = str(tmp / "textparser_config.json")

    success = create_sample_config(filepath)
    print(f"  Created: {success}")

    if success:
        with open(filepath, "r", encoding="utf-8") as f:
            sample = json.load(f)
        print(f"  Content: {json.dumps(sample, indent=2)}")
        Path(filepath).unlink(missing_ok=True)
    print()


def example_copy() -> None:
    """Deep copy for isolated modifications."""
    print("=" * 60)
    print("8. Config Copy")
    print("=" * 60)

    original = Config(defaults={"locale": "es_ES", "strength": 1})
    cloned = original.copy()
    cloned.set("locale", "en_US")

    print(f"  original['locale'] = {original['locale']}")
    print(f"  cloned['locale']   = {cloned['locale']}")
    print()


def example_environment() -> None:
    """Load from environment variables."""
    print("=" * 60)
    print("9. Environment Variables")
    print("=" * 60)

    import os

    os.environ["TEXTPARSER_LOCALE"] = "fr_FR"
    os.environ["TEXTPARSER_STRENGTH"] = "2"

    config = Config(defaults={"locale": "es_ES", "strength": 1})
    config.load_env(prefix="TEXTPARSER_")

    print(f"  locale   = {config.get('locale')}  (from TEXTPARSER_LOCALE)")
    print(f"  strength = {config.get('strength')}  (from TEXTPARSER_STRENGTH)")

    del os.environ["TEXTPARSER_LOCALE"]
    del os.environ["TEXTPARSER_STRENGTH"]
    print()


def example_load_args() -> None:
    """Load from argparse Namespace."""
    print("=" * 60)
    print("10. Load from argparse")
    print("=" * 60)

    import argparse

    args = argparse.Namespace(locale="de_DE", strength=3, keep_case=None)

    config = Config(defaults={"locale": "es_ES", "strength": 1, "keep_case": False})
    config.load_args(args)

    print(f"  locale    = {config.get('locale')}  (from args)")
    print(f"  strength  = {config.get('strength')}  (from args)")
    print(f"  keep_case = {config.get('keep_case')}  (default — args was None)")
    print()


if __name__ == "__main__":
    example_basic_usage()
    example_fluent_api()
    example_dictionary_access()
    example_require()
    example_schema_validation()
    example_load_config()
    example_sample_config()
    example_copy()
    example_environment()
    example_load_args()

    print("All config examples completed.")
