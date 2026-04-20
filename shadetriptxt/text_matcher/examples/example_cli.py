"""
Example: CLI Programmatic API
===============================
Use the TextMatcher CLI module from Python code — no subprocess needed.

Features:
    - run_api()           — call any CLI command programmatically
    - CLIResult           — structured result (ok, data, stats, error)
    - Output utilities    — colored messages, tables, progress bars
    - CI mode             — JSON output, exit codes

Run: python -m shadetriptxt.text_matcher.examples.example_cli
"""

from shadetriptxt.text_matcher.cli import (
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
)


def example_compare() -> None:
    """Single-name and full-name comparison via the API."""
    print_header("1. Comparison Commands")

    # Single-word comparison
    result: CLIResult = run_api(["compare", "José", "Jose", "--locale", "es_ES"])
    if result.ok and result.data:
        metrics = result.data.get("metrics", {})
        print_success(
            f"compare: match={result.data.get('match')}  "
            f"Lev={metrics.get('levenshtein_ratio', 0):.4f}"
        )

    # Full-name comparison
    result = run_api(["compare-names", "Juan Fco García", "Juan Francisco Garcia"])
    if result.ok and result.data:
        print_success(f"compare-names: match={result.data.get('match')}")

    # Phrase comparison
    result = run_api(["compare-text", "premium leather wallet", "leather wallet premium"])
    if result.ok and result.data:
        metrics = result.data.get("metrics", {})
        print_success(
            f"compare-text: match={result.data.get('match')}  "
            f"sim={metrics.get('similarity', 0):.4f}"
        )
    print()


def example_search() -> None:
    """Best-match and ranked-match search."""
    print_header("2. Search Commands")

    # Best match
    result = run_api(["find-match", "Smithe",
                      "--candidates", "Smith,Smyth,Jones,Smithson"])
    if result.ok and result.data:
        print_success(
            f"find-match: '{result.data.get('best_match')}' "
            f"(score: {result.data.get('score', 0):.4f})"
        )

    # Ranked matches
    result = run_api(["find-matches", "García",
                      "--candidates", "Garcia,Garzia,Gracia,González,Garcés",
                      "--top-k", "3", "--threshold", "0.6"])
    if result.ok and result.data:
        headers = ["#", "Candidate", "Score"]
        rows = [[i + 1, m["candidate"], f"{m['score']:.4f}"]
                for i, m in enumerate(result.data)]
        print_table(headers, rows)
    print()


def example_utilities() -> None:
    """Showcase output utilities: tables, progress, summaries."""
    print_header("3. Output Utilities")

    print_success("Match found")
    print_error("No candidates provided")
    print_warning("Threshold too low — may produce false positives")
    print_info("Using preset: default")
    print()

    # Progress bar
    print_info("Analyzing duplicates...")
    for i in range(101):
        print_progress(i, 100, prefix="Comparing", suffix="Done")
    print()

    # Summary
    stats = {
        "pairs_compared": 1500,
        "matches": 340,
        "non_matches": 1160,
        "duplicates_found": 85,
    }
    print_summary(stats, title="MATCHING RESULTS")


def example_ci_mode() -> None:
    """CI mode: JSON output, no colours, exit codes."""
    print_header("4. CI Mode")

    exit_code = main(["compare", "Juan", "Joan", "--ci"])
    print(f"  Exit code: {exit_code}  (0=success, 1=user error, 2=unexpected)")
    print()


def example_error_handling() -> None:
    """Error handling with CLIResult."""
    print_header("5. Error Handling")

    result = run_api(["find-match", "test"])
    print(f"  OK: {result.ok}")
    print(f"  Exit code: {result.exit_code}")
    if result.error:
        print(f"  Error: {result.error}")
    print()


if __name__ == "__main__":
    example_compare()
    example_search()
    example_utilities()
    example_ci_mode()
    example_error_handling()

    print_info("All CLI examples completed.")
