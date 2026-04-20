"""
Batch Generation & Convenience Functions
==========================================
generate_batch() for bulk generation of any data type,
and module-level fake_*() convenience functions that don't
require creating a TextDummy instance.

README sections: Batch Generation, Convenience Functions
"""

from shadetriptxt.text_dummy.text_dummy import (
    TextDummy,
    # Convenience functions
    fake_name, fake_email, fake_phone, fake_address, fake_text,
    fake_id_document, fake_dni, fake_credit_card, fake_iban, fake_swift,
    fake_ipv4, fake_userlogin, fake_license_plate, fake_date_of_birth,
    fake_profile, fake_product, fake_product_name,
    fake_password, fake_gender, fake_age,
    fake_random_number, fake_random_date,
    fake_unique_key, fake_autoincrement,
    fake_batch,
    fake_model, fake_model_batch, fake_records, fake_columns,
    random_from_list, random_sample_from_list,
    get_generator,
)

gen = TextDummy("es_ES")

# ══════════════════════════════════════════════════════════════
#  BATCH GENERATION
# ══════════════════════════════════════════════════════════════

# ── Batch of different types ──────────────────────────────────
print("=== generate_batch — various types ===")
types_to_demo = [
    ("name", 5),
    ("email", 5),
    ("phone", 3),
    ("city", 4),
    ("company", 3),
    ("iban", 3),
    ("credit_card_number", 3),
    ("ipv4", 3),
    ("uuid4", 3),
    ("product_name", 5),
    ("product_sku", 3),
    ("license_plate", 3),
    ("color_name", 4),
    ("order_status", 5),
    ("userlogin", 5),
]
for data_type, count in types_to_demo:
    values = gen.generate_batch(data_type, count)
    print(f"  {data_type:25s} → {values}")

# ── Batch with custom generators ──────────────────────────────
print("\n=== generate_batch — custom generators ===")
gen.register_custom("severity", ["INFO", "WARNING", "ERROR", "CRITICAL"])
gen.register_custom("tier", ["Free", "Basic", "Pro", "Enterprise"])
for ct in ["severity", "tier"]:
    values = gen.generate_batch(ct, 6)
    print(f"  {ct:25s} → {values}")

# ── Large batch ───────────────────────────────────────────────
print("\n=== generate_batch — large (1000 emails) ===")
emails = gen.generate_batch("email", 1000)
print(f"  Generated {len(emails)} emails")
print(f"  First 3:  {emails[:3]}")
print(f"  Unique:   {len(set(emails))}")

# ══════════════════════════════════════════════════════════════
#  CONVENIENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════

# ── Personal data shortcuts ───────────────────────────────────
print("\n=== Convenience — personal ===")
print(f"  fake_name():          {fake_name()}")
print(f"  fake_name('en_US'):   {fake_name('en_US')}")
print(f"  fake_email():         {fake_email()}")
print(f"  fake_phone():         {fake_phone()}")
print(f"  fake_address():       {fake_address()}")
print(f"  fake_text(50):        {fake_text(50)}")
print(f"  fake_date_of_birth(): {fake_date_of_birth()}")
print(f"  fake_gender():        {fake_gender()}")
print(f"  fake_age():           {fake_age()}")
print(f"  fake_password():      {fake_password()}")

# ── ID document shortcuts ─────────────────────────────────────
print("\n=== Convenience — ID documents ===")
print(f"  fake_id_document():       {fake_id_document()}")
print(f"  fake_id_document('en_US'):{fake_id_document('en_US')}")
print(f"  fake_dni():               {fake_dni()}")

# ── Financial shortcuts ───────────────────────────────────────
print("\n=== Convenience — financial ===")
print(f"  fake_credit_card():  {fake_credit_card()}")
print(f"  fake_iban():         {fake_iban()}")
print(f"  fake_swift():        {fake_swift()}")

# ── Internet shortcuts ────────────────────────────────────────
print("\n=== Convenience — internet ===")
print(f"  fake_ipv4():          {fake_ipv4()}")
print(f"  fake_userlogin():     {fake_userlogin()}")
print(f"  fake_license_plate(): {fake_license_plate()}")

# ── Number & date shortcuts ───────────────────────────────────
print("\n=== Convenience — numbers & dates ===")
print(f"  fake_random_number():       {fake_random_number()}")
print(f"  fake_random_number(float):  {fake_random_number('float', currency=True)}")
print(f"  fake_random_date():         {fake_random_date()}")
print(f"  fake_random_date('en_US'):  {fake_random_date(locale='en_US')}")

# ── Key & autoincrement shortcuts ─────────────────────────────
print("\n=== Convenience — keys & autoincrement ===")
print(f"  fake_unique_key():      {fake_unique_key()}")
print(f"  fake_unique_key(hex):   {fake_unique_key(key_type='hex', prefix='REF-', length=8)}")
print(f"  fake_autoincrement():   {fake_autoincrement(zfill=4)}")

# ── Product shortcuts ─────────────────────────────────────────
print("\n=== Convenience — products ===")
print(f"  fake_product_name():  {fake_product_name()}")
print("\n  fake_profile():")
profile = fake_profile("en_US")
for k, v in profile.items():
    print(f"    {k}: {v}")

# ── Random selection shortcuts ────────────────────────────────
print("\n=== Convenience — random selection ===")
statuses = ["Active", "Pending", "Closed"]
print(f"  random_from_list:       {random_from_list(statuses)}")
print(f"  random_sample(2):       {random_sample_from_list(statuses, count=2)}")

# ── Batch convenience ─────────────────────────────────────────
print("\n=== Convenience — fake_batch ===")
emails = fake_batch("email", count=5, locale="en_US")
for e in emails:
    print(f"  {e}")

# ── Pydantic convenience ─────────────────────────────────────
print("\n=== Convenience — Pydantic ===")
try:
    from pydantic import BaseModel

    class SimpleUser(BaseModel):
        name: str
        email: str
        age: int

    print("  fake_model:")
    print(f"    {fake_model(SimpleUser)}")

    print("  fake_model_batch (3):")
    for u in fake_model_batch(SimpleUser, count=3, locale="en_US"):
        print(f"    {u.name:25s} {u.email}")

    print("  fake_records (3):")
    for r in fake_records(SimpleUser, count=3):
        print(f"    {r}")

    print("  fake_columns (3):")
    for field_name, values in fake_columns(SimpleUser, count=3).items():
        print(f"    {field_name}: {values}")
except ImportError:
    print("  (pydantic not installed — skipping)")

# ── Instance caching ──────────────────────────────────────────
print("\n=== Instance caching (get_generator) ===")
g1 = get_generator("es_ES")
g2 = get_generator("es_ES")
print(f"  Same instance? {g1 is g2}")
