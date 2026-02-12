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

import csv
import io
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
    "main",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ============================================================================
# CONSTANTS AND ENUMS
# ============================================================================

STRATEGIES = ["mask", "replace", "hash", "redact", "generalize", "pseudonymize", "suppress"]

PII_TYPES = [
    "NAME", "EMAIL", "PHONE", "ADDRESS", "ID_DOCUMENT", "CREDIT_CARD",
    "IBAN", "IP_ADDRESS", "DATE", "URL", "ORGANIZATION", "LOCATION",
    "NUMBER", "CURRENCY", "CUSTOM",
]

SUPPORTED_LOCALES = [
    "es_ES", "es_MX", "es_AR", "es_CO", "es_CL",
    "en_US", "en_GB",
    "pt_BR", "pt_PT",
    "fr_FR", "de_DE", "it_IT",
]


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
    prog_name: str = "textanonymizer"
    version: str = "0.1.0"
    description: str = "PII detection & anonymization across 12 locales"
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
    """Base class for the TextAnonymizer CLI application.

    Usage:
        cli = CLIBase(prog="textanonymizer", description="TextAnonymizer CLI", version="0.1.0")
        cli.init_subcommands()
        cli.add_subcommand("anonymize", "Anonymize text", handler=run_anonymize)
        args = cli.parse_args()
        cli.run()
    """

    def __init__(
        self,
        prog: str = "textanonymizer",
        description: str = "PII detection & anonymization across 12 locales",
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
    prog: str = "textanonymizer",
    description: str = "PII detection & anonymization across 12 locales",
    version: str = "0.1.0",
) -> CLIBase:
    """Factory function to create a configured TextAnonymizer CLI instance."""
    return CLIBase(prog=prog, description=description, version=version)


# ============================================================================
# SHARED HELPERS
# ============================================================================

def _write_output(data: Any, args: argparse.Namespace) -> None:
    """Write result to stdout or file, respecting output format."""
    output_file = getattr(args, "output", None)
    fmt = getattr(args, "output_format", "summary")

    if fmt == "json":
        text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    elif fmt == "csv" and isinstance(data, list):
        if data and isinstance(data[0], dict):
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

    # Get text from positional arg or stdin
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
        _write_output(output, args)
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
        _write_output(output, args)
    elif fmt == "table" or fmt == "summary":
        if entities:
            headers = ["PII Type", "Text", "Position", "Confidence", "Source"]
            rows = [
                [e.pii_type.value, e.text, f"{e.start}-{e.end}",
                 f"{e.confidence:.2f}", e.source]
                for e in entities
            ]
            print_table(headers, rows)
        else:
            print_info("No PII entities detected.")
    else:
        for e in entities:
            print(f"{e.pii_type.value}: {e.text} ({e.confidence:.2f})")

    cli.last_result = [
        {"text": e.text, "pii_type": e.pii_type.value, "confidence": e.confidence}
        for e in entities
    ]
    cli.increment_stat("texts_scanned", 1)
    cli.increment_stat("entities_found", len(entities))


def run_anonymize_file(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: anonymize a text file line by line."""
    anon = _build_anonymizer(args)

    input_path = args.input
    output_path = getattr(args, "output", None)
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
        print_success(f"Anonymized {total} lines → {output_path}")
    else:
        fmt = getattr(args, "output_format", "summary")
        if fmt == "json":
            _write_output({"lines": total, "entities": total_entities,
                           "content": anonymized_lines}, args)
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

    input_path = args.input
    output_path = getattr(args, "output", None)
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

    anonymized_records = anon.anonymize_records(
        records, fields=columns,
    )

    cli.increment_stat("records_processed", len(records))
    cli.increment_stat("columns_anonymized", len(columns) if columns else len(fieldnames))

    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(anonymized_records, args)
    elif output_path:
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(anonymized_records)
        print_success(f"Anonymized {len(records)} records → {output_path}")
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

    _write_output(result, args)
    cli.last_result = result


def run_locales(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: list supported locales."""
    from .text_anonymizer import LOCALE_PROFILES

    rows = [
        [p.code, p.country, p.language, p.spacy_model,
         str(len(p.id_patterns))]
        for p in LOCALE_PROFILES.values()
    ]
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
        "generalize": "Reduce precision (e.g. age 34 → 30-40)",
        "pseudonymize": "Consistent replacement (same input → same output)",
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
# MAIN
# ============================================================================

def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on the CLI instance."""
    cli.add_examples([
        '%(prog)s anonymize "DNI: 12345678Z, email: juan@test.com"',
        '%(prog)s anonymize "Call 612345678" --strategy mask --locale es_ES',
        '%(prog)s detect "My SSN is 123-45-6789" --locale en_US',
        '%(prog)s detect "DNI: 12345678Z, tel: 612345678" --output-format json',
        '%(prog)s anonymize-file input.txt -o output.txt --strategy replace',
        '%(prog)s anonymize-csv data.csv --columns name,email,phone -o clean.csv',
        '%(prog)s anonymize-dict \'{"name": "Juan", "email": "j@test.com"}\'',
        '%(prog)s locales',
        '%(prog)s strategies',
        '%(prog)s pii-types',
    ])

    cli.init_subcommands()

    # Common anonymizer arguments shared across subcommands
    def _add_anonymizer_args(sub: argparse.ArgumentParser) -> None:
        grp = sub.add_argument_group("Anonymizer Options")
        grp.add_argument("--locale", "-l", default="es_ES",
                         choices=SUPPORTED_LOCALES, help="Locale (default: es_ES)")
        grp.add_argument("--strategy", "-s", default="redact",
                         choices=STRATEGIES, help="Anonymization strategy (default: redact)")
        grp.add_argument("--seed", type=int, default=None,
                         help="Random seed for reproducible output")

    def _add_detection_args(sub: argparse.ArgumentParser) -> None:
        grp = sub.add_argument_group("Detection Options")
        grp.add_argument("--use-spacy", action="store_true",
                         help="Enable spaCy NER detection (requires spaCy)")
        grp.add_argument("--use-nltk", action="store_true",
                         help="Enable NLTK NER detection (requires NLTK)")
        grp.add_argument("--min-confidence", type=float, default=0.0,
                         help="Minimum confidence threshold 0.0-1.0 (default: 0.0)")
        grp.add_argument("--pii-types", type=str, default=None,
                         help="Comma-separated PII types to detect (e.g. NAME,EMAIL,PHONE)")

    # --- anonymize ---
    p_anon = cli.add_subcommand(
        "anonymize", "Anonymize text (argument or stdin)",
        handler=run_anonymize, aliases=["anon"],
    )
    p_anon.add_argument("text", nargs="?", default=None,
                        help="Text to anonymize (or pipe from stdin)")
    p_anon.add_argument("--output", "-o", help="Write result to file")
    _add_anonymizer_args(p_anon)
    _add_detection_args(p_anon)

    # --- detect ---
    p_detect = cli.add_subcommand(
        "detect", "Detect PII in text without anonymizing",
        handler=run_detect, aliases=["scan"],
    )
    p_detect.add_argument("text", nargs="?", default=None,
                          help="Text to scan (or pipe from stdin)")
    p_detect.add_argument("--output", "-o", help="Write result to file")
    _add_anonymizer_args(p_detect)
    _add_detection_args(p_detect)

    # --- anonymize-file ---
    p_file = cli.add_subcommand(
        "anonymize-file", "Anonymize a text file line by line",
        handler=run_anonymize_file, aliases=["file"],
    )
    p_file.add_argument("input", help="Input text file path")
    p_file.add_argument("--output", "-o", help="Output file path")
    _add_anonymizer_args(p_file)
    _add_detection_args(p_file)

    # --- anonymize-csv ---
    p_csv = cli.add_subcommand(
        "anonymize-csv", "Anonymize columns in a CSV file",
        handler=run_anonymize_csv, aliases=["csv"],
    )
    p_csv.add_argument("input", help="Input CSV file path")
    p_csv.add_argument("--output", "-o", help="Output CSV file path")
    p_csv.add_argument("--columns", "-c",
                       help="Comma-separated columns to anonymize (default: auto-detect)")
    p_csv.add_argument("--delimiter", "-d", default=",", help="CSV delimiter (default: ,)")
    _add_anonymizer_args(p_csv)

    # --- anonymize-dict ---
    p_dict = cli.add_subcommand(
        "anonymize-dict", "Anonymize a JSON record",
        handler=run_anonymize_dict_cmd, aliases=["dict"],
    )
    p_dict.add_argument("json_input", nargs="?", default=None,
                        help="JSON string (object or array) — or pipe from stdin")
    p_dict.add_argument("--output", "-o", help="Write result to file")
    p_dict.add_argument("--fields", "-f",
                        help="Comma-separated fields to anonymize (default: auto-detect)")
    _add_anonymizer_args(p_dict)

    # --- locales ---
    cli.add_subcommand("locales", "List supported locales", handler=run_locales)

    # --- strategies ---
    cli.add_subcommand("strategies", "List anonymization strategies", handler=run_strategies)

    # --- pii-types ---
    cli.add_subcommand("pii-types", "List detectable PII types", handler=run_pii_types,
                       aliases=["types"])


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the TextAnonymizer CLI.

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
        argv: Command-line arguments (e.g. ``["anonymize", "text with PII"]``).

    Returns:
        CLIResult with exit_code, data, stats, and optional error.

    Example Usage::

        from shadetriptxt.text_anonymizer.cli import run_api
        result = run_api(["detect", "DNI: 12345678Z", "--locale", "es_ES"])
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
