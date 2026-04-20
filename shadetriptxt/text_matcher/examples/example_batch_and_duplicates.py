"""
Example: Batch Comparison and Duplicate Detection
==================================================
Process many pairs at once and find duplicates in a list.

Features:
    - batch_compare()      — evaluate many (text1, text2) pairs efficiently
    - detect_duplicates()   — find duplicate entries in a list above a threshold

Run: python -m shadetriptxt.text_matcher.examples.example_batch_and_duplicates
"""

from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig


def example_batch_compare() -> None:
    """Evaluate a list of pairs with batch_compare()."""
    print("=" * 70)
    print("1. Batch Comparison (batch_compare)")
    print("=" * 70)

    matcher = TextMatcher()

    pairs = [
        ("programacion", "programación"),
        ("desarrollo", "desarollo"),
        ("computadora", "computador"),
        ("telefono", "telefno"),
        ("aplicacion", "aplikacion"),
        ("organizacion", "organisation"),
        ("color", "colour"),
        ("teatro", "theatro"),
    ]

    results = matcher.batch_compare(pairs)

    print(f"\n  {'Word 1':<20} {'Word 2':<20} {'Match':<8} {'Lev':<10} {'JW':<10}")
    print("  " + "-" * 68)

    for (w1, w2), (is_match, metrics) in zip(pairs, results):
        lev = metrics.get("levenshtein_ratio", 0)
        jw = metrics.get("jaro_winkler_score", 0)
        mark = "✓" if is_match else "✗"
        print(f"  {w1:<20} {w2:<20} {mark:<8} {lev:<10.4f} {jw:<10.2f}")

    match_count = sum(1 for m, _ in results if m)
    print(f"\n  Total: {len(pairs)} pairs | Matches: {match_count} | "
          f"Rate: {match_count / len(pairs) * 100:.1f}%")


def example_detect_duplicates() -> None:
    """Find duplicates in a name list with detect_duplicates()."""
    print("\n\n" + "=" * 70)
    print("2. Duplicate Detection (detect_duplicates)")
    print("=" * 70)

    matcher = TextMatcher(
        config=MatcherConfig.lenient(),
        locale="es_ES",
    )

    names = [
        "José García López",
        "Jose Garcia Lopez",
        "María Fernández",
        "Maria Fernandez",
        "Carlos Ruiz",
        "Pedro Martínez",
    ]

    print("\n  Input list:")
    for i, name in enumerate(names, 1):
        print(f"    {i}. {name}")

    duplicates = matcher.detect_duplicates(names, threshold=0.85)

    print(f"\n  Duplicates found ({len(duplicates)}):")
    for name1, name2, score in duplicates:
        print(f"    '{name1}' ≈ '{name2}'  (score: {score:.4f})")


def main() -> None:
    """Run all batch / duplicate examples."""
    print()
    example_batch_compare()
    example_detect_duplicates()
    print("\n\nAll batch & duplicate examples completed.\n")


if __name__ == "__main__":
    main()
