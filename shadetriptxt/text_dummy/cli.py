"""
cli.py - Command Line Interface for TextDummy

Fake data generation from the command line: names, emails, phones,
ID documents, products, financial data, and more across 12 locales.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from typing import Any, Dict, List, Optional

from shadetriptxt.utils.cli_base import (
    CLIBase,
    CLIResult,
    print_error,
    print_info,
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
    """Create a configured TextDummy CLI instance."""
    return CLIBase(
        prog="textdummy",
        description="Fake data generation across 12 locales",
        version="0.1.0",
    )


# ============================================================================

AVAILABLE_TYPES = [
    "name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "address",
    "city",
    "state",
    "postcode",
    "country",
    "company",
    "job",
    "department",
    "sentence",
    "word",
    "dni",
    "id_document",
    "price",
    "iban",
    "bban",
    "swift",
    "credit_card_number",
    "credit_card_expire",
    "credit_card_provider",
    "credit_card_full",
    "cryptocurrency_code",
    "cryptocurrency_name",
    "payment_method",
    "invoice_number",
    "url",
    "domain_name",
    "username",
    "userlogin",
    "password",
    "ipv4",
    "ipv6",
    "mac_address",
    "user_agent",
    "slug",
    "uuid4",
    "file_name",
    "file_extension",
    "mime_type",
    "file_path",
    "date",
    "random_date",
    "random_number",
    "license_plate",
    "latitude",
    "longitude",
    "coordinate",
    "color_name",
    "hex_color",
    "rgb_color",
    "isbn10",
    "isbn13",
    "ean13",
    "ean8",
    "product_name",
    "product_category",
    "product_material",
    "product_sku",
    "order_status",
    "tracking_number",
    "unique_key",
    "autoincrement",
    "gender",
    "age",
    "date_of_birth",
    "ssn",
    "prefix",
    "suffix",
]


# ============================================================================
# SUBCOMMAND HANDLERS
# ============================================================================


def run_generate(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate fake data of a given type."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    data_type = args.data_type
    count = args.count

    try:
        results = gen.generate_batch(data_type, count)
    except ValueError as e:
        print_error(str(e))
        return

    write_output(results, args)
    cli.last_result = results
    cli.increment_stat("generated", count)


def run_batch(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate multiple columns of fake data."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    types = [t.strip() for t in args.types.split(",")]
    count = args.count

    # Validate all types
    for t in types:
        if t not in AVAILABLE_TYPES:
            print_error(f"Unknown data type: '{t}'. Use 'textdummy types' to see valid types.")
            return

    # Generate columns
    columns: Dict[str, List[Any]] = {}
    for t in types:
        columns[t] = gen.generate_batch(t, count)
        cli.increment_stat("generated", count)

    fmt = getattr(args, "output_format", "summary")
    output_file = getattr(args, "output", None)
    if output_file:
        output_file = os.path.realpath(output_file)

    if fmt == "json":
        # Convert to list-of-dicts (records)
        records = []
        for i in range(count):
            record = {t: columns[t][i] for t in types}
            records.append(record)
        text = json.dumps(records, ensure_ascii=False, indent=2, default=str)
    else:
        # CSV format
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=args.delimiter)
        writer.writerow(types)
        for i in range(count):
            writer.writerow([columns[t][i] for t in types])
        text = buf.getvalue()

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print_success(f"Wrote {count} rows × {len(types)} columns to {output_file}")
    else:
        print(text)

    # Store structured result for API
    records = []
    for i in range(count):
        record = {t: columns[t][i] for t in types}
        records.append(record)
    cli.last_result = records


def run_profile(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate complete fake profiles."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count

    profiles = [gen.profile_data() for _ in range(count)]
    cli.last_result = profiles
    cli.increment_stat("profiles", count)

    fmt = getattr(args, "output_format", "summary")
    if fmt == "table" and count <= 20:
        if profiles:
            headers = list(profiles[0].keys())
            rows = [[str(p.get(h, "")) for h in headers] for p in profiles]
            print_table(headers, rows)
    else:
        write_output(profiles, args)


def run_product(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate complete fake products."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count

    products = [gen.product_full() for _ in range(count)]
    cli.last_result = products
    cli.increment_stat("products", count)

    write_output(products, args)


def run_types(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: list available data types."""
    rows = [[t] for t in sorted(AVAILABLE_TYPES)]
    print_table(["Data Type"], rows)
    print_info(f"Total: {len(AVAILABLE_TYPES)} types available")


def run_locale_info(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: show locale information."""
    from .text_dummy import TextDummy

    if args.list_all:
        locales = TextDummy.supported_locales()
        rows = [[code, country] for code, country in sorted(locales.items())]
        print_table(["Locale", "Country"], rows)
    else:
        gen = TextDummy(locale=args.locale)
        info = gen.locale_info()
        write_output(info, args)


def run_id_document(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate fake ID documents."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count
    doc_type = getattr(args, "doc_type", None)

    results = [gen.id_document(doc_type=doc_type) for _ in range(count)]
    cli.last_result = results
    cli.increment_stat("documents", count)

    write_output(results, args)


def run_number(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate random numbers."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count

    results = [
        gen.random_number(
            number_type=args.number_type,
            digits=args.digits,
            decimals=args.decimals,
            min_val=args.min_val,
            max_val=args.max_val,
            currency=args.currency,
        )
        for _ in range(count)
    ]
    cli.increment_stat("numbers", count)
    cli.last_result = results
    write_output(results, args)


def run_date(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate random dates."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count

    results = [
        gen.random_date(
            start=args.start,
            end=args.end,
            pattern=args.pattern,
        )
        for _ in range(count)
    ]
    cli.increment_stat("dates", count)
    cli.last_result = results
    write_output(results, args)


def run_key(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate unique keys."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count

    results = [
        gen.unique_key(
            length=args.length,
            key_type=args.key_type,
            prefix=args.prefix_str,
            separator=args.separator,
            segment_length=args.segment_length,
        )
        for _ in range(count)
    ]
    cli.increment_stat("keys", count)
    cli.last_result = results
    write_output(results, args)


# ============================================================================
# MAIN
# ============================================================================


def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on the CLI instance."""
    cli.add_examples(
        [
            "%(prog)s generate name --count 10 --locale es_ES",
            "%(prog)s generate email --count 5 --locale en_US",
            '%(prog)s batch "name,email,phone,city" --count 50 -o contacts.csv',
            '%(prog)s batch "name,dni,email" --count 100 --output-format json -o data.json',
            "%(prog)s profile --count 5 --locale pt_BR",
            "%(prog)s product --count 10 --locale de_DE",
            "%(prog)s id-doc --locale es_ES --doc-type NIE --count 10",
            "%(prog)s number --number-type float --min-val 0 --max-val 1000 --count 20",
            "%(prog)s date --start 2020-01-01 --end 2025-12-31 --count 10",
            "%(prog)s key --key-type hex --length 12 --separator - --segment-length 4 --count 5",
            "%(prog)s types",
            "%(prog)s locale --list-all",
        ]
    )

    cli.init_subcommands()

    # --- generate ---
    p_gen = cli.add_subcommand(
        "generate",
        "Generate fake data of a single type",
        handler=run_generate,
        aliases=["gen"],
    )
    p_gen.add_argument("data_type", choices=AVAILABLE_TYPES, help="Type of data to generate")
    p_gen.add_argument("--count", "-n", type=int, default=10, help="Number of items (default: 10)")
    p_gen.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_gen.add_argument("--output", "-o", help="Write result to file")

    # --- batch ---
    p_batch = cli.add_subcommand("batch", "Generate multiple columns of fake data", handler=run_batch)
    p_batch.add_argument("types", help="Comma-separated data types (e.g. 'name,email,phone')")
    p_batch.add_argument("--count", "-n", type=int, default=10, help="Number of rows (default: 10)")
    p_batch.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_batch.add_argument("--output", "-o", help="Write result to file")
    p_batch.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")

    # --- profile ---
    p_prof = cli.add_subcommand(
        "profile",
        "Generate complete fake personal profiles",
        handler=run_profile,
        aliases=["prof"],
    )
    p_prof.add_argument("--count", "-n", type=int, default=1, help="Number of profiles (default: 1)")
    p_prof.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_prof.add_argument("--output", "-o", help="Write result to file")

    # --- product ---
    p_prod = cli.add_subcommand(
        "product",
        "Generate complete fake products",
        handler=run_product,
        aliases=["prod"],
    )
    p_prod.add_argument("--count", "-n", type=int, default=1, help="Number of products (default: 1)")
    p_prod.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_prod.add_argument("--output", "-o", help="Write result to file")

    # --- id-doc ---
    p_id = cli.add_subcommand("id-doc", "Generate fake ID documents", handler=run_id_document, aliases=["id"])
    p_id.add_argument("--count", "-n", type=int, default=10, help="Number of documents (default: 10)")
    p_id.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_id.add_argument("--doc-type", "-d", help="Document type (e.g. NIE, RFC, CNPJ)")
    p_id.add_argument("--output", "-o", help="Write result to file")

    # --- number ---
    p_num = cli.add_subcommand("number", "Generate random numbers", handler=run_number, aliases=["num"])
    p_num.add_argument("--count", "-n", type=int, default=10, help="Number of values (default: 10)")
    p_num.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_num.add_argument(
        "--number-type",
        choices=["integer", "float"],
        default="integer",
        help="integer or float",
    )
    p_num.add_argument("--digits", type=int, default=6, help="Significant digits (default: 6)")
    p_num.add_argument("--decimals", type=int, default=2, help="Decimal places for float (default: 2)")
    p_num.add_argument("--min-val", type=float, default=None, help="Minimum value")
    p_num.add_argument("--max-val", type=float, default=None, help="Maximum value")
    p_num.add_argument("--currency", action="store_true", help="Format with currency symbol")
    p_num.add_argument("--output", "-o", help="Write result to file")

    # --- date ---
    p_date = cli.add_subcommand("date", "Generate random dates", handler=run_date)
    p_date.add_argument("--count", "-n", type=int, default=10, help="Number of dates (default: 10)")
    p_date.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_date.add_argument("--start", help="Start date YYYY-MM-DD (default: 1970-01-01)")
    p_date.add_argument("--end", help="End date YYYY-MM-DD (default: today)")
    p_date.add_argument("--pattern", help="Output date format (strftime)")
    p_date.add_argument("--output", "-o", help="Write result to file")

    # --- key ---
    p_key = cli.add_subcommand("key", "Generate unique keys", handler=run_key)
    p_key.add_argument("--count", "-n", type=int, default=10, help="Number of keys (default: 10)")
    p_key.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_key.add_argument("--length", type=int, default=8, help="Key length (default: 8)")
    p_key.add_argument(
        "--key-type",
        choices=["alphanumeric", "alpha", "numeric", "hex", "uuid"],
        default="alphanumeric",
    )
    p_key.add_argument("--prefix-str", default="", help="Key prefix")
    p_key.add_argument("--separator", default="", help="Segment separator")
    p_key.add_argument("--segment-length", type=int, default=0, help="Characters per segment")
    p_key.add_argument("--output", "-o", help="Write result to file")

    # --- types ---
    cli.add_subcommand("types", "List all available data types", handler=run_types)

    # --- locale ---
    p_locale = cli.add_subcommand("locale", "Show locale information", handler=run_locale_info)
    p_locale.add_argument("--locale", "-l", default="es_ES", help="Locale to inspect")
    p_locale.add_argument("--list-all", action="store_true", help="List all supported locales")


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the TextDummy CLI.

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
        argv: Command-line arguments (e.g. ``["generate", "name", "--count", "5"]``).

    Returns:
        CLIResult with exit_code, data, stats, and optional error.

    Example Usage::

        from shadetriptxt.text_dummy.cli import run_api
        result = run_api(["generate", "email", "--count", "10", "--locale", "en_US"])
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
