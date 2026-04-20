"""
cli_base.py - Shared CLI infrastructure for ShadeTripTxt modules.

Provides CLIBase, output utilities, CLIResult, and common dataclasses
used by all module-specific CLI interfaces. Plain-text output only
(Unicode status prefixes, ASCII tables, no ANSI color codes).

Author: DatamanEdge
Version: 0.1.0
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

__all__ = [
    "CLIBase",
    "CLIConfig",
    "CLIResult",
    "OutputFormat",
    "Subcommand",
    "confirm_action",
    "print_error",
    "print_header",
    "print_info",
    "print_progress",
    "print_success",
    "print_summary",
    "print_table",
    "print_warning",
    "write_output",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ============================================================================
# DATACLASSES AND ENUMS
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


@dataclass
class CLIConfig:
    """Configuration for CLI behavior."""

    prog_name: str = "shadetriptxt"
    version: str = "0.1.0"
    description: str = ""
    epilog: str = ""

    default_output_format: OutputFormat = OutputFormat.SUMMARY

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
# OUTPUT UTILITIES — plain text, no ANSI
# ============================================================================


def print_success(message: str) -> None:
    """Print success message with checkmark."""
    print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print error message with X mark."""
    print(f"✗ {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message with warning sign."""
    print(f"⚠ {message}")


def print_info(message: str) -> None:
    """Print info message with info symbol."""
    print(f"ℹ {message}")


def print_header(title: str, width: int = 60) -> None:
    """Print formatted section header."""
    print()
    print("=" * width)
    print(f" {title}")
    print("=" * width)


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

    def _truncate(value: Any, width: int) -> str:
        s = str(value)
        return s[: width - 3] + "..." if len(s) > width else s

    header_row = " | ".join(_truncate(h, w).ljust(w) for h, w in zip(headers, col_widths))
    separator = "-+-".join("-" * w for w in col_widths)

    print(header_row)
    print(separator)

    for row in rows:
        print(" | ".join(_truncate(row[i] if i < len(row) else "", w).ljust(w) for i, w in enumerate(col_widths)))


def print_summary(
    stats: Dict[str, Any],
    title: str = "SUMMARY",
    width: int = 60,
) -> None:
    """Print formatted summary statistics."""
    print()
    print("=" * width)
    print(f" {title}")
    print("=" * width)
    for key, value in stats.items():
        label = key.replace("_", " ").title()
        print(f"  {label + ':':<25} {value}")
    print("=" * width)


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


def write_output(data: Any, args: argparse.Namespace) -> None:
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
        safe_path = os.path.realpath(output_file)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print_success(f"Output written to {safe_path}")
    else:
        print(text)


# ============================================================================
# CLI BASE CLASS
# ============================================================================


class CLIBase:
    """Base class for CLI applications with subcommand support.

    Usage::

        cli = CLIBase(prog="mytool", description="My tool", version="1.0")
        cli.init_subcommands()
        p = cli.add_subcommand("run", "Run something", handler=my_handler)
        p.add_argument("--input", required=True)
        args = cli.parse_args()
        cli.run()
    """

    def __init__(
        self,
        prog: str = "shadetriptxt",
        description: str = "",
        version: str = "0.1.0",
        epilog: str = "",
        config: Optional[CLIConfig] = None,
    ):
        self.config = config or CLIConfig(
            prog_name=prog,
            version=version,
            description=description,
            epilog=epilog,
        )

        self.parser = argparse.ArgumentParser(
            prog=self.config.prog_name,
            description=self.config.description,
            epilog=self.config.epilog or None,
            fromfile_prefix_chars="@" if self.config.allow_parameter_files else None,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self.parser.add_argument(
            "--version",
            "-V",
            action="version",
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
        self,
        title: str = "Commands",
        dest: str = "command",
    ) -> argparse._SubParsersAction:
        """Initialize subcommand support."""
        self._subparsers = self.parser.add_subparsers(
            title=title,
            dest=dest,
            help="Available commands",
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
            name,
            help=help_text,
            aliases=aliases,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._add_global_arguments_to_subparser(subparser)

        subcmd = Subcommand(
            name=name,
            help=help_text,
            handler=handler,
            aliases=aliases,
            parser=subparser,
        )
        self._subcommands[name] = subcmd
        for alias in aliases:
            self._subcommands[alias] = subcmd

        return subparser

    def set_handler(
        self,
        command: str,
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
    # ARGUMENTS
    # -------------------------------------------------------------------

    def _add_global_arguments(self) -> None:
        """Add global arguments available to all CLI tools."""
        self.parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (-v INFO, -vv DEBUG)",
        )
        self.parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
        self.parser.add_argument(
            "--ci",
            action="store_true",
            help="CI mode (JSON output, quiet, exit codes)",
        )
        self.parser.add_argument("--dry-run", action="store_true", help="Simulate only")
        self.parser.add_argument(
            "--output-format",
            choices=["table", "json", "csv", "summary", "quiet"],
            default="summary",
            help="Output format (default: summary)",
        )
        self.parser.add_argument("--log-file", help="Write logs to file")
        self.parser.add_argument(
            "--config-file",
            help="Load settings from JSON config file",
        )

    def _add_global_arguments_to_subparser(
        self,
        subparser: argparse.ArgumentParser,
    ) -> None:
        """Add global options to a subparser."""
        subparser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (-v INFO, -vv DEBUG)",
        )
        subparser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
        subparser.add_argument(
            "--ci",
            action="store_true",
            help="CI mode (JSON output, quiet, exit codes)",
        )
        subparser.add_argument("--dry-run", action="store_true", help="Simulate only")
        subparser.add_argument(
            "--output-format",
            choices=["table", "json", "csv", "summary", "quiet"],
            default="summary",
            help="Output format (default: summary)",
        )
        subparser.add_argument("--log-file", help="Write logs to file")
        subparser.add_argument(
            "--config-file",
            help="Load settings from JSON config file",
        )

    def add_group(
        self,
        name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> argparse._ArgumentGroup:
        """Add a custom argument group."""
        group = self.parser.add_argument_group(title or name, description)
        self._groups[name] = group
        return group

    # -------------------------------------------------------------------
    # PARSING
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
            self.args.output_format = "json"
            self.args.quiet = True
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
