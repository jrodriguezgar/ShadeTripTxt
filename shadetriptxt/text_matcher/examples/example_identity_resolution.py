"""
Example: Identity Resolution
=============================
Match incoming records against a reference database to validate and
correct person and company names.

Demonstrates a two-phase lookup:
    1. find_best_match()        — fast fuzzy search for the closest candidate
    2. compare_name_bytokens()  — token-level alignment for multi-word names

Run: python -m shadetriptxt.text_matcher.examples.example_identity_resolution
"""

from typing import Optional, Tuple, List

from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig


# ── Reference data (simulates a database) ────────────────────

PERSON_DB = [
    ("P001", "Juan Francisco Dieguez"),
    ("P002", "María García López"),
    ("P003", "José Rodríguez Villa"),
    ("P004", "Ana Martínez Sánchez"),
    ("P005", "Carlos Miguel Mateo"),
    ("P006", "Laura Fernández"),
    ("P007", "David López"),
]

COMPANY_DB = [
    ("C001", "Google Inc."),
    ("C002", "Microsoft Corp."),
    ("C003", "Apple S.A."),
    ("C004", "Amazon Web Services"),
    ("C005", "Oracle Corp"),
]


def resolve(
    input_name: str,
    reference: List[Tuple[str, str]],
    matcher: TextMatcher,
) -> Tuple[Optional[str], Optional[str], float, str]:
    """
    Find the best-matching record for *input_name* in *reference*.

    Returns:
        (record_id, matched_name, score, status)
    """
    ref_names = [name for _, name in reference]

    # Phase 1 — fast fuzzy lookup
    best, score, _ = matcher.find_best_match(input_name, ref_names, threshold=0.60)

    if best and score >= 0.85:
        rec_id = next(rid for rid, n in reference if n == best)
        return rec_id, best, score, "validated"

    # Phase 2 — token-level alignment (handles abbreviations, reorder)
    best_token_match = None
    best_token_id = None
    best_token_score = 0.0

    for rec_id, ref_name in reference:
        is_match, metrics = matcher.compare_name_bytokens(input_name, ref_name)
        lev = metrics.get("levenshtein_ratio", 0.0)

        if is_match and lev > best_token_score:
            best_token_score = lev
            best_token_match = ref_name
            best_token_id = rec_id

    if best_token_match:
        return best_token_id, best_token_match, best_token_score, "validated (token)"

    # Phase 3 — return approximate match if available
    if best:
        rec_id = next(rid for rid, n in reference if n == best)
        return rec_id, best, score, "approximate — review"

    return None, None, 0.0, "no match"


def main() -> None:
    """Run the identity-resolution example."""
    print()
    print("=" * 70)
    print("Identity Resolution — Validate Incoming Records Against Database")
    print("=" * 70)

    matcher = TextMatcher(config=MatcherConfig.lenient(), locale="es_ES")

    incoming = [
        # Person names (typos, abbreviations, accent issues)
        {"name": "Juan Fco Dieguez", "type": "Person"},
        {"name": "Maria G. Lopez", "type": "Person"},
        {"name": "Jose R. Villa", "type": "Person"},
        {"name": "Ana M Sanchez", "type": "Person"},
        {"name": "Carlos Mateos", "type": "Person"},
        {"name": "Albert Einstein", "type": "Person"},   # not in DB
        # Company names (typos)
        {"name": "Gooogle Inc", "type": "Company"},
        {"name": "Microsot Corp", "type": "Company"},
        {"name": "Aple SA", "type": "Company"},
        {"name": "Tesla Motors", "type": "Company"},      # not in DB
    ]

    print(f"\n  {'Input':<25} {'Type':<10} {'Match':<25} {'Score':<8} {'Status'}")
    print("  " + "-" * 80)

    matched = 0
    for item in incoming:
        ref = PERSON_DB if item["type"] == "Person" else COMPANY_DB
        rec_id, name, score, status = resolve(item["name"], ref, matcher)

        name_str = f"[{rec_id}] {name}" if rec_id else "—"
        score_str = f"{score:.4f}" if rec_id else "—"
        print(f"  {item['name']:<25} {item['type']:<10} {name_str:<25} {score_str:<8} {status}")

        if rec_id:
            matched += 1

    total = len(incoming)
    print(f"\n  Total: {total} | Matched: {matched} | Unmatched: {total - matched}")
    print("\nIdentity-resolution example completed.\n")


if __name__ == "__main__":
    main()
