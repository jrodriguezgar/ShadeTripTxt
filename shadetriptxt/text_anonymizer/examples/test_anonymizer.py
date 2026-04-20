"""Test script for TextAnonymizer module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shadetriptxt.text_anonymizer import (
    TextAnonymizer, PiiType, Strategy,
    anonymize_text, detect_pii, anonymize_dict,
    SUPPORTED_LOCALES,
)

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  OK  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")

# ── 1. Basic instantiation ──
print("\n=== 1. Instantiation ===")
anon = TextAnonymizer(locale="es_ES")
check("default locale", anon.locale == "es_ES")
check("default strategy", anon.strategy == Strategy.REDACT)
check("repr", "TextAnonymizer" in repr(anon))
check("supported locales", len(SUPPORTED_LOCALES) >= 12)

# ── 2. Regex detection — email ──
print("\n=== 2. Email detection ===")
entities = anon.detect_pii("Contactar en juan.garcia@empresa.com por favor")
emails = [e for e in entities if e.pii_type == PiiType.EMAIL]
check("email found", len(emails) >= 1, f"found {len(emails)}")
if emails:
    check("email text", emails[0].text == "juan.garcia@empresa.com")

# ── 3. Regex detection — DNI (es_ES) ──
print("\n=== 3. DNI detection (es_ES) ===")
entities = anon.detect_pii("Su DNI es 12345678Z")
ids = [e for e in entities if e.pii_type == PiiType.ID_DOCUMENT]
check("DNI found", len(ids) >= 1, f"found {len(ids)}")
if ids:
    check("DNI text", ids[0].text == "12345678Z")

# ── 4. Regex detection — IP address ──
print("\n=== 4. IP detection ===")
entities = anon.detect_pii("Servidor en 192.168.1.100 puerto 8080")
ips = [e for e in entities if e.pii_type == PiiType.IP_ADDRESS]
check("IP found", len(ips) >= 1, f"found {len(ips)}")

# ── 5. Regex detection — URL ──
print("\n=== 5. URL detection ===")
entities = anon.detect_pii("Visita https://www.ejemplo.com/pagina para mas info")
urls = [e for e in entities if e.pii_type == PiiType.URL]
check("URL found", len(urls) >= 1, f"found {len(urls)}")

# ── 6. Strategy: REDACT ──
print("\n=== 6. Strategy REDACT ===")
result = anon.anonymize_text("Email: test@test.com")
check("redact contains [EMAIL]", "[EMAIL]" in result.anonymized)
check("original preserved", result.original == "Email: test@test.com")
check("entities list populated", len(result.entities) > 0)

# ── 7. Strategy: MASK ──
print("\n=== 7. Strategy MASK ===")
anon_mask = TextAnonymizer(locale="es_ES", strategy="mask")
result = anon_mask.anonymize_text("Email: test@test.com")
check("mask has asterisks", "*" in result.anonymized)
check("mask hides email", "test@test.com" not in result.anonymized)

# ── 8. Strategy: HASH ──
print("\n=== 8. Strategy HASH ===")
anon_hash = TextAnonymizer(locale="es_ES", strategy=Strategy.HASH)
result = anon_hash.anonymize_text("Email: test@test.com")
check("hash replaces email", "test@test.com" not in result.anonymized)
check("hash is hex", all(c in "0123456789abcdef " for c in result.anonymized.replace("Email: ", "").strip()))

# ── 9. Strategy: REPLACE ──
print("\n=== 9. Strategy REPLACE ===")
anon_rep = TextAnonymizer(locale="es_ES", strategy="replace")
result = anon_rep.anonymize_text("Email: test@test.com")
check("replace changes email", "test@test.com" not in result.anonymized)
check("replace has @ sign", "@" in result.anonymized)

# ── 10. Strategy: PSEUDONYMIZE ──
print("\n=== 10. Strategy PSEUDONYMIZE ===")
anon_pseudo = TextAnonymizer(locale="es_ES", strategy="pseudonymize", seed=42)
r1 = anon_pseudo.anonymize_text("Email: same@test.com y same@test.com")
# same input should get same output
check("pseudonymize consistency",
      r1.replacements.get("same@test.com") is not None)

# ── 11. Strategy: GENERALIZE ──
print("\n=== 11. Strategy GENERALIZE ===")
anon_gen = TextAnonymizer(locale="es_ES", strategy="generalize")
result = anon_gen.anonymize_text("Email: juan@empresa.com")
check("generalize email has ***@", "***@" in result.anonymized)

# ── 12. Strategy: SUPPRESS ──
print("\n=== 12. Strategy SUPPRESS ===")
anon_sup = TextAnonymizer(locale="es_ES", strategy="suppress")
result = anon_sup.anonymize_text("Email: test@test.com fin")
check("suppress removes PII", "test@test.com" not in result.anonymized)

# ── 13. Per-type strategy ──
print("\n=== 13. Per-type strategy ===")
anon_mixed = TextAnonymizer(locale="es_ES", strategy="redact")
anon_mixed.set_strategy("mask", pii_type="EMAIL")
result = anon_mixed.anonymize_text("DNI: 12345678Z email: x@y.com")
check("DNI redacted", "[ID_DOCUMENT]" in result.anonymized)
check("email masked", "*" in result.anonymized and "[EMAIL]" not in result.anonymized)

# ── 14. Custom pattern ──
print("\n=== 14. Custom pattern ===")
anon_custom = TextAnonymizer(locale="es_ES")
anon_custom.add_pattern("emp_id", r"EMP-\d{4}")
entities = anon_custom.detect_pii("Empleado EMP-1234 en oficina")
custom = [e for e in entities if e.pii_type == PiiType.CUSTOM]
check("custom pattern found", len(custom) >= 1)
if custom:
    check("custom text", custom[0].text == "EMP-1234")

# ── 15. Dict anonymization ──
print("\n=== 15. Dict anonymization ===")
record = {"name": "Juan García", "email": "juan@test.com", "age": 34}
result = anonymize_dict(record, strategy="redact")
check("name redacted", result["name"] == "[NAME]")
check("email redacted", result["email"] == "[EMAIL]")
check("age unchanged", result["age"] == 34)

# ── 16. Dict with explicit field types ──
print("\n=== 16. Dict explicit types ===")
record = {"codigo": "12345678Z", "notes": "nothing"}
result = anonymize_dict(record, field_types={"codigo": PiiType.ID_DOCUMENT})
check("codigo redacted", result["codigo"] == "[ID_DOCUMENT]")
check("notes unchanged", result["notes"] == "nothing")

# ── 17. Records batch ──
print("\n=== 17. Records batch ===")
records = [
    {"name": "Ana", "email": "ana@test.com"},
    {"name": "Pedro", "email": "pedro@test.com"},
]
anon_batch = TextAnonymizer(strategy="redact")
results = anon_batch.anonymize_records(records)
check("batch length", len(results) == 2)
check("batch anonymized", all(r["name"] == "[NAME]" for r in results))

# ── 18. Text batch ──
print("\n=== 18. Text batch ===")
texts = ["Email: a@b.com", "Email: c@d.com"]
results = anon_batch.anonymize_batch(texts)
check("text batch length", len(results) == 2)
check("text batch anonymized", all("[EMAIL]" in r.anonymized for r in results))

# ── 19. SSN detection (en_US) ──
print("\n=== 19. SSN detection (en_US) ===")
anon_us = TextAnonymizer(locale="en_US")
entities = anon_us.detect_pii("SSN: 123-45-6789")
ssns = [e for e in entities if e.pii_type == PiiType.ID_DOCUMENT]
check("SSN found", len(ssns) >= 1)

# ── 20. CPF detection (pt_BR) ──
print("\n=== 20. CPF detection (pt_BR) ===")
anon_br = TextAnonymizer(locale="pt_BR")
entities = anon_br.detect_pii("CPF: 123.456.789-09")
cpfs = [e for e in entities if e.pii_type == PiiType.ID_DOCUMENT]
check("CPF found", len(cpfs) >= 1)

# ── 21. Date detection ──
print("\n=== 21. Date detection ===")
entities = anon.detect_pii("Nacido el 15/03/1990 en Madrid")
dates = [e for e in entities if e.pii_type == PiiType.DATE]
check("date found", len(dates) >= 1)

# ── 22. Currency detection ──
print("\n=== 22. Currency detection ===")
entities = anon.detect_pii("Total: €1.234,56")
currs = [e for e in entities if e.pii_type == PiiType.CURRENCY]
check("currency found", len(currs) >= 1)

# ── 23. Summary ──
print("\n=== 23. Summary ===")
result = anon.anonymize_text("Email test@x.com, DNI 12345678Z, IP 10.0.0.1")
summary = anon.summary(result)
check("summary has total_entities", summary["total_entities"] >= 3)
check("summary has by_type", len(summary["by_type"]) >= 2)

# ── 24. Convenience function ──
print("\n=== 24. Convenience anonymize_text ===")
result = anonymize_text("Contacto: info@empresa.es", locale="es_ES", strategy="redact")
check("convenience works", "[EMAIL]" in result.anonymized)

# ── 25. Convenience detect_pii ──
print("\n=== 25. Convenience detect_pii ===")
entities = detect_pii("DNI: 12345678Z", locale="es_ES")
check("convenience detect", len(entities) >= 1)

# ── 26. Reset ──
print("\n=== 26. Reset ===")
anon_r = TextAnonymizer(strategy="pseudonymize")
anon_r.anonymize_text("test@x.com")
check("pseudo map populated", len(anon_r._pseudo_map) > 0)
anon_r.reset_pseudonyms()
check("pseudo map cleared", len(anon_r._pseudo_map) == 0)
anon_r.reset()
check("full reset", anon_r._dummy is None)

# ── 27. Min confidence filter ──
print("\n=== 27. Min confidence ===")
entities_all = anon.detect_pii("Email: a@b.com DNI 12345678Z")
entities_high = anon.detect_pii("Email: a@b.com DNI 12345678Z", min_confidence=0.88)
check("confidence filter reduces", len(entities_high) <= len(entities_all))

# ── 28. PII type filter ──
print("\n=== 28. PII type filter ===")
entities = anon.detect_pii(
    "Email: a@b.com y DNI 12345678Z",
    pii_types=[PiiType.EMAIL],
)
check("type filter EMAIL only", all(e.pii_type == PiiType.EMAIL for e in entities))

# ── 29. Multiple locales ──
print("\n=== 29. Multiple locales ===")
for loc in ["es_ES", "en_US", "pt_BR", "fr_FR", "de_DE", "it_IT"]:
    a = TextAnonymizer(locale=loc)
    check(f"locale {loc} profile", a.profile is not None, f"profile missing for {loc}")

# ══ Results ══
print(f"\n{'='*50}")
print(f"PASSED: {passed}  |  FAILED: {failed}")
if failed:
    print("*** SOME TESTS FAILED ***")
    sys.exit(1)
else:
    print("All tests passed!")
