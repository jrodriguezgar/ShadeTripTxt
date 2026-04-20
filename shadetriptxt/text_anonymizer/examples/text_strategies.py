"""
Example: Text PII Detection & Anonymization Strategies
========================================================
Detect PII in free text and compare all 7 anonymization strategies.
Includes per-type strategy dispatch and custom patterns.

Covers documentation sections:
  - 3.1–3.7 Anonymization Techniques
  - 5.2 Mask sensitive data in free text
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shadetriptxt.text_anonymizer import TextAnonymizer, Strategy, PiiType

# ── Sample text with multiple PII types ──
text_es = (
    "El cliente Juan García López con DNI 12345678Z vive en "
    "Calle Mayor 15, Madrid 28001. Su email es juan.garcia@empresa.com "
    "y su teléfono es +34 612 345 678. Nacido el 15/03/1990. "
    "IP de acceso: 192.168.1.100. Visita https://www.ejemplo.com"
)

print("=" * 70)
print("ORIGINAL TEXT:")
print("=" * 70)
print(text_es)
print()

# ── 1. PII Detection ──
print("=" * 70)
print("1. PII DETECTION (regex)")
print("=" * 70)
anon = TextAnonymizer(locale="es_ES")
entities = anon.detect_pii(text_es)
for e in entities:
    print(f"  [{e.pii_type.value:15s}] '{e.text}'  "
          f"(pos {e.start}-{e.end}, conf={e.confidence:.2f})")

# ── 2. All 7 strategies side by side ──
strategies = [
    Strategy.REDACT, Strategy.MASK, Strategy.HASH,
    Strategy.REPLACE, Strategy.PSEUDONYMIZE,
    Strategy.GENERALIZE, Strategy.SUPPRESS,
]

for strat in strategies:
    print()
    print(f"{'=' * 70}")
    print(f"2. STRATEGY: {strat.value.upper()}")
    print(f"{'=' * 70}")
    a = TextAnonymizer(locale="es_ES", strategy=strat, seed=42)
    result = a.anonymize_text(text_es)
    print(result.anonymized)
    print(f"  -> Entities: {len(result.entities)}, "
          f"Replacements: {len(result.replacements)}")

# ── 3. Per-type mixed strategies ──
print()
print("=" * 70)
print("3. PER-TYPE STRATEGIES (mask emails, hash IDs, suppress IPs)")
print("=" * 70)
anon_mixed = TextAnonymizer(locale="es_ES", strategy="redact")
anon_mixed.set_strategy("mask", pii_type=PiiType.EMAIL)
anon_mixed.set_strategy("hash", pii_type=PiiType.ID_DOCUMENT)
anon_mixed.set_strategy("suppress", pii_type=PiiType.IP_ADDRESS)
result = anon_mixed.anonymize_text(text_es)
print(result.anonymized)
print()

# ── 4. Custom patterns ──
print("=" * 70)
print("4. CUSTOM PATTERNS")
print("=" * 70)
anon_custom = TextAnonymizer(locale="es_ES", strategy="redact")
anon_custom.add_pattern("employee_id", r"EMP-\d{4}")
anon_custom.add_pattern("project_code", r"PRJ-[A-Z]{3}-\d{3}")

text_custom = "Empleado EMP-1234 asignado al proyecto PRJ-ABC-001, email ana@test.com"
result = anon_custom.anonymize_text(text_custom)
print(f"Original:   {text_custom}")
print(f"Anonymized: {result.anonymized}")
for e in result.entities:
    print(f"  [{e.pii_type.value:15s}] '{e.text}'")
print()

# ── 5. Summary statistics ──
print("=" * 70)
print("5. ANONYMIZATION SUMMARY")
print("=" * 70)
anon_sum = TextAnonymizer(locale="es_ES", strategy="redact")
result = anon_sum.anonymize_text(text_es)
summary = anon_sum.summary(result)
print(f"Total entities detected: {summary['total_entities']}")
print(f"By type:")
for pii_type, count in summary["by_type"].items():
    print(f"  {pii_type:15s}: {count}")
print()

# ── 6. Confidence filtering ──
print("=" * 70)
print("6. CONFIDENCE FILTERING")
print("=" * 70)
all_entities = anon.detect_pii(text_es)
high_conf = anon.detect_pii(text_es, min_confidence=0.88)
print(f"All entities:             {len(all_entities)}")
print(f"High confidence (>=0.88): {len(high_conf)}")
print()

# ── 7. PII type filtering ──
print("=" * 70)
print("7. PII TYPE FILTERING (only EMAIL)")
print("=" * 70)
emails_only = anon.detect_pii(
    text_es, pii_types=[PiiType.EMAIL],
)
for e in emails_only:
    print(f"  [{e.pii_type.value}] '{e.text}'")
print()

# ── 8. English text ──
print("=" * 70)
print("8. ENGLISH TEXT (en_US)")
print("=" * 70)
text_en = (
    "Customer John Smith, SSN 123-45-6789, lives at 742 Evergreen Terrace. "
    "Contact: john.smith@company.com, phone (555) 123-4567. "
    "IP: 10.0.0.1, DOB: 03/15/1985. Website: https://example.com"
)
anon_us = TextAnonymizer(locale="en_US", strategy="redact")
result = anon_us.anonymize_text(text_en)
print(f"Original:   {text_en[:80]}...")
print(f"Anonymized: {result.anonymized[:80]}...")
for e in result.entities:
    print(f"  [{e.pii_type.value:15s}] '{e.text}'")

# ── 9. Batch text anonymization ──
print()
print("=" * 70)
print("9. BATCH TEXT ANONYMIZATION")
print("=" * 70)
texts = [
    "Email de Juan: juan@empresa.com",
    "DNI del cliente: 87654321X",
    "IP del servidor: 10.0.0.1",
]
anon_batch = TextAnonymizer(locale="es_ES", strategy="redact")
results = anon_batch.anonymize_batch(texts)
for orig, res in zip(texts, results):
    print(f"  {orig}")
    print(f"    -> {res.anonymized}")

print()
print("Done!")
