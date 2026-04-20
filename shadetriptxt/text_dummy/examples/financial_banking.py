"""
Financial & Banking
====================
Currency, price, IBAN, BBAN, SWIFT, credit cards,
and cryptocurrency generators.

README section: Financial / Banking
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Currency ──────────────────────────────────────────────────
print("=== Currency ===")
print(f"  Code:   {gen.currency_code()}")
print(f"  Symbol: {gen.currency_symbol()}")
print(f"  Price:  {gen.price()}")
print(f"  Price (10-50, 0 dec): {gen.price(10, 50, 0)}")

# ── Banking ───────────────────────────────────────────────────
print("\n=== Banking ===")
print(f"  IBAN:  {gen.iban()}")
print(f"  BBAN:  {gen.bban()}")
print(f"  SWIFT: {gen.swift()}")

# ── Credit Cards ──────────────────────────────────────────────
print("\n=== Credit Cards ===")
print(f"  Number:        {gen.credit_card_number()}")
print(f"  Expiry:        {gen.credit_card_expire()}")
print(f"  Provider:      {gen.credit_card_provider()}")
print(f"  Security code: {gen.credit_card_security_code()}")
print(f"  Full details:\n{gen.credit_card_full()}")

# ── Cryptocurrency ────────────────────────────────────────────
print("\n=== Cryptocurrency ===")
print(f"  Code: {gen.cryptocurrency_code()}")
print(f"  Name: {gen.cryptocurrency_name()}")

# ── Currency & Price across locales ───────────────────────────
print("\n=== Currency & Price by locale ===")
for loc in ["es_ES", "en_US", "en_GB", "pt_BR", "fr_FR", "de_DE"]:
    g = TextDummy(loc)
    print(f"  {loc} → {g.currency_code():4s} ({g.currency_symbol():3s})  price: {g.price()}")
