"""
Example usage of the TextDummy configuration module.

Demonstrates:
    - Basic Config instantiation with defaults
    - Loading from file, environment, and arguments
    - Accessing values with get(), dictionary-style, require()
    - Schema validation
    - Error handling patterns
    - Sample config file generation

Run: python -m shadetriptxt.text_dummy.config_example
"""

from shadetriptxt.text_dummy.config import (
    Config,
    ConfigSchema,
    load_config,
    create_sample_config,
)


def example_basic_usage() -> None:
    """Basic configuration with defaults."""
    print("=" * 60)
    print("1. Basic Usage with Defaults")
    print("=" * 60)

    config = Config(defaults={
        "locale": "es_ES",
        "count": 10,
        "delimiter": ",",
        "encoding": "utf-8",
    })

    print(f"  locale    = {config.get('locale')}")
    print(f"  count     = {config.get('count', type=int)}")
    print(f"  delimiter = {config.get('delimiter')}")
    print(f"  encoding  = {config.get('encoding')}")
    print()


def example_method_chaining() -> None:
    """Method chaining with fluent API."""
    print("=" * 60)
    print("2. Method Chaining (Fluent API)")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES", "count": 10})
    config.load_env(prefix="TEXTDUMMY_")

    # Override via set (highest priority)
    config.set("locale", "en_US").set("count", 50)

    print(f"  locale = {config['locale']}")
    print(f"  count  = {config['count']}")
    print()


def example_dictionary_access() -> None:
    """Dictionary-style access patterns."""
    print("=" * 60)
    print("3. Dictionary-Style Access")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES", "count": 10})

    # Read
    print(f"  config['locale'] = {config['locale']}")

    # Write
    config["locale"] = "pt_BR"
    print(f"  config['locale'] = {config['locale']}  (after update)")

    # Contains check
    print(f"  'locale' in config = {'locale' in config}")
    print(f"  'debug' in config  = {'debug' in config}")
    print()


def example_require() -> None:
    """Required value access with error handling."""
    print("=" * 60)
    print("4. Required Values (require)")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES"})

    # This works — value exists
    locale = config.require("locale")
    print(f"  locale = {locale}")

    # This raises ValueError — value missing
    try:
        config.require("missing_key", message="'missing_key' is required for generation")
    except ValueError as e:
        print(f"  Error: {e}")
    print()


def example_schema_validation() -> None:
    """Schema-based validation."""
    print("=" * 60)
    print("5. Schema Validation")
    print("=" * 60)

    schema = ConfigSchema()
    schema.add_field("locale", type=str, required=True,
                     choices=["es_ES", "en_US", "en_GB", "pt_BR", "pt_PT",
                              "fr_FR", "de_DE", "it_IT", "es_MX", "es_AR",
                              "es_CO", "es_CL"])
    schema.add_field("count", type=int, min_value=1, max_value=1000000)
    schema.add_field("digits", type=int, min_value=1, max_value=20)
    schema.add_field("decimals", type=int, min_value=0, max_value=10)

    # Valid configuration
    config = Config(
        defaults={"locale": "es_ES", "count": 10, "digits": 6, "decimals": 2},
        schema=schema,
    )
    is_valid, errors = config.validate(raise_on_error=False)
    print(f"  Valid config: is_valid={is_valid}, errors={errors}")

    # Invalid configuration
    config_bad = Config(
        defaults={"locale": "xx_XX", "count": -5},
        schema=schema,
    )
    is_valid, errors = config_bad.validate(raise_on_error=False)
    print(f"  Bad config:   is_valid={is_valid}")
    for err in errors:
        print(f"    - {err}")
    print()


def example_load_config_convenience() -> None:
    """Convenience function load_config()."""
    print("=" * 60)
    print("6. Convenience Function: load_config()")
    print("=" * 60)

    # Load with module defaults + environment variables
    config = load_config(env_prefix="TEXTDUMMY_")

    print("  All defaults:")
    for key, value in config.all().items():
        print(f"    {key:25s} = {value}")
    print()


def example_sample_config_generation() -> None:
    """Generate a sample configuration file."""
    print("=" * 60)
    print("7. Sample Config File Generation")
    print("=" * 60)

    import tempfile
    import json
    from pathlib import Path

    # Generate in temp directory
    tmp = Path(tempfile.mkdtemp())
    filepath = str(tmp / "textdummy_config.json")

    success = create_sample_config(filepath)
    print(f"  Created: {success}")

    if success:
        with open(filepath, "r", encoding="utf-8") as f:
            sample = json.load(f)
        print(f"  Content: {json.dumps(sample, indent=2)}")

        # Clean up
        Path(filepath).unlink(missing_ok=True)
    print()


def example_config_copy() -> None:
    """Deep copy for isolated modifications."""
    print("=" * 60)
    print("8. Config Copy (Isolated Modifications)")
    print("=" * 60)

    original = Config(defaults={"locale": "es_ES", "count": 10})
    cloned = original.copy()

    cloned.set("locale", "en_US")

    print(f"  original['locale'] = {original['locale']}")
    print(f"  cloned['locale']   = {cloned['locale']}")
    print()


def example_environment_variables() -> None:
    """Loading from environment variables."""
    print("=" * 60)
    print("9. Environment Variables")
    print("=" * 60)

    import os

    # Simulate environment variables
    os.environ["TEXTDUMMY_LOCALE"] = "fr_FR"
    os.environ["TEXTDUMMY_COUNT"] = "100"
    os.environ["TEXTDUMMY_DELIMITER"] = ";"

    config = Config(defaults={"locale": "es_ES", "count": 10, "delimiter": ","})
    config.load_env(prefix="TEXTDUMMY_")

    print(f"  locale    = {config.get('locale')}  (from env: TEXTDUMMY_LOCALE=fr_FR)")
    print(f"  count     = {config.get('count')}  (from env: TEXTDUMMY_COUNT=100)")
    print(f"  delimiter = {config.get('delimiter')}  (from env: TEXTDUMMY_DELIMITER=;)")

    # Clean up environment
    del os.environ["TEXTDUMMY_LOCALE"]
    del os.environ["TEXTDUMMY_COUNT"]
    del os.environ["TEXTDUMMY_DELIMITER"]
    print()


def example_load_args() -> None:
    """Loading from command-line arguments (argparse Namespace)."""
    print("=" * 60)
    print("10. Load from Arguments (argparse)")
    print("=" * 60)

    import argparse

    # Simulate parsed arguments
    args = argparse.Namespace(locale="de_DE", count=25, delimiter=None)

    config = Config(defaults={"locale": "es_ES", "count": 10, "delimiter": ","})
    config.load_args(args)

    print(f"  locale    = {config.get('locale')}  (from args)")
    print(f"  count     = {config.get('count')}  (from args)")
    print(f"  delimiter = {config.get('delimiter')}  (from defaults, args was None)")
    print()


if __name__ == "__main__":
    example_basic_usage()
    example_method_chaining()
    example_dictionary_access()
    example_require()
    example_schema_validation()
    example_load_config_convenience()
    example_sample_config_generation()
    example_config_copy()
    example_environment_variables()
    example_load_args()

    print("All examples completed.")
