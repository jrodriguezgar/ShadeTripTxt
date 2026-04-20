"""Tests for shadetriptxt.text_parser.text_readability — readability metrics."""

import pytest

from shadetriptxt.text_parser.text_readability import (
    count_syllables,
    flesch_reading_ease,
    flesch_kincaid_grade,
    gunning_fog_index,
    coleman_liau_index,
    automated_readability_index,
    is_gibberish,
    is_placeholder_text,
    text_density_score,
)


# ---------------------------------------------------------------------------
# count_syllables
# ---------------------------------------------------------------------------


class TestCountSyllables:
    def test_empty(self):
        assert count_syllables("") == 0

    def test_monosyllable(self):
        assert count_syllables("the") == 1

    def test_cat(self):
        assert count_syllables("cat") == 1

    def test_beautiful(self):
        assert count_syllables("beautiful") == 3

    def test_example(self):
        assert count_syllables("example") == 3

    def test_programming(self):
        # pro-gram-ming → 3
        assert count_syllables("programming") == 3

    def test_minimum_one(self):
        # Any non-empty word should have at least 1 syllable
        assert count_syllables("a") >= 1

    @pytest.mark.parametrize(
        "word, expected_min",
        [
            ("elephant", 2),
            ("university", 4),
            ("I", 1),
        ],
    )
    def test_varied_words(self, word: str, expected_min: int):
        assert count_syllables(word) >= expected_min


# ---------------------------------------------------------------------------
# flesch_reading_ease
# ---------------------------------------------------------------------------


class TestFleschReadingEase:
    def test_simple_sentence(self):
        score = flesch_reading_ease("The cat sat on the mat.")
        # Very simple sentence → very high score
        assert score > 80.0

    def test_complex_text(self):
        text = (
            "The epistemological ramifications of contemporary "
            "hermeneutical methodologies necessitate a comprehensive "
            "reevaluation of foundational philosophical assumptions."
        )
        score = flesch_reading_ease(text)
        # Complex academic text → lower score
        assert score < 30.0

    def test_empty_text(self):
        assert flesch_reading_ease("") == 0.0

    def test_returns_float(self):
        assert isinstance(flesch_reading_ease("Hello world."), float)

    def test_multiple_sentences(self):
        text = "The sun is bright. The sky is blue. Birds fly."
        score = flesch_reading_ease(text)
        assert score > 60.0


# ---------------------------------------------------------------------------
# flesch_kincaid_grade
# ---------------------------------------------------------------------------


class TestFleschKincaidGrade:
    def test_simple_sentence(self):
        grade = flesch_kincaid_grade("The cat sat on the mat.")
        # Simple → low grade level
        assert grade < 5.0

    def test_complex_text(self):
        text = (
            "The epistemological ramifications of contemporary "
            "hermeneutical methodologies necessitate a comprehensive "
            "reevaluation of foundational philosophical assumptions."
        )
        grade = flesch_kincaid_grade(text)
        # Complex → higher grade level
        assert grade > 10.0

    def test_empty_text(self):
        assert flesch_kincaid_grade("") == 0.0

    def test_returns_float(self):
        assert isinstance(flesch_kincaid_grade("Hello world."), float)

    def test_relationship_with_ease(self):
        text = "The dog ran fast. The cat sat down."
        ease = flesch_reading_ease(text)
        grade = flesch_kincaid_grade(text)
        # Higher ease → lower grade (inverse relationship)
        assert ease > 50.0
        assert grade < 10.0


# ---------------------------------------------------------------------------
# gunning_fog_index
# ---------------------------------------------------------------------------


class TestGunningFogIndex:
    def test_simple_text(self):
        score = gunning_fog_index("The cat sat on the mat.")
        assert isinstance(score, float)
        assert score < 10.0

    def test_complex_text(self):
        text = (
            "The epistemological ramifications of contemporary "
            "hermeneutical methodologies necessitate a comprehensive "
            "reevaluation of foundational philosophical assumptions."
        )
        score = gunning_fog_index(text)
        assert score > 10.0

    def test_empty_text(self):
        assert gunning_fog_index("") == 0.0

    def test_returns_float(self):
        assert isinstance(gunning_fog_index("Hello world."), float)


# ---------------------------------------------------------------------------
# coleman_liau_index
# ---------------------------------------------------------------------------


class TestColemanLiauIndex:
    def test_simple_text(self):
        score = coleman_liau_index("The cat sat on the mat.")
        assert isinstance(score, float)

    def test_empty_text(self):
        assert coleman_liau_index("") == 0.0

    def test_returns_float(self):
        assert isinstance(coleman_liau_index("Hello world."), float)


# ---------------------------------------------------------------------------
# automated_readability_index
# ---------------------------------------------------------------------------


class TestAutomatedReadabilityIndex:
    def test_simple_text(self):
        score = automated_readability_index("The cat sat on the mat.")
        assert isinstance(score, float)

    def test_empty_text(self):
        assert automated_readability_index("") == 0.0

    def test_returns_float(self):
        assert isinstance(automated_readability_index("Hello world."), float)


# ---------------------------------------------------------------------------
# text_complexity_score
# ---------------------------------------------------------------------------

from shadetriptxt.text_parser.text_readability import text_complexity_score


class TestTextComplexityScore:
    def test_returns_dict(self):
        result = text_complexity_score("The cat sat on the mat.")
        assert isinstance(result, dict)
        assert "complexity_score" in result
        assert "flesch" in result
        assert "coleman_liau" in result
        assert "ari" in result
        assert "lexical_diversity" in result

    def test_empty_text(self):
        result = text_complexity_score("")
        assert result["complexity_score"] == 0.0

    def test_score_range(self):
        result = text_complexity_score("The cat sat on the mat. It was a nice day.")
        assert 0.0 <= result["complexity_score"] <= 100.0


# ---------------------------------------------------------------------------
# is_gibberish
# ---------------------------------------------------------------------------


class TestIsGibberish:
    def test_normal_english(self):
        assert is_gibberish("The cat sat on the mat.") is False

    def test_random_noise(self):
        assert is_gibberish("xkjf8 wqp3z mbn!v") is True

    def test_empty_string(self):
        assert is_gibberish("") is True

    def test_whitespace_only(self):
        assert is_gibberish("   ") is True

    def test_single_letter(self):
        assert is_gibberish("a") is True

    def test_keyboard_smash(self):
        assert is_gibberish("asdfghjklqwerty") is True

    def test_short_real_word(self):
        assert is_gibberish("hello world") is False

    def test_sentence_with_numbers(self):
        assert is_gibberish("She bought 12 apples at the store.") is False

    def test_non_string(self):
        assert is_gibberish(12345) is True

    def test_custom_threshold_high(self):
        # Normal text with very high threshold → not gibberish
        assert is_gibberish("The cat sat on the mat.", threshold=0.99) is False


# ---------------------------------------------------------------------------
# is_placeholder_text
# ---------------------------------------------------------------------------


class TestIsPlaceholderText:
    def test_lorem_ipsum(self):
        assert is_placeholder_text("lorem ipsum dolor sit amet") is True

    def test_na(self):
        assert is_placeholder_text("N/A") is True

    def test_tbd(self):
        assert is_placeholder_text("TBD") is True

    def test_test(self):
        assert is_placeholder_text("test") is True

    def test_xxx(self):
        assert is_placeholder_text("xxx") is True

    def test_real_text(self):
        assert is_placeholder_text("Quarterly report Q2") is False

    def test_empty(self):
        assert is_placeholder_text("") is True

    def test_repeated_chars(self):
        assert is_placeholder_text("------") is True

    def test_non_string(self):
        assert is_placeholder_text(12345) is True


# ---------------------------------------------------------------------------
# text_density_score
# ---------------------------------------------------------------------------


class TestTextDensityScore:
    def test_hello_world(self):
        assert text_density_score("Hello World") == pytest.approx(0.9091, abs=0.001)

    def test_sparse(self):
        assert text_density_score("   x   ") == pytest.approx(1 / 7, abs=0.001)

    def test_empty(self):
        assert text_density_score("") == 0.0

    def test_all_alnum(self):
        assert text_density_score("abc123") == 1.0

    def test_non_string(self):
        assert text_density_score(None) == 0.0
