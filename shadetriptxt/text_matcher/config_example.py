"""
Example usage of the TextMatcher configuration module.

Demonstrates:
    - Basic Config instantiation with defaults
    - Loading from file, environment, and arguments
    - Accessing values with get(), dictionary-style, require()
    - Schema validation
    - Error handling patterns
    - Sample config file generation

Run: python -m shadetriptxt.text_matcher.config_example
"""

from shadetriptxt.text_matcher.config import (
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
        "preset": "default",
        "levenshtein_threshold": 0.85,
        "jaro_winkler_threshold": 0.9,
        "ignore_case": True,
    })

    print(f"  locale                = {config.get('locale')}")
    print(f"  preset                = {config.get('preset')}")
    print(f"  levenshtein_threshold = {config.get('levenshtein_threshold', type=float)}")
    print(f"  jaro_winkler_threshold= {config.get('jaro_winkler_threshold', type=float)}")
    print(f"  ignore_case           = {config.get('ignore_case')}")
    print()


def example_method_chaining() -> None:
    """Method chaining with fluent API."""
    print("=" * 60)
    print("2. Method Chaining (Fluent API)")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES", "preset": "default"})
    config.load_env(prefix="TEXTMATCHER_")

    # Override via set (highest priority)
    config.set("preset", "lenient").set("threshold", 0.7)

    print(f"  preset    = {config['preset']}")
    print(f"  threshold = {config['threshold']}")
    print()


def example_dictionary_access() -> None:
    """Dictionary-style access patterns."""
    print("=" * 60)
    print("3. Dictionary-Style Access")
    print("=" * 60)

    config = Config(defaults={"locale": "es_ES", "preset": "default"})

    # Read
    print(f"  config['preset'] = {config['preset']}")

    # Write
    config["preset"] = "strict"
    print(f"  config['preset'] = {config['preset']}  (after update)")

    # Contains check
    print(f"  'preset' in config = {'preset' in config}")
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
        config.require("missing_key", message="'missing_key' is required for matching")
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
    schema.add_field("levenshtein_threshold", type=float, min_value=0.0, max_value=1.0)
    schema.add_field("jaro_winkler_threshold", type=float, min_value=0.0, max_value=1.0)
    schema.add_field("cache_size", type=int, min_value=1, max_value=100000)

    # Valid configuration
    config = Config(
        defaults={
            "locale": "es_ES",
            "levenshtein_threshold": 0.85,
            "jaro_winkler_threshold": 0.9,
            "cache_size": 1024,
        },
        schema=schema,
    )
    is_valid, errors = config.validate(raise_on_error=False)
    print(f"  Valid config: is_valid={is_valid}, errors={errors}")

    # Invalid configuration
    config_bad = Config(
        defaults={"locale": "xx_XX", "levenshtein_threshold": 1.5},
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
    config = load_config(env_prefix="TEXTMATCHER_")

    print("  All defaults:")
    for key, value in config.all().items():
        print(f"    {key:30s} = {value}")
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
    filepath = str(tmp / "textmatcher_config.json")

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

    original = Config(defaults={"preset": "default", "threshold": 0.85})
    cloned = original.copy()

    cloned.set("preset", "lenient").set("threshold", 0.7)

    print(f"  original['preset']    = {original['preset']}")
    print(f"  original['threshold'] = {original['threshold']}")
    print(f"  cloned['preset']      = {cloned['preset']}")
    print(f"  cloned['threshold']   = {cloned['threshold']}")
    print()


def example_environment_variables() -> None:
    """Loading from environment variables."""
    print("=" * 60)
    print("9. Environment Variables")
    print("=" * 60)

    import os

    # Simulate environment variables
    os.environ["TEXTMATCHER_LOCALE"] = "fr_FR"
    os.environ["TEXTMATCHER_PRESET"] = "strict"
    os.environ["TEXTMATCHER_THRESHOLD"] = "0.95"

    config = Config(defaults={"locale": "es_ES", "preset": "default", "threshold": 0.85})
    config.load_env(prefix="TEXTMATCHER_")

    print(f"  locale    = {config.get('locale')}  (from env: TEXTMATCHER_LOCALE=fr_FR)")
    print(f"  preset    = {config.get('preset')}  (from env: TEXTMATCHER_PRESET=strict)")
    print(f"  threshold = {config.get('threshold')}  (from env: TEXTMATCHER_THRESHOLD=0.95)")

    # Clean up environment
    del os.environ["TEXTMATCHER_LOCALE"]
    del os.environ["TEXTMATCHER_PRESET"]
    del os.environ["TEXTMATCHER_THRESHOLD"]
    print()


def example_load_args() -> None:
    """Loading from command-line arguments (argparse Namespace)."""
    print("=" * 60)
    print("10. Load from Arguments (argparse)")
    print("=" * 60)

    import argparse

    # Simulate parsed arguments
    args = argparse.Namespace(locale="de_DE", preset="fuzzy", threshold=None)

    config = Config(defaults={"locale": "es_ES", "preset": "default", "threshold": 0.85})
    config.load_args(args)

    print(f"  locale    = {config.get('locale')}  (from args)")
    print(f"  preset    = {config.get('preset')}  (from args)")
    print(f"  threshold = {config.get('threshold')}  (from defaults, args was None)")
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
