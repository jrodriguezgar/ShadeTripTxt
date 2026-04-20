"""
Text Matcher — fuzzy string comparison and phonetic matching.

Compare words, names, and texts using multiple algorithms with
locale-aware normalization across 12 locales.

Quick start::

    from shadetriptxt.text_matcher import TextMatcher

    matcher = TextMatcher(locale="es_ES")
    is_match, metrics = matcher.compare("José", "Jose")
    print(is_match, metrics["score"])
"""

from .text_matcher import TextMatcher, MatcherConfig
from .match_result import MatchResult
from .algorithm_selector import AlgorithmSelector, UseCase

from .config import (
    Config,
    ConfigSchema,
    ConfigValue,
    ConfigSource,
    ConfigFormat,
    load_config,
    create_sample_config,
)
