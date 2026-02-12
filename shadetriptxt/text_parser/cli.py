"""
cli.py - Command Line Interface for TextParser

Locale-aware text parsing, extraction, normalization, encoding repair,
phonetic reduction, and ID validation from the command line.

Usage:
    python -m shadetriptxt.text_parser.cli --help
    python -m shadetriptxt.text_parser.cli normalize "  José García-López  " --locale es_ES
    python -m shadetriptxt.text_parser.cli extract-phones "+34 91 303 20 60"
    python -m shadetriptxt.text_parser.cli validate-id "12345678Z" --locale es_ES
    python -m shadetriptxt.text_parser.cli fix-encoding "Ã¡rbol"
    python -m shadetriptxt.text_parser.cli @params.txt

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
    prog_name: str = "textparser"
    version: str = "0.1.0"
    description: str = "Locale-aware text parsing, extraction, and normalization"
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
    """Base class for the TextParser CLI application.

    Usage:
        cli = CLIBase(prog="textparser", description="TextParser CLI", version="0.1.0")
        cli.init_subcommands()
        cli.add_subcommand("normalize", "Normalize text", handler=run_normalize)
        args = cli.parse_args()
        cli.run()
    """

    def __init__(
        self,
        prog: str = "textparser",
        description: str = "Locale-aware text parsing, extraction, and normalization",
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
    prog: str = "textparser",
    description: str = "Locale-aware text parsing, extraction, and normalization",
    version: str = "0.1.0",
) -> CLIBase:
    """Factory function to create a configured TextParser CLI instance."""
    return CLIBase(prog=prog, description=description, version=version)


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
        with open(input_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    print_error("No input provided. Use positional argument, --input, or pipe via stdin.")
    sys.exit(1)


def _write_output(result: Any, args: argparse.Namespace) -> None:
    """Write result to stdout or file."""
    output_file = getattr(args, "output", None)
    fmt = getattr(args, "output_format", "summary")

    if fmt == "json":
        text = json.dumps(result, ensure_ascii=False, indent=2)
    elif isinstance(result, list):
        text = "\n".join(str(r) for r in result)
    else:
        text = str(result) if result is not None else ""

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print_success(f"Output written to {output_file}")
    else:
        print(text)


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
    _write_output(result, args)
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
        _write_output(results, args)
        cli.last_result = results
        cli.increment_stat("extractions", len(results))
    else:
        func = extractors.get(extract_type)
        if not func:
            print_error(f"Unknown extraction type: {extract_type}. "
                        f"Valid: {', '.join(sorted(extractors.keys()))}")
            return
        result = func(text)
        _write_output(result, args)
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
        _write_output(result, args)
        cli.last_result = result
    else:
        result = parser.fix_mojibake(text, normalize_quotes=args.normalize_quotes)
        _write_output(result, args)
        cli.last_result = result
        cli.increment_stat("fixed", 1)


def run_phonetic(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: phonetic reduction."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.reduce_phonetic(text, strength=args.strength)
    _write_output(result, args)
    cli.last_result = result
    cli.increment_stat("reduced", 1)


def run_prepare(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: prepare text for comparison."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.prepare_for_comparison(text, aggressive=args.aggressive)
    _write_output(result, args)
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
    _write_output(result, args)
    cli.last_result = result
    cli.increment_stat("masked", 1)


def run_parse_name(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: parse / rearrange a name."""
    from .text_parser import TextParser

    text = _read_input(args)
    parser = TextParser(locale=args.locale)
    result = parser.parse_name(text)
    _write_output(result, args)
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
        _write_output(output, args)
        cli.last_result = output
    else:
        _write_output(None, args)
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
        _write_output(info, args)


def run_batch(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: process a file line by line."""
    from .text_parser import TextParser

    parser = TextParser(locale=args.locale)

    with open(args.input, "r", encoding=args.encoding) as f:
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
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(results) + "\n")
        print_success(f"Wrote {total} lines to {args.output}")
    else:
        for r in results:
            print(r)


# ============================================================================
# MAIN
# ============================================================================

def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on the CLI instance."""
    cli.add_examples([
        '%(prog)s normalize "  José García-López  " --locale es_ES',
        '%(prog)s extract "+34 600 123 456 email@test.com" --type all',
        '%(prog)s validate-id "12345678Z" --locale es_ES',
        '%(prog)s fix-encoding "Ã¡rbol" --locale es_ES',
        '%(prog)s phonetic "García" --locale es_ES --strength 2',
        '%(prog)s batch --input data.txt --operation normalize --output clean.txt',
    ])

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
        "--type", "-t", default="all",
        choices=["all", "phones", "emails", "urls", "dates", "ids", "ibans",
                 "credit_cards", "currency", "hashtags", "mentions", "ips",
                 "numeric", "percentages", "postal_codes"],
        help="Type of content to extract (default: all)",
    )

    # --- validate-id ---
    p_valid = cli.add_subcommand("validate-id", "Validate an ID document", handler=run_validate_id, aliases=["vid"])
    p_valid.add_argument("text", nargs="?", help="ID string to validate")
    p_valid.add_argument("--input", "-i", help="Read ID from file")
    p_valid.add_argument("--output", "-o", help="Write result to file")
    p_valid.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_valid.add_argument("--doc-type", "-d", help="Document type (e.g. DNI, NIE, CIF)")

    # --- fix-encoding ---
    p_enc = cli.add_subcommand("fix-encoding", "Fix mojibake / encoding issues", handler=run_fix_encoding, aliases=["fix"])
    p_enc.add_argument("text", nargs="?", help="Text with encoding issues")
    p_enc.add_argument("--input", "-i", help="Read text from file")
    p_enc.add_argument("--output", "-o", help="Write result to file")
    p_enc.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_enc.add_argument("--detect", action="store_true", help="Detect encoding issues instead of fixing")
    p_enc.add_argument("--normalize-quotes", action="store_true", help="Convert typographic quotes to ASCII")

    # --- phonetic ---
    p_phon = cli.add_subcommand("phonetic", "Phonetic reduction", handler=run_phonetic, aliases=["phon"])
    p_phon.add_argument("text", nargs="?", help="Text for phonetic reduction")
    p_phon.add_argument("--input", "-i", help="Read text from file")
    p_phon.add_argument("--output", "-o", help="Write result to file")
    p_phon.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")
    p_phon.add_argument("--strength", "-s", type=int, default=1, choices=[0, 1, 2, 3], help="Reduction strength 0-3 (default: 1)")

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
    p_mask.add_argument("--keep-first", type=int, default=1, help="Characters to keep at start (default: 1)")
    p_mask.add_argument("--keep-last", type=int, default=1, help="Characters to keep at end (default: 1)")
    p_mask.add_argument("--mask-char", default="*", help="Masking character (default: *)")

    # --- parse-name ---
    p_pname = cli.add_subcommand("parse-name", "Parse / rearrange a person name", handler=run_parse_name, aliases=["pn"])
    p_pname.add_argument("text", nargs="?", help="Name to parse (e.g. 'García López, José')")
    p_pname.add_argument("--input", "-i", help="Read name from file")
    p_pname.add_argument("--output", "-o", help="Write result to file")
    p_pname.add_argument("--locale", "-l", default="es_ES", help="Locale (default: es_ES)")

    # --- parse-company ---
    p_pcomp = cli.add_subcommand("parse-company", "Parse a company name", handler=run_parse_company, aliases=["pc"])
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
        "--operation", default="normalize",
        choices=["normalize", "fix-encoding", "phonetic", "prepare", "remove-articles"],
        help="Operation to apply (default: normalize)",
    )
    p_batch.add_argument("--strength", "-s", type=int, default=1, help="Phonetic strength (for phonetic operation)")
    p_batch.add_argument("--aggressive", "-a", action="store_true", help="Aggressive mode (for prepare operation)")


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the TextParser CLI.

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
        argv: Command-line arguments (e.g. ``["normalize", "José García"]``).

    Returns:
        CLIResult with exit_code, data, stats, and optional error.

    Example Usage::

        from shadetriptxt.text_parser.cli import run_api
        result = run_api(["normalize", "  José García-López  "])
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
