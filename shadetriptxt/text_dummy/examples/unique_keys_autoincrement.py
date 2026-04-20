"""
Unique Keys & Autoincrement
=============================
Guaranteed-unique random keys (alphanumeric, hex, numeric, UUID,
alpha) with prefix/suffix/segments/groups.
Sequential auto-incrementing counters with prefix/zfill/step/groups.

README sections: Unique Keys, Autoincrement
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

# ══════════════════════════════════════════════════════════════
#  UNIQUE KEYS
# ══════════════════════════════════════════════════════════════

gen = TextDummy("es_ES")

# ── Basic (alphanumeric, 8 chars) ─────────────────────────────
print("=== unique_key: basic ===")
for _ in range(5):
    print(f"  {gen.unique_key()}")

# ── Prefix + suffix ──────────────────────────────────────────
print("\n=== unique_key: prefix + suffix ===")
for _ in range(3):
    print(f"  {gen.unique_key(prefix='USR-', suffix='-ES', length=6)}")

# ── Hex with segments (####-####-####) ────────────────────────
print("\n=== unique_key: hex segmented ===")
for _ in range(3):
    print(f"  {gen.unique_key(key_type='hex', length=12, separator='-', segment_length=4)}")

# ── Numeric ───────────────────────────────────────────────────
print("\n=== unique_key: numeric ===")
for _ in range(3):
    print(f"  {gen.unique_key(key_type='numeric', length=10, prefix='INV-')}")

# ── UUID ──────────────────────────────────────────────────────
print("\n=== unique_key: uuid ===")
for _ in range(3):
    print(f"  {gen.unique_key(key_type='uuid')}")

# ── Alpha lowercase ──────────────────────────────────────────
print("\n=== unique_key: alpha lowercase ===")
for _ in range(3):
    print(f"  {gen.unique_key(key_type='alpha', length=10, uppercase=False)}")

# ── Independent groups ────────────────────────────────────────
print("\n=== unique_key: independent groups ===")
gen2 = TextDummy("en_US")
for _ in range(3):
    client = gen2.unique_key(prefix="CLI-", length=4, group="clients")
    order = gen2.unique_key(prefix="ORD-", length=6, group="orders")
    print(f"  client={client}  order={order}")

# ── Reset ─────────────────────────────────────────────────────
print("\n=== unique_key: reset ===")
used_before = len(gen2._used_keys.get("clients", set()))
gen2.reset_unique_keys("clients")
used_after = len(gen2._used_keys.get("clients", set()))
print(f"  Before reset: {used_before} keys tracked")
print(f"  After reset:  {used_after} keys tracked")

# ══════════════════════════════════════════════════════════════
#  AUTOINCREMENT
# ══════════════════════════════════════════════════════════════

# ── Basic (1, 2, 3...) ───────────────────────────────────────
gen3 = TextDummy("es_ES")
print("\n=== autoincrement: basic ===")
for _ in range(5):
    print(f"  {gen3.autoincrement()}")

# ── Prefix + zfill ───────────────────────────────────────────
gen4 = TextDummy("es_ES")
print("\n=== autoincrement: prefix + zfill ===")
for _ in range(5):
    print(f"  {gen4.autoincrement(prefix='EMP-', zfill=5)}")

# ── Custom start and step ────────────────────────────────────
gen5 = TextDummy("es_ES")
print("\n=== autoincrement: start=1000, step=10 ===")
for _ in range(5):
    print(f"  {gen5.autoincrement(start=1000, step=10, group='tens')}")

# ── Suffix ────────────────────────────────────────────────────
gen6 = TextDummy("es_ES")
print("\n=== autoincrement: suffix ===")
for _ in range(3):
    print(f"  {gen6.autoincrement(start=1, suffix='-A', group='sfx')}")

# ── Independent groups ────────────────────────────────────────
gen7 = TextDummy("es_ES")
print("\n=== autoincrement: independent groups ===")
for _ in range(4):
    emp = gen7.autoincrement(start=100, prefix="EMP-", zfill=4, group="employees")
    inv = gen7.autoincrement(start=5000, step=5, prefix="INV-", group="invoices")
    print(f"  employee={emp}  invoice={inv}")

# ── Reset ─────────────────────────────────────────────────────
print("\n=== autoincrement: reset ===")
gen7.reset_autoincrement("employees")
new_val = gen7.autoincrement(start=100, prefix="EMP-", zfill=4, group="employees")
print(f"  After resetting 'employees': {new_val} (restarts)")

# ══════════════════════════════════════════════════════════════
#  PYDANTIC INTEGRATION
# ══════════════════════════════════════════════════════════════

print("\n=== Pydantic: DummyField with unique_key + autoincrement ===")
try:
    from typing import Annotated
    from pydantic import BaseModel
    from shadetriptxt.text_dummy.text_dummy import DummyField

    class Employee(BaseModel):
        emp_id: Annotated[str, DummyField("autoincrement", start=1000, prefix="EMP-", zfill=5)]
        ref_code: Annotated[str, DummyField("unique_key", prefix="REF-", length=6, key_type="hex")]
        name: str
        email: str

    gen_p = TextDummy("es_ES")
    employees = gen_p.fill_model_batch(Employee, count=5)
    for e in employees:
        print(f"  {e.emp_id} | {e.ref_code} | {e.name} | {e.email}")
except ImportError:
    print("  (pydantic not installed — skipping)")
