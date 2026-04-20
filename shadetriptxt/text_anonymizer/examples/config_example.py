"""
Example usage of the TextAnonymizer configuration module.

Demonstrates loading configuration from files, environment variables,
and programmatic arguments, plus schema validation.

Run:
    python -m shadetriptxt.text_anonymizer.config_example
"""

from shadetriptxt.text_anonymizer.config import (
    Config,
    ConfigSchema,
    load_config,
    create_sample_config,
)


def example_basic() -> None:
    """Basic configuration usage."""
    config = Config(defaults={
        "locale": "es_ES",
        "strategy": "redact",
        "detection.use_regex": True,
        "detection.use_spacy": False,
        "detection.min_confidence": 0.0,
    })

    print(f"Locale:     {config['locale']}")
    print(f"Strategy:   {config.get('strategy')}")
    print(f"Use regex:  {config.get('detection.use_regex')}")
    print(f"Confidence: {config.get('detection.min_confidence', type=float)}")


def example_file_and_env() -> None:
    """Load from file + environment variables."""
    # Generate a sample config file
    create_sample_config("anonymizer_config.json")

    # Load with priority: env > file > defaults
    config = load_config(
        filepath="anonymizer_config.json",
        env_prefix="ANONYMIZER_",
    )

    print(f"Locale:    {config['locale']}")
    print(f"Strategy:  {config['strategy']}")
    print(f"All keys:  {list(config.all().keys())}")


def example_schema_validation() -> None:
    """Schema validation example."""
    schema = ConfigSchema()
    schema.add_field("locale", type=str, required=True,
                     choices=["es_ES", "en_US", "en_GB", "pt_BR", "pt_PT",
                              "fr_FR", "de_DE", "it_IT", "es_MX", "es_AR",
                              "es_CO", "es_CL"])
    schema.add_field("strategy", type=str, required=True,
                     choices=["mask", "replace", "hash", "redact",
                              "generalize", "pseudonymize", "suppress"])
    schema.add_field("detection.min_confidence", type=float,
                     min_value=0.0, max_value=1.0)

    config = Config(
        defaults={"locale": "es_ES", "strategy": "redact"},
        schema=schema,
    )

    is_valid, errors = config.validate(raise_on_error=False)
    print(f"Valid: {is_valid}, Errors: {errors}")


def example_with_anonymizer() -> None:
    """Use config to initialize TextAnonymizer."""
    from shadetriptxt.text_anonymizer.text_anonymizer import TextAnonymizer, Strategy

    config = load_config(filepath="anonymizer_config.json")

    anon = TextAnonymizer(
        locale=config.get("locale", "es_ES"),
        strategy=config.get("strategy", "redact"),
        seed=config.get("seed", type=int),
    )

    # Apply per-type strategy overrides from config
    type_overrides = {
        k.replace("type_overrides.", ""): v
        for k, v in config.all().items()
        if k.startswith("type_overrides.")
    }
    for pii_type, strategy in type_overrides.items():
        anon.set_strategy(strategy, pii_type=pii_type)

    result = anon.anonymize_text(
        "DNI: 12345678Z, email: juan@test.com, tel: 612345678",
        use_regex=config.get("detection.use_regex", True),
        use_spacy=config.get("detection.use_spacy", False),
        use_nltk=config.get("detection.use_nltk", False),
        min_confidence=config.get("detection.min_confidence", 0.0, type=float),
    )

    print(f"Original:   {result.original}")
    print(f"Anonymized: {result.anonymized}")
    print(f"Entities:   {len(result.entities)}")


if __name__ == "__main__":
    print("=== Basic Config ===")
    example_basic()
    print()

    print("=== File + Env ===")
    example_file_and_env()
    print()

    print("=== Schema Validation ===")
    example_schema_validation()
    print()

    print("=== With TextAnonymizer ===")
    example_with_anonymizer()
