"""
cli.py - Command Line Interface for TextAnonymizer

PII detection & anonymization from the command line: detect, anonymize,
and report on Personally Identifiable Information across 12 locales
using 7 strategies.

Usage:
    python -m shadetriptxt.text_anonymizer.cli --help
    python -m shadetriptxt.text_anonymizer.cli anonymize "DNI: 12345678Z, email: juan@test.com"
    python -m shadetriptxt.text_anonymizer.cli detect "Call 612345678 or email info@test.com"
    python -m shadetriptxt.text_anonymizer.cli anonymize-file input.txt -o output.txt --strategy mask
    python -m shadetriptxt.text_anonymizer.cli anonymize-csv data.csv --columns name,email,phone -o clean.csv
    python -m shadetriptxt.text_anonymizer.cli locales
    python -m shadetriptxt.text_anonymizer.cli @params.txt

Author: DatamanEdge
Version: 0.1.0
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from typing import Any, List, Optional

from shadetriptxt.utils.cli_base import (
    CLIBase,
    CLIResult,
    print_error,
    print_info,
    print_progress,
    print_success,
    print_table,
    print_warning,
    write_output,
)

__all__ = [
    "create_cli",
    "main",
    "run_api",
]

# ============================================================================
# CONSTANTS
# ============================================================================

STRATEGIES = [
    "mask",
    "replace",
    "hash",
    "redact",
    "generalize",
    "pseudonymize",
    "suppress",
]

PII_TYPES = [
    "NAME",
    "EMAIL",
    "PHONE",
    "ADDRESS",
    "ID_DOCUMENT",
    "CREDIT_CARD",
    "IBAN",
    "IP_ADDRESS",
    "DATE",
    "URL",
    "ORGANIZATION",
    "LOCATION",
    "NUMBER",
    "CURRENCY",
    "CUSTOM",
]

SUPPORTED_LOCALES = [
    "es_ES",
    "es_MX",
    "es_AR",
    "es_CO",
    "es_CL",
    "en_US",
    "en_GB",
    "pt_BR",
    "pt_PT",
    "fr_FR",
    "de_DE",
    "it_IT",
]


# ============================================================================
# FACTORY
# ============================================================================


def create_cli() -> CLIBase:
    """Create a configured TextAnonymizer CLI instance."""
    return CLIBase(
        prog="textanonymizer",
        description="PII detection & anonymization across 12 locales",
        version="0.1.0",
    )


# ============================================================================
# HELPERS
# ============================================================================


def _build_anonymizer(args: argparse.Namespace) -> Any:
    """Create a TextAnonymizer from parsed CLI arguments."""
    from .text_anonymizer import TextAnonymizer

    locale = getattr(args, "locale", "es_ES")
    strategy = getattr(args, "strategy", "redact")
    seed = getattr(args, "seed", None)
    return TextAnonymizer(locale=locale, strategy=strategy, seed=seed)


# ============================================================================
# SUBCOMMAND HANDLERS
# ============================================================================


def run_anonymize(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: anonymize text provided as argument or from stdin."""
    anon = _build_anonymizer(args)

    text = getattr(args, "text", None)
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print_error("No text provided. Pass text as argument or pipe from stdin.")
            return

    use_spacy = getattr(args, "use_spacy", False)
    use_nltk = getattr(args, "use_nltk", False)
    min_confidence = getattr(args, "min_confidence", 0.0)
    pii_filter = getattr(args, "pii_types", None)
    pii_types = pii_filter.split(",") if pii_filter else None

    result = anon.anonymize_text(
        text,
        use_regex=True,
        use_spacy=use_spacy,
        use_nltk=use_nltk,
        min_confidence=min_confidence,
        pii_types=pii_types,
    )

    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        output = {
            "original": result.original,
            "anonymized": result.anonymized,
            "entities": [
                {
                    "text": e.text,
                    "pii_type": e.pii_type.value,
                    "start": e.start,
                    "end": e.end,
                    "confidence": e.confidence,
                    "source": e.source,
                }
                for e in result.entities
            ],
            "replacements": result.replacements,
        }
        write_output(output, args)
    else:
        if not getattr(args, "quiet", False):
            print_info(f"Strategy: {anon.strategy.value}")
            print_info(f"Locale:   {anon.locale}")
            print_info(f"Entities: {len(result.entities)}")
            print()
        print(result.anonymized)

        output_file = getattr(args, "output", None)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.anonymized + "\n")
            print_success(f"Output written to {output_file}")

    cli.last_result = {
        "anonymized": result.anonymized,
        "entities_count": len(result.entities),
        "replacements": result.replacements,
    }
    cli.increment_stat("texts_anonymized", 1)
    cli.increment_stat("entities_found", len(result.entities))


def run_detect(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: detect PII in text without anonymizing."""
    anon = _build_anonymizer(args)

    text = getattr(args, "text", None)
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print_error("No text provided. Pass text as argument or pipe from stdin.")
            return

    use_spacy = getattr(args, "use_spacy", False)
    use_nltk = getattr(args, "use_nltk", False)
    min_confidence = getattr(args, "min_confidence", 0.0)
    pii_filter = getattr(args, "pii_types", None)
    pii_types = pii_filter.split(",") if pii_filter else None

    entities = anon.detect_pii(
        text,
        use_regex=True,
        use_spacy=use_spacy,
        use_nltk=use_nltk,
        min_confidence=min_confidence,
        pii_types=pii_types,
    )

    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        output = [
            {
                "text": e.text,
                "pii_type": e.pii_type.value,
                "start": e.start,
                "end": e.end,
                "confidence": e.confidence,
                "source": e.source,
            }
            for e in entities
        ]
        write_output(output, args)
    elif fmt in ("table", "summary"):
        if entities:
            headers = ["PII Type", "Text", "Position", "Confidence", "Source"]
            rows = [
                [
                    e.pii_type.value,
                    e.text,
                    f"{e.start}-{e.end}",
                    f"{e.confidence:.2f}",
                    e.source,
                ]
                for e in entities
            ]
            print_table(headers, rows)
        else:
            print_info("No PII entities detected.")
    else:
        for e in entities:
            print(f"{e.pii_type.value}: {e.text} ({e.confidence:.2f})")

    cli.last_result = [{"text": e.text, "pii_type": e.pii_type.value, "confidence": e.confidence} for e in entities]
    cli.increment_stat("texts_scanned", 1)
    cli.increment_stat("entities_found", len(entities))


def run_anonymize_file(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: anonymize a text file line by line."""
    anon = _build_anonymizer(args)

    input_path = os.path.realpath(args.input)
    output_path = os.path.realpath(getattr(args, "output", None)) if getattr(args, "output", None) else None
    use_spacy = getattr(args, "use_spacy", False)
    use_nltk = getattr(args, "use_nltk", False)
    min_confidence = getattr(args, "min_confidence", 0.0)

    if not os.path.isfile(input_path):
        print_error(f"File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total = len(lines)
    anonymized_lines: List[str] = []
    total_entities = 0

    for i, line in enumerate(lines):
        result = anon.anonymize_text(
            line.rstrip("\n"),
            use_regex=True,
            use_spacy=use_spacy,
            use_nltk=use_nltk,
            min_confidence=min_confidence,
        )
        anonymized_lines.append(result.anonymized)
        total_entities += len(result.entities)

        if not getattr(args, "quiet", False) and total > 1:
            print_progress(i + 1, total, prefix="Anonymizing", suffix="lines")

    cli.increment_stat("lines_processed", total)
    cli.increment_stat("entities_found", total_entities)

    output_text = "\n".join(anonymized_lines) + "\n"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print_success(f"Anonymized {total} lines -> {output_path}")
    else:
        fmt = getattr(args, "output_format", "summary")
        if fmt == "json":
            write_output(
                {"lines": total, "entities": total_entities, "content": anonymized_lines},
                args,
            )
        else:
            print(output_text, end="")

    cli.last_result = {
        "lines": total,
        "entities": total_entities,
        "content": anonymized_lines,
    }


def run_anonymize_csv(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: anonymize specific columns in a CSV file."""
    anon = _build_anonymizer(args)

    input_path = os.path.realpath(args.input)
    output_path = os.path.realpath(getattr(args, "output", None)) if getattr(args, "output", None) else None
    columns_arg = getattr(args, "columns", None)
    delimiter = getattr(args, "delimiter", ",")

    if not os.path.isfile(input_path):
        print_error(f"File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            print_error("Could not read CSV headers.")
            return
        fieldnames = list(reader.fieldnames)
        records = list(reader)

    columns = [c.strip() for c in columns_arg.split(",")] if columns_arg else None
    anonymized_records = anon.anonymize_records(records, fields=columns)

    cli.increment_stat("records_processed", len(records))
    cli.increment_stat("columns_anonymized", len(columns) if columns else len(fieldnames))

    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        write_output(anonymized_records, args)
    elif output_path:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(anonymized_records)
        print_success(f"Anonymized {len(records)} records -> {output_path}")
    else:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(anonymized_records)
        print(buf.getvalue(), end="")

    cli.last_result = anonymized_records


def run_anonymize_dict_cmd(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: anonymize a JSON record from argument or stdin."""
    anon = _build_anonymizer(args)

    json_input = getattr(args, "json_input", None)
    if not json_input:
        if not sys.stdin.isatty():
            json_input = sys.stdin.read().strip()
        else:
            print_error("No JSON provided. Pass as argument or pipe from stdin.")
            return

    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        return

    fields_arg = getattr(args, "fields", None)
    fields = [f.strip() for f in fields_arg.split(",")] if fields_arg else None

    if isinstance(data, list):
        result = anon.anonymize_records(data, fields=fields)
        cli.increment_stat("records_anonymized", len(data))
    elif isinstance(data, dict):
        result = anon.anonymize_dict(data, fields=fields)
        cli.increment_stat("records_anonymized", 1)
    else:
        print_error("JSON must be an object or array of objects.")
        return

    write_output(result, args)
    cli.last_result = result


def run_locales(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: list supported locales."""
    from .text_anonymizer import LOCALE_PROFILES

    rows = [[p.code, p.country, p.language, p.spacy_model, str(len(p.id_patterns))] for p in LOCALE_PROFILES.values()]
    print_table(
        ["Locale", "Country", "Language", "spaCy Model", "ID Patterns"],
        rows,
    )
    print_info(f"Total: {len(LOCALE_PROFILES)} locales supported")


def run_strategies(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: list available anonymization strategies."""
    descriptions = {
        "mask": "Replace characters with * (e.g. J*** D**, ****@****.***)",
        "replace": "Replace with realistic fake data (locale-aware)",
        "hash": "Replace with truncated SHA-256 hash",
        "redact": "Replace with [TYPE] label (e.g. [NAME], [EMAIL])",
        "generalize": "Reduce precision (e.g. age 34 -> 30-40)",
        "pseudonymize": "Consistent replacement (same input -> same output)",
        "suppress": "Remove completely (empty string)",
    }
    rows = [[s, descriptions.get(s, "")] for s in STRATEGIES]
    print_table(["Strategy", "Description"], rows)


def run_pii_types(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: list detectable PII types."""
    rows = [[t] for t in PII_TYPES]
    print_table(["PII Type"], rows)
    print_info(f"Total: {len(PII_TYPES)} types detectable")


# ============================================================================
# SUBCOMMAND SETUP
# ============================================================================


def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on the CLI instance."""
    cli.add_examples(
        [
            '%(prog)s anonymize "DNI: 12345678Z, email: juan@test.com"',
            '%(prog)s anonymize "Call 612345678" --strategy mask --locale es_ES',
            '%(prog)s detect "My SSN is 123-45-6789" --locale en_US',
            '%(prog)s detect "DNI: 12345678Z, tel: 612345678" --output-format json',
            "%(prog)s anonymize-file input.txt -o output.txt --strategy replace",
            "%(prog)s anonymize-csv data.csv --columns name,email,phone -o clean.csv",
            '%(prog)s anonymize-dict \'{"name": "Juan", "email": "j@test.com"}\'',
            "%(prog)s locales",
            "%(prog)s strategies",
            "%(prog)s pii-types",
        ]
    )

    cli.init_subcommands()

    def _add_anonymizer_args(sub: argparse.ArgumentParser) -> None:
        grp = sub.add_argument_group("Anonymizer Options")
        grp.add_argument(
            "--locale",
            "-l",
            default="es_ES",
            choices=SUPPORTED_LOCALES,
            help="Locale (default: es_ES)",
        )
        grp.add_argument(
            "--strategy",
            "-s",
            default="redact",
            choices=STRATEGIES,
            help="Anonymization strategy (default: redact)",
        )
        grp.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")

    def _add_detection_args(sub: argparse.ArgumentParser) -> None:
        grp = sub.add_argument_group("Detection Options")
        grp.add_argument("--use-spacy", action="store_true", help="Enable spaCy NER detection")
        grp.add_argument("--use-nltk", action="store_true", help="Enable NLTK NER detection")
        grp.add_argument("--min-confidence", type=float, default=0.0, help="Minimum confidence 0.0-1.0")
        grp.add_argument("--pii-types", type=str, default=None, help="Comma-separated PII types (e.g. NAME,EMAIL,PHONE)")

    # --- anonymize ---
    p_anon = cli.add_subcommand("anonymize", "Anonymize text (argument or stdin)", handler=run_anonymize, aliases=["anon"])
    p_anon.add_argument("text", nargs="?", default=None, help="Text to anonymize (or pipe from stdin)")
    p_anon.add_argument("--output", "-o", help="Write result to file")
    _add_anonymizer_args(p_anon)
    _add_detection_args(p_anon)

    # --- detect ---
    p_detect = cli.add_subcommand("detect", "Detect PII without anonymizing", handler=run_detect, aliases=["scan"])
    p_detect.add_argument("text", nargs="?", default=None, help="Text to scan (or pipe from stdin)")
    p_detect.add_argument("--output", "-o", help="Write result to file")
    _add_anonymizer_args(p_detect)
    _add_detection_args(p_detect)

    # --- anonymize-file ---
    p_file = cli.add_subcommand("anonymize-file", "Anonymize a text file line by line", handler=run_anonymize_file, aliases=["file"])
    p_file.add_argument("input", help="Input text file path")
    p_file.add_argument("--output", "-o", help="Output file path")
    _add_anonymizer_args(p_file)
    _add_detection_args(p_file)

    # --- anonymize-csv ---
    p_csv = cli.add_subcommand("anonymize-csv", "Anonymize columns in a CSV file", handler=run_anonymize_csv, aliases=["csv"])
    p_csv.add_argument("input", help="Input CSV file path")
    p_csv.add_argument("--output", "-o", help="Output CSV file path")
    p_csv.add_argument("--columns", "-c", help="Comma-separated columns to anonymize")
    p_csv.add_argument("--delimiter", "-d", default=",", help="CSV delimiter (default: ,)")
    _add_anonymizer_args(p_csv)

    # --- anonymize-dict ---
    p_dict = cli.add_subcommand("anonymize-dict", "Anonymize a JSON record", handler=run_anonymize_dict_cmd, aliases=["dict"])
    p_dict.add_argument("json_input", nargs="?", default=None, help="JSON string (or pipe from stdin)")
    p_dict.add_argument("--output", "-o", help="Write result to file")
    p_dict.add_argument("--fields", "-f", help="Comma-separated fields to anonymize")
    _add_anonymizer_args(p_dict)

    # --- info commands ---
    cli.add_subcommand("locales", "List supported locales", handler=run_locales)
    cli.add_subcommand("strategies", "List anonymization strategies", handler=run_strategies)
    cli.add_subcommand("pii-types", "List detectable PII types", handler=run_pii_types, aliases=["types"])


# ============================================================================
# ENTRY POINTS
# ============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the TextAnonymizer CLI.

    Returns:
        Exit code: 0 success, 1 user error, 2 unexpected error, 130 interrupt.
    """
    cli = create_cli()
    _setup_subcommands(cli)

    try:
        args = cli.parse_args(argv)
        cli.run()

        if cli._stats and not getattr(args, "quiet", False):
            cli.print_final_summary()
        if not getattr(args, "quiet", False):
            print_info(f"Elapsed time: {cli.get_elapsed_time()}")

        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    except KeyboardInterrupt:
        print_warning("\nInterrupted")
        return 130
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        return 2


def run_api(argv: List[str]) -> CLIResult:
    """Programmatic entry point -- returns structured result instead of printing.

    Args:
        argv: Command-line arguments (e.g. `["anonymize", "text with PII"]`).

    Returns:
        CLIResult with exit_code, data, stats, and optional error.
    """
    cli = create_cli()
    _setup_subcommands(cli)

    try:
        cli.parse_args(argv)
        cli.args.output_format = "json"
        cli.args.quiet = True
        cli.run()
        return CLIResult(exit_code=0, data=cli.last_result, stats=dict(cli._stats))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return CLIResult(exit_code=code, error=f"SystemExit({exc.code})")
    except Exception as exc:
        return CLIResult(exit_code=2, error=str(exc))


if __name__ == "__main__":
    sys.exit(main())
