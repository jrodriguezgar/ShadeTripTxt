"""
Example usage of the TextParser CLI module.

Demonstrates:
    - Programmatic API with run_api() and CLIResult
    - Output utilities (colors, tables, progress bars, summaries)
    - CI mode invocation with exit codes
    - Interactive CLI entry point

Run: python -m shadetriptxt.text_parser.cli_example
"""

from shadetriptxt.text_parser.cli import (
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


def demo_programmatic_api() -> None:
    """Use run_api() for programmatic access — no subprocess needed."""
    print_header("1. Programmatic API (run_api)")

    # Normalize text
    result: CLIResult = run_api(["normalize", "  José  García-López  "])
    print(f"  OK: {result.ok}")
    print(f"  Data: {result.data}")
    print(f"  Stats: {result.stats}")
    print()

    # Extract emails
    result = run_api(["extract", "Contacto: juan@test.com y maria@empresa.es", "--type", "emails"])
    if result.ok:
        print_success(f"Emails found: {result.data}")
    else:
        print_error(f"Error: {result.error}")
    print()

    # Validate ID document
    result = run_api(["validate-id", "12345678Z", "--locale", "es_ES"])
    if result.ok:
        print_success(f"Valid ID: {result.data}")
    print()

    # Fix encoding (mojibake)
    result = run_api(["fix-encoding", "Ã¡rbol"])
    if result.ok:
        print_success(f"Fixed: {result.data}")
    print()

    # Phonetic reduction
    result = run_api(["phonetic", "García", "--locale", "es_ES", "--strength", "2"])
    if result.ok:
        print_success(f"Phonetic: {result.data}")
    print()

    # Parse a person name
    result = run_api(["parse-name", "García López, José", "--locale", "es_ES"])
    if result.ok:
        print_success(f"Parsed name: {result.data}")
    print()

    # Parse a company name
    result = run_api(["parse-company", "ATRESMEDIA CORPORACION S.A.", "--locale", "es_ES"])
    if result.ok:
        print_success(f"Parsed company: {result.data}")
    print()


def demo_batch_api() -> None:
    """Use run_api() in a loop for batch processing."""
    print_header("2. Batch Processing via API")

    texts = [
        "  josé  garcía  ",
        "MARÍA FERNÁNDEZ-LÓPEZ",
        "  aNtOnIo   DE LA  cruz  ",
    ]

    results = []
    for text in texts:
        r = run_api(["normalize", text])
        if r.ok:
            results.append((text.strip(), r.data))
            print_success(f"'{text.strip()}' → '{r.data}'")
        else:
            print_error(f"Failed: {r.error}")

    print_info(f"Processed {len(results)} texts")
    print()


def demo_output_utilities() -> None:
    """Showcase output utilities: colors, tables, progress, summaries."""
    print_header("3. Output Utilities")

    # Colored messages
    print_success("Operation completed successfully")
    print_error("An error occurred")
    print_warning("This is a warning message")
    print_info("Informational message")
    print()

    # Progress bar
    print_info("Processing items...")
    for i in range(101):
        print_progress(i, 100, prefix="Progress", suffix="Complete")
    print()

    # Table output
    headers = ["Operation", "Input", "Result"]
    rows = [
        ["normalize", "José García-López", "jose garcia lopez"],
        ["phonetic", "García", "GARSIA"],
        ["mask", "12345678Z", "1*******Z"],
    ]
    print_table(headers, rows)
    print()

    # Summary statistics
    stats = {
        "total_processed": 253,
        "normalized": 200,
        "extracted": 40,
        "validated": 13,
    }
    print_summary(stats, title="EXECUTION SUMMARY")


def demo_ci_mode() -> None:
    """CI mode invocation — returns exit code."""
    print_header("4. CI Mode")

    # --ci forces JSON output, disables colors, returns exit codes
    exit_code = main(["normalize", "José García", "--ci"])
    print(f"  Exit code: {exit_code}")
    print("  (0=success, 1=user error, 2=unexpected error)")
    print()


def demo_error_handling() -> None:
    """Error handling with CLIResult."""
    print_header("5. Error Handling")

    # Missing input — should return error
    result = run_api(["extract", "--type", "emails"])
    print(f"  OK: {result.ok}")
    print(f"  Exit code: {result.exit_code}")
    if result.error:
        print(f"  Error: {result.error}")
    print()


if __name__ == "__main__":
    demo_programmatic_api()
    demo_batch_api()
    demo_output_utilities()
    demo_ci_mode()
    demo_error_handling()

    print_info("All CLI examples completed.")
