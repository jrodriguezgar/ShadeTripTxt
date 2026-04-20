"""
Example: Multi-locale PII Detection & Anonymization
=====================================================
Detect locale-specific PII across different countries.
Includes fake data generation by country with TextDummy.

Covers documentation section:
  - 5.9 Multi-language anonymization
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shadetriptxt.text_anonymizer import TextAnonymizer, SUPPORTED_LOCALES

# Sample texts with locale-specific PII
samples = {
    "es_ES": (
        "Juan García, DNI 12345678Z, teléfono +34 612 345 678, "
        "email juan@correo.es, C.P. 28001"
    ),
    "es_MX": (
        "María López, CURP LOMA850315HDFRRL09, RFC LOMA8503159A0, "
        "teléfono +52 55 1234 5678, email maria@correo.mx"
    ),
    "en_US": (
        "John Smith, SSN 123-45-6789, phone (555) 123-4567, "
        "email john@company.com, ZIP 90210"
    ),
    "en_GB": (
        "Jane Doe, NINO AB123456C, phone +44 20 7946 0958, "
        "email jane@company.co.uk, postcode SW1A 1AA"
    ),
    "pt_BR": (
        "Pedro Silva, CPF 123.456.789-09, CNPJ 12.345.678/0001-95, "
        "telefone +55 11 91234-5678, email pedro@empresa.com.br"
    ),
    "fr_FR": (
        "Pierre Dupont, NIR 1 85 03 75 123 456 78, "
        "téléphone +33 6 12 34 56 78, email pierre@entreprise.fr"
    ),
    "de_DE": (
        "Hans Müller, email hans@firma.de, "
        "Telefon +49 30 12345678, PLZ 10115"
    ),
    "it_IT": (
        "Marco Rossi, Codice Fiscale RSSMRC85C15H501Z, "
        "telefono +39 06 12345678, email marco@azienda.it, CAP 00100"
    ),
}

print("=" * 80)
print("MULTI-LOCALE PII DETECTION")
print("=" * 80)

for locale, text in samples.items():
    print(f"\n{'─' * 80}")
    print(f"LOCALE: {locale}")
    print(f"{'─' * 80}")
    print(f"Text: {text[:75]}...")

    anon = TextAnonymizer(locale=locale)
    entities = anon.detect_pii(text)

    if entities:
        for e in entities:
            print(f"  [{e.pii_type.value:15s}] '{e.text}'  "
                  f"(confidence={e.confidence:.2f}, source={e.source})")
    else:
        print("  (no PII detected)")

    # Anonymize
    result = anon.anonymize_text(text, strategy="redact")
    print(f"  Anonymized: {result.anonymized[:75]}...")

print(f"\n{'=' * 80}")
print(f"Supported locales: {', '.join(SUPPORTED_LOCALES)}")
print()

# ── Generate fake data by country ──
print("=" * 80)
print("FAKE DATA GENERATION BY COUNTRY (TextDummy)")
print("=" * 80)
from shadetriptxt.text_dummy.text_dummy import TextDummy

locales = ["es_ES", "en_US", "pt_BR", "fr_FR", "de_DE", "it_IT"]

for locale in locales:
    gen = TextDummy(locale)
    info = gen.locale_info()
    print(f"\n[{locale}] {info['country']} ({info['language']})")
    print(f"  Name:        {gen.name()}")
    print(f"  Email:       {gen.email()}")
    print(f"  Phone:       {gen.phone()}")
    print(f"  ID Document: {gen.id_document()} ({info['id_document']})")
    print(f"  Price:       {gen.price()}")
    print(f"  IBAN:        {gen.iban()}")
    print(f"  Date:        {gen.date()}")

print()
print("Done!")
