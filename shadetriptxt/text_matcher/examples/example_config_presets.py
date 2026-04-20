"""
Example: Configuration Presets
==============================
Shows how MatcherConfig presets control matching strictness.

Presets:
    - MatcherConfig.strict()   — high threshold, phonetic required
    - MatcherConfig()          — balanced defaults
    - MatcherConfig.lenient()  — lower thresholds, more tolerant
    - MatcherConfig.fuzzy()    — very permissive, broad matching

Run: python -m shadetriptxt.text_matcher.examples.example_config_presets
"""

from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig


def main() -> None:
    """Compare US vs UK spelling variants across all presets."""
    print()
    print("=" * 70)
    print("Config Presets — Effect on Matching Strictness")
    print("=" * 70)

    word_pairs = [
        ("color", "colour"),
        ("theater", "theatre"),
        ("organize", "organise"),
        ("center", "centre"),
    ]

    presets = [
        ("strict", MatcherConfig.strict()),
        ("default", MatcherConfig()),
        ("lenient", MatcherConfig.lenient()),
        ("fuzzy", MatcherConfig.fuzzy()),
    ]

    print("\n  US vs UK spelling variants:\n")

    for word1, word2 in word_pairs:
        print(f"  '{word1}' vs '{word2}':")
        for name, config in presets:
            matcher = TextMatcher(config=config)
            is_match, metrics = matcher.compare_names(word1, word2)
            lev = metrics.get("levenshtein_ratio", 0)
            mark = "✓" if is_match else "✗"
            print(f"    {name:<10}: {mark} (Lev: {lev:.4f})")
        print()

    print("All config-preset examples completed.\n")


if __name__ == "__main__":
    main()
