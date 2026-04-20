"""Tests for detect_language in shadetriptxt.text_parser.language_normalizer."""

import pytest

from shadetriptxt.text_parser.language_normalizer import detect_language


class TestDetectLanguage:
    def test_english(self):
        assert detect_language("the cat is on the table and the dog is here") == "en"

    def test_spanish(self):
        assert detect_language("el gato está en la mesa y el perro está aquí") == "es"

    def test_french(self):
        assert detect_language("le chat est sur la table et le chien est ici") == "fr"

    def test_german(self):
        assert detect_language("der Hund ist auf dem Tisch und die Katze ist hier") == "de"

    def test_unknown(self):
        assert detect_language("xyz abc") == "unknown"

    def test_empty(self):
        assert detect_language("") == "unknown"

    def test_type_error(self):
        with pytest.raises(TypeError):
            detect_language(42)
