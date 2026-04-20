"""Tests for shadetriptxt.utils.string_validation — checksum algorithms."""

import pytest

from shadetriptxt.utils.string_validation import (
    luhn_checksum,
    is_valid_luhn,
    ean13_check_digit,
    is_valid_iban,
    is_valid_isbn,
    is_valid_credit_card,
    is_valid_vat,
    is_valid_ean,
)


# ---------------------------------------------------------------------------
# Luhn
# ---------------------------------------------------------------------------


class TestLuhnChecksum:
    def test_known_value(self):
        assert luhn_checksum("7992739871") == 3

    def test_single_digit(self):
        # checksum of "0" should be 0
        assert luhn_checksum("0") == 0

    def test_strips_hyphens(self):
        assert luhn_checksum("7992-7398-71") == 3

    def test_strips_spaces(self):
        assert luhn_checksum("7992 7398 71") == 3

    def test_non_digit_raises(self):
        with pytest.raises(ValueError):
            luhn_checksum("ABC")


class TestIsValidLuhn:
    def test_valid_number(self):
        assert is_valid_luhn("79927398713") is True

    def test_invalid_number(self):
        assert is_valid_luhn("79927398710") is False

    def test_visa_test_card(self):
        # Visa test number
        assert is_valid_luhn("4111111111111111") is True

    def test_with_hyphens(self):
        assert is_valid_luhn("4111-1111-1111-1111") is True

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            is_valid_luhn("5")

    def test_non_digit_raises(self):
        with pytest.raises(ValueError):
            is_valid_luhn("ABCDEF")


# ---------------------------------------------------------------------------
# EAN-13
# ---------------------------------------------------------------------------


class TestEan13CheckDigit:
    def test_known_barcode(self):
        assert ean13_check_digit("590123412345") == "7"

    def test_isbn_prefix(self):
        # 978-0-306-40615-? → check digit 7
        assert ean13_check_digit("978030640615") == "7"

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError):
            ean13_check_digit("12345")

    def test_non_digits_raises(self):
        with pytest.raises(ValueError):
            ean13_check_digit("59012341234A")


# ---------------------------------------------------------------------------
# IBAN
# ---------------------------------------------------------------------------


class TestIsValidIban:
    def test_valid_gb(self):
        assert is_valid_iban("GB29 NWBK 6016 1331 9268 19") is True

    def test_valid_es(self):
        assert is_valid_iban("ES9121000418450200051332") is True

    def test_valid_de(self):
        assert is_valid_iban("DE89370400440532013000") is True

    def test_invalid_checksum(self):
        assert is_valid_iban("GB29 NWBK 6016 1331 9268 18") is False

    def test_too_short(self):
        assert is_valid_iban("GB29") is False

    def test_wrong_length_for_country(self):
        # GB expects 22 chars; this is 23
        assert is_valid_iban("GB29NWBK60161331926819X") is False

    def test_empty(self):
        assert is_valid_iban("") is False

    def test_strips_hyphens(self):
        assert is_valid_iban("DE89-3704-0044-0532-0130-00") is True


# ---------------------------------------------------------------------------
# ISBN
# ---------------------------------------------------------------------------


class TestIsValidIsbn:
    def test_isbn10_valid(self):
        assert is_valid_isbn("0-306-40615-2") is True

    def test_isbn10_with_x(self):
        assert is_valid_isbn("0-8044-2957-X") is True

    def test_isbn10_invalid(self):
        assert is_valid_isbn("0-306-40615-3") is False

    def test_isbn13_valid(self):
        assert is_valid_isbn("978-0-306-40615-7") is True

    def test_isbn13_invalid(self):
        assert is_valid_isbn("978-0-306-40615-8") is False

    def test_wrong_length(self):
        assert is_valid_isbn("12345") is False

    def test_empty(self):
        assert is_valid_isbn("") is False

    def test_no_hyphens(self):
        assert is_valid_isbn("9780306406157") is True


# ---------------------------------------------------------------------------
# Credit Card
# ---------------------------------------------------------------------------


class TestIsValidCreditCard:
    def test_visa(self):
        result = is_valid_credit_card("4111111111111111")
        assert result["valid"] is True
        assert result["network"] == "visa"

    def test_mastercard(self):
        result = is_valid_credit_card("5500000000000004")
        assert result["valid"] is True
        assert result["network"] == "mastercard"

    def test_amex(self):
        result = is_valid_credit_card("378282246310005")
        assert result["valid"] is True
        assert result["network"] == "amex"

    def test_invalid_luhn(self):
        result = is_valid_credit_card("4111111111111110")
        assert result["valid"] is False

    def test_strips_spaces(self):
        result = is_valid_credit_card("4111 1111 1111 1111")
        assert result["valid"] is True

    def test_type_error(self):
        with pytest.raises(AttributeError):
            is_valid_credit_card(4111111111111111)


# ---------------------------------------------------------------------------
# VAT
# ---------------------------------------------------------------------------


class TestIsValidVat:
    def test_spain(self):
        assert is_valid_vat("ESB12345678") is True

    def test_germany(self):
        assert is_valid_vat("DE123456789") is True

    def test_france(self):
        assert is_valid_vat("FR12345678901") is True

    def test_invalid_country(self):
        assert is_valid_vat("XX123456789") is False

    def test_too_short(self):
        assert is_valid_vat("ES") is False

    def test_type_error(self):
        with pytest.raises(AttributeError):
            is_valid_vat(12345)


# ---------------------------------------------------------------------------
# EAN-8 / EAN-13
# ---------------------------------------------------------------------------


class TestIsValidEan:
    def test_ean13_valid(self):
        assert is_valid_ean("5901234123457") is True

    def test_ean13_invalid(self):
        assert is_valid_ean("5901234123458") is False

    def test_ean8_valid(self):
        assert is_valid_ean("96385074") is True

    def test_wrong_length(self):
        assert is_valid_ean("12345") is False

    def test_type_error(self):
        with pytest.raises(AttributeError):
            is_valid_ean(12345678)


# ---------------------------------------------------------------------------
# SWIFT/BIC validation
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_validation import is_valid_swift_bic


class TestIsValidSwiftBic:
    def test_valid_8_char(self):
        assert is_valid_swift_bic("DEUTDEFF") is True

    def test_valid_11_char(self):
        assert is_valid_swift_bic("DEUTDEFF500") is True

    def test_invalid_short(self):
        assert is_valid_swift_bic("DE") is False

    def test_invalid_bank_digits(self):
        assert is_valid_swift_bic("1234DEFF") is False

    def test_non_string(self):
        assert is_valid_swift_bic(12345678) is False


# ---------------------------------------------------------------------------
# Data type inference
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_validation import data_type_inference


class TestDataTypeInference:
    def test_integer(self):
        assert data_type_inference("42") == "integer"

    def test_float(self):
        assert data_type_inference("3.14") == "float"

    def test_boolean(self):
        assert data_type_inference("true") == "boolean"

    def test_date_iso(self):
        assert data_type_inference("2024-01-15") == "date"

    def test_email(self):
        assert data_type_inference("a@b.com") == "email"

    def test_url(self):
        assert data_type_inference("https://example.com") == "url"

    def test_empty(self):
        assert data_type_inference("") == "empty"

    def test_plain_string(self):
        assert data_type_inference("hello world") == "string"


# ---------------------------------------------------------------------------
# Phone format validation
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_validation import is_valid_phone_format


class TestIsValidPhoneFormat:
    def test_spain_mobile_with_prefix(self):
        assert is_valid_phone_format("+34612345678") is True

    def test_spain_mobile_no_prefix(self):
        assert is_valid_phone_format("612345678", "ES") is True

    def test_spain_with_spaces(self):
        assert is_valid_phone_format("612 345 678", "ES") is True

    def test_spain_with_dashes(self):
        assert is_valid_phone_format("612-345-678", "ES") is True

    def test_spain_landline(self):
        assert is_valid_phone_format("912345678", "ES") is True

    def test_spain_invalid_prefix(self):
        assert is_valid_phone_format("112345678", "ES") is False

    def test_us_valid(self):
        assert is_valid_phone_format("202-555-0100", "US") is True

    def test_us_with_country_code(self):
        assert is_valid_phone_format("+12025550100", "US") is True

    def test_gb_valid(self):
        assert is_valid_phone_format("+447911123456", "GB") is True

    def test_fr_valid(self):
        assert is_valid_phone_format("+33612345678", "FR") is True

    def test_unknown_country(self):
        assert is_valid_phone_format("12345", "ZZ") is False

    def test_non_string(self):
        assert is_valid_phone_format(612345678) is False

    def test_empty(self):
        assert is_valid_phone_format("") is False


# ---------------------------------------------------------------------------
# Email domain type classification
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_validation import email_domain_type


class TestEmailDomainType:
    def test_free_gmail(self):
        assert email_domain_type("user@gmail.com") == "free"

    def test_free_yahoo(self):
        assert email_domain_type("user@yahoo.com") == "free"

    def test_free_protonmail(self):
        assert email_domain_type("user@protonmail.com") == "free"

    def test_disposable_mailinator(self):
        assert email_domain_type("user@mailinator.com") == "disposable"

    def test_disposable_yopmail(self):
        assert email_domain_type("user@yopmail.com") == "disposable"

    def test_corporate(self):
        assert email_domain_type("user@company.com") == "corporate"

    def test_corporate_custom_domain(self):
        assert email_domain_type("admin@mybank.org") == "corporate"

    def test_invalid_no_at(self):
        assert email_domain_type("bad-email") == "invalid"

    def test_invalid_empty(self):
        assert email_domain_type("") == "invalid"

    def test_invalid_non_string(self):
        assert email_domain_type(12345) == "invalid"

    def test_case_insensitive(self):
        assert email_domain_type("User@GMAIL.COM") == "free"


# ---------------------------------------------------------------------------
# Mixed case anomaly detection
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_validation import has_mixed_case_anomaly


class TestHasMixedCaseAnomaly:
    def test_anomalous(self):
        assert has_mixed_case_anomaly("hELLo WoRLd") is True

    def test_normal_title(self):
        assert has_mixed_case_anomaly("Hello World") is False

    def test_all_upper(self):
        assert has_mixed_case_anomaly("HELLO WORLD") is False

    def test_all_lower(self):
        assert has_mixed_case_anomaly("hello world") is False

    def test_camelCase(self):
        assert has_mixed_case_anomaly("camelCase") is False

    def test_empty(self):
        assert has_mixed_case_anomaly("") is False

    def test_non_string(self):
        assert has_mixed_case_anomaly(123) is False


# ---------------------------------------------------------------------------
# Repeated words detection
# ---------------------------------------------------------------------------

from shadetriptxt.utils.string_validation import contains_repeated_words


class TestContainsRepeatedWords:
    def test_repeated(self):
        assert contains_repeated_words("the the cat") is True

    def test_no_repeats(self):
        assert contains_repeated_words("the cat sat") is False

    def test_case_insensitive(self):
        assert contains_repeated_words("The the cat") is True

    def test_empty(self):
        assert contains_repeated_words("") is False

    def test_single_word(self):
        assert contains_repeated_words("hello") is False


# =====================================================================
# Homoglyph & mixed-script detection
# =====================================================================


class TestDetectMixedScripts:
    def test_pure_latin(self):
        from shadetriptxt.utils.string_validation import detect_mixed_scripts

        result = detect_mixed_scripts("hello world")
        assert list(result.keys()) == ["LATIN"]

    def test_mixed_latin_cyrillic(self):
        from shadetriptxt.utils.string_validation import detect_mixed_scripts

        # 'е' below is Cyrillic U+0435
        result = detect_mixed_scripts("T\u0435st")
        assert "LATIN" in result
        assert "CYRILLIC" in result

    def test_no_letters(self):
        from shadetriptxt.utils.string_validation import detect_mixed_scripts

        result = detect_mixed_scripts("12345 !@#")
        assert result == {}

    def test_type_error(self):
        from shadetriptxt.utils.string_validation import detect_mixed_scripts

        with pytest.raises(TypeError):
            detect_mixed_scripts(12345)


class TestHomoglyphRiskScore:
    def test_pure_ascii(self):
        from shadetriptxt.utils.string_validation import homoglyph_risk_score

        assert homoglyph_risk_score("hello") == 0.0

    def test_all_confusable(self):
        from shadetriptxt.utils.string_validation import homoglyph_risk_score

        # Cyrillic а, е, о (all have Latin look-alikes)
        assert homoglyph_risk_score("\u0430\u0435\u043e") == 1.0

    def test_mixed(self):
        from shadetriptxt.utils.string_validation import homoglyph_risk_score

        # 'h' is normal Latin, '\u0435' is Cyrillic е
        score = homoglyph_risk_score("h\u0435llo")
        assert 0.0 < score < 1.0

    def test_empty(self):
        from shadetriptxt.utils.string_validation import homoglyph_risk_score

        assert homoglyph_risk_score("") == 0.0

    def test_type_error(self):
        from shadetriptxt.utils.string_validation import homoglyph_risk_score

        with pytest.raises(TypeError):
            homoglyph_risk_score(None)
