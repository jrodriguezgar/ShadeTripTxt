"""Tests for obfuscate_email in shadetriptxt.text_anonymizer."""

import pytest

from shadetriptxt.text_anonymizer.text_anonymizer import obfuscate_email


class TestObfuscateEmail:
    def test_basic(self):
        assert obfuscate_email("john@example.com") == "j***@example.com"

    def test_single_char_local(self):
        assert obfuscate_email("a@x.com") == "a@x.com"

    def test_long_local(self):
        assert obfuscate_email("firstname.lastname@company.org") == "f***@company.org"

    def test_type_error(self):
        with pytest.raises(TypeError):
            obfuscate_email(123)

    def test_no_at_sign(self):
        with pytest.raises(ValueError):
            obfuscate_email("invalid")

    def test_multiple_at(self):
        # rsplit("@", 1) keeps only the last @
        result = obfuscate_email("user@sub@domain.com")
        assert result.endswith("@domain.com")
