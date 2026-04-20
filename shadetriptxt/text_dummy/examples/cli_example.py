"""
Example usage of the TextDummy CLI module.

Demonstrates:
    - Programmatic API with run_api() and CLIResult
    - Output utilities (colors, tables, progress bars, summaries)
    - CI mode invocation with exit codes
    - Interactive CLI entry point

Run: python -m shadetriptxt.text_dummy.cli_example
"""

from shadetriptxt.text_dummy.cli import (
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

    # Generate names
    result: CLIResult = run_api(["generate", "name", "--count", "5", "--locale", "es_ES"])
    print(f"  OK: {result.ok}")
    print(f"  Stats: {result.stats}")
    if result.ok:
        for name in result.data:
            print(f"    - {name}")
    print()

    # Generate emails
    result = run_api(["generate", "email", "--count", "3", "--locale", "en_US"])
    if result.ok:
        print_success(f"Emails: {result.data}")
    print()

    # Generate a profile
    result = run_api(["profile", "--count", "1", "--locale", "pt_BR"])
    if result.ok:
        for key, value in result.data[0].items():
            print(f"    {key}: {value}")
    print()

    # Generate ID documents
    result = run_api(["id-doc", "--locale", "es_ES", "--count", "3"])
    if result.ok:
        print_success(f"IDs: {result.data}")
    print()

    # Generate unique keys
    result = run_api(["key", "--key-type", "hex", "--length", "12",
                      "--separator", "-", "--segment-length", "4", "--count", "3"])
    if result.ok:
        for key in result.data:
            print(f"    {key}")
    print()


def demo_batch_api() -> None:
    """Use run_api() for multi-column batch generation."""
    print_header("2. Batch Generation via API")

    # Generate a dataset with multiple columns
    result = run_api(["batch", "name,email,phone,city",
                      "--count", "5", "--locale", "es_ES"])
    if result.ok:
        # result.data is a list of dicts
        if result.data:
            headers = list(result.data[0].keys())
            rows = [[str(record.get(h, "")) for h in headers] for record in result.data]
            print_table(headers, rows)
    print()

    # Generate numbers
    result = run_api(["number", "--number-type", "float",
                      "--min-val", "0", "--max-val", "1000",
                      "--decimals", "2", "--count", "5"])
    if result.ok:
        print_success(f"Numbers: {result.data}")
    print()

    # Generate dates
    result = run_api(["date", "--start", "2020-01-01", "--end", "2025-12-31",
                      "--count", "5"])
    if result.ok:
        print_success(f"Dates: {result.data}")
    print()


def demo_output_utilities() -> None:
    """Showcase output utilities: colors, tables, progress, summaries."""
    print_header("3. Output Utilities")

    # Colored messages
    print_success("Data generation completed")
    print_error("Invalid data type specified")
    print_warning("Large batch may take time")
    print_info("Using locale: es_ES")
    print()

    # Progress bar
    print_info("Generating records...")
    for i in range(101):
        print_progress(i, 100, prefix="Generating", suffix="Done")
    print()

    # Table output
    headers = ["Type", "Count", "Locale"]
    rows = [
        ["name", "100", "es_ES"],
        ["email", "100", "en_US"],
        ["phone", "50", "pt_BR"],
        ["id_document", "200", "de_DE"],
    ]
    print_table(headers, rows)
    print()

    # Summary statistics
    stats = {
        "names_generated": 100,
        "emails_generated": 100,
        "phones_generated": 50,
        "ids_generated": 200,
        "total_records": 450,
    }
    print_summary(stats, title="GENERATION SUMMARY")


def demo_ci_mode() -> None:
    """CI mode invocation — returns exit code."""
    print_header("4. CI Mode")

    # --ci forces JSON output, disables colors, returns exit codes
    exit_code = main(["generate", "email", "--count", "3", "--ci"])
    print(f"  Exit code: {exit_code}")
    print("  (0=success, 1=user error, 2=unexpected error)")
    print()


def demo_error_handling() -> None:
    """Error handling with CLIResult."""
    print_header("5. Error Handling")

    # Invalid data type — should return error
    result = run_api(["generate", "invalid_type_xyz", "--count", "1"])
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
