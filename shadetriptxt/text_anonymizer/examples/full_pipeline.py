"""
Example: Full Pipeline -- Normalize, Validate & Anonymize
==========================================================
End-to-end pipeline combining TextParser and TextAnonymizer
for data preprocessing, validation, and anonymization.

Covers documentation sections:
  - 5.5 Normalize and clean text before anonymizing
  - 5.7 Full pipeline: detection, validation and anonymization
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType

# ══════════════════════════════════════════════════════════════════════
# PART 1: Normalize and clean text before anonymizing (5.5)
# ══════════════════════════════════════════════════════════════════════

print("=" * 70)
print("1. TEXT NORMALIZATION (TextParser)")
print("=" * 70)
from shadetriptxt.text_parser.text_parser import TextParser
from shadetriptxt.text_parser.text_normalizer import normalize_text, mask_text

parser = TextParser("es_ES")

# Normalize text with inconsistencies
texto_sucio = "  Jose   Garcia-Lopez  (CEO)   EMPRESA S.L.  "
limpio = parser.normalize(texto_sucio)
print(f"  Dirty:  '{texto_sucio}'")
print(f"  Clean:  '{limpio}'")
print()

# ── 2. Extract PII from text ──
print("=" * 70)
print("2. PII EXTRACTION (TextParser)")
print("=" * 70)
texto = "Llamar al +34 612 345 678 o escribir a juan@test.com"
telefonos = parser.extract_phones(texto)
emails = parser.extract_emails(texto)
print(f"  Text:   '{texto}'")
print(f"  Phones: {telefonos}")
print(f"  Emails: {emails}")
print()

# ── 3. Granular masking ──
print("=" * 70)
print("3. GRANULAR MASKING WITH mask_text")
print("=" * 70)
datos = {
    "dni":     "12345678Z",
    "email":   "juan.garcia@empresa.com",
    "iban":    "ES9121000418450200051332",
    "tarjeta": "4111111111111111",
}

for campo, valor in datos.items():
    if campo == "email":
        masked = mask_text(valor, keep_first=1, keep_last=4, keep_chars="@.")
    elif campo == "tarjeta":
        masked = mask_text(valor, keep_first=4, keep_last=4)
    elif campo == "iban":
        masked = mask_text(valor, keep_first=4, keep_last=4)
    else:
        masked = mask_text(valor, keep_first=2, keep_last=1)
    print(f"  {campo:10s}: {valor} -> {masked}")
print()

# ── 4. Fix mojibake before anonymizing ──
print("=" * 70)
print("4. FIX ENCODING ISSUES (EncodingFixer)")
print("=" * 70)
from shadetriptxt.text_parser.encoding_fixer import EncodingFixer

fixer = EncodingFixer(language="es")
# Simulate mojibake: UTF-8 bytes decoded as Latin-1
texto_roto = "Jos\u00c3\u00a9 Garc\u00c3\u00ada"
texto_reparado = fixer.fix(texto_roto)
print(f"  Broken:  '{texto_roto}'")
print(f"  Fixed:   '{texto_reparado}'")

# Anonymize the repaired text
anon = TextAnonymizer(locale="es_ES", strategy="redact")
result = anon.anonymize_text(texto_reparado)
print(f"  Anonymized: '{result.anonymized}'")
print()

# ══════════════════════════════════════════════════════════════════════
# PART 2: Full pipeline -- normalize -> validate -> anonymize (5.7)
# ══════════════════════════════════════════════════════════════════════

print("=" * 70)
print("5. FULL PIPELINE: normalize -> validate -> anonymize")
print("=" * 70)

# Raw text with format issues
texto_raw = "  Juan   Garcia  Lopez, DNI:12 345 678Z, email: JUAN @ TEST.COM  "
print(f"  RAW INPUT: '{texto_raw}'")

# Step 1: Normalize
texto_limpio = parser.normalize(texto_raw, remove_accents=False)
print(f"  STEP 1 (normalize): '{texto_limpio}'")

# Step 2: Validate documents
dni_candidato = "12345678Z"
dni_valido = parser.validate_id(dni_candidato)
print(f"  STEP 2 (validate DNI '{dni_candidato}'): {'valid' if dni_valido else 'INVALID'}")

# Step 3: Anonymize with mixed strategies
anon = TextAnonymizer(locale="es_ES", strategy="redact", seed=42)
anon.set_strategy("mask", pii_type=PiiType.EMAIL)
anon.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)
result = anon.anonymize_text(texto_limpio)
print(f"  STEP 3 (anonymize): '{result.anonymized}'")
print(f"  Entities detected: {len(result.entities)}")
for e in result.entities:
    print(f"    [{e.pii_type.value:15s}] '{e.text}'")
print()

# ── 6. Validate before anonymize -- filter bad data ──
print("=" * 70)
print("6. VALIDATE DOCUMENTS BEFORE ANONYMIZING")
print("=" * 70)
documentos = ["12345678Z", "99999999X", "X1234567L", "INVALIDO"]

for doc in documentos:
    valido = parser.validate_id(doc)
    status = "VALID -> anonymize" if valido else "INVALID -> skip"
    print(f"  {doc:15s} -> {status}")

print()
print("Done!")
