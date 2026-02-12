"""
cli.py - Command Line Interface for TextMatcher

Fuzzy text comparison, name matching, duplicate detection, phonetic
analysis, and best-match search from the command line.

Usage:
    python -m shadetriptxt.text_matcher.cli --help
    python -m shadetriptxt.text_matcher.cli compare "José" "Jose" --locale es_ES
    python -m shadetriptxt.text_matcher.cli compare-names "Juan Fco García" "Juan Francisco Garcia"
    python -m shadetriptxt.text_matcher.cli find-match "Smithe" --candidates "Smith,Smyth,Jones"
    python -m shadetriptxt.text_matcher.cli duplicates --input names.txt --threshold 0.85
    python -m shadetriptxt.text_matcher.cli @params.txt

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
    cprint(f"✓ {message}", Colors.SUCCESS)


def print_error(message: str, file=sys.stderr) -> None:
    cprint(f"✗ {message}", Colors.ERROR, file=file)


def print_warning(message: str) -> None:
    cprint(f"⚠ {message}", Colors.WARNING)


def print_info(message: str) -> None:
    cprint(f"ℹ {message}", Colors.INFO)


def print_header(title: str, width: int = 70, char: str = "=") -> None:
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
    current: int, total: int, prefix: str = "", suffix: str = "", width: int = 40,
) -> None:
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
    prog_name: str = "textmatcher"
    version: str = "0.1.0"
    description: str = "Fuzzy text comparison, name matching, and duplicate detection"
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
    name: str
    help: str
    handler: Optional[Callable[[argparse.Namespace, "CLIBase"], None]] = None
    aliases: List[str] = field(default_factory=list)
    parser: Optional[argparse.ArgumentParser] = None


# ============================================================================
# CLI BASE CLASS
# ============================================================================

class CLIBase:
    """Base class for the TextMatcher CLI application."""

    def __init__(
        self,
        prog: str = "textmatcher",
        description: str = "Fuzzy text comparison, name matching, and duplicate detection",
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

    def init_subcommands(
        self, title: str = "Commands", dest: str = "command",
    ) -> argparse._SubParsersAction:
        self._subparsers = self.parser.add_subparsers(
            title=title, dest=dest, help="Available commands",
        )
        return self._subparsers

    def add_subcommand(
        self, name: str, help_text: str,
        handler: Optional[Callable[[argparse.Namespace, "CLIBase"], None]] = None,
        aliases: Optional[List[str]] = None,
    ) -> argparse.ArgumentParser:
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

    def _add_global_arguments_to_subparser(self, subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
        subparser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
        subparser.add_argument("--no-color", action="store_true", help="Disable colors")
        subparser.add_argument("--dry-run", action="store_true", help="Simulate only")
        subparser.add_argument(
            "--output-format", choices=["table", "json", "csv", "summary", "quiet"],
            default="summary", help="Output format (default: summary)",
        )
        subparser.add_argument("--log-file", help="Write logs to file")
        subparser.add_argument("--config-file", help="Load settings from JSON config file")
        subparser.add_argument(
            "--ci", action="store_true",
            help="CI mode: disable colors, force JSON output, use exit codes",
        )

    def set_handler(self, command: str, handler: Callable) -> None:
        if command in self._subcommands:
            self._subcommands[command].handler = handler

    def run(self) -> None:
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

    def _add_global_arguments(self) -> None:
        self.parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
        self.parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
        self.parser.add_argument("--no-color", action="store_true", help="Disable colors")
        self.parser.add_argument("--dry-run", action="store_true", help="Simulate only")
        self.parser.add_argument(
            "--output-format", choices=["table", "json", "csv", "summary", "quiet"],
            default="summary", help="Output format (default: summary)",
        )
        self.parser.add_argument("--log-file", help="Write logs to file")
        self.parser.add_argument("--config-file", help="Load settings from JSON config file")
        self.parser.add_argument(
            "--ci", action="store_true",
            help="CI mode: disable colors, force JSON output, use exit codes",
        )

    def add_group(self, name: str, title: Optional[str] = None, description: Optional[str] = None) -> argparse._ArgumentGroup:
        group = self.parser.add_argument_group(title or name, description)
        self._groups[name] = group
        return group

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        self.start_time = datetime.now()
        self.args = self.parser.parse_args(args)
        self._post_process_args()
        return self.args

    def _post_process_args(self) -> None:
        if self.args is None:
            return
        if getattr(self.args, "ci", False):
            Colors.disable()
            self.args.output_format = "json"
            self.args.quiet = True
        elif getattr(self.args, "no_color", False):
            Colors.disable()
        self._configure_logging()

    def _configure_logging(self) -> None:
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

    def increment_stat(self, name: str, value: int = 1) -> None:
        self._stats[name] = self._stats.get(name, 0) + value

    def print_final_summary(self) -> None:
        if self._stats:
            print_summary(self._stats, title="RESULTS")

    def get_elapsed_time(self) -> str:
        if not self.start_time:
            return "N/A"
        delta = datetime.now() - self.start_time
        return str(delta).split(".")[0]

    def exit_success(self, message: str = "Done") -> None:
        print_success(message)
        sys.exit(0)

    def exit_with_error(self, message: str, code: int = 1) -> None:
        print_error(message)
        sys.exit(code)

    def add_examples(self, examples: List[str]) -> None:
        lines = ["\nExamples:"] + [f"  {e}" for e in examples]
        existing = self.parser.epilog or ""
        self.parser.epilog = existing + "\n".join(lines)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_cli(
    prog: str = "textmatcher",
    description: str = "Fuzzy text comparison, name matching, and duplicate detection",
    version: str = "0.1.0",
) -> CLIBase:
    return CLIBase(prog=prog, description=description, version=version)


# ============================================================================
# HELPERS
# ============================================================================

SUPPORTED_LOCALES = [
    "es_ES", "es_MX", "es_AR", "es_CO", "es_CL",
    "en_US", "en_GB",
    "pt_BR", "pt_PT",
    "fr_FR", "de_DE", "it_IT",
]

PRESET_CHOICES = ["strict", "default", "lenient", "fuzzy"]


def _build_matcher(args: argparse.Namespace):
    """Create a TextMatcher from parsed CLI arguments."""
    from .text_matcher import TextMatcher, MatcherConfig

    preset = getattr(args, "preset", "default")
    config_factory = {
        "strict": MatcherConfig.strict,
        "default": MatcherConfig.default,
        "lenient": MatcherConfig.lenient,
        "fuzzy": MatcherConfig.fuzzy,
    }
    config = config_factory[preset]()

    # Override specific thresholds if provided
    lev = getattr(args, "levenshtein", None)
    if lev is not None:
        config.levenshtein_threshold = lev
    jw = getattr(args, "jaro_winkler", None)
    if jw is not None:
        config.jaro_winkler_threshold = jw
    mp = getattr(args, "metaphone", None)
    if mp is not None:
        config.metaphone_required = mp
    if getattr(args, "debug", False):
        config.debug_mode = True

    locale = getattr(args, "locale", None)
    return TextMatcher(config=config, locale=locale)


def _add_matcher_args(subparser: argparse.ArgumentParser) -> None:
    """Add common matcher arguments to a subparser."""
    subparser.add_argument("--locale", "-l", default="es_ES", choices=SUPPORTED_LOCALES, help="Locale (default: es_ES)")
    subparser.add_argument("--preset", "-p", default="default", choices=PRESET_CHOICES, help="Config preset (default: default)")
    subparser.add_argument("--levenshtein", type=float, help="Levenshtein threshold override (0.0-1.0)")
    subparser.add_argument("--jaro-winkler", type=float, dest="jaro_winkler", help="Jaro-Winkler threshold override (0.0-1.0)")
    subparser.add_argument("--metaphone", type=_str_to_bool, help="Require metaphone match (true/false)")
    subparser.add_argument("--debug", action="store_true", help="Enable debug mode with detailed explanations")


def _str_to_bool(v: str) -> bool:
    if v.lower() in ("true", "yes", "1", "si"):
        return True
    if v.lower() in ("false", "no", "0"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{v}'")


def _write_output(result: Any, args: argparse.Namespace) -> None:
    """Write result to stdout or file."""
    output_file = getattr(args, "output", None)
    fmt = getattr(args, "output_format", "summary")

    if fmt == "json":
        text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
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


def _format_match_result(is_match: bool, metrics: Dict[str, Any], debug: bool = False) -> str:
    """Format a comparison result for display."""
    status = f"{Colors.GREEN}MATCH{Colors.RESET}" if is_match else f"{Colors.RED}NO MATCH{Colors.RESET}"
    lev = metrics.get("levenshtein_ratio", 0.0)
    jw = metrics.get("jaro_winkler_score", 0.0)
    meta = metrics.get("metaphone_match", False)

    lines = [
        f"Result: {status}",
        f"  Levenshtein ratio : {lev:.4f}",
        f"  Jaro-Winkler score: {jw:.1f}",
        f"  Metaphone match   : {meta}",
    ]

    if debug and "debug_info" in metrics:
        di = metrics["debug_info"]
        lines.append(f"  Decision          : {di.get('match_decision', '')}")
        for reason in di.get("reasons", []):
            lines.append(f"    {reason}")
        lines.append(f"  Summary           : {di.get('summary', '')}")

    return "\n".join(lines)


# ============================================================================
# SUBCOMMAND HANDLERS
# ============================================================================

def run_compare(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: compare two single words/names."""
    matcher = _build_matcher(args)
    is_match, metrics = matcher.compare_names(
        args.text1, args.text2, strict=args.strict,
    )

    result = {"match": is_match, "metrics": metrics}
    cli.last_result = result
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(result, args)
    else:
        print(_format_match_result(is_match, metrics, debug=args.debug))
    cli.increment_stat("comparisons", 1)


def run_compare_names(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: compare multi-word full names."""
    matcher = _build_matcher(args)
    threshold = getattr(args, "threshold", 0.9)
    keep_order = not getattr(args, "no_order", False)
    fuzzy_align = getattr(args, "fuzzy_align", False)

    is_match, metrics = matcher.compare_name_bytokens(
        args.text1, args.text2,
        threshold=threshold,
        keep_order=keep_order,
        fuzzy_align=fuzzy_align,
    )

    result = {"match": is_match, "metrics": metrics}
    cli.last_result = result
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output({"match": is_match, "metrics": metrics}, args)
    else:
        status = f"{Colors.GREEN}MATCH{Colors.RESET}" if is_match else f"{Colors.RED}NO MATCH{Colors.RESET}"
        rule = metrics.get("rule_applied", "none")
        coincidences = metrics.get("min_coincidences", 0)
        print(f"Result: {status}")
        print(f"  Tokens name1    : {metrics.get('words_name1', [])}")
        print(f"  Tokens name2    : {metrics.get('words_name2', [])}")
        print(f"  Coincidences    : {coincidences}")
        print(f"  Rule applied    : {rule}")
        if metrics.get("word_pair_comparisons"):
            print(f"  Word pairs:")
            for wp in metrics["word_pair_comparisons"]:
                mark = "✓" if wp["match"] else "✗"
                print(f"    {mark} '{wp['word1']}' vs '{wp['word2']}'")
    cli.increment_stat("comparisons", 1)


def run_compare_text(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: compare two phrases/sentences."""
    matcher = _build_matcher(args)
    threshold = getattr(args, "threshold", 0.8)

    is_match, metrics = matcher.compare_phrases(
        args.text1, args.text2, threshold=threshold,
    )

    result = {"match": is_match, "metrics": metrics}
    cli.last_result = result
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(result, args)
    else:
        status = f"{Colors.GREEN}MATCH{Colors.RESET}" if is_match else f"{Colors.RED}NO MATCH{Colors.RESET}"
        print(f"Result: {status}")
        print(f"  Similarity: {metrics.get('similarity', 0):.4f} ({metrics.get('score', 0):.1f}%)")
        print(f"  Common words    : {', '.join(metrics.get('common_words', []))}")
        print(f"  Unique to text1 : {', '.join(metrics.get('unique_to_phrase1', []))}")
        print(f"  Unique to text2 : {', '.join(metrics.get('unique_to_phrase2', []))}")
    cli.increment_stat("comparisons", 1)


def run_find_match(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: find best match from candidates."""
    matcher = _build_matcher(args)
    threshold = getattr(args, "threshold", 0.85)

    candidates = _parse_candidates(args)
    if not candidates:
        print_error("No candidates provided. Use --candidates or --candidates-file.")
        return

    best, score, metrics = matcher.find_best_match(
        args.target, candidates, threshold=threshold,
    )

    result = {"target": args.target, "best_match": best, "score": score, "metrics": metrics}
    cli.last_result = result
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(result, args)
    elif best:
        print_success(f"Best match: '{best}' (score: {score:.4f})")
    else:
        print_warning(f"No match found above threshold {threshold:.2f}")
    cli.increment_stat("comparisons", 1)


def run_find_matches(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: find top-K matches from candidates."""
    matcher = _build_matcher(args)
    threshold = getattr(args, "threshold", 0.7)
    top_k = getattr(args, "top_k", None)

    candidates = _parse_candidates(args)
    if not candidates:
        print_error("No candidates provided. Use --candidates or --candidates-file.")
        return

    results = matcher.compare_lists(
        args.target, candidates, top_k=top_k, threshold=threshold,
    )

    out = [{"candidate": c, "score": s, "metrics": m} for c, s, m in results]
    cli.last_result = out
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(out, args)
    elif results:
        rows = [[i + 1, c, f"{s:.4f}"] for i, (c, s, _) in enumerate(results)]
        print_table(["#", "Candidate", "Score"], rows)
    else:
        print_warning(f"No matches found above threshold {threshold:.2f}")
    cli.increment_stat("comparisons", len(results))


def run_duplicates(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: detect duplicates in a list."""
    matcher = _build_matcher(args)
    threshold = getattr(args, "threshold", 0.85)

    items = _read_items(args)
    if not items:
        print_error("No items provided. Use --items or --input file.")
        return

    if not getattr(args, "quiet", False):
        print_info(f"Analyzing {len(items)} items for duplicates (threshold: {threshold:.2f})...")

    duplicates = matcher.detect_duplicates(
        items, threshold=threshold,
        use_blocking=getattr(args, "blocking", True),
        parallel=getattr(args, "parallel", False),
    )

    out = [{"item1": a, "item2": b, "score": s} for a, b, s in duplicates]
    cli.last_result = out
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(out, args)
    elif duplicates:
        rows = [[a, b, f"{s:.4f}"] for a, b, s in duplicates]
        print_table(["Item 1", "Item 2", "Score"], rows)
        print_info(f"Found {len(duplicates)} duplicate pairs")
    else:
        print_success("No duplicates found")

    cli.increment_stat("items_analyzed", len(items))
    cli.increment_stat("duplicates_found", len(duplicates))


def run_phonetic_dups(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: find phonetic duplicates."""
    matcher = _build_matcher(args)
    threshold = getattr(args, "threshold", 0.8)

    items = _read_items(args)
    if not items:
        print_error("No items provided. Use --items or --input file.")
        return

    groups = matcher.find_phonetic_duplicates(
        items, threshold=threshold,
        use_mra=not getattr(args, "use_metaphone", False),
    )

    cli.last_result = groups
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(groups, args)
    elif groups:
        for i, group in enumerate(groups, 1):
            print(f"  Group {i}: {', '.join(group)}")
        print_info(f"Found {len(groups)} phonetic groups")
    else:
        print_success("No phonetic duplicates found")

    cli.increment_stat("items_analyzed", len(items))
    cli.increment_stat("groups_found", len(groups))


def run_diff(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: detailed text diff."""
    matcher = _build_matcher(args)

    text1 = args.text1
    text2 = args.text2

    # Support reading from files
    if getattr(args, "file1", None):
        with open(args.file1, "r", encoding="utf-8") as f:
            text1 = f.read()
    if getattr(args, "file2", None):
        with open(args.file2, "r", encoding="utf-8") as f:
            text2 = f.read()

    result = matcher.compare_text_detailed(
        text1, text2,
        case_sensitive=getattr(args, "case_sensitive", False),
        show_diff=True,
        context_lines=getattr(args, "context_lines", 3),
    )

    cli.last_result = result
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(result, args)
    else:
        print(f"Similarity: {result['score']:.1f}%")
        print(f"Lines added  : {result['lines_added']}")
        print(f"Lines removed: {result['lines_removed']}")
        print(f"Lines changed: {result['lines_changed']}")
        if result.get("diff"):
            print()
            print(result["diff"])
    cli.increment_stat("comparisons", 1)


def run_diff_code(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: code block comparison."""
    matcher = _build_matcher(args)

    code1 = args.text1
    code2 = args.text2

    if getattr(args, "file1", None):
        with open(args.file1, "r", encoding="utf-8") as f:
            code1 = f.read()
    if getattr(args, "file2", None):
        with open(args.file2, "r", encoding="utf-8") as f:
            code2 = f.read()

    result = matcher.compare_code_blocks(
        code1, code2,
        language=getattr(args, "language", "python"),
        ignore_whitespace=not getattr(args, "keep_whitespace", False),
        ignore_comments=getattr(args, "ignore_comments", False),
    )

    cli.last_result = result
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(result, args)
    else:
        print(f"Structural similarity: {result['structural_similarity']:.1f}%")
        print(f"Original similarity  : {result['original_similarity']:.1f}%")
        print(f"Lines added  : {result['lines_added']}")
        print(f"Lines removed: {result['lines_removed']}")
        print(f"Lines changed: {result['lines_changed']}")
        if result.get("diff"):
            print()
            print(result["diff"])
    cli.increment_stat("comparisons", 1)


def run_normalize(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: normalize text."""
    matcher = _build_matcher(args)
    for_names = getattr(args, "for_names", False)
    case_mode = getattr(args, "case_mode", "upper" if for_names else "lower")

    result = matcher.normalize_text(
        args.text, for_names=for_names, case_mode=case_mode,
    )
    _write_output(result, args)
    cli.increment_stat("normalized", 1)


def run_similarity(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: simple similarity percentage between two strings."""
    from .text_matcher import TextMatcher

    score = TextMatcher.similarity_percentage(args.text1, args.text2)
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output({"text1": args.text1, "text2": args.text2, "similarity": score}, args)
    else:
        print(f"Similarity: {score:.1f}%")
    cli.increment_stat("comparisons", 1)


def run_same_chars(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: check if two strings have the same characters."""
    matcher = _build_matcher(args)
    result = matcher.same_chars(args.text1, args.text2)
    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        similarity = matcher.same_chars_similarity(args.text1, args.text2)
        _write_output({"same_chars": result, "similarity": similarity}, args)
    elif result:
        print_success(f"Same characters: '{args.text1}' ≡ '{args.text2}'")
    else:
        print_error(f"Different characters: '{args.text1}' ≠ '{args.text2}'")
    cli.increment_stat("comparisons", 1)


def run_patterns(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: find common patterns (LCS) between two texts."""
    matcher = _build_matcher(args)
    min_length = getattr(args, "min_length", 3)

    result = matcher.find_common_patterns(
        args.text1, args.text2, min_length=min_length,
    )

    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        _write_output(result, args)
    else:
        print(f"LCS length    : {result['lcs_length']}")
        print(f"LCS ratio     : {result['lcs_ratio']:.4f}")
        print(f"Similarity    : {result['score']:.1f}%")
        overlap = "Yes" if result["has_significant_overlap"] else "No"
        print(f"Significant   : {overlap}")
    cli.increment_stat("comparisons", 1)


def run_algorithm_info(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: show algorithm selection info."""
    from .algorithm_selector import AlgorithmSelector, UseCase

    if getattr(args, "list_all", False):
        use_cases = AlgorithmSelector.get_all_use_cases()
        rows = [
            [uc.value, cfg["primary"], ", ".join(cfg["secondary"]), f"{cfg['speed_gain']:.1f}x"]
            for uc, cfg in use_cases
        ]
        print_table(["Use Case", "Primary", "Secondary", "Speedup"], rows)
        return

    if getattr(args, "text1", None) and getattr(args, "text2", None):
        selector = AlgorithmSelector(auto_detect=True)
        explanation = selector.explain_selection(args.text1, args.text2)
        print(explanation)
        return

    # Default: list use cases
    use_cases = AlgorithmSelector.get_all_use_cases()
    rows = [
        [uc.value, cfg["primary"], f"{cfg['speed_gain']:.1f}x"]
        for uc, cfg in use_cases
    ]
    print_table(["Use Case", "Primary Algorithm", "Speedup"], rows)


def run_batch(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: batch compare pairs from file (CSV: word1,word2 per line)."""
    matcher = _build_matcher(args)

    with open(args.input, "r", encoding=getattr(args, "encoding", "utf-8")) as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    delimiter = getattr(args, "delimiter", ",")
    pairs = []
    for line in raw_lines:
        parts = line.split(delimiter, maxsplit=1)
        if len(parts) == 2:
            pairs.append((parts[0].strip(), parts[1].strip()))

    if not pairs:
        print_error(f"No valid pairs found in {args.input} (expected: word1{delimiter}word2)")
        return

    if not getattr(args, "quiet", False):
        print_info(f"Comparing {len(pairs)} pairs...")

    results = matcher.batch_compare(pairs)

    fmt = getattr(args, "output_format", "summary")
    if fmt == "json":
        out = []
        for (w1, w2), (is_match, metrics) in zip(pairs, results):
            out.append({"word1": w1, "word2": w2, "match": is_match, "metrics": metrics})
        _write_output(out, args)
    else:
        rows = []
        for (w1, w2), (is_match, metrics) in zip(pairs, results):
            lev = metrics.get("levenshtein_ratio", 0.0)
            mark = "✓" if is_match else "✗"
            rows.append([mark, w1, w2, f"{lev:.4f}"])
        print_table(["Match", "Word 1", "Word 2", "Levenshtein"], rows)

    total = len(pairs)
    matches = sum(1 for _, (m, _) in zip(pairs, results) if m)
    cli.increment_stat("pairs_compared", total)
    cli.increment_stat("matches", matches)
    cli.increment_stat("non_matches", total - matches)


def run_presets(args: argparse.Namespace, cli: CLIBase) -> None:
    """Handler: show available config presets."""
    from .text_matcher import MatcherConfig

    presets = {
        "strict": MatcherConfig.strict(),
        "default": MatcherConfig.default(),
        "lenient": MatcherConfig.lenient(),
        "fuzzy": MatcherConfig.fuzzy(),
    }

    rows = []
    for name, cfg in presets.items():
        rows.append([
            name,
            f"{cfg.levenshtein_threshold:.2f}",
            f"{cfg.jaro_winkler_threshold:.2f}",
            str(cfg.metaphone_required),
        ])
    print_table(["Preset", "Levenshtein", "Jaro-Winkler", "Metaphone"], rows)


# ============================================================================
# INPUT HELPERS
# ============================================================================

def _parse_candidates(args: argparse.Namespace) -> List[str]:
    """Parse candidate list from --candidates or --candidates-file."""
    raw = getattr(args, "candidates", None)
    if raw:
        return [c.strip() for c in raw.split(",") if c.strip()]
    cfile = getattr(args, "candidates_file", None)
    if cfile:
        with open(cfile, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


def _read_items(args: argparse.Namespace) -> List[str]:
    """Read items from --items or --input file."""
    raw = getattr(args, "items", None)
    if raw:
        return [i.strip() for i in raw.split(",") if i.strip()]
    input_file = getattr(args, "input", None)
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


# ============================================================================
# MAIN
# ============================================================================

# ============================================================================
# SUBCOMMAND SETUP
# ============================================================================

def _setup_subcommands(cli: CLIBase) -> None:
    """Register all subcommands on a CLIBase instance."""
    cli.init_subcommands()

    # --- compare (single word/name) ---
    p_cmp = cli.add_subcommand("compare", "Compare two single words or names", handler=run_compare, aliases=["cmp"])
    p_cmp.add_argument("text1", help="First word or name")
    p_cmp.add_argument("text2", help="Second word or name")
    p_cmp.add_argument("--output", "-o", help="Write result to file")
    p_cmp.add_argument("--strict", action="store_true", help="Require phonetic match")
    _add_matcher_args(p_cmp)

    # --- compare-names (multi-word full name) ---
    p_cn = cli.add_subcommand("compare-names", "Compare multi-word full names", handler=run_compare_names, aliases=["cn"])
    p_cn.add_argument("text1", help="First full name")
    p_cn.add_argument("text2", help="Second full name")
    p_cn.add_argument("--output", "-o", help="Write result to file")
    p_cn.add_argument("--threshold", "-t", type=float, default=0.9, help="Similarity threshold (default: 0.9)")
    p_cn.add_argument("--no-order", action="store_true", help="Ignore word order")
    p_cn.add_argument("--fuzzy-align", action="store_true", help="Use fuzzy alignment (e.g. ROBERT ≈ ROBERTO)")
    _add_matcher_args(p_cn)

    # --- compare-text (phrases) ---
    p_ct = cli.add_subcommand("compare-text", "Compare two phrases or sentences", handler=run_compare_text, aliases=["ct"])
    p_ct.add_argument("text1", help="First phrase")
    p_ct.add_argument("text2", help="Second phrase")
    p_ct.add_argument("--output", "-o", help="Write result to file")
    p_ct.add_argument("--threshold", "-t", type=float, default=0.8, help="Similarity threshold (default: 0.8)")
    _add_matcher_args(p_ct)

    # --- find-match ---
    p_fm = cli.add_subcommand("find-match", "Find best match from candidates", handler=run_find_match, aliases=["fm"])
    p_fm.add_argument("target", help="Target string to match")
    p_fm.add_argument("--candidates", "-c", help="Comma-separated candidates")
    p_fm.add_argument("--candidates-file", "-cf", help="File with one candidate per line")
    p_fm.add_argument("--output", "-o", help="Write result to file")
    p_fm.add_argument("--threshold", "-t", type=float, default=0.85, help="Minimum threshold (default: 0.85)")
    _add_matcher_args(p_fm)

    # --- find-matches (top-K) ---
    p_fms = cli.add_subcommand("find-matches", "Find top-K matches from candidates", handler=run_find_matches, aliases=["fms"])
    p_fms.add_argument("target", help="Target string to match")
    p_fms.add_argument("--candidates", "-c", help="Comma-separated candidates")
    p_fms.add_argument("--candidates-file", "-cf", help="File with one candidate per line")
    p_fms.add_argument("--output", "-o", help="Write result to file")
    p_fms.add_argument("--threshold", "-t", type=float, default=0.7, help="Minimum threshold (default: 0.7)")
    p_fms.add_argument("--top-k", "-k", type=int, help="Maximum results to return")
    _add_matcher_args(p_fms)

    # --- duplicates ---
    p_dup = cli.add_subcommand("duplicates", "Detect duplicates in a list", handler=run_duplicates, aliases=["dup"])
    p_dup.add_argument("--items", help="Comma-separated items")
    p_dup.add_argument("--input", "-i", help="File with one item per line")
    p_dup.add_argument("--output", "-o", help="Write result to file")
    p_dup.add_argument("--threshold", "-t", type=float, default=0.85, help="Similarity threshold (default: 0.85)")
    p_dup.add_argument("--no-blocking", dest="blocking", action="store_false", help="Disable blocking optimization")
    p_dup.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    _add_matcher_args(p_dup)

    # --- phonetic-dups ---
    p_pd = cli.add_subcommand("phonetic-dups", "Find phonetically similar names", handler=run_phonetic_dups, aliases=["pd"])
    p_pd.add_argument("--items", help="Comma-separated names")
    p_pd.add_argument("--input", "-i", help="File with one name per line")
    p_pd.add_argument("--output", "-o", help="Write result to file")
    p_pd.add_argument("--threshold", "-t", type=float, default=0.8, help="Similarity threshold (default: 0.8)")
    p_pd.add_argument("--use-metaphone", action="store_true", help="Use metaphone instead of MRA")
    _add_matcher_args(p_pd)

    # --- diff ---
    p_diff = cli.add_subcommand("diff", "Detailed text/line diff", handler=run_diff)
    p_diff.add_argument("text1", nargs="?", default="", help="First text")
    p_diff.add_argument("text2", nargs="?", default="", help="Second text")
    p_diff.add_argument("--file1", help="Read first text from file")
    p_diff.add_argument("--file2", help="Read second text from file")
    p_diff.add_argument("--output", "-o", help="Write result to file")
    p_diff.add_argument("--case-sensitive", action="store_true", help="Case-sensitive comparison")
    p_diff.add_argument("--context-lines", type=int, default=3, help="Context lines in diff (default: 3)")
    _add_matcher_args(p_diff)

    # --- diff-code ---
    p_dc = cli.add_subcommand("diff-code", "Compare code blocks", handler=run_diff_code, aliases=["dc"])
    p_dc.add_argument("text1", nargs="?", default="", help="First code snippet")
    p_dc.add_argument("text2", nargs="?", default="", help="Second code snippet")
    p_dc.add_argument("--file1", help="Read first code from file")
    p_dc.add_argument("--file2", help="Read second code from file")
    p_dc.add_argument("--output", "-o", help="Write result to file")
    p_dc.add_argument("--language", default="python", help="Programming language (default: python)")
    p_dc.add_argument("--keep-whitespace", action="store_true", help="Don't ignore whitespace")
    p_dc.add_argument("--ignore-comments", action="store_true", help="Remove comments before comparison")
    _add_matcher_args(p_dc)

    # --- normalize ---
    p_norm = cli.add_subcommand("normalize", "Normalize text for comparison", handler=run_normalize, aliases=["norm"])
    p_norm.add_argument("text", help="Text to normalize")
    p_norm.add_argument("--output", "-o", help="Write result to file")
    p_norm.add_argument("--for-names", action="store_true", help="Name-specific normalization")
    p_norm.add_argument("--case-mode", choices=["upper", "lower", "title", "none"], default=None, help="Case conversion mode")
    _add_matcher_args(p_norm)

    # --- similarity ---
    p_sim = cli.add_subcommand("similarity", "Simple similarity percentage", handler=run_similarity, aliases=["sim"])
    p_sim.add_argument("text1", help="First string")
    p_sim.add_argument("text2", help="Second string")
    p_sim.add_argument("--output", "-o", help="Write result to file")

    # --- same-chars ---
    p_sc = cli.add_subcommand("same-chars", "Check if strings have same characters", handler=run_same_chars, aliases=["sc"])
    p_sc.add_argument("text1", help="First string")
    p_sc.add_argument("text2", help="Second string")
    p_sc.add_argument("--output", "-o", help="Write result to file")
    _add_matcher_args(p_sc)

    # --- patterns ---
    p_pat = cli.add_subcommand("patterns", "Find common patterns (LCS)", handler=run_patterns, aliases=["pat"])
    p_pat.add_argument("text1", help="First text")
    p_pat.add_argument("text2", help="Second text")
    p_pat.add_argument("--output", "-o", help="Write result to file")
    p_pat.add_argument("--min-length", type=int, default=3, help="Minimum subsequence length (default: 3)")
    _add_matcher_args(p_pat)

    # --- algorithm ---
    p_algo = cli.add_subcommand("algorithm", "Show algorithm selection info", handler=run_algorithm_info, aliases=["algo"])
    p_algo.add_argument("text1", nargs="?", help="First text (for auto-detection)")
    p_algo.add_argument("text2", nargs="?", help="Second text (for auto-detection)")
    p_algo.add_argument("--list-all", action="store_true", help="List all use cases and algorithms")

    # --- presets ---
    cli.add_subcommand("presets", "Show available config presets", handler=run_presets)

    # --- batch ---
    p_batch = cli.add_subcommand("batch", "Batch compare pairs from CSV file", handler=run_batch)
    p_batch.add_argument("--input", "-i", required=True, help="CSV file (word1,word2 per line)")
    p_batch.add_argument("--output", "-o", help="Write result to file")
    p_batch.add_argument("--delimiter", "-d", default=",", help="Column delimiter (default: ,)")
    p_batch.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    _add_matcher_args(p_batch)


# ============================================================================
# MAIN
# ============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the TextMatcher CLI.

    Returns:
        Exit code: 0 on success, 1 on user error, 2 on unexpected error.
    """
    Colors.init()
    cli = create_cli()

    cli.add_examples([
        '%(prog)s compare "José" "Jose" --locale es_ES',
        '%(prog)s compare-names "Juan Fco García" "Juan Francisco Garcia"',
        '%(prog)s compare-text "premium leather wallet" "leather wallet premium"',
        '%(prog)s find-match "Smithe" --candidates "Smith,Smyth,Jones"',
        '%(prog)s find-matches "Smithe" --candidates "Smith,Smyth,Jones,Smithson" --top-k 3',
        '%(prog)s duplicates --input names.txt --threshold 0.85',
        '%(prog)s phonetic-dups --input names.txt',
        '%(prog)s diff "The quick brown fox" "The fast brown fox"',
        '%(prog)s batch --input pairs.csv',
        '%(prog)s presets',
    ])

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
    """Programmatic API entry point — run CLI and return structured results.

    Use this function to invoke the CLI from Python code without sys.exit.

    Args:
        argv: Command-line arguments (same as CLI).

    Returns:
        CLIResult with exit_code, data, stats, and error fields.

    Example:
        from shadetriptxt.text_matcher.cli import run_api
        result = run_api(["compare", "José", "Jose", "--locale", "es_ES"])
        if result.ok:
            print(result.data)
    """
    cli = create_cli()
    _setup_subcommands(cli)

    try:
        args = cli.parse_args(argv)
        # Force JSON + quiet for programmatic usage
        args.output_format = "json"
        args.quiet = True
        Colors.disable()

        cli.run()
        return CLIResult(
            exit_code=0,
            data=cli.last_result,
            stats=dict(cli._stats),
        )
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return CLIResult(exit_code=code, error="Argument parsing failed")
    except Exception as exc:
        return CLIResult(exit_code=2, error=str(exc))


if __name__ == "__main__":
    sys.exit(main())
