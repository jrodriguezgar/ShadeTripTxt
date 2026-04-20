"""
Configuration Module for TextMatcher CLI

Multi-source configuration with priority resolution.

Priority Order (highest to lowest):
    1. Command-line arguments
    2. Environment variables (TEXTMATCHER_*)
    3. Configuration files (JSON, YAML, TOML)
    4. Default values

Usage:
    from shadetriptxt.text_matcher.config import Config, load_config

    # Quick setup
    config = load_config(filepath='config.json')

    # Full control with method chaining
    config = Config(defaults={'locale': 'es_ES', 'preset': 'default'})
    config.load_file('config.json').load_env(prefix='TEXTMATCHER_')

    # Access values
    locale = config.get('locale')
    threshold = config.get('levenshtein_threshold', type=float)

    # Dictionary-style access
    value = config['preset']
    config['preset'] = 'lenient'

    # Validation with schema
    schema = ConfigSchema()
    schema.add_field('locale', type=str, required=True,
                     choices=['es_ES', 'en_US', 'en_GB', 'pt_BR', 'pt_PT',
                              'fr_FR', 'de_DE', 'it_IT', 'es_MX', 'es_AR',
                              'es_CO', 'es_CL'])
    schema.add_field('levenshtein_threshold', type=float, min_value=0.0, max_value=1.0)

    config = Config(schema=schema)
    config.load_file('config.json')
    config.validate()
"""

from __future__ import annotations

import os
import json
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Type
from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "Config",
    "ConfigSchema",
    "ConfigValue",
    "ConfigSource",
    "ConfigFormat",
    "load_config",
    "create_sample_config",
]

T = TypeVar("T")

# Config file names to search (priority order)
STANDARD_CONFIG_NAMES = [
    "textmatcher_config.json",
    "textmatcher_config.yaml",
    "textmatcher_config.yml",
    "textmatcher_config.toml",
    "config.json",
    "config.yaml",
    "config.yml",
    "config.toml",
]

ENV_PREFIX = "TEXTMATCHER_"


class ConfigSource(Enum):
    """Sources for configuration values."""

    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    ARGUMENT = "argument"


class ConfigFormat(Enum):
    """Supported configuration file formats."""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class ConfigValue:
    """Configuration value with source metadata."""

    value: Any
    source: ConfigSource = ConfigSource.DEFAULT
    key: str = ""


@dataclass
class ConfigSchema:
    """Schema for configuration validation.

    Example:
        schema = ConfigSchema()
        schema.add_field('locale', type=str, required=True)
        schema.add_field('levenshtein_threshold', type=float, min_value=0.0, max_value=1.0)
    """

    @dataclass
    class Field:
        name: str
        type: Type = str
        required: bool = False
        default: Any = None
        choices: List[Any] = field(default_factory=list)
        min_value: Optional[float] = None
        max_value: Optional[float] = None

        def validate(self, value: Any) -> tuple[bool, Optional[str]]:
            if value is None:
                if self.required:
                    return False, f"Required field '{self.name}' is missing"
                return True, None
            if self.choices and value not in self.choices:
                return False, f"Field '{self.name}' must be one of: {self.choices}"
            if isinstance(value, (int, float)):
                if self.min_value is not None and value < self.min_value:
                    return False, f"Field '{self.name}' must be >= {self.min_value}"
                if self.max_value is not None and value > self.max_value:
                    return False, f"Field '{self.name}' must be <= {self.max_value}"
            return True, None

    fields: List[Field] = field(default_factory=list)

    def add_field(self, name: str, **kwargs: Any) -> ConfigSchema:
        """Add a field to the schema. Returns self for chaining."""
        self.fields.append(ConfigSchema.Field(name=name, **kwargs))
        return self

    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate config dict against schema. Returns (is_valid, errors)."""
        errors: List[str] = []
        for field_def in self.fields:
            value = config.get(field_def.name, field_def.default)
            is_valid, error = field_def.validate(value)
            if not is_valid and error:
                errors.append(error)
        return len(errors) == 0, errors


class Config:
    """Unified configuration manager for TextMatcher CLI.

    Example:
        config = Config(defaults={'locale': 'es_ES', 'preset': 'default'})
        config.load_file('config.json').load_env(prefix='TEXTMATCHER_')

        locale = config.get('locale')
        threshold = config.get('levenshtein_threshold', type=float)
    """

    def __init__(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        schema: Optional[ConfigSchema] = None,
        auto_discover: bool = False,
    ):
        self.schema = schema

        self._defaults: Dict[str, ConfigValue] = {}
        self._file_values: Dict[str, ConfigValue] = {}
        self._env_values: Dict[str, ConfigValue] = {}
        self._arg_values: Dict[str, ConfigValue] = {}

        if defaults:
            for key, value in defaults.items():
                self._defaults[key] = ConfigValue(
                    value=value,
                    source=ConfigSource.DEFAULT,
                    key=key,
                )

        if auto_discover:
            self._auto_discover()

    def _auto_discover(self) -> None:
        for config_name in STANDARD_CONFIG_NAMES:
            config_file = Path.cwd() / config_name
            if config_file.exists():
                self.load_file(str(config_file))
                return

    def load_file(self, filepath: str, format: Optional[ConfigFormat] = None) -> Config:
        """Load configuration from file. Returns self for chaining."""
        path = Path(filepath)
        if not path.exists():
            return self

        if format is None:
            ext = path.suffix.lower()
            format = {
                ".json": ConfigFormat.JSON,
                ".yaml": ConfigFormat.YAML,
                ".yml": ConfigFormat.YAML,
                ".toml": ConfigFormat.TOML,
            }.get(ext, ConfigFormat.JSON)

        try:
            with open(path, "r", encoding="utf-8") as f:
                if format == ConfigFormat.JSON:
                    data = json.load(f)
                elif format == ConfigFormat.YAML:
                    import yaml

                    data = yaml.safe_load(f)
                elif format == ConfigFormat.TOML:
                    try:
                        import tomllib
                    except ImportError:
                        import tomli as tomllib  # type: ignore[no-redef]
                    data = tomllib.loads(f.read())
                else:
                    data = json.load(f)

            self._flatten_and_store(data, self._file_values, ConfigSource.FILE)
        except Exception:
            pass

        return self

    def _flatten_and_store(
        self,
        data: Dict[str, Any],
        storage: Dict[str, ConfigValue],
        source: ConfigSource,
        prefix: str = "",
    ) -> None:
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_and_store(value, storage, source, full_key)
            else:
                storage[full_key] = ConfigValue(value=value, source=source, key=full_key)

    def load_env(self, prefix: str = ENV_PREFIX) -> Config:
        """Load configuration from environment variables. Returns self for chaining.

        Mapping: TEXTMATCHER_KEY -> key, TEXTMATCHER_NESTED__KEY -> nested.key
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].replace("__", ".").lower()
                parsed_value = self._parse_env_value(value)
                self._env_values[config_key] = ConfigValue(
                    value=parsed_value,
                    source=ConfigSource.ENVIRONMENT,
                    key=config_key,
                )
        return self

    def _parse_env_value(self, value: str) -> Any:
        if value.lower() in ("true", "false", "yes", "no"):
            return value.lower() in ("true", "yes")
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if value.startswith(("[", "{")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value

    def load_args(self, args: Union[Dict[str, Any], object]) -> Config:
        """Load configuration from parsed arguments. Returns self for chaining."""
        if hasattr(args, "__dict__"):
            args = vars(args)
        for key, value in args.items():  # type: ignore[union-attr]
            if value is not None:
                self._arg_values[key] = ConfigValue(
                    value=value,
                    source=ConfigSource.ARGUMENT,
                    key=key,
                )
        return self

    def get(self, key: str, default: Any = None, type: Optional[Type[T]] = None) -> Any:
        """Get configuration value using priority resolution.

        Priority: Arguments > Environment > File > Default
        """
        sources = [self._arg_values, self._env_values, self._file_values, self._defaults]

        for source in sources:
            if key in source:
                value = source[key].value
                if type is not None:
                    try:
                        return type(value)
                    except (ValueError, TypeError):
                        pass
                return value
        return default

    def set(self, key: str, value: Any) -> Config:
        """Set a configuration value (highest priority). Returns self for chaining."""
        self._arg_values[key] = ConfigValue(
            value=value,
            source=ConfigSource.ARGUMENT,
            key=key,
        )
        return self

    def require(self, key: str, message: Optional[str] = None) -> Any:
        """Get required value, raising ValueError if not found."""
        value = self.get(key)
        if value is None:
            raise ValueError(message or f"Required config '{key}' not found")
        return value

    def all(self) -> Dict[str, Any]:
        """Get all configuration values as dictionary."""
        result: Dict[str, Any] = {}
        for source in [self._defaults, self._file_values, self._env_values, self._arg_values]:
            for key, cv in source.items():
                result[key] = cv.value
        return result

    def validate(self, raise_on_error: bool = True) -> tuple[bool, List[str]]:
        """Validate configuration against schema."""
        if not self.schema:
            return True, []
        is_valid, errors = self.schema.validate(self.all())
        if not is_valid and raise_on_error:
            raise ValueError(
                "Validation failed:\n" + "\n".join(f"  - {e}" for e in errors),
            )
        return is_valid, errors

    def copy(self) -> Config:
        """Create a deep copy of this configuration."""
        new = Config(schema=self.schema, auto_discover=False)
        new._defaults = copy.deepcopy(self._defaults)
        new._file_values = copy.deepcopy(self._file_values)
        new._env_values = copy.deepcopy(self._env_values)
        new._arg_values = copy.deepcopy(self._arg_values)
        return new

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __repr__(self) -> str:
        return f"Config(keys={len(self.all())})"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def load_config(
    filepath: Optional[str] = None,
    defaults: Optional[Dict[str, Any]] = None,
    env_prefix: str = ENV_PREFIX,
) -> Config:
    """Convenience function to create and load configuration.

    Args:
        filepath: Path to config file (optional).
        defaults: Default values dictionary.
        env_prefix: Environment variable prefix (default: 'TEXTMATCHER_').

    Example:
        config = load_config(filepath='textmatcher_config.json')
    """
    if defaults is None:
        defaults = {
            "locale": "es_ES",
            "preset": "default",
            "levenshtein_threshold": 0.85,
            "jaro_winkler_threshold": 0.9,
            "metaphone_required": True,
            "ignore_case": True,
            "normalize_whitespace": True,
            "normalize_punctuation": True,
            "normalize_parentheses": False,
            "remove_accents": False,
            "debug_mode": False,
            "enable_cache": True,
            "cache_size": 1024,
            "threshold": 0.85,
            "use_blocking": True,
            "parallel": False,
        }
    config = Config(defaults=defaults, auto_discover=False)
    if filepath:
        config.load_file(filepath)
    config.load_env(prefix=env_prefix)
    return config


def create_sample_config(filepath: str = "textmatcher_config.json") -> bool:
    """Create a sample TextMatcher configuration file.

    Args:
        filepath: Output file path (default: 'textmatcher_config.json').
    """
    sample = {
        "matcher": {
            "locale": "es_ES",
            "preset": "default",
            "levenshtein_threshold": 0.85,
            "jaro_winkler_threshold": 0.9,
            "metaphone_required": True,
        },
        "normalization": {
            "ignore_case": True,
            "normalize_whitespace": True,
            "normalize_punctuation": True,
            "normalize_parentheses": False,
            "remove_accents": False,
        },
        "performance": {
            "enable_cache": True,
            "cache_size": 1024,
            "use_blocking": True,
            "parallel": False,
        },
        "comparison": {
            "threshold": 0.85,
            "debug_mode": False,
        },
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
