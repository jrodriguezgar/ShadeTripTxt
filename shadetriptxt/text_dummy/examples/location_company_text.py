"""
Location, Company & Text
=========================
Address/city/country, company/job/department,
and text generation (words, sentences, paragraphs).

README sections: Location, Company, Text
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Location ──────────────────────────────────────────────────
print("=== Location ===")
print(f"  Address:  {gen.address()}")
print(f"  City:     {gen.city()}")
print(f"  State:    {gen.state()}")
print(f"  Postcode: {gen.postcode()}")
print(f"  Country:  {gen.country()}")

# ── Company ───────────────────────────────────────────────────
print("\n=== Company ===")
print(f"  Company:    {gen.company()}")
print(f"  Job:        {gen.job()}")
print(f"  Department: {gen.department()}")

# ── Text ──────────────────────────────────────────────────────
print("\n=== Text ===")
print(f"  Word:         {gen.word()}")
print(f"  Words(3):     {gen.words(3)}")
print(f"  Sentence:     {gen.sentence()}")
print(f"  Paragraph(2): {gen.paragraph(2)}")
print(f"  Text(80):     {gen.text(80)}")
