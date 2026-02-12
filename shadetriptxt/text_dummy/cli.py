"""
cli.py - Command Line Interface for TextDummy

Fake data generation from the command line: names, emails, phones,
ID documents, products, financial data, and more across 12 locales.

Usage:
    python -m shadetriptxt.text_dummy.cli --help
    python -m shadetriptxt.text_dummy.cli generate name --count 10 --locale es_ES
    python -m shadetriptxt.text_dummy.cli batch name,email,phone --count 50 -o data.csv
    python -m shadetriptxt.text_dummy.cli profile --locale en_US
    python -m shadetriptxt.text_dummy.cli locale --list-all
    python -m shadetriptxt.text_dummy.cli @params.txt

Author: DatamanEdge
Version: 0.1.0
"""

from __future__ import annotations

import sys
import os
import argparse
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

__all__ = [
    "CLIBase",
    "CLIResult",
    "Subcommand",
    "OutputFormat",
    "Colors",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_table",
    "print_summary",
    "print_progress",
    "confirm_action",
    "create_cli",
    "run_api",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ============================================================================
# CONSTANTS AND ENUMS
# ============================================================================

@dataclass
class CLIResult:
    """Result from programmatic CLI invocation.

    Attributes:
        exit_code: 0 for success, non-zero for errors.
        data: Structured output data (dict, list, or str).
        stats: Processing statistics.
        error: Error message if exit_code != 0.
    """
    exit_code: int = 0
    data: Any = None
    stats: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class OutputFormat(Enum):
    """Supported output formats for CLI display."""
    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    SUMMARY = "summary"
    QUIET = "quiet"


class LogLevel(Enum):
    """Logging verbosity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUIET = "quiet"


class Colors:
    """ANSI color codes with Windows compatibility."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = CYAN

    _enabled: bool = True

    @classmethod
    def disable(cls) -> None:
        """Disable colors for non-TTY or unsupported terminals."""
        cls._enabled = False
        for attr in ("RESET", "BOLD", "RED", "GREEN", "YELLOW", "BLUE",
                      "MAGENTA", "CYAN", "WHITE", "GRAY",
                      "SUCCESS", "ERROR", "WARNING", "INFO"):
            setattr(cls, attr, "")

    @classmethod
    def init(cls) -> None:
        """Initialize colors with Windows ANSI support and TTY auto-detection."""
        if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
            cls.disable()
            return
        if os.name == "nt":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                try:
                    import colorama
                    colorama.init()
                except ImportError:
                    pass


Colors.init()


# ============================================================================
# OUTPUT UTILITIES
# ============================================================================

def cprint(message: str, color: str = "", bold: bool = False, file=sys.stdout) -> None:
    """Print colored message to terminal."""
    prefix = ""
    if bold:
        prefix += Colors.BOLD
    if color:
        prefix += color
    suffix = Colors.RESET if (bold or color) else ""
    print(f"{prefix}{message}{suffix}", file=file)


def print_success(message: str) -> None:
    """Print success message with checkmark."""
    cprint(f"✓ {message}", Colors.SUCCESS)


def print_error(message: str, file=sys.stderr) -> None:
    """Print error message with X mark."""
    cprint(f"✗ {message}", Colors.ERROR, file=file)


def print_warning(message: str) -> None:
    """Print warning message with warning sign."""
    cprint(f"⚠ {message}", Colors.WARNING)


def print_info(message: str) -> None:
    """Print info message with info symbol."""
    cprint(f"ℹ {message}", Colors.INFO)


def print_header(title: str, width: int = 70, char: str = "=") -> None:
    """Print formatted section header."""
    print()
    cprint(char * width, Colors.CYAN, bold=True)
    cprint(f" {title}", Colors.CYAN, bold=True)
    cprint(char * width, Colors.CYAN, bold=True)


def print_table(
    headers: List[str],
    rows: List[List[Any]],
    max_col_width: int = 40,
) -> None:
    """Print formatted ASCII table."""
    if not headers or not rows:
        return

    col_widths: List[int] = []
    for i, header in enumerate(headers):
        max_width = len(str(header))
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(min(max_width, max_col_width))

    def truncate(value: Any, width: int) -> str:
        s = str(value)
        return s[:width - 3] + "..." if len(s) > width else s

    header_row = " | ".join(
        truncate(h, w).ljust(w) for h, w in zip(headers, col_widths)
    )
    separator = "-+-".join("-" * w for w in col_widths)

    cprint(header_row, Colors.CYAN, bold=True)
    print(separator)

    for row in rows:
        row_str = " | ".join(
            truncate(row[i] if i < len(row) else "", w).ljust(w)
            for i, w in enumerate(col_widths)
        )
        print(row_str)


def print_summary(stats: Dict[str, Any], title: str = "SUMMARY", width: int = 70) -> None:
    """Print formatted summary statistics."""
    print()
    cprint("=" * width, Colors.CYAN, bold=True)
    cprint(f" {title}", Colors.CYAN, bold=True)
    cprint("=" * width, Colors.CYAN, bold=True)

    for key, value in stats.items():
        key_display = key.replace("_", " ").title()
        value_color = ""
        if isinstance(value, (int, float)):
            value_color = Colors.GREEN if value > 0 else Colors.GRAY
        print(f"  {key_display:<30} ", end="")
        cprint(str(value), value_color)

    cprint("=" * width, Colors.CYAN, bold=True)


def print_progress(
    current: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    width: int = 40,
) -> None:
    """Print progress bar."""
    if total == 0:
        percent, filled = 100, width
    else:
        percent = (current / total) * 100
        filled = int(width * current // total)

    bar = "█" * filled + "-" * (width - filled)
    print(f"\r{prefix} |{bar}| {percent:.1f}% {suffix}", end="", flush=True)

    if current >= total:
        print()


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation."""
    suffix = " [Y/n]" if default else " [y/N]"
    response = input(f"{message}{suffix}: ").strip().lower()

    if not response:
        return default
    return response in ("y", "yes", "si", "s")


# ============================================================================
# CLI CONFIGURATION
# ============================================================================

@dataclass
class CLIConfig:
    """Configuration for CLI behavior and appearance."""
    prog_name: str = "textdummy"
    version: str = "0.1.0"
    description: str = "Fake data generation across 12 locales"
    epilog: str = ""

    colors_enabled: bool = True
    default_output_format: OutputFormat = OutputFormat.SUMMARY
    default_log_level: LogLevel = LogLevel.INFO

    allow_parameter_files: bool = True
    require_confirmation: bool = False
    dry_run_by_default: bool = False

    default_timeout: int = 30
    default_page_size: int = 1000


@dataclass
class Subcommand:
    """Definition of a CLI subcommand."""
    name: str
    help: str
    handler: Optional[Callable[[argparse.Namespace, "CLIBase"], None]] = None
    aliases: List[str] = field(default_factory=list)
    parser: Optional[argparse.ArgumentParser] = None


# ============================================================================
# CLI BASE CLASS
# ============================================================================

class CLIBase:
    """Base class for the TextDummy CLI application.

    Usage:
        cli = CLIBase(prog="textdummy", description="TextDummy CLI", version="0.1.0")
        cli.init_subcommands()
        cli.add_subcommand("generate", "Generate fake data", handler=run_generate)
        args = cli.parse_args()
        cli.run()
    """

    def __init__(
        self,
        prog: str = "textdummy",
        description: str = "Fake data generation across 12 locales",
        version: str = "0.1.0",
        epilog: str = "",
        config: Optional[CLIConfig] = None,
    ):
        self.config = config or CLIConfig(
            prog_name=prog, version=version,
            description=description, epilog=epilog,
        )

        self.parser = argparse.ArgumentParser(
            prog=self.config.prog_name,
            description=self.config.description,
            epilog=self.config.epilog or None,
            fromfile_prefix_chars="@" if self.config.allow_parameter_files else None,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self.parser.add_argument(
            "--version", "-V", action="version",
            version=f"%(prog)s {self.config.version}",
        )

        self._subparsers: Optional[argparse._SubParsersAction] = None
        self._subcommands: Dict[str, Subcommand] = {}
        self._groups: Dict[str, argparse._ArgumentGroup] = {}
        self.args: Optional[argparse.Namespace] = None
        self._stats: Dict[str, int] = {}
        self.start_time: Optional[datetime] = None
        self.last_result: Any = None

        self._add_global_arguments()

    # -------------------------------------------------------------------
    # SUBCOMMAND SUPPORT
    # -------------------------------------------------------------------

    def init_subcommands(
        self, title: str = "Commands", dest: str = "command",
    ) -> argparse._SubParsersAction:
        """Initialize subcommand support."""
        self._subparsers = self.parser.add_subparsers(
            title=title, dest=dest, help="Available commands",
        )
        return self._subparsers

    def add_subcommand(
        self,
        name: str,
        help_text: str,
        handler: Optional[Callable[[argparse.Namespace, "CLIBase"], None]] = None,
        aliases: Optional[List[str]] = None,
    ) -> argparse.ArgumentParser:
        """Add a subcommand with optional handler and aliases."""
        if self._subparsers is None:
            self.init_subcommands()

        aliases = aliases or []
        subparser = self._subparsers.add_parser(  # type: ignore[union-attr]
            name, help=help_text, aliases=aliases,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._add_global_arguments_to_subparser(subparser)

        subcmd = Subcommand(
            name=name, help=help_text, handler=handler,
            aliases=aliases, parser=subparser,
        )
        self._subcommands[name] = subcmd
        for alias in aliases:
            self._subcommands[alias] = subcmd

        return subparser

    def _add_global_arguments_to_subparser(
        self, subparser: argparse.ArgumentParser,
    ) -> None:
        """Add global options to a subparser."""
        subparser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Increase verbosity (-v INFO, -vv DEBUG)",
        )
        subparser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
        subparser.add_argument("--no-color", action="store_true", help="Disable colors")
        subparser.add_argument("--ci", action="store_true", help="CI mode (JSON output, no colors, exit codes)")
        subparser.add_argument("--dry-run", action="store_true", help="Simulate only")
        subparser.add_argument(
            "--output-format", choices=["table", "json", "csv", "summary", "quiet"],
            default="summary", help="Output format (default: summary)",
        )
        subparser.add_argument("--log-file", help="Write logs to file")
        subparser.add_argument(
            "--config-file", help="Load settings from JSON config file",
        )

    def set_handler(
        self, command: str,
        handler: Callable[[argparse.Namespace, "CLIBase"], None],
    ) -> None:
        """Set or update the handler for a subcommand."""
        if command in self._subcommands:
            self._subcommands[command].handler = handler

    def run(self) -> None:
        """Execute the handler for the parsed subcommand."""
        if self.args is None:
            self.parse_args()
        command = getattr(self.args, "command", None)
        if not command:
            self.parser.print_help()
            return
        subcmd = self._subcommands.get(command)
        if subcmd and subcmd.handler:
            subcmd.handler(self.args, self)
        else:
            print_error(f"No handler for command '{command}'")
            self.parser.print_help()

    # -------------------------------------------------------------------
    # GLOBAL ARGUMENTS
    # -------------------------------------------------------------------

    def _add_global_arguments(self) -> None:
        """Add global arguments available to all CLI tools."""
        self.parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Increase verbosity (-v INFO, -vv DEBUG)",
        )
        self.parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
        self.parser.add_argument("--no-color", action="store_true", help="Disable colors")
        self.parser.add_argument("--ci", action="store_true", help="CI mode (JSON output, no colors, exit codes)")
        self.parser.add_argument("--dry-run", action="store_true", help="Simulate only")
        self.parser.add_argument(
            "--output-format", choices=["table", "json", "csv", "summary", "quiet"],
            default="summary", help="Output format (default: summary)",
        )
        self.parser.add_argument("--log-file", help="Write logs to file")
        self.parser.add_argument(
            "--config-file", help="Load settings from JSON config file",
        )

    def add_group(
        self, name: str, title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> argparse._ArgumentGroup:
        """Add a custom argument group."""
        group = self.parser.add_argument_group(title or name, description)
        self._groups[name] = group
        return group

    # -------------------------------------------------------------------
    # ARGUMENT PARSING
    # -------------------------------------------------------------------

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command-line arguments."""
        self.start_time = datetime.now()
        self.args = self.parser.parse_args(args)
        self._post_process_args()
        return self.args

    def _post_process_args(self) -> None:
        """Post-process parsed arguments."""
        if self.args is None:
            return
        if getattr(self.args, "ci", False):
            self.args.no_color = True
            self.args.output_format = "json"
            self.args.quiet = True
        if getattr(self.args, "no_color", False):
            Colors.disable()
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure logging based on verbosity."""
        if self.args is None:
            return
        verbose = getattr(self.args, "verbose", 0)
        quiet = getattr(self.args, "quiet", False)

        if quiet:
            level = logging.CRITICAL
        elif verbose >= 2:
            level = logging.DEBUG
        elif verbose >= 1:
            level = logging.INFO
        else:
            level = logging.WARNING

        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")

        log_file = getattr(self.args, "log_file", None)
        if log_file:
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(level)
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logging.getLogger().addHandler(handler)

    # -------------------------------------------------------------------
    # STATISTICS AND OUTPUT
    # -------------------------------------------------------------------

    def increment_stat(self, name: str, value: int = 1) -> None:
        """Track a statistic counter."""
        self._stats[name] = self._stats.get(name, 0) + value

    def print_final_summary(self) -> None:
        """Print tracked statistics summary."""
        if self._stats:
            print_summary(self._stats, title="RESULTS")

    def get_elapsed_time(self) -> str:
        """Get formatted elapsed time since parse_args."""
        if not self.start_time:
            return "N/A"
        delta = datetime.now() - self.start_time
        return str(delta).split(".")[0]

    def exit_success(self, message: str = "Done") -> None:
        """Exit with success code."""
        print_success(message)
        sys.exit(0)

    def exit_with_error(self, message: str, code: int = 1) -> None:
        """Exit with error message and code."""
        print_error(message)
        sys.exit(code)

    def add_examples(self, examples: List[str]) -> None:
        """Add usage examples to the epilog."""
        lines = ["\nExamples:"] + [f"  {e}" for e in examples]
        existing = self.parser.epilog or ""
        self.parser.epilog = existing + "\n".join(lines)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_cli(
    prog: str = "textdummy",
    description: str = "Fake data generation across 12 locales",
    version: str = "0.1.0",
) -> CLIBase:
    """Factory function to create a configured TextDummy CLI instance."""
    return CLIBase(prog=prog, description=description, version=version)


# ============================================================================
# AVAILABLE DATA TYPES
# ============================================================================

AVAILABLE_TYPES = [
    "name", "first_name", "last_name", "email", "phone", "address",
    "city", "state", "postcode", "country", "company", "job",
    "department", "sentence", "word", "dni", "id_document",
    "price", "iban", "bban", "swift", "credit_card_number",
    "credit_card_expire", "credit_card_provider", "credit_card_full",
    "cryptocurrency_code", "cryptocurrency_name", "payment_method",
    "invoice_number", "url", "domain_name", "username", "userlogin",
    "password", "ipv4", "ipv6", "mac_address", "user_agent", "slug",
    "uuid4", "file_name", "file_extension", "mime_type", "file_path",
    "date", "random_date", "random_number", "license_plate",
    "latitude", "longitude", "coordinate", "color_name", "hex_color",
    "rgb_color", "isbn10", "isbn13", "ean13", "ean8",
    "product_name", "product_category", "product_material",
    "product_sku", "order_status", "tracking_number",
    "unique_key", "autoincrement", "gender", "age", "date_of_birth",
    "ssn", "prefix", "suffix",
]


# ============================================================================
# SUBCOMMAND HANDLERS
# ============================================================================

def _write_output(data: Any, args: argparse.Namespace) -> None:
    """Write result to stdout or file, respecting output format."""
    output_file = getattr(args, "output", None)
    fmt = getattr(args, "output_format", "summary")

    if fmt == "json":
        text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    elif fmt == "csv" and isinstance(data, list):
        if data and isinstance(data[0], dict):
            import csv
            import io
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            text = buf.getvalue()
        else:
            text = "\n".join(str(v) for v in data)
    elif isinstance(data, list):
        text = "\n".join(str(v) for v in data)
    elif isinstance(data, dict):
        text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    else:
        text = str(data) if data is not None else ""

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print_success(f"Output written to {output_file}")
    else:
        print(text)


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

    _write_output(results, args)
    cli.last_result = results
    cli.increment_stat("generated", count)


def run_batch(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate multiple columns of fake data."""
    from .text_dummy import TextDummy
    import csv
    import io

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
        _write_output(profiles, args)


def run_product(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate complete fake products."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count

    products = [gen.product_full() for _ in range(count)]
    cli.last_result = products
    cli.increment_stat("products", count)

    _write_output(products, args)


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
        _write_output(info, args)


def run_id_document(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: generate fake ID documents."""
    from .text_dummy import TextDummy

    gen = TextDummy(locale=args.locale)
    count = args.count
    doc_type = getattr(args, "doc_type", None)

    results = [gen.id_document(doc_type=doc_type) for _ in range(count)]
    cli.last_result = results
    cli.increment_stat("documents", count)

    _write_output(results, args)


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
    _write_output(results, args)


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
    _write_output(results, args)


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
    _write_output(results, args)


# ============================================================================
# MAIN
# ============================================================================

def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on the CLI instance."""
    cli.add_examples([
        '%(prog)s generate name --count 10 --locale es_ES',
        '%(prog)s generate email --count 5 --locale en_US',
        '%(prog)s batch "name,email,phone,city" --count 50 -o contacts.csv',
        '%(prog)s batch "name,dni,email" --count 100 --output-format json -o data.json',
        '%(prog)s profile --count 5 --locale pt_BR',
        '%(prog)s product --count 10 --locale de_DE',
        '%(prog)s id-doc --locale es_ES --doc-type NIE --count 10',
        '%(prog)s number --number-type float --min-val 0 --max-val 1000 --count 20',
        '%(prog)s date --start 2020-01-01 --end 2025-12-31 --count 10',
        '%(prog)s key --key-type hex --length 12 --separator - --segment-length 4 --count 5',
        '%(prog)s types',
        '%(prog)s locale --list-all',
    ])

    cli.init_subcommands()

    # --- generate ---
    p_gen = cli.add_subcommand("generate", "Generate fake data of a single type", handler=run_generate, aliases=["gen"])
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
    p_prof = cli.add_subcommand("profile", "Generate complete fake personal profiles", handler=run_profile, aliases=["prof"])
    p_prof.add_argument("--count", "-n", type=int, default=1, help="Number of profiles (default: 1)")
    p_prof.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_prof.add_argument("--output", "-o", help="Write result to file")

    # --- product ---
    p_prod = cli.add_subcommand("product", "Generate complete fake products", handler=run_product, aliases=["prod"])
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
    p_num.add_argument("--number-type", choices=["integer", "float"], default="integer", help="integer or float")
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
    p_key.add_argument("--key-type", choices=["alphanumeric", "alpha", "numeric", "hex", "uuid"], default="alphanumeric")
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
    Colors.init()
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
    Colors.disable()
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
