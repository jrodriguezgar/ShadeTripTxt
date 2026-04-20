"""
Example usage of the TextAnonymizer CLI module.

Demonstrates:
    - Programmatic API with run_api() and CLIResult
    - PII detection and anonymization
    - Output utilities (colors, tables, progress bars, summaries)
    - CI mode invocation with exit codes
    - Error handling patterns

Run: python -m shadetriptxt.text_anonymizer.examples.cli_example
"""

from shadetriptxt.text_anonymizer.cli import (
    CLIResult,
    run_api,
    main,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_header,
    print_table,
    print_summary,
    print_progress,
    Colors,
)


def demo_anonymize_text() -> None:
    """Anonymize text using run_api() — no subprocess needed."""
    print_header("1. Anonymize Text (run_api)")

    # Anonymize with default strategy (redact)
    result: CLIResult = run_api([
        "anonymize", "DNI: 12345678Z, email: juan@test.com, tel: 612345678",
        "--locale", "es_ES",
    ])
    print(f"  OK: {result.ok}")
    print(f"  Stats: {result.stats}")
    if result.ok and result.data:
        print(f"  Anonymized: {result.data.get('anonymized', '')}")
        print(f"  Entities: {result.data.get('entities_count', 0)}")
    print()

    # Anonymize with mask strategy
    result = run_api([
        "anonymize", "Email: user@example.com, phone: +34 612 345 678",
        "--strategy", "mask", "--locale", "es_ES",
    ])
    if result.ok and result.data:
        print_success(f"Masked: {result.data.get('anonymized', '')}")
    print()

    # Anonymize with pseudonymize strategy (reproducible with seed)
    result = run_api([
        "anonymize", "Juan García called María López",
        "--strategy", "pseudonymize", "--seed", "42", "--locale", "es_ES",
    ])
    if result.ok and result.data:
        print_success(f"Pseudonymized: {result.data.get('anonymized', '')}")
    print()


def demo_detect_pii() -> None:
    """Detect PII entities without anonymizing."""
    print_header("2. Detect PII (run_api)")

    result = run_api([
        "detect", "My SSN is 123-45-6789, email bob@example.com, call 555-1234",
        "--locale", "en_US",
    ])
    if result.ok and result.data:
        print_info(f"Found {len(result.data)} entities:")
        for entity in result.data:
            print(f"    {entity['pii_type']}: {entity['text']} (conf={entity['confidence']:.2f})")
    print()

    # Spanish PII detection
    result = run_api([
        "detect", "DNI: 12345678Z, IBAN: ES91 2100 0418 4502 0005 1332",
        "--locale", "es_ES",
    ])
    if result.ok and result.data:
        print_info(f"Found {len(result.data)} entities:")
        for entity in result.data:
            print(f"    {entity['pii_type']}: {entity['text']}")
    print()


def demo_anonymize_dict() -> None:
    """Anonymize a JSON record via CLI."""
    print_header("3. Anonymize JSON Record (run_api)")

    import json
    record = json.dumps({"name": "Juan García", "email": "juan@test.com", "age": 34})

    result = run_api([
        "anonymize-dict", record,
        "--locale", "es_ES", "--strategy", "redact",
    ])
    if result.ok and result.data:
        print_success(f"Anonymized record: {result.data}")
    print()


def demo_list_commands() -> None:
    """List available locales, strategies, and PII types."""
    print_header("4. Reference Commands")

    # List strategies
    print_info("Calling: strategies")
    main(["strategies"])
    print()

    # List PII types
    print_info("Calling: pii-types")
    main(["pii-types"])
    print()


def demo_output_utilities() -> None:
    """Showcase output utilities: colors, tables, progress, summaries."""
    print_header("5. Output Utilities")

    # Colored messages
    print_success("Anonymization completed")
    print_error("No PII detected in input")
    print_warning("spaCy model not installed — using regex only")
    print_info("Using locale: es_ES, strategy: mask")
    print()

    # Progress bar
    print_info("Anonymizing lines...")
    for i in range(101):
        print_progress(i, 100, prefix="Processing", suffix="Done")
    print()

    # Table output
    headers = ["PII Type", "Count", "Strategy"]
    rows = [
        ["NAME", "42", "pseudonymize"],
        ["EMAIL", "38", "mask"],
        ["PHONE", "15", "redact"],
        ["ID_DOCUMENT", "7", "hash"],
    ]
    print_table(headers, rows)
    print()

    # Summary statistics
    stats = {
        "texts_scanned": 500,
        "entities_found": 102,
        "names_detected": 42,
        "emails_detected": 38,
        "phones_detected": 15,
        "ids_detected": 7,
    }
    print_summary(stats, title="ANONYMIZATION SUMMARY")


def demo_ci_mode() -> None:
    """CI mode invocation — returns exit code."""
    print_header("6. CI Mode")

    # --ci forces JSON output, disables colors, returns exit codes
    exit_code = main([
        "detect", "email: test@example.com", "--ci", "--locale", "en_US",
    ])
    print(f"  Exit code: {exit_code}")
    print("  (0=success, 1=user error, 2=unexpected error)")
    print()


def demo_error_handling() -> None:
    """Error handling with CLIResult."""
    print_header("7. Error Handling")

    # Missing text — should produce error
    result = run_api(["anonymize"])
    print(f"  OK: {result.ok}")
    print(f"  Exit code: {result.exit_code}")
    if result.error:
        print(f"  Error: {result.error}")
    print()


if __name__ == "__main__":
    demo_anonymize_text()
    demo_detect_pii()
    demo_anonymize_dict()
    demo_list_commands()
    demo_output_utilities()
    demo_ci_mode()
    demo_error_handling()

    print_info("All CLI examples completed.")
