"""
Personal Data
==============
Personal Data + Extra Personal Data: names, email, phone,
date of birth, gender, age, password, prefix, suffix, SSN,
and full profile.

README sections: Personal Data, Extra Personal Data
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Personal Data ─────────────────────────────────────────────
print("=== Personal Data ===")
print(f"  Name:       {gen.name()}")
print(f"  First name: {gen.first_name()}")
print(f"  Last name:  {gen.last_name()}")
print(f"  Email:      {gen.email()}")
print(f"  Phone:      {gen.phone()}")

# ── Extra Personal Data ───────────────────────────────────────
print("\n=== Extra Personal Data ===")
print(f"  Date of birth:     {gen.date_of_birth()}")
print(f"  DOB (25-35):       {gen.date_of_birth(25, 35)}")
print(f"  Prefix:            {gen.prefix()}")
print(f"  Suffix:            {gen.suffix()}")
print(f"  SSN:               {gen.ssn()}")

# ── Gender (locale-aware labels) ──────────────────────────────
print("\n=== Gender ===")
locales = ["es_ES", "en_US", "fr_FR", "de_DE", "it_IT", "pt_BR"]
for loc in locales:
    g = TextDummy(loc)
    samples = [g.gender() for _ in range(4)]
    print(f"  {loc}: {', '.join(samples)}")

# ── Age ───────────────────────────────────────────────────────
print("\n=== Age ===")
ages_default = [gen.age() for _ in range(10)]
ages_custom = [gen.age(min_val=25, max_val=35) for _ in range(10)]
ages_child = [gen.age(min_val=0, max_val=12) for _ in range(10)]
print(f"  Default (18-80):  {ages_default}")
print(f"  Custom  (25-35):  {ages_custom}")
print(f"  Children (0-12):  {ages_child}")

# ── Password ──────────────────────────────────────────────────
print("\n=== Password ===")
print(f"  Default (12 chars):   {gen.password()}")
print(f"  Long (20 chars):      {gen.password(length=20)}")
print(f"  PIN (digits only):    {gen.password(length=6, upper=False, lower=False, special=False)}")
print(f"  Letters only:         {gen.password(length=16, digits=False, special=False)}")
print(f"  Upper + digits:       {gen.password(length=10, lower=False, special=False)}")

# ── Full Profile ──────────────────────────────────────────────
print("\n=== Full Profile ===")
profile = gen.profile_data()
for key, value in profile.items():
    print(f"  {key:15s} {value}")
