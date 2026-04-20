"""Tests for shadetriptxt.utils.string_ops — core string utility functions."""

from shadetriptxt.utils.string_ops import (
    flat_vowels,
    normalize_spaces,
    erase_allspaces,
    normalize_symbols,
    erase_specialchar,
    fix_spanish,
    string_filter,
    string_aZ,
    string_aZ09,
    reorder_comma_fullname,
    split_all,
)


class TestFlatVowels:
    def test_accented_vowels(self):
        assert flat_vowels("áéíóú") == "aeiou"

    def test_upper_accented(self):
        assert flat_vowels("ÁÉÍÓÚ") == "AEIOU"

    def test_ene(self):
        assert flat_vowels("niño") == "nino"

    def test_cedilla(self):
        assert flat_vowels("Ça va") == "Ca va"

    def test_diaeresis(self):
        assert flat_vowels("über") == "uber"

    def test_empty(self):
        assert flat_vowels("") == ""

    def test_no_accents(self):
        assert flat_vowels("hello") == "hello"

    def test_eszett(self):
        assert flat_vowels("Straße") == "Strasse"

    def test_ligature_ae(self):
        assert flat_vowels("Ærodynamic") == "AErodynamic"


class TestNormalizeSpaces:
    def test_multiple_spaces(self):
        assert normalize_spaces("hello   world") == "hello world"

    def test_tabs_and_newlines(self):
        assert normalize_spaces("hello\t\nworld") == "hello world"

    def test_leading_trailing(self):
        assert normalize_spaces("  hello  ") == "hello"

    def test_empty(self):
        assert normalize_spaces("") == ""

    def test_single_space(self):
        assert normalize_spaces("hello world") == "hello world"


class TestEraseAllspaces:
    def test_basic(self):
        assert erase_allspaces("hello world") == "helloworld"

    def test_multiple_spaces(self):
        assert erase_allspaces("a b c") == "abc"

    def test_empty(self):
        assert erase_allspaces("") == ""

    def test_tabs(self):
        assert erase_allspaces("a\tb") == "ab"


class TestNormalizeSymbols:
    def test_curly_quotes(self):
        result = normalize_symbols("\u2018hello\u2019")
        assert result == "'hello'"

    def test_em_dash(self):
        result = normalize_symbols("hello\u2014world")
        assert result == "hello-world"

    def test_empty(self):
        assert normalize_symbols("") == ""


class TestEraseSpecialchar:
    def test_basic(self):
        result = erase_specialchar("hello @world!")
        assert result == "hello world"

    def test_allowed_chars(self):
        result = erase_specialchar("hello@world", "@")
        assert result == "hello@world"

    def test_spanish_chars(self):
        result = erase_specialchar("niño")
        assert result == "niño"

    def test_empty(self):
        assert erase_specialchar("") == ""


class TestFixSpanish:
    def test_basic(self):
        result = fix_spanish("José García")
        assert "Jos" in result
        assert "Garc" in result

    def test_empty(self):
        assert fix_spanish("") == ""


class TestStringFilter:
    def test_keep_letters(self):
        result = string_filter("abc 123 !@#", "a-z")
        assert "abc" in result
        assert "123" not in result.replace(" ", "")

    def test_empty(self):
        assert string_filter("", "a-z") == ""


class TestStringAZ:
    def test_removes_numbers(self):
        result = string_aZ("hello 123 world")
        assert "123" not in result
        assert "hello" in result
        assert "world" in result

    def test_keeps_spanish(self):
        result = string_aZ("García ñoño")
        assert "García" in result
        assert "ñoño" in result


class TestStringAZ09:
    def test_keeps_numbers(self):
        result = string_aZ09("hello 123 world")
        assert "123" in result
        assert "hello" in result


class TestReorderCommaFullname:
    def test_basic(self):
        assert reorder_comma_fullname("García López, José") == "José García López"

    def test_no_comma(self):
        assert reorder_comma_fullname("José García") is None

    def test_empty(self):
        assert reorder_comma_fullname("") is None

    def test_none(self):
        assert reorder_comma_fullname(None) is None


class TestSplitAll:
    def test_basic(self):
        result = split_all("hello-world.test")
        assert "hello" in result
        assert "world" in result
        assert "test" in result

    def test_empty(self):
        assert split_all("") == []

    def test_no_dividers(self):
        result = split_all("hello")
        assert result == ["hello"]
