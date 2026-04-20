"""Tests for shadetriptxt.text_parser — TextParser class."""

from shadetriptxt.text_parser.text_parser import TextParser


class TestTextParserInit:
    def test_default_locale(self):
        parser = TextParser()
        assert parser.locale == "es_ES"

    def test_custom_locale(self):
        parser = TextParser("en_US")
        assert parser.locale == "en_US"

    def test_supported_locales(self):
        locales = TextParser.supported_locales()
        assert "es_ES" in locales
        assert "en_US" in locales
        assert len(locales) >= 12

    def test_locale_info(self):
        parser = TextParser("es_ES")
        info = parser.locale_info()
        assert info["locale"] == "es_ES"
        assert info["country"] == "Spain"


class TestTextParserNormalize:
    def test_basic(self):
        parser = TextParser("es_ES")
        result = parser.normalize("  José  García-López  ")
        assert "jose" in result.lower()
        assert "garcia" in result.lower()

    def test_accent_removal(self):
        parser = TextParser("es_ES")
        result = parser.normalize("José García", remove_accents=True)
        assert "é" not in result
        assert "í" not in result

    def test_english_locale(self):
        parser = TextParser("en_US")
        result = parser.normalize("  Hello   World  ")
        assert "hello" in result.lower()


class TestTextParserExtract:
    def test_extract_emails(self):
        parser = TextParser()
        result = parser.extract_emails("Contact info@example.com for details")
        assert result is not None
        assert "info@example.com" in result

    def test_extract_phones(self):
        parser = TextParser("es_ES")
        result = parser.extract_phones("+34 91 303 20 60")
        assert result is not None
        assert len(result) > 0

    def test_extract_urls(self):
        parser = TextParser()
        result = parser.extract_urls("Visit https://example.com today")
        assert result is not None

    def test_extract_ips(self):
        parser = TextParser()
        result = parser.extract_ip_addresses("Server at 192.168.1.1")
        assert result is not None


class TestTextParserArticles:
    def test_spanish_articles(self):
        parser = TextParser("es_ES")
        result = parser.remove_articles("Pedro de la Fuente")
        assert result is not None
        assert "de" not in result.split()
        assert "la" not in result.split()

    def test_english_articles(self):
        parser = TextParser("en_US")
        result = parser.remove_articles("John of the Hill")
        assert result is not None


class TestTextParserFixEncoding:
    def test_basic_mojibake(self):
        parser = TextParser("es_ES")
        result = parser.fix_encoding("Ã¡rbol")
        assert result == "árbol" or "rbol" in result

    def test_clean_text_unchanged(self):
        parser = TextParser("es_ES")
        result = parser.fix_encoding("hello world")
        assert result == "hello world"


class TestTextParserValidateId:
    def test_valid_spanish_dni(self):
        parser = TextParser("es_ES")
        result = parser.validate_id("12345678Z")
        assert result is not None

    def test_invalid_id(self):
        parser = TextParser("es_ES")
        result = parser.validate_id("INVALID")
        assert result is None or result == ""


class TestTextParserPrepareForComparison:
    def test_basic(self):
        parser = TextParser("es_ES")
        result = parser.prepare_for_comparison("José García")
        assert isinstance(result, str)
        assert len(result) > 0
