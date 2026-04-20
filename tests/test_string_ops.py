"""Tests for shadetriptxt.utils.string_ops — string utility operations."""

from shadetriptxt.utils.string_ops import normalize_phone


# ---------------------------------------------------------------------------
# normalize_phone
# ---------------------------------------------------------------------------


class TestNormalizePhone:
    def test_spain_default(self):
        assert normalize_phone("612 345 678") == "+34612345678"

    def test_spain_with_prefix(self):
        assert normalize_phone("+34612345678") == "+34612345678"

    def test_spain_with_dashes(self):
        assert normalize_phone("612-345-678") == "+34612345678"

    def test_us(self):
        assert normalize_phone("(202) 555-0100", "US") == "+12025550100"

    def test_us_with_prefix(self):
        assert normalize_phone("+12025550100", "US") == "+12025550100"

    def test_gb_strip_leading_zero(self):
        assert normalize_phone("07911123456", "GB") == "+447911123456"

    def test_fr_strip_leading_zero(self):
        assert normalize_phone("0612345678", "FR") == "+33612345678"

    def test_de(self):
        assert normalize_phone("030 12345678", "DE") == "+493012345678"

    def test_pt(self):
        assert normalize_phone("912345678", "PT") == "+351912345678"

    def test_mx(self):
        assert normalize_phone("5512345678", "MX") == "+525512345678"

    def test_unknown_country_no_prefix(self):
        # Unknown country returns cleaned digits
        assert normalize_phone("12345", "ZZ") == "12345"

    def test_empty_string(self):
        assert normalize_phone("") == ""

    def test_non_string(self):
        assert normalize_phone(12345) == 12345

    def test_dots_stripped(self):
        assert normalize_phone("612.345.678", "ES") == "+34612345678"
