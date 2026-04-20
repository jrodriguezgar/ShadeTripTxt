"""
Locales & Country Comparison
==============================
Locale support, locale_info metadata, available documents,
and side-by-side comparison of all 12 supported locales:
names, IDs, currency, numbers, dates, gender, phones, addresses.

README sections: Locale Information, Supported Locales
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

LOCALES = [
    "es_ES", "es_MX", "es_AR", "es_CO", "es_CL",
    "en_US", "en_GB",
    "pt_BR", "pt_PT",
    "fr_FR", "de_DE", "it_IT",
]

# ── Supported locales ────────────────────────────────────────
print("=== Supported Locales ===")
for code, country in TextDummy.supported_locales().items():
    print(f"  {code} → {country}")

# ── Locale info details ──────────────────────────────────────
print("\n=== Locale Info (es_ES) ===")
gen_es = TextDummy("es_ES")
for key, value in gen_es.locale_info().items():
    print(f"  {key}: {value}")

# ── Locale metadata summary ──────────────────────────────────
print("\n=== Locale metadata — all locales ===")
for loc in LOCALES:
    g = TextDummy(loc)
    info = g.locale_info()
    print(f"  {loc:6s} | {info['country']:16s} | {info['language']:12s} "
          f"| {info['currency']:10s} | ID: {info['id_document']}")

# ── Names ─────────────────────────────────────────────────────
print("\n=== Names ===")
for loc in LOCALES:
    g = TextDummy(loc)
    print(f"  {loc:6s} → {g.name()}")

# ── ID Documents ──────────────────────────────────────────────
print("\n=== ID Documents ===")
for loc in LOCALES:
    g = TextDummy(loc)
    docs = g.available_documents()
    print(f"  {loc:6s} → {g.id_document():25s}  types: {docs}")

# ── Currency & Price ──────────────────────────────────────────
print("\n=== Currency & Price ===")
for loc in LOCALES:
    g = TextDummy(loc)
    print(f"  {loc:6s} → {g.currency_code():4s} ({g.currency_symbol():3s})  price: {g.price()}")

# ── Random Numbers ────────────────────────────────────────────
print("\n=== Random Numbers (locale-aware separators) ===")
for loc in LOCALES:
    g = TextDummy(loc)
    integer = g.random_number("integer", digits=7)
    decimal = g.random_number("float", digits=6, decimals=2)
    cur = g.random_number("float", digits=5, decimals=2, currency=True)
    print(f"  {loc:6s} → int: {integer:>12s}  float: {decimal:>12s}  currency: {cur}")

# ── Dates ─────────────────────────────────────────────────────
print("\n=== Dates ===")
for loc in LOCALES:
    g = TextDummy(loc)
    fmt = g.profile.date_format if g.profile else "N/A"
    print(f"  {loc:6s} → {g.random_date('2020-01-01', '2025-12-31'):12s}  format: {fmt}")

# ── Gender labels ─────────────────────────────────────────────
print("\n=== Gender (locale-aware labels) ===")
for loc in LOCALES:
    g = TextDummy(loc)
    samples = sorted(set(g.gender() for _ in range(20)))
    print(f"  {loc:6s} → {' / '.join(samples)}")

# ── Phone numbers ─────────────────────────────────────────────
print("\n=== Phone Numbers ===")
for loc in LOCALES:
    g = TextDummy(loc)
    prefix = g.profile.phone_prefix if g.profile else "?"
    print(f"  {loc:6s} ({prefix:>4s}) → {g.phone()}")

# ── Addresses ─────────────────────────────────────────────────
print("\n=== Addresses ===")
for loc in LOCALES:
    g = TextDummy(loc)
    addr = g.address().replace("\n", ", ")
    print(f"  {loc:6s} → {addr[:70]}")

# ── Pydantic: same model, different locales ───────────────────
print("\n=== Pydantic — same model in different locales ===")
try:
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        email: str
        gender: str
        age: int

    for loc in ["es_ES", "en_US", "fr_FR", "pt_BR", "de_DE"]:
        g = TextDummy(loc)
        p = g.fill_model(Person)
        print(f"  {loc:6s} → {p.name:30s} | {p.gender:10s} | age={p.age:3d} | {p.email}")
except ImportError:
    print("  (pydantic not installed — skipping)")

# ── Unsupported locale — still works for basics ──────────────
print("\n=== Unsupported locale (ja_JP) ===")
gen_jp = TextDummy("ja_JP")
print(f"  Name:        {gen_jp.name()}")
print(f"  Email:       {gen_jp.email()}")
print(f"  City:        {gen_jp.city()}")
print(f"  Has profile: {gen_jp.profile is not None}")
