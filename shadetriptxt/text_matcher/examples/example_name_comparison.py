"""
Example: Name Comparison
========================
Demonstrates single-word and multi-word name comparison.

Features:
    - compare_names()          — single-word comparison with accent, nickname,
                                 and phonetic handling
    - compare_name_bytokens()  — multi-word full-name comparison with token
                                 alignment and abbreviation expansion

Run: python -m shadetriptxt.text_matcher.examples.example_name_comparison
"""

from shadetriptxt.text_matcher.text_matcher import TextMatcher


def example_single_word() -> None:
    """Compare individual words / first names with compare_names()."""
    print("=" * 70)
    print("1. Single-Word Comparison (compare_names)")
    print("=" * 70)

    matcher = TextMatcher(locale="es_ES")

    pairs = [
        ("José", "Jose", "Accent removal"),
        ("María", "Maria", "Accent variation"),
        ("François", "Francois", "French accent"),
        ("Smith", "Smyth", "Name variant"),
        ("Paco", "Francisco", "Spanish nickname"),
        ("Juan", "Pedro", "Different names"),
    ]

    for name1, name2, description in pairs:
        is_match, metrics = matcher.compare_names(name1, name2)
        lev = metrics.get("levenshtein_ratio", "-")
        print(f"\n  {description}:")
        print(f"    '{name1}' vs '{name2}' → {is_match}  (Lev: {lev})")

    # Strict vs normal mode
    print("\n\n  Strict vs Normal mode:")
    print("  " + "-" * 50)

    for name1, name2 in [("Michael", "Mikhail"), ("Smith", "Smyth")]:
        is_normal, _ = matcher.compare_names(name1, name2, strict=False)
        is_strict, _ = matcher.compare_names(name1, name2, strict=True)
        print(f"    '{name1}' vs '{name2}': normal={is_normal}, strict={is_strict}")


def example_full_name() -> None:
    """Compare multi-word names with compare_name_bytokens()."""
    print("\n\n" + "=" * 70)
    print("2. Full-Name Comparison (compare_name_bytokens)")
    print("=" * 70)

    matcher = TextMatcher(locale="es_ES")

    pairs = [
        ("José García López", "Jose Garcia Lopez", "Accents removed"),
        ("Juan Fco García", "Juan Francisco García", "Abbreviation expansion"),
        ("Fritz Müller", "Friedrich Muller", "German nickname + accent"),
        ("García López, Juan", "Juan García López", "Token reorder"),
        ("Ana García", "Ana Martínez", "Different surname"),
    ]

    for name1, name2, description in pairs:
        is_match, metrics = matcher.compare_name_bytokens(name1, name2)
        rule = metrics.get("rule_applied", "-")
        print(f"\n  {description}:")
        print(f"    '{name1}' vs '{name2}' → {is_match}  (rule: {rule})")


def main() -> None:
    """Run all name-comparison examples."""
    print()
    example_single_word()
    example_full_name()
    print("\n\nAll name-comparison examples completed.\n")


if __name__ == "__main__":
    main()
