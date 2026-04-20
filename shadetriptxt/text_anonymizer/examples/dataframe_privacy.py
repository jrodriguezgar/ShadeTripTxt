"""
Example: DataFrame Anonymization & Privacy Metrics
====================================================
Anonymize columns in a DataFrame, apply k-Anonymity / l-Diversity /
t-Closeness, and measure privacy metrics with pycanon.

Covers documentation sections:
  - 3.8 k-Anonymity, l-Diversity and t-Closeness
  - 5.4 Anonymize DataFrames with k-Anonymity
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
from shadetriptxt.text_anonymizer import TextAnonymizer, PiiType, Strategy

# ── 1. Create sample DataFrame ──
print("=" * 70)
print("1. SAMPLE DATAFRAME")
print("=" * 70)
df = pd.DataFrame({
    "name": ["Juan García", "María López", "Carlos Ruiz", "Ana Martín",
             "Pedro Sánchez", "Laura Torres", "Diego Flores", "Elena Vega"],
    "email": ["juan@test.com", "maria@test.com", "carlos@test.com",
              "ana@test.com", "pedro@test.com", "laura@test.com",
              "diego@test.com", "elena@test.com"],
    "phone": ["611001001", "622002002", "633003003", "644004004",
              "655005005", "666006006", "677007007", "688008008"],
    "age": [25, 32, 45, 28, 55, 38, 42, 30],
    "city": ["Madrid", "Barcelona", "Madrid", "Sevilla",
             "Madrid", "Barcelona", "Valencia", "Madrid"],
    "salary": [30000, 45000, 55000, 35000, 65000, 48000, 52000, 40000],
})
print(df.to_string(index=False))
print()

# ── 2. Column-level anonymization by field name ──
print("=" * 70)
print("2. COLUMN ANONYMIZATION (auto-detect by field name)")
print("=" * 70)
anon = TextAnonymizer(locale="es_ES", strategy="mask")
df_anon = anon.anonymize_columns(df)
print(df_anon.to_string(index=False))
print()

# ── 3. Strategy: REDACT ──
print("=" * 70)
print("3. COLUMN ANONYMIZATION -- REDACT")
print("=" * 70)
anon_r = TextAnonymizer(locale="es_ES", strategy="redact")
df_redact = anon_r.anonymize_columns(df)
print(df_redact[["name", "email", "phone", "city"]].to_string(index=False))
print()

# ── 4. Explicit column types ──
print("=" * 70)
print("4. EXPLICIT COLUMN TYPES")
print("=" * 70)
df_custom = anon.anonymize_columns(
    df,
    column_types={"salary": PiiType.CURRENCY},
    strategy="redact",
)
print(df_custom[["name", "salary"]].to_string(index=False))
print()

# ── 5. Column whitelist ──
print("=" * 70)
print("5. COLUMN WHITELIST -- anonymize only specific columns")
print("=" * 70)
df_partial = anon.anonymize_columns(
    df,
    columns=["email", "phone"],
    strategy="redact",
)
print(df_partial[["name", "email", "phone"]].to_string(index=False))
print("  -> Only email and phone anonymized; name untouched")
print()

# ── 6. Privacy metrics with pycanon ──
print("=" * 70)
print("6. PRIVACY METRICS (pycanon)")
print("=" * 70)
try:
    print("On original data:")
    report_orig = anon.measure_privacy(
        df, quasi_identifiers=["age", "city"], sensitive_attrs=["salary"],
    )
    print(f"  k-anonymity:  {report_orig.k_anonymity}")
    print(f"  l-diversity:  {report_orig.l_diversity}")
    print(f"  t-closeness:  {report_orig.t_closeness:.4f}")
except Exception as e:
    print(f"  Privacy metrics skipped (requires pycanon): {e}")
print()

# ── 7. k-Anonymity generalization (python-anonymity) ──
print("=" * 70)
print("7. k-ANONYMITY GENERALIZATION (python-anonymity)")
print("=" * 70)
print("Applying data_fly with identifiers suppressed:")
try:
    df_kanon = anon.anonymize_dataframe(
        df,
        identifiers=["name", "email", "phone"],
        quasi_identifiers=["age", "city"],
        k=2,
        supp_threshold=2,
    )
    print(df_kanon.to_string(index=False))
    print()

    # Measure after anonymization
    report_after = anon.measure_privacy(
        df_kanon, quasi_identifiers=["age", "city"], sensitive_attrs=["salary"],
    )
    print(f"  k-anonymity after: {report_after.k_anonymity}")
    if report_after.l_diversity:
        print(f"  l-diversity after: {report_after.l_diversity}")
except Exception as e:
    print(f"  k-anonymity skipped (library issue): {e}")

# ── 8. l-Diversity (python-anonymity) ──
print()
print("=" * 70)
print("8. l-DIVERSITY -- diverse sensitive values per group")
print("=" * 70)
try:
    df_ldiv = anon.apply_l_diversity(
        df,
        sensitive_attrs=["salary"],
        quasi_identifiers=["age", "city"],
        l=2,
        identifiers=["name", "email", "phone"],
    )
    print(df_ldiv.to_string(index=False))
except Exception as e:
    print(f"  l-diversity skipped (library issue): {e}")

# ── 9. t-Closeness (python-anonymity) ──
print()
print("=" * 70)
print("9. t-CLOSENESS -- distribution protection")
print("=" * 70)
try:
    df_tclose = anon.apply_t_closeness(
        df,
        sensitive_attrs=["salary"],
        quasi_identifiers=["age", "city"],
        t=0.2,
        identifiers=["name", "email", "phone"],
    )
    print(df_tclose.to_string(index=False))
except Exception as e:
    print(f"  t-closeness skipped (library issue): {e}")

