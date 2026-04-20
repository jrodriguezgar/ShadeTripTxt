"""
Dates & Random Numbers
=======================
Locale-aware date formatting, random dates with ranges/masks,
and random numbers with locale-specific separators and currency.

README sections: Dates, Random Numbers
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Date (locale format) ─────────────────────────────────────
print("=== Date ===")
print(f"  Locale format:  {gen.date()}")
print(f"  Custom pattern: {gen.date('%Y-%m-%d')}")

# ── Random Date ───────────────────────────────────────────────
print("\n=== Random Date ===")
print(f"  Default:           {gen.random_date()}")
print(f"  Range 2020-2025:   {gen.random_date('2020-01-01', '2025-12-31')}")
print(f"  ISO pattern:       {gen.random_date(pattern='%Y-%m-%d')}")
print(f"  Mask year/month:   {gen.random_date(mask='FEC-{year}{month}{day}')}")
print(f"  Mask quarter:      {gen.random_date('2020-01-01', '2025-12-31', mask='Report_{year}-Q{quarter}')}")
print(f"  Mask full date:    {gen.random_date(mask='Created on: {date}')}")

# ── Dates across locales ─────────────────────────────────────
print("\n=== Dates by locale ===")
for loc in ["es_ES", "en_US", "de_DE", "fr_FR", "pt_BR"]:
    g = TextDummy(loc)
    fmt = g.profile.date_format if g.profile else "N/A"
    print(f"  {loc} → {g.random_date('2020-01-01', '2025-12-31'):12s}  format: {fmt}")

# ── Random Number — basic ────────────────────────────────────
print("\n=== Random Number (es_ES) ===")
print(f"  Integer (6 digits):  {gen.random_number()}")
print(f"  Integer (4 digits):  {gen.random_number('integer', digits=4)}")
print(f"  Float (2 dec):       {gen.random_number('float')}")
print(f"  Float (4 dec):       {gen.random_number('float', decimals=4)}")
print(f"  min/max int:         {gen.random_number('integer', min_val=1, max_val=100)}")
print(f"  min/max float:       {gen.random_number('float', min_val=0, max_val=1, decimals=6)}")

# ── Random Number — currency ─────────────────────────────────
print("\n=== Random Number with currency ===")
print(f"  es_ES: {gen.random_number('float', currency=True)}")
gen_us = TextDummy("en_US")
print(f"  en_US: {gen_us.random_number('float', currency=True)}")
gen_fr = TextDummy("fr_FR")
print(f"  fr_FR: {gen_fr.random_number('float', currency=True)}")
gen_de = TextDummy("de_DE")
print(f"  de_DE: {gen_de.random_number('float', currency=True)}")
gen_br = TextDummy("pt_BR")
print(f"  pt_BR: {gen_br.random_number('float', currency=True)}")

# ── Random Number — masks ────────────────────────────────────
print("\n=== Random Number with masks ===")
print(f"  Mask # digits:    {gen.random_number(mask='REF-######')}")
print(f"  Mask {{value}}:     {gen.random_number('float', mask='Total: {currency}{value}')}")
print(f"  Mask {{currency}}:  {gen.random_number('integer', mask='{value} {currency}')}")

# ── Number formatting across locales ──────────────────────────
print("\n=== Number formatting by locale ===")
for loc in ["es_ES", "en_US", "fr_FR", "de_DE", "pt_BR", "it_IT"]:
    g = TextDummy(loc)
    integer = g.random_number(number_type="integer", digits=7)
    decimal = g.random_number(number_type="float", digits=6, decimals=2)
    cur = g.random_number(number_type="float", digits=5, decimals=2, currency=True)
    print(f"  {loc} → int: {integer:>12s}  float: {decimal:>12s}  currency: {cur}")
