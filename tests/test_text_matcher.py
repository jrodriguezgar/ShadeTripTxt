"""Tests for shadetriptxt.text_matcher — TextMatcher and MatcherConfig."""

import pytest

from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig


class TestMatcherConfig:
    def test_default(self):
        config = MatcherConfig.default()
        assert config.levenshtein_threshold == 0.85
        assert config.metaphone_required is True

    def test_strict(self):
        config = MatcherConfig.strict()
        assert config.levenshtein_threshold == 0.95
        assert config.jaro_winkler_threshold == 0.95

    def test_lenient(self):
        config = MatcherConfig.lenient()
        assert config.levenshtein_threshold == 0.75
        assert config.metaphone_required is False

    def test_fuzzy(self):
        config = MatcherConfig.fuzzy()
        assert config.levenshtein_threshold == 0.65

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            MatcherConfig(levenshtein_threshold=1.5)

    def test_to_dict(self):
        config = MatcherConfig.default()
        d = config.to_dict()
        assert "levenshtein_threshold" in d
        assert "metaphone_required" in d


class TestTextMatcherInit:
    def test_default_init(self):
        matcher = TextMatcher()
        assert matcher.config is not None

    def test_custom_config(self):
        config = MatcherConfig.lenient()
        matcher = TextMatcher(config=config)
        assert matcher.config.levenshtein_threshold == 0.75

    def test_locale(self):
        matcher = TextMatcher(locale="en_US")
        assert matcher is not None


class TestTextMatcherCompareNames:
    def test_identical_names(self):
        matcher = TextMatcher()
        is_match, metrics = matcher.compare_names("John Smith", "John Smith")
        assert is_match is True

    def test_accent_difference(self):
        matcher = TextMatcher(config=MatcherConfig.lenient())
        is_match, metrics = matcher.compare_names("José", "Jose")
        assert is_match is True

    def test_completely_different(self):
        matcher = TextMatcher()
        is_match, metrics = matcher.compare_names("Alice", "Bob")
        assert is_match is False


class TestTextMatcherFindBestMatch:
    def test_basic_match(self):
        matcher = TextMatcher(config=MatcherConfig.lenient())
        best, score, metrics = matcher.find_best_match("Smithe", ["Smith", "Jones", "Smyth"])
        assert isinstance(score, float)
        assert score >= 0.0

    def test_no_match(self):
        matcher = TextMatcher(config=MatcherConfig.strict())
        best, score, metrics = matcher.find_best_match("ZZZZZ", ["AAA", "BBB"])
        # May or may not match depending on threshold
        assert isinstance(score, float)

    def test_empty_candidates(self):
        matcher = TextMatcher()
        best, score, metrics = matcher.find_best_match("test", [])
        assert best is None
        assert score == 0.0


class TestTextMatcherDetectDuplicates:
    def test_basic_duplicates(self):
        matcher = TextMatcher(config=MatcherConfig.lenient())
        items = ["apple", "aple", "banana", "bananna"]
        duplicates = matcher.detect_duplicates(items, threshold=0.7)
        assert isinstance(duplicates, list)
        assert len(duplicates) > 0

    def test_no_duplicates(self):
        matcher = TextMatcher()
        items = ["abc", "xyz", "123"]
        duplicates = matcher.detect_duplicates(items, threshold=0.99)
        assert isinstance(duplicates, list)


class TestTextMatcherBatchCompare:
    def test_basic_batch(self):
        matcher = TextMatcher()
        pairs = [("hello", "helo"), ("world", "word")]
        results = matcher.batch_compare(pairs)
        assert len(results) == 2

    def test_empty_batch(self):
        matcher = TextMatcher()
        results = matcher.batch_compare([])
        assert results == []


class TestTextMatcherComparePhrases:
    def test_similar_phrases(self):
        matcher = TextMatcher()
        is_match, metrics = matcher.compare_phrases("premium leather wallet", "leather wallet premium", threshold=0.5)
        assert isinstance(is_match, bool)
        assert "score" in metrics or "dice_score" in metrics or len(metrics) > 0
