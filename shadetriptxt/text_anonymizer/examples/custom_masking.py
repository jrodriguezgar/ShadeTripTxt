"""
Example: Custom Masking for Data Protection
=============================================
Demonstrates custom mask characters, global mask functions, and per-type
mask functions for real-world data protection scenarios.

Use cases covered:
  - Custom mask character (GDPR-friendly displays)
  - IP address masking preserving network prefix
  - Credit card PCI-DSS compliant masking
  - Email masking preserving domain for business analytics
  - ID document masking with fixed-length output
  - Phone number masking keeping country code
  - Combined per-type masks for a GDPR audit report
  - Applying custom masks to dictionary records and batches
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType, Strategy


# ── Shared sample texts ──
TEXT_ES = (
    "El cliente Juan García López con DNI 12345678Z vive en "
    "Calle Mayor 15, Madrid 28001. Su email es juan.garcia@empresa.com "
    "y su teléfono es +34 612 345 678. Nacido el 15/03/1990. "
    "IP de acceso: 192.168.1.100. Tarjeta: 4111 1111 1111 1111."
)

TEXT_EN = (
    "Customer John Smith, SSN 123-45-6789, "
    "email john.smith@acme.com, phone (555) 123-4567. "
    "IP: 10.0.0.42. Card: 5500 0000 0000 0004."
)


def section(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════
# 1. CUSTOM MASK CHARACTER
# ═══════════════════════════════════════════════════════════════════════════
section("1. CUSTOM MASK CHARACTER — GDPR-friendly displays")

# Replace '*' with '·' for a softer visual in customer-facing screens
anon = TextAnonymizer(locale="es_ES", strategy="mask", mask_char="·")
result = anon.anonymize_text(TEXT_ES)
print(f"mask_char='·':\n  {result.anonymized}\n")

# Use 'X' for a more explicit redaction feel (common in banking)
anon_x = TextAnonymizer(locale="es_ES", strategy="mask", mask_char="X")
result_x = anon_x.anonymize_text(TEXT_ES)
print(f"mask_char='X':\n  {result_x.anonymized}\n")

# Use '█' for a "blackout" effect (document previews)
anon_block = TextAnonymizer(locale="es_ES", strategy="mask", mask_char="█")
result_block = anon_block.anonymize_text("DNI: 12345678Z, email: juan@test.com")
print(f"mask_char='█':\n  {result_block.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 2. IP ADDRESS MASKING — preserve network prefix
# ═══════════════════════════════════════════════════════════════════════════
section("2. IP ADDRESS MASKING — preserve network prefix for IT audits")

# Use case: IT security logs need the network segment visible
# but the host address must be hidden.

def mask_ip_preserve_subnet(text: str, pii_type: PiiType) -> str:
    """Keep the first two octets, mask the rest → 192.168.*.*"""
    if "." in text:
        octets = text.split(".")
        return ".".join(octets[:2] + ["*"] * (len(octets) - 2))
    # IPv6 fallback: mask last 4 groups
    groups = text.split(":")
    visible = max(len(groups) // 2, 1)
    return ":".join(groups[:visible] + ["****"] * (len(groups) - visible))

anon_ip = TextAnonymizer(locale="es_ES", strategy="mask")
anon_ip.set_mask_function(mask_ip_preserve_subnet, pii_type="IP_ADDRESS")

for text, label in [
    ("Acceso desde IP 192.168.1.100", "Private network"),
    ("Login from 10.0.0.42", "Corporate VPN"),
    ("External IP: 85.123.45.67", "Public IP"),
]:
    result = anon_ip.anonymize_text(text)
    print(f"  [{label:16s}] {result.anonymized}")

# Variant: mask ALL octets except the first (stricter)
def mask_ip_first_octet_only(text: str, pii_type: PiiType) -> str:
    """Keep only the first octet → 192.*.*.*"""
    if "." in text:
        octets = text.split(".")
        return ".".join([octets[0]] + ["*"] * (len(octets) - 1))
    return "*" * len(text)

print()
anon_ip2 = TextAnonymizer(locale="es_ES", strategy="mask")
anon_ip2.set_mask_function(mask_ip_first_octet_only, pii_type="IP_ADDRESS")
result = anon_ip2.anonymize_text("Server IP: 172.16.254.1")
print(f"  [First octet   ] {result.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 3. CREDIT CARD PCI-DSS MASKING
# ═══════════════════════════════════════════════════════════════════════════
section("3. CREDIT CARD — PCI-DSS compliant masking")

# PCI-DSS allows showing the first 6 (BIN) and last 4 digits.
# Everything else must be masked.

def mask_credit_card_pci(text: str, pii_type: PiiType) -> str:
    """PCI-DSS compliant: show BIN (first 6) + last 4, mask middle."""
    import re
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 13:
        bin_part = digits[:6]
        last4 = digits[-4:]
        middle = "*" * (len(digits) - 10)
        return f"{bin_part}{middle}{last4}"
    return "*" * len(digits)

anon_pci = TextAnonymizer(locale="es_ES", strategy="mask")
anon_pci.set_mask_function(mask_credit_card_pci, pii_type="CREDIT_CARD")

cards = [
    "Visa:       4111 1111 1111 1111",
    "Mastercard: 5500 0000 0000 0004",
    "Amex:       3782 822463 10005",
]
for card_text in cards:
    result = anon_pci.anonymize_text(card_text)
    print(f"  {result.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 4. EMAIL MASKING — preserve domain for analytics
# ═══════════════════════════════════════════════════════════════════════════
section("4. EMAIL MASKING — preserve domain for business analytics")

# Use case: Marketing needs to know the email domain (gmail, empresa.com)
# but the local part must be hidden.

def mask_email_preserve_domain(text: str, pii_type: PiiType) -> str:
    """Hide local part, keep full domain → ***@empresa.com"""
    parts = text.split("@")
    if len(parts) == 2:
        return f"***@{parts[1]}"
    return "***@***"

anon_email = TextAnonymizer(locale="es_ES", strategy="mask")
anon_email.set_mask_function(mask_email_preserve_domain, pii_type="EMAIL")

emails_text = (
    "Contactos: juan.garcia@empresa.com, maria@gmail.com, "
    "pedro.lopez@outlook.es"
)
result = anon_email.anonymize_text(emails_text)
print(f"  {result.anonymized}")

# Variant: show first initial + domain
def mask_email_initial_domain(text: str, pii_type: PiiType) -> str:
    """Show first char of local part + domain → j***@empresa.com"""
    parts = text.split("@")
    if len(parts) == 2 and parts[0]:
        return f"{parts[0][0]}***@{parts[1]}"
    return "***@***"

print()
anon_email2 = TextAnonymizer(locale="es_ES", strategy="mask")
anon_email2.set_mask_function(mask_email_initial_domain, pii_type="EMAIL")
result = anon_email2.anonymize_text(emails_text)
print(f"  {result.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 5. ID DOCUMENT MASKING — fixed-length safe output
# ═══════════════════════════════════════════════════════════════════════════
section("5. ID DOCUMENT MASKING — fixed-length safe output")

# Use case: Call center agents need to confirm "last 3 chars" of the
# document but must not see the full number. Fixed-length output avoids
# leaking the document length.

def mask_id_last3(text: str, pii_type: PiiType) -> str:
    """Show only last 3 characters, pad to fixed 12 chars → *********78Z"""
    visible = text[-3:] if len(text) >= 3 else text
    return "*" * (12 - len(visible)) + visible

anon_id = TextAnonymizer(locale="es_ES", strategy="mask")
anon_id.set_mask_function(mask_id_last3, pii_type="ID_DOCUMENT")

ids_text = "DNI: 12345678Z, NIE: X1234567L"
result = anon_id.anonymize_text(ids_text)
print(f"  {result.anonymized}")

# English: SSN last 4 digits only
def mask_ssn_last4(text: str, pii_type: PiiType) -> str:
    """SSN: show only last 4 digits → ***-**-6789"""
    import re
    digits = re.sub(r"\D", "", text)
    if len(digits) == 9:
        return f"***-**-{digits[-4:]}"
    return "*" * len(text)

anon_ssn = TextAnonymizer(locale="en_US", strategy="mask")
anon_ssn.set_mask_function(mask_ssn_last4, pii_type="ID_DOCUMENT")

result = anon_ssn.anonymize_text("SSN: 123-45-6789")
print(f"  {result.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 6. PHONE MASKING — keep country code
# ═══════════════════════════════════════════════════════════════════════════
section("6. PHONE MASKING — keep country code for geographic analysis")

# Use case: Analytics needs the country code to segment by region,
# but the subscriber number must be masked.

def mask_phone_keep_country(text: str, pii_type: PiiType) -> str:
    """Keep country code prefix, mask the rest → +34 *** *** ***"""
    import re
    # Match leading +XX or +XXX
    m = re.match(r"(\+\d{1,3}[\s.-]?)", text)
    if m:
        prefix = m.group(1)
        rest = text[len(prefix):]
        masked_rest = re.sub(r"\d", "*", rest)
        return prefix + masked_rest
    # No country code: mask all digits
    return re.sub(r"\d", "*", text)

anon_phone = TextAnonymizer(locale="es_ES", strategy="mask")
anon_phone.set_mask_function(mask_phone_keep_country, pii_type="PHONE")

phones = [
    "Teléfono: +34 612 345 678",
    "Móvil: +34 698 765 432",
]
for phone_text in phones:
    result = anon_phone.anonymize_text(phone_text)
    print(f"  {result.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 7. COMBINED PER-TYPE MASKS — GDPR audit report
# ═══════════════════════════════════════════════════════════════════════════
section("7. COMBINED PER-TYPE MASKS — GDPR audit report")

# Real-world scenario: different departments need different masking rules.
# Build a single TextAnonymizer with all custom masks for a compliance report.

anon_gdpr = TextAnonymizer(locale="es_ES", strategy="mask")

# Emails: hide local part, keep domain
anon_gdpr.set_mask_function(mask_email_preserve_domain, pii_type="EMAIL")

# IPs: keep subnet
anon_gdpr.set_mask_function(mask_ip_preserve_subnet, pii_type="IP_ADDRESS")

# IDs: fixed-length, last 3 visible
anon_gdpr.set_mask_function(mask_id_last3, pii_type="ID_DOCUMENT")

# Phones: keep country code
anon_gdpr.set_mask_function(mask_phone_keep_country, pii_type="PHONE")

# Credit cards: PCI-DSS
anon_gdpr.set_mask_function(mask_credit_card_pci, pii_type="CREDIT_CARD")

# Everything else (dates, URLs, etc.) uses the built-in mask with custom char
anon_gdpr.mask_char = "·"

print(f"Original:\n  {TEXT_ES}\n")
result = anon_gdpr.anonymize_text(TEXT_ES)
print(f"GDPR masked:\n  {result.anonymized}\n")

# Show what each entity was mapped to
print("Replacement map:")
for orig, masked in result.replacements.items():
    print(f"  '{orig}' → '{masked}'")


# ═══════════════════════════════════════════════════════════════════════════
# 8. GLOBAL MASK FUNCTION — uniform "blackout" for maximum privacy
# ═══════════════════════════════════════════════════════════════════════════
section("8. GLOBAL MASK FUNCTION — uniform blackout (maximum privacy)")

# Use case: Completely opaque masking for external data sharing.
# All PII replaced with fixed-length blocks regardless of type or content.

def blackout_mask(text: str, pii_type: PiiType) -> str:
    """Replace any PII with a fixed [BLOCKED] tag."""
    return "[BLOCKED]"

anon_blackout = TextAnonymizer(locale="es_ES", strategy="mask")
anon_blackout.set_mask_function(blackout_mask)

result = anon_blackout.anonymize_text(TEXT_ES)
print(f"  {result.anonymized}")

# Variant: length-preserving blackout (useful for column alignment)
def blackout_length_preserving(text: str, pii_type: PiiType) -> str:
    """Replace every character with '█', preserving length."""
    return "█" * len(text)

anon_block2 = TextAnonymizer(locale="en_US", strategy="mask")
anon_block2.set_mask_function(blackout_length_preserving)

result = anon_block2.anonymize_text(TEXT_EN)
print(f"  {result.anonymized}")


# ═══════════════════════════════════════════════════════════════════════════
# 9. CUSTOM MASK ON DICTIONARY RECORDS
# ═══════════════════════════════════════════════════════════════════════════
section("9. CUSTOM MASKS ON DICTIONARY RECORDS")

# Custom masks apply to anonymize_dict / anonymize_records too, because
# _mask is called through the same _apply_strategy dispatcher.

anon_dict = TextAnonymizer(locale="es_ES", strategy="mask")
anon_dict.set_mask_function(mask_email_preserve_domain, pii_type="EMAIL")
anon_dict.set_mask_function(mask_id_last3, pii_type="ID_DOCUMENT")

records = [
    {"nombre": "Juan García", "email": "juan@empresa.com", "dni": "12345678Z", "edad": 34},
    {"nombre": "María López", "email": "maria@gmail.com", "dni": "98765432W", "edad": 28},
    {"nombre": "Pedro Ruiz", "email": "pedro@outlook.es", "dni": "X1234567L", "edad": 45},
]

results = anon_dict.anonymize_records(records)
for orig, anon_rec in zip(records, results):
    print(f"  Original: {orig}")
    print(f"  Masked:   {anon_rec}")
    print()


# ═══════════════════════════════════════════════════════════════════════════
# 10. CUSTOM MASK WITH CONSTRUCTOR — one-liner setup
# ═══════════════════════════════════════════════════════════════════════════
section("10. CUSTOM MASK VIA CONSTRUCTOR — one-liner setup")

# For simple cases, pass the mask function directly in the constructor
# instead of calling set_mask_function() afterwards.

anon_oneliner = TextAnonymizer(
    locale="es_ES",
    strategy="mask",
    custom_mask_fn=lambda text, pt: f"[{pt.value}:{len(text)}chars]",
)

result = anon_oneliner.anonymize_text(
    "DNI: 12345678Z, email: juan@test.com, IP: 10.0.0.1"
)
print(f"  {result.anonymized}")
# Each PII shows its type and original length:
#   DNI: [ID_DOCUMENT:9chars], email: [EMAIL:13chars], IP: [IP_ADDRESS:8chars]


# ═══════════════════════════════════════════════════════════════════════════
# 11. RESET — return to defaults
# ═══════════════════════════════════════════════════════════════════════════
section("11. RESET — return to default masking")

anon_reset = TextAnonymizer(locale="es_ES", strategy="mask", mask_char="#")
anon_reset.set_mask_function(blackout_mask)

# Before reset
r1 = anon_reset.anonymize_text("DNI: 12345678Z")
print(f"  Before reset: {r1.anonymized}")

# After reset: mask_char returns to '*', custom functions are cleared
anon_reset.reset()
anon_reset.set_strategy(Strategy.MASK)  # reset() clears state, re-set strategy
r2 = anon_reset.anonymize_text("DNI: 12345678Z")
print(f"  After reset:  {r2.anonymized}")


print()
print("Done!")
