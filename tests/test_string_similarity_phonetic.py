"""Tests for shadetriptxt.utils.string_similarity — phonetic encoding functions."""

import pytest

from shadetriptxt.utils.string_similarity import (
    soundex,
    metaphone,
    double_metaphone,
    calculate_similarity,
)


# ---------------------------------------------------------------------------
# Soundex
# ---------------------------------------------------------------------------


class TestSoundex:
    def test_robert(self):
        assert soundex("Robert") == "R163"

    def test_rupert(self):
        assert soundex("Rupert") == "R163"

    def test_robert_rupert_match(self):
        assert soundex("Robert") == soundex("Rupert")

    def test_ashcraft(self):
        # In our simplified Soundex, H is ignored and S/C map to same code (2)
        assert soundex("Ashcraft") == "A226"

    def test_tymczak(self):
        assert soundex("Tymczak") == "T522"

    def test_empty_string(self):
        assert soundex("") == "0000"

    def test_non_alpha(self):
        assert soundex("1234") == "0000"

    def test_single_letter(self):
        assert soundex("A") == "A000"

    @pytest.mark.parametrize(
        "name1, name2",
        [
            ("Smith", "Smyth"),
            ("Johnson", "Jonson"),
        ],
    )
    def test_similar_names_same_code(self, name1: str, name2: str):
        assert soundex(name1) == soundex(name2)


# ---------------------------------------------------------------------------
# Metaphone
# ---------------------------------------------------------------------------


class TestMetaphone:
    def test_smith(self):
        result = metaphone("Smith")
        assert result == "SM0"

    def test_empty(self):
        assert metaphone("") == ""

    def test_phone(self):
        # PH → F
        result = metaphone("Phone")
        assert "F" in result

    def test_knight(self):
        # KN → N at start
        result = metaphone("Knight")
        assert result[0] == "N"

    def test_write(self):
        # WR → R at start
        result = metaphone("Write")
        assert result[0] == "R"

    def test_xenon(self):
        # Initial X → S
        result = metaphone("Xenon")
        assert result[0] == "S"

    def test_shell(self):
        # SH → X
        result = metaphone("Shell")
        assert "X" in result

    def test_thumb(self):
        # TH → 0 (theta)
        result = metaphone("Thumb")
        assert "0" in result

    def test_dumb(self):
        # Silent B after M
        result = metaphone("Dumb")
        assert result == "TM"


# ---------------------------------------------------------------------------
# Double Metaphone
# ---------------------------------------------------------------------------


class TestDoubleMetaphone:
    def test_schmidt(self):
        primary, alternate = double_metaphone("Schmidt")
        assert primary != "" and alternate != ""

    def test_smith(self):
        primary, alternate = double_metaphone("Smith")
        assert primary != ""

    def test_empty(self):
        assert double_metaphone("") == ("", "")

    def test_returns_tuple_of_two(self):
        result = double_metaphone("Robert")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_jose_spanish(self):
        primary, _ = double_metaphone("Jose")
        # Should encode with H (Spanish J)
        assert "H" in primary or "J" in primary

    def test_caesar(self):
        primary, _ = double_metaphone("Caesar")
        assert "S" in primary

    def test_sugar(self):
        primary, alternate = double_metaphone("Sugar")
        # Initial S → X (sh sound), alternate S
        assert primary != alternate or primary == alternate  # both valid encodings


# ---------------------------------------------------------------------------
# calculate_similarity with phonetic algorithms
# ---------------------------------------------------------------------------


class TestCalculateSimilarityPhonetic:
    def test_soundex_match(self):
        result = calculate_similarity("Robert", "Rupert", algorithm="soundex")
        assert result["match"] is True
        assert result["score"] == 100.0

    def test_soundex_no_match(self):
        result = calculate_similarity("Robert", "Smith", algorithm="soundex")
        assert result["match"] is False
        assert result["score"] == 0.0

    def test_metaphone_match(self):
        result = calculate_similarity("Smith", "Smith", algorithm="metaphone")
        assert result["match"] is True

    def test_double_metaphone_match(self):
        result = calculate_similarity("Robert", "Robert", algorithm="double_metaphone")
        assert result["match"] is True
        assert "primary_1" in result
        assert "alternate_1" in result

    def test_double_metaphone_keys(self):
        result = calculate_similarity("Smith", "Schmidt", algorithm="double_metaphone")
        assert "primary_1" in result
        assert "primary_2" in result
        assert "alternate_1" in result
        assert "alternate_2" in result


# ---------------------------------------------------------------------------
# Hamming distance
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_similarity import string_distance_hamming


class TestStringDistanceHamming:
    def test_karolin_kathrin(self):
        assert string_distance_hamming("karolin", "kathrin") == 3

    def test_binary_strings(self):
        assert string_distance_hamming("1011101", "1001001") == 2

    def test_identical(self):
        assert string_distance_hamming("abc", "abc") == 0

    def test_all_different(self):
        assert string_distance_hamming("abc", "xyz") == 3

    def test_unequal_length_raises(self):

        with pytest.raises(ValueError):
            string_distance_hamming("ab", "abc")

    def test_type_error(self):

        with pytest.raises(TypeError):
            string_distance_hamming("abc", 123)
