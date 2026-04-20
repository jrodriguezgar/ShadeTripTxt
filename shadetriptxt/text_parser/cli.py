"""
cli.py - Command Line Interface for TextParser

Locale-aware text parsing, extraction, normalization, encoding repair,
phonetic reduction, and batch processing from the command line.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Callable, Dict, List, Optional

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
# FACTORY
# ============================================================================


def create_cli() -> CLIBase:
    """Create a configured TextParser CLI instance."""
    return CLIBase(
        prog="textparser",
        description="Locale-aware text parsing, extraction, and normalization",
        version="0.1.0",
    )


# ============================================================================
# SUBCOMMAND HANDLERS
# ============================================================================


def _read_input(args: argparse.Namespace) -> str:
    """Read input text from argument or stdin."""
    text = getattr(args, "text", None)
    if text:
        return text
    input_file = getattr(args, "input", None)
    if input_file:
        input_file = os.path.realpath(input_file)
        with open(input_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    print_error("No input provided. Use positional argument, --input, or pipe via stdin.")
    sys.exit(1)


def run_normalize(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: normalize text."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.normalize(
        text,
        lowercase=not args.keep_case,
        remove_punctuation=not args.keep_punctuation,
        remove_accents=not args.keep_accents,
        remove_parentheses_content=args.remove_parentheses,
    )
    write_output(result, args)
    cli.last_result = result
    cli.increment_stat("normalized", 1)


def run_extract(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: extract content from text."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)

    extractors: Dict[str, Callable] = {
        "phones": parser.extract_phones,
        "emails": parser.extract_emails,
        "urls": parser.extract_urls,
        "dates": parser.extract_dates,
        "ids": parser.extract_ids,
        "ibans": parser.extract_ibans,
        "credit_cards": parser.extract_credit_cards,
        "currency": parser.extract_currency,
        "hashtags": parser.extract_hashtags,
        "mentions": parser.extract_mentions,
        "ips": parser.extract_ip_addresses,
        "numeric": parser.extract_numeric,
        "percentages": parser.extract_percentages,
        "postal_codes": parser.extract_postal_codes,
    }

    extract_type = args.type
    if extract_type == "all":
        results: Dict[str, Any] = {}
        for name, func in extractors.items():
            found = func(text)
            if found:
                results[name] = found
        write_output(results, args)
        cli.last_result = results
        cli.increment_stat("extractions", len(results))
    else:
        func = extractors.get(extract_type)
        if not func:
            print_error(f"Unknown extraction type: {extract_type}. Valid: {', '.join(sorted(extractors.keys()))}")
            return
        result = func(text)
        write_output(result, args)
        cli.last_result = result
        cli.increment_stat("extractions", 1)


def run_validate_id(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: validate an ID document."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    doc_type = getattr(args, "doc_type", None)
    result = parser.validate_id(text.strip(), doc_type=doc_type)

    if result:
        print_success(f"Valid: {result}")
        cli.last_result = {"valid": True, "result": result}
        cli.increment_stat("valid", 1)
    else:
        print_error(f"Invalid ID: {text.strip()}")
        cli.last_result = {"valid": False, "input": text.strip()}
        cli.increment_stat("invalid", 1)


def run_fix_encoding(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: fix mojibake / encoding issues."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)

    if args.detect:
        result = parser.detect_encoding(text)
        write_output(result, args)
        cli.last_result = result
    else:
        result = parser.fix_mojibake(text, normalize_quotes=args.normalize_quotes)
        write_output(result, args)
        cli.last_result = result
        cli.increment_stat("fixed", 1)


def run_phonetic(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: phonetic reduction."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.reduce_phonetic(text, strength=args.strength)
    write_output(result, args)
    cli.last_result = result
    cli.increment_stat("reduced", 1)


def run_prepare(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: prepare text for comparison."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.prepare_for_comparison(text, aggressive=args.aggressive)
    write_output(result, args)
    cli.last_result = result
    cli.increment_stat("prepared", 1)


def run_mask(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: mask sensitive text."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.mask(
        text,
        keep_first=args.keep_first,
        keep_last=args.keep_last,
        mask_char=args.mask_char,
    )
    write_output(result, args)
    cli.last_result = result
    cli.increment_stat("masked", 1)


def run_parse_name(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: parse / rearrange a name."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.parse_name(text)
    write_output(result, args)
    cli.last_result = result
    cli.increment_stat("parsed", 1)


def run_parse_company(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: parse a company name."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.parse_company(text)
    if result:
        output = {"name": result[0], "legal_form": result[1]}
        write_output(output, args)
        cli.last_result = output
    else:
        write_output(None, args)
        cli.last_result = None
    cli.increment_stat("parsed", 1)


def run_locale_info(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: show locale information."""
    from .text_parser import TextParser

    if args.list_all:
        locales = TextParser.supported_locales()
        rows = [[code, country] for code, country in sorted(locales.items())]
        print_table(["Locale", "Country"], rows)
    else:
        parser = TextParser(locale=args.locale)
        info = parser.locale_info()
        write_output(info, args)


def run_batch(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: process a file line by line."""
    from .text_parser import TextParser

    parser = TextParser(locale=args.locale)

    input_path = os.path.realpath(args.input)
    with open(input_path, "r", encoding=args.encoding) as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)
    results: List[str] = []

    for i, line in enumerate(lines):
        if args.operation == "normalize":
            result = parser.normalize(line)
        elif args.operation == "fix-encoding":
            result = parser.fix_mojibake(line)
        elif args.operation == "phonetic":
            result = parser.reduce_phonetic(line, strength=args.strength)
        elif args.operation == "prepare":
            result = parser.prepare_for_comparison(line, aggressive=args.aggressive)
        elif args.operation == "remove-articles":
            result = parser.remove_articles(line)
        else:
            result = parser.normalize(line)

        results.append(str(result) if result is not None else "")
        if not getattr(args, "quiet", False):
            print_progress(i + 1, total, prefix="Processing")

    cli.increment_stat("processed", total)

    if args.output:
        output_path = os.path.realpath(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(results) + "\n")
        print_success(f"Wrote {total} lines to {output_path}")
    else:
        for r in results:
            print(r)


# ============================================================================
# MAIN
# ============================================================================


def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on the CLI instance."""
    cli.add_examples(
        [
            '%(prog)s normalize "  José García-López  " --locale es_ES',
            '%(prog)s extract "+34 600 123 456 email@test.com" --type all',
            '%(prog)s validate-id "12345678Z" --locale es_ES',
            '%(prog)s fix-encoding "Ã¡rbol" --locale es_ES',
            '%(prog)s phonetic "García" --locale es_ES --strength 2',
            "%(prog)s batch --input data.txt --operation normalize --output clean.txt",
        ]
    )

    cli.init_subcommands()

    # --- normalize ---
    p_norm = cli.add_subcommand("normalize", "Normalize text", handler=run_normalize, aliases=["norm"])
    p_norm.add_argument("text", nargs="?", help="Text to normalize")
    p_norm.add_argument("--input", "-i", help="Read text from file")
    p_norm.add_argument("--output", "-o", help="Write result to file")
    p_norm.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_norm.add_argument("--keep-case", action="store_true", help="Preserve original case")
    p_norm.add_argument("--keep-punctuation", action="store_true", help="Preserve punctuation")
    p_norm.add_argument("--keep-accents", action="store_true", help="Preserve accents")
    p_norm.add_argument("--remove-parentheses", action="store_true", help="Remove parenthesized content")

    # --- extract ---
    p_extract = cli.add_subcommand("extract", "Extract content from text", handler=run_extract, aliases=["ex"])
    p_extract.add_argument("text", nargs="?", help="Text to extract from")
    p_extract.add_argument("--input", "-i", help="Read text from file")
    p_extract.add_argument("--output", "-o", help="Write result to file")
    p_extract.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_extract.add_argument(
        "--type",
        "-t",
        default="all",
        choices=[
            "all",
            "phones",
            "emails",
            "urls",
            "dates",
            "ids",
            "ibans",
            "credit_cards",
            "currency",
            "hashtags",
            "mentions",
            "ips",
            "numeric",
            "percentages",
            "postal_codes",
        ],
        help="Type of content to extract (default: all)",
    )

    # --- validate-id ---
    p_valid = cli.add_subcommand(
        "validate-id",
        "Validate an ID document",
        handler=run_validate_id,
        aliases=["vid"],
    )
    p_valid.add_argument("text", nargs="?", help="ID string to validate")
    p_valid.add_argument("--input", "-i", help="Read ID from file")
    p_valid.add_argument("--output", "-o", help="Write result to file")
    p_valid.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_valid.add_argument("--doc-type", "-d", help="Document type (e.g. DNI, NIE, CIF)")

    # --- fix-encoding ---
    p_enc = cli.add_subcommand(
        "fix-encoding",
        "Fix mojibake / encoding issues",
        handler=run_fix_encoding,
        aliases=["fix"],
    )
    p_enc.add_argument("text", nargs="?", help="Text with encoding issues")
    p_enc.add_argument("--input", "-i", help="Read text from file")
    p_enc.add_argument("--output", "-o", help="Write result to file")
    p_enc.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_enc.add_argument("--detect", action="store_true", help="Detect encoding issues instead of fixing")
    p_enc.add_argument(
        "--normalize-quotes",
        action="store_true",
        help="Convert typographic quotes to ASCII",
    )

    # --- phonetic ---
    p_phon = cli.add_subcommand("phonetic", "Phonetic reduction", handler=run_phonetic, aliases=["phon"])
    p_phon.add_argument("text", nargs="?", help="Text for phonetic reduction")
    p_phon.add_argument("--input", "-i", help="Read text from file")
    p_phon.add_argument("--output", "-o", help="Write result to file")
    p_phon.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_phon.add_argument(
        "--strength",
        "-s",
        type=int,
        default=1,
        choices=[0, 1, 2, 3],
        help="Reduction strength 0-3 (default: 1)",
    )

    # --- prepare ---
    p_prep = cli.add_subcommand("prepare", "Prepare text for comparison", handler=run_prepare, aliases=["prep"])
    p_prep.add_argument("text", nargs="?", help="Text to prepare")
    p_prep.add_argument("--input", "-i", help="Read text from file")
    p_prep.add_argument("--output", "-o", help="Write result to file")
    p_prep.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_prep.add_argument("--aggressive", "-a", action="store_true", help="Apply phonetic reduction")

    # --- mask ---
    p_mask = cli.add_subcommand("mask", "Mask sensitive text", handler=run_mask)
    p_mask.add_argument("text", nargs="?", help="Text to mask")
    p_mask.add_argument("--input", "-i", help="Read text from file")
    p_mask.add_argument("--output", "-o", help="Write result to file")
    p_mask.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_mask.add_argument(
        "--keep-first",
        type=int,
        default=1,
        help="Characters to keep at start (default: 1)",
    )
    p_mask.add_argument(
        "--keep-last",
        type=int,
        default=1,
        help="Characters to keep at end (default: 1)",
    )
    p_mask.add_argument("--mask-char", default="*", help="Masking character (default: *)")

    # --- parse-name ---
    p_pname = cli.add_subcommand(
        "parse-name",
        "Parse / rearrange a person name",
        handler=run_parse_name,
        aliases=["pn"],
    )
    p_pname.add_argument("text", nargs="?", help="Name to parse (e.g. 'García López, José')")
    p_pname.add_argument("--input", "-i", help="Read name from file")
    p_pname.add_argument("--output", "-o", help="Write result to file")
    p_pname.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")

    # --- parse-company ---
    p_pcomp = cli.add_subcommand(
        "parse-company",
        "Parse a company name",
        handler=run_parse_company,
        aliases=["pc"],
    )
    p_pcomp.add_argument("text", nargs="?", help="Company name to parse")
    p_pcomp.add_argument("--input", "-i", help="Read company name from file")
    p_pcomp.add_argument("--output", "-o", help="Write result to file")
    p_pcomp.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")

    # --- locale ---
    p_locale = cli.add_subcommand("locale", "Show locale information", handler=run_locale_info)
    p_locale.add_argument("--locale", "-l", default="es_ES", help="Locale to inspect")
    p_locale.add_argument("--list-all", action="store_true", help="List all supported locales")

    # --- batch ---
    p_batch = cli.add_subcommand("batch", "Process a file line by line", handler=run_batch)
    p_batch.add_argument("--input", "-i", required=True, help="Input file (one text per line)")
    p_batch.add_argument("--output", "-o", help="Output file")
    p_batch.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_batch.add_argument("--encoding", default="utf-8", help="Input file encoding (default: utf-8)")
    p_batch.add_argument(
        "--operation",
        default="normalize",
        choices=["normalize", "fix-encoding", "phonetic", "prepare", "remove-articles"],
        help="Operation to apply (default: normalize)",
    )
    p_batch.add_argument(
        "--strength",
        "-s",
        type=int,
        default=1,
        help="Phonetic strength (for phonetic operation)",
    )
    p_batch.add_argument(
        "--aggressive",
        "-a",
        action="store_true",
        help="Aggressive mode (for prepare operation)",
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the TextParser CLI.

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
    """Programmatic entry point — returns structured result instead of printing.

    Args:
        argv: Command-line arguments (e.g. ``["normalize", "José García"]``).

    Returns:
        CLIResult with exit_code, data, stats, and optional error.

    Example Usage::

        from shadetriptxt.text_parser.cli import run_api
        result = run_api(["normalize", "  José García-López  "])
        if result.ok:
            print(result.data)
    """
    cli = create_cli()
    _setup_subcommands(cli)

    try:
        cli.parse_args(argv)
        cli.args.output_format = "json"
        cli.args.quiet = True
        cli.args.no_color = True
        cli.run()
        return CLIResult(
            exit_code=0,
            data=cli.last_result,
            stats=dict(cli._stats),
        )
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return CLIResult(exit_code=code, error=f"SystemExit({exc.code})")
    except Exception as exc:
        return CLIResult(exit_code=2, error=str(exc))


if __name__ == "__main__":
    sys.exit(main())
