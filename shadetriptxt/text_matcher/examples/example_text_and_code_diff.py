"""
Example: Text and Code Diff
============================
Compare text documents and source-code blocks with detailed diff output.

Features:
    - compare_text_detailed()  — unified diff, line-level change counts
    - compare_code_blocks()    — language-aware diff (comment stripping,
                                 whitespace normalization)

Use cases:
    - Document change tracking
    - Code-review assistance / duplication detection
    - Version-control diff previews

Run: python -m shadetriptxt.text_matcher.examples.example_text_and_code_diff
"""

from shadetriptxt.text_matcher.text_matcher import TextMatcher


def example_text_diff() -> None:
    """Text comparison with unified-diff output."""
    print("=" * 70)
    print("1. Text Comparison (compare_text_detailed)")
    print("=" * 70)

    matcher = TextMatcher()

    text1 = (
        "The quick brown fox jumps over the lazy dog.\n"
        "A journey of a thousand miles begins with a single step.\n"
        "To be or not to be, that is the question."
    )
    text2 = (
        "The fast brown fox runs over the sleepy dog.\n"
        "A journey of a thousand kilometers begins with a single step.\n"
        "To be or not to be, that remains the question."
    )

    result = matcher.compare_text_detailed(
        text1, text2,
        case_sensitive=False,
        show_diff=True,
        context_lines=2,
    )

    print(f"\n  Similarity : {result['score']:.2f}%")
    print(f"  Added      : {result['lines_added']}")
    print(f"  Removed    : {result['lines_removed']}")
    print(f"  Changed    : {result['lines_changed']}")
    print(f"\n  --- UNIFIED DIFF ---\n{result['diff']}")


def example_code_diff() -> None:
    """Python code comparison with optional comment filtering."""
    print("\n" + "=" * 70)
    print("2. Code Comparison — Python (compare_code_blocks)")
    print("=" * 70)

    matcher = TextMatcher()

    code_v1 = (
        "def calculate_sum(numbers):\n"
        "    # Calculate the sum of a list\n"
        "    total = 0\n"
        "    for num in numbers:\n"
        "        total += num\n"
        "    return total\n"
        "\n"
        "def calculate_average(numbers):\n"
        "    return calculate_sum(numbers) / len(numbers)"
    )
    code_v2 = (
        "def calculate_sum(numbers):\n"
        "    # Calculate total\n"
        "    total = 0\n"
        "    for num in numbers:\n"
        "        total = total + num  # Addition\n"
        "    return total\n"
        "\n"
        "def calculate_mean(numbers):\n"
        "    return calculate_sum(numbers) / len(numbers)"
    )

    # With comments
    r1 = matcher.compare_code_blocks(
        code_v1, code_v2,
        language="python", ignore_comments=False, ignore_whitespace=True,
    )
    # Without comments
    r2 = matcher.compare_code_blocks(
        code_v1, code_v2,
        language="python", ignore_comments=True, ignore_whitespace=True,
    )

    print(f"\n  Structural similarity (with comments)    : {r1['structural_similarity']:.2f}%")
    print(f"  Structural similarity (without comments)  : {r2['structural_similarity']:.2f}%")
    print(f"\n  --- DIFF ---\n{r1['diff']}")


def example_duplication_detection() -> None:
    """Detect potential code duplication via structural similarity."""
    print("\n" + "=" * 70)
    print("3. Code Duplication Detection")
    print("=" * 70)

    matcher = TextMatcher()

    code_a = (
        "def process_data(items):\n"
        "    result = []\n"
        "    for item in items:\n"
        "        if item > 0:\n"
        "            result.append(item * 2)\n"
        "    return result"
    )
    code_b = (
        "def transform_list(elements):\n"
        "    output = []\n"
        "    for element in elements:\n"
        "        if element > 0:\n"
        "            output.append(element * 3)\n"
        "    return output"
    )

    result = matcher.compare_code_blocks(code_a, code_b, language="python")

    print(f"\n  Structural similarity : {result['structural_similarity']:.2f}%")
    print(f"  Matching blocks       : {len(result['matching_blocks'])}")

    if result["structural_similarity"] > 70:
        print("  ⚠  Moderate similarity — review for potential duplication")


def example_version_control() -> None:
    """Simulate a git-style diff between two file versions."""
    print("\n" + "=" * 70)
    print("4. Version-Control Diff Simulation")
    print("=" * 70)

    matcher = TextMatcher()

    old = (
        "class User:\n"
        "    def __init__(self, name, email):\n"
        "        self.name = name\n"
        "        self.email = email\n"
        "\n"
        "    def get_info(self):\n"
        '        return f"{self.name} ({self.email})"\n'
        "\n"
        "    def validate_email(self):\n"
        "        return '@' in self.email"
    )
    new = (
        "class User:\n"
        "    def __init__(self, name, email, age=None):\n"
        "        self.name = name\n"
        "        self.email = email\n"
        "        self.age = age\n"
        "\n"
        "    def get_info(self):\n"
        '        info = f"{self.name} ({self.email})"\n'
        "        if self.age:\n"
        '            info += f" - Age: {self.age}"\n'
        "        return info\n"
        "\n"
        "    def validate_email(self):\n"
        "        import re\n"
        "        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$'\n"
        "        return re.match(pattern, self.email) is not None"
    )

    result = matcher.compare_text_detailed(
        old, new, case_sensitive=True, show_diff=True, context_lines=3,
    )

    print(f"\n  Similarity : {result['score']:.2f}%")
    print(f"  Added      : {result['lines_added']}")
    print(f"  Removed    : {result['lines_removed']}")
    print(f"  Changed    : {result['lines_changed']}")
    print(f"\n  --- GIT-STYLE DIFF ---\n{result['diff']}")


def main() -> None:
    """Run all text/code-diff examples."""
    print()
    example_text_diff()
    example_code_diff()
    example_duplication_detection()
    example_version_control()
    print("\n\nAll text & code diff examples completed.\n")


if __name__ == "__main__":
    main()
