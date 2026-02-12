"""
Configuration Module for TextDummy CLI

Multi-source configuration with priority resolution.

Priority Order (highest to lowest):
    1. Command-line arguments
    2. Environment variables (TEXTDUMMY_*)
    3. Configuration files (JSON, YAML, TOML)
    4. Default values

Usage:
    from shadetriptxt.text_dummy.config import Config, load_config

    # Quick setup
    config = load_config(filepath='config.json')

    # Full control with method chaining
    config = Config(defaults={'locale': 'es_ES', 'count': 10})
    config.load_file('config.json').load_env(prefix='TEXTDUMMY_')

    # Access values
    locale = config.get('locale')
    count = config.get('count', type=int)

    # Dictionary-style access
    value = config['locale']
    config['locale'] = 'en_US'

    # Validation with schema
    schema = ConfigSchema()
    schema.add_field('locale', type=str, required=True,
                     choices=['es_ES', 'en_US', 'en_GB', 'pt_BR', 'pt_PT',
                              'fr_FR', 'de_DE', 'it_IT', 'es_MX', 'es_AR',
                              'es_CO', 'es_CL'])
    schema.add_field('count', type=int, min_value=1, max_value=1000000)

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
    "textdummy_config.json",
    "textdummy_config.yaml",
    "textdummy_config.yml",
    "textdummy_config.toml",
    "config.json",
    "config.yaml",
    "config.yml",
    "config.toml",
]

ENV_PREFIX = "TEXTDUMMY_"


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
        schema.add_field('count', type=int, min_value=1, max_value=1000000)
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
    """Unified configuration manager for TextDummy CLI.

    Example:
        config = Config(defaults={'locale': 'es_ES', 'count': 10})
        config.load_file('config.json').load_env(prefix='TEXTDUMMY_')

        locale = config.get('locale')
        count = config.get('count', type=int)
    """

    def __init__(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        schema: Optional[ConfigSchema] = None,
        auto_discover: bool = False,
    ):
        """Initialize configuration manager.

        Args:
            defaults: Default values dictionary.
            schema: Optional schema for validation.
            auto_discover: Whether to search for config files in cwd.
        """
        self.schema = schema

        self._defaults: Dict[str, ConfigValue] = {}
        self._file_values: Dict[str, ConfigValue] = {}
        self._env_values: Dict[str, ConfigValue] = {}
        self._arg_values: Dict[str, ConfigValue] = {}

        if defaults:
            for key, value in defaults.items():
                self._defaults[key] = ConfigValue(
                    value=value, source=ConfigSource.DEFAULT, key=key,
                )

        if auto_discover:
            self._auto_discover()

    def _auto_discover(self) -> None:
        """Search for config files in current directory."""
        for config_name in STANDARD_CONFIG_NAMES:
            config_file = Path.cwd() / config_name
            if config_file.exists():
                self.load_file(str(config_file))
                return

    def load_file(self, filepath: str, format: Optional[ConfigFormat] = None) -> Config:
        """Load configuration from file. Returns self for chaining.

        Args:
            filepath: Path to configuration file.
            format: File format (auto-detected from extension if not specified).
        """
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
        """Flatten nested dictionary and store as ConfigValues."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._flatten_and_store(value, storage, source, full_key)
            else:
                storage[full_key] = ConfigValue(value=value, source=source, key=full_key)

    def load_env(self, prefix: str = ENV_PREFIX) -> Config:
        """Load configuration from environment variables. Returns self for chaining.

        Mapping: TEXTDUMMY_KEY -> key, TEXTDUMMY_NESTED__KEY -> nested.key

        Args:
            prefix: Environment variable prefix (default: 'TEXTDUMMY_').
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].replace("__", ".").lower()
                parsed_value = self._parse_env_value(value)
                self._env_values[config_key] = ConfigValue(
                    value=parsed_value, source=ConfigSource.ENVIRONMENT, key=config_key,
                )
        return self

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value, detecting type."""
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
        """Load configuration from parsed arguments. Returns self for chaining.

        Args:
            args: Dictionary or argparse.Namespace with argument values.
        """
        if hasattr(args, "__dict__"):
            args = vars(args)
        for key, value in args.items():  # type: ignore[union-attr]
            if value is not None:
                self._arg_values[key] = ConfigValue(
                    value=value, source=ConfigSource.ARGUMENT, key=key,
                )
        return self

    def get(self, key: str, default: Any = None, type: Optional[Type[T]] = None) -> Any:
        """Get configuration value using priority resolution.

        Priority: Arguments > Environment > File > Default

        Args:
            key: Configuration key (use dot notation for nested: 'generator.locale').
            default: Default value if not found.
            type: Type to coerce value to (e.g., int, bool).
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
            value=value, source=ConfigSource.ARGUMENT, key=key,
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
        """Validate configuration against schema.

        Args:
            raise_on_error: If True, raises ValueError on validation failure.

        Returns:
            Tuple of (is_valid, list of error messages).
        """
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
        env_prefix: Environment variable prefix (default: 'TEXTDUMMY_').

    Example:
        config = load_config(filepath='config.json', env_prefix='TEXTDUMMY_')
    """
    if defaults is None:
        defaults = {
            "locale": "es_ES",
            "count": 10,
            "delimiter": ",",
            "encoding": "utf-8",
            "number_type": "integer",
            "digits": 6,
            "decimals": 2,
            "key_length": 8,
            "key_type": "alphanumeric",
        }
    config = Config(defaults=defaults, auto_discover=False)
    if filepath:
        config.load_file(filepath)
    config.load_env(prefix=env_prefix)
    return config


def create_sample_config(filepath: str = "textdummy_config.json") -> bool:
    """Create a sample TextDummy configuration file.

    Args:
        filepath: Output file path (default: 'textdummy_config.json').
    """
    sample = {
        "generator": {
            "locale": "es_ES",
            "count": 10,
        },
        "batch": {
            "delimiter": ",",
            "encoding": "utf-8",
        },
        "number": {
            "type": "integer",
            "digits": 6,
            "decimals": 2,
            "currency": False,
        },
        "date": {
            "start": "1970-01-01",
            "end": None,
            "pattern": None,
        },
        "key": {
            "length": 8,
            "type": "alphanumeric",
            "prefix": "",
            "separator": "",
            "segment_length": 0,
        },
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sample, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
