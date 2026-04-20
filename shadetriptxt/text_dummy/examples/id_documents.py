"""
ID Documents
=============
Country-specific identification numbers: DNI/NIF, NIE, SSN,
EIN, CPF, CNPJ, CURP, RFC, RUT, NINO, NIF, NIR,
Personalausweis, Codice Fiscale.

README section: ID Documents
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

# ── Spain (es_ES) ────────────────────────────────────────────
print("=== Spain (es_ES) ===")
gen = TextDummy("es_ES")
print(f"  DNI/NIF (primary):  {gen.id_document()}")
print(f"  NIE (alternative):  {gen.id_document('NIE')}")
print(f"  dni() alias:        {gen.dni()}")
print(f"  Available types:    {gen.available_documents()}")

# ── All locales ───────────────────────────────────────────────
print("\n=== ID Documents across all locales ===")
cases = [
    ("es_ES", None,   "DNI/NIF"),
    ("es_ES", "NIE",  "NIE"),
    ("es_MX", None,   "CURP"),
    ("es_MX", "RFC",  "RFC"),
    ("es_AR", None,   "DNI"),
    ("es_AR", "CUIL", "CUIL"),
    ("es_CO", None,   "Cédula"),
    ("es_CL", None,   "RUT"),
    ("en_US", None,   "SSN"),
    ("en_US", "EIN",  "EIN"),
    ("en_GB", None,   "NINO"),
    ("pt_BR", None,   "CPF"),
    ("pt_BR", "CNPJ", "CNPJ"),
    ("pt_PT", None,   "NIF"),
    ("fr_FR", None,   "NIR"),
    ("de_DE", None,   "Personalausweis"),
    ("it_IT", None,   "Codice Fiscale"),
]
for locale, doc_type, label in cases:
    g = TextDummy(locale)
    result = g.id_document(doc_type)
    print(f"  {locale}  {label:20s} → {result}")

# ── Available doc types per locale ────────────────────────────
print("\n=== Available document types per locale ===")
for loc in ["es_ES", "es_MX", "es_AR", "en_US", "pt_BR", "en_GB"]:
    g = TextDummy(loc)
    print(f"  {loc}: {g.available_documents()}")
