"""
Example: Dictionary and Records Anonymization
===============================================
Anonymize structured data (dicts, lists of records).
Includes auto-detection, explicit field types, field whitelist,
batch processing, and pseudonymization consistency.

Covers documentation sections:
  - 5.3 Anonymize records and dictionaries
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType, Strategy, anonymize_dict

# ── 1. Single record — automatic field detection ──
print("=" * 70)
print("1. AUTO-DETECT FIELDS (by field name)")
print("=" * 70)
record = {
    "name": "María López García",
    "email": "maria.lopez@correo.es",
    "phone": "+34 611 222 333",
    "dni": "12345678Z",
    "address": "Calle Gran Vía 25, Madrid",
    "age": 34,
    "department": "Marketing",
}
print("Original:", record)
anon_record = anonymize_dict(record, strategy="redact")
print("Redacted:", anon_record)
print()

# ── 2. Different strategies ──
print("=" * 70)
print("2. STRATEGY COMPARISON on same record")
print("=" * 70)
for strat in ["redact", "mask", "replace", "hash", "pseudonymize"]:
    result = anonymize_dict(record, strategy=strat)
    print(f"  {strat:15s} -> name={result['name']!r}, email={result['email']!r}")
print()

# ── 3. Explicit field types ──
print("=" * 70)
print("3. EXPLICIT FIELD TYPES")
print("=" * 70)
custom_record = {
    "codigo_empleado": "EMP-00123",
    "salario": "45000",
    "observaciones": "Trabaja en Barcelona",
}
result = anonymize_dict(
    custom_record,
    field_types={
        "codigo_empleado": PiiType.ID_DOCUMENT,
        "salario": PiiType.CURRENCY,
    },
    strategy="redact",
)
print("Original: ", custom_record)
print("Anonymized:", result)
print()

# ── 4. Field whitelist (fields parameter) ──
print("=" * 70)
print("4. FIELD WHITELIST -- anonymize only specific fields")
print("=" * 70)
registro = {
    "nombre": "Juan García",
    "email": "juan@test.com",
    "telefono": "+34 612 345 678",
    "salario": 45000,
    "departamento": "Marketing",
}

# Without fields → auto-detection anonymizes nombre, email, telefono
result_all = anonymize_dict(registro, strategy="redact", locale="es_ES")
print("Without fields (all auto-detected):")
for k, v in result_all.items():
    print(f"  {k:15s}: {v}")

# With fields → only email and telefono are anonymized
result_wl = anonymize_dict(
    registro, strategy="redact", locale="es_ES",
    fields=["email", "telefono"],
)
print("\nWith fields=['email', 'telefono']:")
for k, v in result_wl.items():
    print(f"  {k:15s}: {v}")
print()

# ── 5. Field whitelist + explicit types ──
print("=" * 70)
print("5. FIELD WHITELIST + EXPLICIT TYPES")
print("=" * 70)
record_mixed = {
    "codigo": "12345678Z",
    "nombre": "Ana Martín",
    "notas": "texto libre sin PII",
}
anon = TextAnonymizer(locale="es_ES", strategy="redact")
result = anon.anonymize_dict(
    record_mixed,
    fields=["codigo"],
    field_types={"codigo": PiiType.ID_DOCUMENT},
)
print("Original: ", record_mixed)
print("Anonymized:", result)
print("  -> Only 'codigo' was anonymized; 'nombre' and 'notas' untouched")
print()

# ── 6. Batch records ──
print("=" * 70)
print("6. BATCH RECORDS ANONYMIZATION")
print("=" * 70)
records = [
    {"name": "Carlos Ruiz", "email": "carlos@test.com", "phone": "611000111"},
    {"name": "Ana Martín", "email": "ana@test.com", "phone": "622000222"},
    {"name": "Pedro Sánchez", "email": "pedro@test.com", "phone": "633000333"},
]

anon = TextAnonymizer(locale="es_ES", strategy="mask")
anon_records = anon.anonymize_records(records)
for i, (orig, anon_r) in enumerate(zip(records, anon_records)):
    print(f"  Record {i+1}: {orig['name']:15s} -> {anon_r['name']}")
    print(f"            {orig['email']:25s} -> {anon_r['email']}")
print()

# ── 7. Batch records with field whitelist ──
print("=" * 70)
print("7. BATCH RECORDS — field whitelist")
print("=" * 70)
anon_wl = TextAnonymizer(locale="es_ES", strategy="redact")
results_wl = anon_wl.anonymize_records(records, fields=["email"])
for i, r in enumerate(results_wl):
    print(f"  Record {i+1}: name={r['name']!r}, email={r['email']!r}")
print("  -> Names untouched, only emails anonymized")
print()

# ── 8. Pseudonymize for consistency ──
print("=" * 70)
print("8. PSEUDONYMIZE — consistent across records")
print("=" * 70)
records2 = [
    {"name": "Juan García", "email": "juan@test.com"},
    {"name": "Ana López", "email": "ana@test.com"},
    {"name": "Juan García", "email": "juan@test.com"},  # Same as record 1
]
anon_p = TextAnonymizer(strategy="pseudonymize", seed=42)
results = anon_p.anonymize_records(records2)
for i, r in enumerate(results):
    print(f"  Record {i+1}: name={r['name']!r}, email={r['email']!r}")
print(f"  -> Record 1 and 3 match: {results[0]['name'] == results[2]['name']}")

print()
print("Done!")
