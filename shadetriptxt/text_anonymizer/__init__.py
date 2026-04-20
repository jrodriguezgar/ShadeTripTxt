"""
Text Anonymizer — PII detection & data anonymization.

Detect and anonymize Personally Identifiable Information (PII) in text
and tabular data. Supports 12 locales with locale-specific patterns.

Quick start::

    from shadetriptxt.text_anonymizer import anonymize_text, detect_pii

    result = anonymize_text("Llama a Juan García al 612345678")
    print(result.anonymized)

    entities = detect_pii("DNI: 12345678Z, email: juan@test.com")
    for e in entities:
        print(f"{e.pii_type.value}: {e.text}")
"""

from .text_anonymizer import (
    # Classes
    TextAnonymizer,
    # Enums
    PiiType,
    Strategy,
    # Dataclasses
    DetectedEntity,
    AnonymizationResult,
    PrivacyReport,
    AnonymizerLocaleProfile,
    # Convenience functions
    get_anonymizer,
    anonymize_text,
    detect_pii,
    anonymize_dict,
    anonymize_dataframe,
    measure_privacy,
    # Constants
    LOCALE_PROFILES,
    SUPPORTED_LOCALES,
)

from .config import (
    Config,
    ConfigSchema,
    ConfigValue,
    ConfigSource,
    ConfigFormat,
    load_config,
    create_sample_config,
)

from shadetriptxt.utils.cli_base import (
    CLIBase,
    CLIConfig,
    CLIResult,
    OutputFormat,
    Subcommand,
    confirm_action,
    print_error,
    print_info,
    print_progress,
    print_success,
    print_summary,
    print_table,
    print_warning,
)
from .cli import (
    create_cli,
    run_api,
    main,
)

__all__ = [
    "TextAnonymizer",
    "PiiType",
    "Strategy",
    "DetectedEntity",
    "AnonymizationResult",
    "PrivacyReport",
    "AnonymizerLocaleProfile",
    "get_anonymizer",
    "anonymize_text",
    "detect_pii",
    "anonymize_dict",
    "anonymize_dataframe",
    "measure_privacy",
    "LOCALE_PROFILES",
    "SUPPORTED_LOCALES",
    # Config
    "Config",
    "ConfigSchema",
    "ConfigValue",
    "ConfigSource",
    "ConfigFormat",
    "load_config",
    "create_sample_config",
    # CLI
    "CLIBase",
    "CLIConfig",
    "CLIResult",
    "Subcommand",
    "OutputFormat",
    "create_cli",
    "run_api",
    "main",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_table",
    "print_summary",
    "print_progress",
    "confirm_action",
]
