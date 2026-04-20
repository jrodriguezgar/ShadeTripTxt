"""
Custom Generators & Random Selection
======================================
Register custom generators (list-backed or callable-backed),
and use static random selection utilities: random_from_list,
random_sample_from_list, weighted_random_from_list.

README sections: Custom Generators, Random Selection from Lists
"""

import random
from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ══════════════════════════════════════════════════════════════
#  CUSTOM GENERATORS
# ══════════════════════════════════════════════════════════════

# ── Register list-backed generators ───────────────────────────
gen.register_custom("t_shirt_size", ["XS", "S", "M", "L", "XL", "XXL"])
gen.register_custom("priority", ["Low", "Medium", "High", "Critical"])

# ── Register callable-backed generators ───────────────────────
gen.register_custom(
    "order_code",
    lambda: f"ORD-{random.randint(10000, 99999)}"
)
gen.register_custom(
    "score",
    lambda: round(random.uniform(0, 100), 1)
)

# ── Generate values ───────────────────────────────────────────
print("=== Custom Generators ===")
print(f"  T-shirt size: {gen.run_custom('t_shirt_size')}")
print(f"  Priority:     {gen.run_custom('priority')}")
print(f"  Order code:   {gen.run_custom('order_code')}")
print(f"  Score:        {gen.run_custom('score')}")

# ── List registered generators ────────────────────────────────
print("\n=== Registered Generators ===")
for name, desc in gen.list_custom().items():
    print(f"  {name}: {desc}")

# ── Batch with custom generators ─────────────────────────────
print("\n=== Batch (5 priorities) ===")
for val in gen.generate_batch("priority", 5):
    print(f"  - {val}")

# ── Unregister ────────────────────────────────────────────────
gen.unregister_custom("score")
print(f"\n  After unregister 'score': {list(gen.list_custom().keys())}")

# ══════════════════════════════════════════════════════════════
#  RANDOM SELECTION FROM LISTS
# ══════════════════════════════════════════════════════════════

colors = ["Red", "Green", "Blue", "Yellow", "Purple"]

# ── random_from_list ──────────────────────────────────────────
print("\n=== random_from_list ===")
print(f"  Pick one: {TextDummy.random_from_list(colors)}")

# ── random_sample_from_list ──────────────────────────────────
print("\n=== random_sample_from_list ===")
print(f"  3 with duplicates:    {TextDummy.random_sample_from_list(colors, count=3)}")
print(f"  3 without duplicates: {TextDummy.random_sample_from_list(colors, count=3, allow_duplicates=False)}")

# ── weighted_random_from_list ─────────────────────────────────
print("\n=== weighted_random_from_list ===")
tiers = ["Free", "Basic", "Premium", "Enterprise"]
weights = [0.50, 0.30, 0.15, 0.05]
results = [TextDummy.weighted_random_from_list(tiers, weights) for _ in range(20)]
print(f"  20 picks: {results}")
print("  Distribution:")
for tier in tiers:
    count = results.count(tier)
    print(f"    {tier}: {count}/20")
