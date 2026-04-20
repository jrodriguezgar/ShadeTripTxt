"""
Example: Fuzzy Search and Vocabulary Correction
================================================
Find the closest match(es) in a candidate list using fuzzy similarity.

Features:
    - find_best_match()  — return the single best candidate above a threshold
    - compare_lists()    — return ranked candidates sorted by score

Use cases:
    - Autocomplete / did-you-mean suggestions
    - Name, product, or company-name standardization
    - Domain-specific spell correction (no external spell-checker needed)

Run: python -m shadetriptxt.text_matcher.examples.example_fuzzy_search
"""

from shadetriptxt.text_matcher.text_matcher import TextMatcher, MatcherConfig


def example_find_best_match() -> None:
    """Locate the single closest candidate with find_best_match()."""
    print("=" * 70)
    print("1. Find Best Match")
    print("=" * 70)

    matcher = TextMatcher()

    # --- Name matching ---
    print("\n  Name matching:")
    candidates = ["Smith", "Smyth", "Jones", "Johnson", "Williams", "Wilson"]

    for target in ["Smithe", "Smit", "Jonez", "Garcia"]:
        best, score, _ = matcher.find_best_match(target, candidates)
        if best:
            print(f"    '{target}' → '{best}'  (score: {score:.4f})")
        else:
            print(f"    '{target}' → no match found")

    # --- Product matching ---
    print("\n  Product matching (threshold=0.60):")
    products = [
        "iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8",
        "OnePlus 12", "Xiaomi 14",
    ]

    for query in ["iphone 15", "galaxy s24", "pixel8", "huawei"]:
        best, score, _ = matcher.find_best_match(query, products, threshold=0.60)
        if best:
            print(f"    '{query}' → '{best}'  (score: {score:.4f})")
        else:
            print(f"    '{query}' → no match found")


def example_ranked_matches() -> None:
    """Get multiple candidates ranked by score with compare_lists()."""
    print("\n\n" + "=" * 70)
    print("2. Ranked Match List (compare_lists)")
    print("=" * 70)

    matcher = TextMatcher()

    candidates = ["García", "Garzia", "Gracia", "González", "Garcés", "Garzón"]
    results = matcher.compare_lists("García", candidates, top_k=4, threshold=0.60)

    print(f"\n  Target: 'García'  |  Top 4 above 0.60:")
    print(f"    {'#':<4} {'Candidate':<15} {'Score':<10}")
    print("    " + "-" * 30)

    for i, (candidate, score, _) in enumerate(results, 1):
        print(f"    {i:<4} {candidate:<15} {score:.4f}")


def example_vocabulary_correction() -> None:
    """Correct misspelled words against a known vocabulary."""
    print("\n\n" + "=" * 70)
    print("3. Vocabulary Correction")
    print("=" * 70)

    matcher = TextMatcher(config=MatcherConfig.lenient(), locale="es_ES")

    vocabularies = {
        "Person names": (
            ["Javier", "Beatriz", "Alejandro", "Verónica"],
            ["Javierr", "Beatris", "Alexandro", "Veronik"],
        ),
        "Technical terms": (
            ["PostgreSQL", "Kubernetes", "Elasticsearch", "Terraform", "GraphQL"],
            ["Postgress", "Kubernets", "Elastcisearch", "Teraform", "GrafQL"],
        ),
        "Company names": (
            ["Microsoft", "Google", "Amazon", "Apple", "Netflix"],
            ["Microsft", "Gogle", "Amazone", "Aple", "Netflixx"],
        ),
    }

    for category, (correct, misspelled) in vocabularies.items():
        print(f"\n  {category}:")
        for word in misspelled:
            best, score, _ = matcher.find_best_match(word, correct, threshold=0.70)
            if best:
                print(f"    '{word}' → '{best}'  (score: {score:.4f})")
            else:
                print(f"    '{word}' → no match found")

    # --- Ranked suggestions for ambiguous input ---
    print("\n\n  Ranked suggestions for ambiguous input:")
    vocabulary = [
        "application", "appreciation", "approximation",
        "appropriation", "appellation", "apparition",
    ]

    results = matcher.compare_lists("aplicaton", vocabulary, top_k=3, threshold=0.60)

    print(f"    Input: 'aplicaton'")
    for i, (candidate, score, _) in enumerate(results, 1):
        print(f"      {i}. {candidate:<20} {score:.4f}")


def main() -> None:
    """Run all fuzzy-search examples."""
    print()
    example_find_best_match()
    example_ranked_matches()
    example_vocabulary_correction()
    print("\n\nAll fuzzy-search examples completed.\n")


if __name__ == "__main__":
    main()
