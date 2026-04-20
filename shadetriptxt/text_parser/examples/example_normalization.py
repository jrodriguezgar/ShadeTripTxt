"""
Example: Text Normalization
=============================
Demonstrates text normalization and its integration with TextMatcher.

Features:
    - TextParser.normalize()        — configurable normalization pipeline
    - TextMatcher with MatcherConfig  — normalization flags affect matching
    - detect_duplicates()            — deduplication with normalization

Run: python -m shadetriptxt.text_parser.examples.example_normalization
"""

from shadetriptxt.text_parser.text_parser import TextParser
from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig


def example_basic_normalization() -> None:
    """Apply normalization with various options."""
    print("=" * 70)
    print("1. Basic Text Normalization")
    print("=" * 70)

    parser = TextParser("es_ES")

    cases = [
        "  multiple   spaces  ",
        "Hello, World!",
        "José García",
        "Text (with parentheses)",
        "Mix   of    everything!!!",
    ]

    print()
    for text in cases:
        normalized = parser.normalize(text)
        print(f"  '{text}'")
        print(f"     → '{normalized}'\n")


def example_matcher_normalization() -> None:
    """Show how MatcherConfig flags control normalization during matching."""
    print("=" * 70)
    print("2. TextMatcher with Normalization")
    print("=" * 70)

    config = MatcherConfig(
        normalize_punctuation=True,
        normalize_parentheses=False,
        remove_accents=True,
        levenshtein_threshold=0.85,
    )
    matcher = TextMatcher(config=config)

    pairs = [
        ("José", "Jose", True),
        ("Hello,  World!", "Hello World", True),
        ("Test   String", "Test String", True),
        ("Apple", "Orange", False),
    ]

    print()
    for name1, name2, expected in pairs:
        is_match, metrics = matcher.compare_names(name1, name2)
        score = metrics.get("levenshtein_ratio", 0.0)
        status = "PASS" if is_match == expected else "FAIL"
        print(f"  '{name1}' vs '{name2}' → {is_match} (score: {score:.4f})  [{status}]")


def example_duplicate_detection() -> None:
    """Detect duplicates that differ only by accents, spaces, or parentheses."""
    print("\n\n" + "=" * 70)
    print("3. Duplicate Detection with Normalization")
    print("=" * 70)

    config = MatcherConfig(
        normalize_punctuation=True,
        normalize_parentheses=True,
        remove_accents=True,
    )
    matcher = TextMatcher(config=config)

    items = [
        "José García",
        "Jose Garcia",
        "John  Smith",
        "John Smith",
        "Mary (Jane) Doe",
        "Mary Doe",
        "Peter Pan",
        "Paul McCartney",
    ]

    print("\n  Input list:")
    for i, item in enumerate(items, 1):
        print(f"    {i}. '{item}'")

    duplicates = matcher.detect_duplicates(items, threshold=0.90, use_blocking=False)

    print(f"\n  Duplicates found ({len(duplicates)}):")
    for item1, item2, score in duplicates:
        print(f"    '{item1}' ≈ '{item2}'  (score: {score:.4f})")


def example_config_impact() -> None:
    """Compare matching results with different normalization settings."""
    print("\n\n" + "=" * 70)
    print("4. Normalization Config Impact")
    print("=" * 70)

    text1 = "José (García) - Director"
    text2 = "Jose Garcia Director"

    configs = [
        ("No normalization", MatcherConfig(
            normalize_punctuation=False,
            normalize_parentheses=False,
            remove_accents=False,
        )),
        ("Punctuation only", MatcherConfig(
            normalize_punctuation=True,
            normalize_parentheses=False,
            remove_accents=False,
        )),
        ("Full normalization", MatcherConfig(
            normalize_punctuation=True,
            normalize_parentheses=True,
            remove_accents=True,
        )),
    ]

    print(f"\n  '{text1}' vs '{text2}':\n")

    for label, config in configs:
        matcher = TextMatcher(config=config)
        is_match, metrics = matcher.compare_names(text1, text2)
        score = metrics.get("levenshtein_ratio", 0.0)
        print(f"    {label:<25}: match={is_match}  (score: {score:.4f})")


def main() -> None:
    """Run all normalization examples."""
    print()
    example_basic_normalization()
    example_matcher_normalization()
    example_duplicate_detection()
    example_config_impact()
    print("\n\nAll normalization examples completed.\n")


if __name__ == "__main__":
    main()
