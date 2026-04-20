"""Tests for shadetriptxt.utils.string_similarity — core similarity algorithms."""

from shadetriptxt.utils.string_similarity import (
    levenshtein_score,
    jaro_winkler_score,
    jaccard_similarity,
    sorensen_dice_coefficient,
    ratcliff_obershelp_score,
    lcs_score,
    mra_similarity,
)


class TestLevenshteinScore:
    def test_identical(self):
        assert levenshtein_score("hello", "hello") == 1.0

    def test_empty_both(self):
        assert levenshtein_score("", "") == 1.0

    def test_one_empty(self):
        assert levenshtein_score("hello", "") == 0.0

    def test_similar(self):
        score = levenshtein_score("kitten", "sitting")
        assert 0.4 < score < 0.7

    def test_completely_different(self):
        score = levenshtein_score("abc", "xyz")
        assert score == 0.0

    def test_single_char_diff(self):
        score = levenshtein_score("cat", "bat")
        assert score > 0.5


class TestJaroWinklerScore:
    def test_identical(self):
        assert jaro_winkler_score("hello", "hello") == 1.0

    def test_empty_both(self):
        assert jaro_winkler_score("", "") == 1.0

    def test_one_empty(self):
        assert jaro_winkler_score("hello", "") == 0.0

    def test_similar_names(self):
        score = jaro_winkler_score("Martha", "Marhta")
        assert score > 0.9

    def test_prefix_boost(self):
        # Jaro-Winkler should give higher scores to strings sharing prefix
        score_prefix = jaro_winkler_score("DWAYNE", "DUANE")
        score_no_prefix = jaro_winkler_score("XXXXXX", "DUANE")
        assert score_prefix > score_no_prefix

    def test_no_match(self):
        score = jaro_winkler_score("abc", "xyz")
        assert score == 0.0


class TestJaccardSimilarity:
    def test_identical(self):
        assert jaccard_similarity("abc", "abc") == 1.0

    def test_empty(self):
        assert jaccard_similarity("", "") == 0.0

    def test_char_mode(self):
        score = jaccard_similarity("abc", "bcd", mode="char")
        assert 0.0 < score < 1.0

    def test_token_mode(self):
        score = jaccard_similarity("hello world", "hello test", mode="token")
        assert score > 0.0


class TestSorensenDiceCoefficient:
    def test_identical(self):
        assert sorensen_dice_coefficient("hello", "hello") == 1.0

    def test_empty(self):
        assert sorensen_dice_coefficient("", "") == 0.0

    def test_similar(self):
        score = sorensen_dice_coefficient("night", "nacht")
        assert 0.0 < score < 1.0


class TestRatcliffObershelpScore:
    def test_identical(self):
        assert ratcliff_obershelp_score("hello", "hello") == 1.0

    def test_empty(self):
        assert ratcliff_obershelp_score("", "") == 0.0

    def test_similar(self):
        score = ratcliff_obershelp_score("pennsylvania", "pencilvania")
        assert score > 0.5


class TestLcsScore:
    def test_identical(self):
        result = lcs_score("hello", "hello")
        assert result["similarity"] == 1.0
        assert result["lcs_length"] == 5

    def test_empty(self):
        result = lcs_score("", "")
        assert result["similarity"] == 0.0
        assert result["lcs_length"] == 0

    def test_partial(self):
        result = lcs_score("abc", "ac")
        assert result["lcs_length"] == 2


class TestMraSimilarity:
    def test_identical(self):
        score = mra_similarity("Smith", "Smith")
        assert score == 1.0

    def test_empty(self):
        assert mra_similarity("", "") == 0.0

    def test_similar_names(self):
        score = mra_similarity("Smith", "Smyth")
        assert score > 0.5
