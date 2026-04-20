"""Tests for shadetriptxt.text_parser.text_normalizer — text normalization."""

import pytest

from shadetriptxt.text_parser.text_normalizer import (
    normalize_text,
    normalize_whitespace,
    remove_punctuation_marks,
    remove_special_characters,
    remove_parentheses_and_content,
    strip_quotes,
    prepare_for_comparison,
    mask_text,
)


class TestNormalizeText:
    def test_basic(self):
        result = normalize_text("  John   Smith,  Inc.  ")
        # Comma stays because it's adjacent to a word character
        assert "john" in result
        assert "smith" in result
        assert "inc" in result

    def test_accents(self):
        result = normalize_text("José García", remove_accents=True)
        assert result == "jose garcia"

    def test_parentheses(self):
        result = normalize_text("Microsoft (MSFT)", remove_parentheses_content=True)
        assert "msft" not in result.lower()
        assert "microsoft" in result.lower()

    def test_alphanumeric_only(self):
        result = normalize_text("Product-123 (New!)", preserve_alphanumeric_only=True)
        assert "product" in result.lower()
        assert "123" in result

    def test_no_lowercase(self):
        result = normalize_text("Hello World", lowercase=False)
        assert "Hello" in result

    def test_empty_string(self):
        result = normalize_text("   ")
        assert result == ""

    def test_not_string_raises(self):
        with pytest.raises(ValueError):
            normalize_text(123)

    def test_no_punctuation_removal(self):
        result = normalize_text("123-456-7890", remove_punctuation=False)
        assert "-" in result

    def test_quotes_removed(self):
        result = normalize_text('"Hello"')
        assert '"' not in result

    def test_smart_quotes_removed(self):
        result = normalize_text("\u201cHello\u201d")
        assert "\u201c" not in result
        assert "\u201d" not in result
        assert "hello" in result


class TestNormalizeWhitespace:
    def test_multiple_spaces(self):
        assert normalize_whitespace("  John    Smith  ") == "John Smith"

    def test_tabs(self):
        assert normalize_whitespace("a\t\tb") == "a b"


class TestRemovePunctuationMarks:
    def test_basic(self):
        result = remove_punctuation_marks("Hello, world!")
        assert result == "Hello world"

    def test_preserve_hyphens(self):
        result = remove_punctuation_marks("García-López", preserve_hyphens=True)
        assert "-" in result

    def test_remove_hyphens(self):
        result = remove_punctuation_marks("García-López", preserve_hyphens=False)
        assert "-" not in result


class TestRemoveSpecialCharacters:
    def test_basic(self):
        result = remove_special_characters("Product-123 (New!)")
        assert "Product" in result
        assert "123" in result
        assert "!" not in result


class TestRemoveParenthesesAndContent:
    def test_basic(self):
        result = remove_parentheses_and_content("Microsoft (MSFT)")
        assert "MSFT" not in result
        assert "Microsoft" in result

    def test_square_brackets(self):
        result = remove_parentheses_and_content("Hello [World]")
        assert "World" not in result


class TestStripQuotes:
    def test_double_quotes(self):
        assert strip_quotes('"Hello"') == "Hello"

    def test_single_quotes(self):
        assert strip_quotes("'Hello'") == "Hello"


class TestPrepareForComparison:
    def test_standard(self):
        result = prepare_for_comparison("  John Smith, Inc.  ")
        assert "john" in result
        assert "smith" in result
        assert "inc" in result

    def test_aggressive(self):
        result = prepare_for_comparison("José (CEO)", aggressive=True)
        assert "(" not in result


class TestMaskText:
    def test_basic(self):
        result = mask_text("12345678Z", keep_first=2, keep_last=1)
        assert result.startswith("12")
        assert result.endswith("Z")
        assert "*" in result

    def test_keep_chars(self):
        result = mask_text("user@domain.com", keep_first=1, keep_last=0, keep_chars="@.")
        assert "@" in result
        assert "." in result
