"""
Text Readability - Reading-ease and grade-level metrics.

This module provides functions to evaluate how easy or difficult a piece
of English text is to read, using the Flesch-Kincaid family of formulas.

Metrics:
    - Syllable counting (heuristic for English)
    - Flesch Reading Ease
    - Flesch-Kincaid Grade Level

Author: DatamanEdge
"""

import re


# ---------------------------------------------------------------------------
# Syllable counting
# ---------------------------------------------------------------------------


def count_syllables(word: str, lang: str = "en") -> int:
    """
    Estimate the number of syllables in a word using heuristics.

    Currently supports English (``"en"``). Falls back to a vowel-cluster
    count for other languages.

    Args:
        word: A single word (no spaces).
        lang: ISO 639-1 language code. Default ``"en"``.

    Returns:
        The estimated syllable count (minimum 1 for non-empty words).

    Raises:
        None

    Example Usage:
        count_syllables("beautiful")   # 3
        count_syllables("the")         # 1
        count_syllables("example")     # 3

    Cost:
        O(n), where n is the length of the word.
    """
    if not word:
        return 0

    word = word.lower().strip()

    if not word:
        return 0

    if lang != "en":
        # Generic fallback: count vowel clusters
        clusters = re.findall(r"[aeiouyàáâãäåèéêëìíîïòóôõöùúûüæœ]+", word)
        return max(len(clusters), 1)

    # English heuristic
    word = re.sub(r"[^a-z]", "", word)

    if not word:
        return 0

    # Special short words
    if len(word) <= 3:
        return 1

    count = 0

    # Remove trailing silent-e
    if word.endswith("e") and not word.endswith("le"):
        word = word[:-1]

    # Count vowel groups
    vowels = "aeiouy"
    prev_was_vowel = False

    for ch in word:
        is_vowel = ch in vowels

        if is_vowel and not prev_was_vowel:
            count += 1

        prev_was_vowel = is_vowel

    # Handle -le ending (already removed 'e', so word ends in 'l')
    # Edge case: if we removed the trailing 'e' and the word ended with 'le',
    # we didn't remove it — the syllable is already counted.

    # Ensure at least 1 syllable
    return max(count, 1)


# ---------------------------------------------------------------------------
# Sentence / word tokenization helpers
# ---------------------------------------------------------------------------


def _count_sentences(text: str) -> int:
    """Count sentences by splitting on sentence-ending punctuation."""
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return max(len(sentences), 1)


def _tokenize_words(text: str) -> list[str]:
    """Extract word tokens (alphabetic sequences)."""
    return re.findall(r"[a-zA-Z]+", text)


# ---------------------------------------------------------------------------
# Flesch metrics
# ---------------------------------------------------------------------------


def flesch_reading_ease(text: str) -> float:
    """
    Compute the Flesch Reading Ease score for English text.

    Higher scores indicate easier text. Typical ranges:

    - 90-100: Very easy (5th grade)
    - 60-70:  Standard (8th-9th grade)
    - 0-30:   Very difficult (college graduate)

    Formula::

        206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

    Args:
        text: The input text (English).

    Returns:
        The Flesch Reading Ease score. Can be negative for
        extremely difficult text.

    Raises:
        None

    Example Usage:
        flesch_reading_ease("The cat sat on the mat.")  # ~116.1

    Cost:
        O(n), where n is the total character count.
    """
    words = _tokenize_words(text)
    num_words = len(words)

    if num_words == 0:
        return 0.0

    num_sentences = _count_sentences(text)
    num_syllables = sum(count_syllables(w) for w in words)

    return 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)


def flesch_kincaid_grade(text: str) -> float:
    """
    Compute the Flesch-Kincaid Grade Level for English text.

    The result approximates the U.S. school grade level needed to
    understand the text.

    Formula::

        0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

    Args:
        text: The input text (English).

    Returns:
        The grade level (e.g. 8.0 ≈ eighth grade).

    Raises:
        None

    Example Usage:
        flesch_kincaid_grade("The cat sat on the mat.")  # ~-1.1

    Cost:
        O(n), where n is the total character count.
    """
    words = _tokenize_words(text)
    num_words = len(words)

    if num_words == 0:
        return 0.0

    num_sentences = _count_sentences(text)
    num_syllables = sum(count_syllables(w) for w in words)

    return 0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59


def gunning_fog_index(text: str) -> float:
    """
    Compute the Gunning Fog readability index for English text.

    Estimates the years of formal education required to understand
    the text on a first reading.

    Formula::

        0.4 * ((words / sentences) + 100 * (complex_words / words))

    A "complex word" is one with 3 or more syllables.

    Args:
        text (str): The input text (English).

    Returns:
        float: The Gunning Fog index (higher = harder to read).

    Raises:
        None

    Example Usage:
        gunning_fog_index("The cat sat on the mat.")  # low index

    Cost:
        O(n), where n is the total character count.
    """
    words = _tokenize_words(text)
    num_words = len(words)

    if num_words == 0:
        return 0.0

    num_sentences = _count_sentences(text)
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)

    return 0.4 * ((num_words / num_sentences) + 100 * (complex_words / num_words))


def coleman_liau_index(text: str) -> float:
    """
    Compute the Coleman-Liau readability index.

    Uses character and sentence counts rather than syllables.

    Formula::

        0.0588 * L - 0.296 * S - 15.8

    Where L = average letters per 100 words, S = average sentences per 100 words.

    Args:
        text (str): The input text (English).

    Returns:
        float: The Coleman-Liau index (approximates U.S. grade level).

    Raises:
        None

    Example Usage:
        coleman_liau_index("The cat sat on the mat.")  # low grade

    Cost:
        O(n), where n is the total character count.
    """
    words = _tokenize_words(text)
    num_words = len(words)

    if num_words == 0:
        return 0.0

    num_letters = sum(len(w) for w in words)
    num_sentences = _count_sentences(text)

    avg_letters = (num_letters / num_words) * 100
    avg_sentences = (num_sentences / num_words) * 100

    return 0.0588 * avg_letters - 0.296 * avg_sentences - 15.8


def automated_readability_index(text: str) -> float:
    """
    Compute the Automated Readability Index (ARI).

    A character-based readability formula that approximates the
    U.S. grade level needed to comprehend the text.

    Formula::

        4.71 * (characters / words) + 0.5 * (words / sentences) - 21.43

    Args:
        text (str): The input text (English).

    Returns:
        float: The ARI value (approximates U.S. grade level).

    Raises:
        None

    Example Usage:
        automated_readability_index("The cat sat on the mat.")  # low

    Cost:
        O(n), where n is the total character count.
    """
    words = _tokenize_words(text)
    num_words = len(words)

    if num_words == 0:
        return 0.0

    num_characters = sum(len(w) for w in words)
    num_sentences = _count_sentences(text)

    return 4.71 * (num_characters / num_words) + 0.5 * (num_words / num_sentences) - 21.43


def text_complexity_score(text: str) -> dict[str, float]:
    """
    Compute a composite text complexity score.

    Combines several readability indices (Flesch Reading Ease,
    Coleman-Liau, ARI) with lexical diversity (type-token ratio)
    into a single normalised 0-100 score, where higher = more
    complex.

    Args:
        text (str): The input text (English).

    Returns:
        dict: Keys ``'flesch'``, ``'coleman_liau'``, ``'ari'``,
              ``'lexical_diversity'`` and ``'complexity_score'``.

    Raises:
        None

    Example Usage:
        text_complexity_score("The cat sat on the mat.")  # low complexity

    Cost:
        O(n), where n is the total character count.
    """
    words = _tokenize_words(text)
    num_words = len(words)

    if num_words == 0:
        return {
            "flesch": 0.0,
            "coleman_liau": 0.0,
            "ari": 0.0,
            "lexical_diversity": 0.0,
            "complexity_score": 0.0,
        }

    fre = flesch_reading_ease(text)
    cli = coleman_liau_index(text)
    ari = automated_readability_index(text)

    unique_words = len(set(w.lower() for w in words))
    lex_div = unique_words / num_words

    # Normalise Flesch: 0 (very hard) to 100 (very easy) → invert
    flesch_complexity = max(0.0, min(100.0, 100.0 - fre))

    # Coleman-Liau and ARI are grade levels — cap at ~20
    cli_norm = max(0.0, min(100.0, cli * 5.0))
    ari_norm = max(0.0, min(100.0, ari * 5.0))

    # Lexical diversity 0-1 → 0-100
    lex_norm = lex_div * 100.0

    score = 0.4 * flesch_complexity + 0.2 * cli_norm + 0.2 * ari_norm + 0.2 * lex_norm

    return {
        "flesch": round(fre, 2),
        "coleman_liau": round(cli, 2),
        "ari": round(ari, 2),
        "lexical_diversity": round(lex_div, 4),
        "complexity_score": round(score, 2),
    }


# Common English bigrams for gibberish detection (module-level constant)
_COMMON_BIGRAMS: frozenset[str] = frozenset(
    {
        "th",
        "he",
        "in",
        "er",
        "an",
        "re",
        "on",
        "at",
        "en",
        "nd",
        "ti",
        "es",
        "or",
        "te",
        "of",
        "ed",
        "is",
        "it",
        "al",
        "ar",
        "st",
        "to",
        "nt",
        "ng",
        "se",
        "ha",
        "as",
        "ou",
        "io",
        "le",
        "ve",
        "co",
        "me",
        "de",
        "hi",
        "ri",
        "ro",
        "ic",
        "ne",
        "ea",
    }
)

# Placeholder/dummy text keywords (module-level constant)
_PLACEHOLDERS: frozenset[str] = frozenset(
    {
        "lorem ipsum",
        "n/a",
        "na",
        "tbd",
        "tba",
        "todo",
        "fixme",
        "test",
        "testing",
        "xxx",
        "aaa",
        "abc",
        "asdf",
        "foo",
        "bar",
        "baz",
        "sample",
        "example",
        "placeholder",
        "dummy",
        "temp",
        "tmp",
        "none",
        "null",
        "undefined",
        "pending",
    }
)


def is_gibberish(text: str, threshold: float = 0.35) -> bool:
    """
    Detect whether a text string is likely gibberish / random noise.

    Uses three heuristics:
    1. **Vowel ratio** — natural language typically has 30-50 % vowels.
    2. **Bigram transition score** — measures how many consecutive
       character pairs are common in English.
    3. **Unique-char ratio** — random strings tend to have high
       character diversity relative to length.

    The three signals are averaged into a "gibberish score" in [0, 1].
    A score above *threshold* flags the text as gibberish.

    Args:
        text (str): The input text.
        threshold (float): Decision boundary (default 0.35).

    Returns:
        bool: ``True`` if the text is likely gibberish.

    Raises:
        None

    Example Usage:
        is_gibberish("The cat sat on the mat.")  # False
        is_gibberish("xkjf8 wqp3z mbn!v")       # True

    Cost:
        O(n), where n is the character count.
    """
    if not isinstance(text, str) or not text.strip():
        return True

    alpha = [ch.lower() for ch in text if ch.isalpha()]

    if len(alpha) < 3:
        return True

    # 1. Vowel ratio
    vowels = set("aeiou")
    vowel_count = sum(1 for ch in alpha if ch in vowels)
    vowel_ratio = vowel_count / len(alpha)
    vowel_penalty = 0.0 if 0.2 <= vowel_ratio <= 0.6 else 1.0

    # 2. Common English bigram score
    bigrams = [alpha[i] + alpha[i + 1] for i in range(len(alpha) - 1)]

    if bigrams:
        common_hits = sum(1 for bg in bigrams if bg in _COMMON_BIGRAMS)
        bigram_penalty = 1.0 - (common_hits / len(bigrams))
    else:
        bigram_penalty = 1.0

    # 3. Unique-char ratio (high diversity → suspicious)
    unique_ratio = len(set(alpha)) / len(alpha)
    diversity_penalty = unique_ratio if unique_ratio > 0.8 else 0.0

    score = (vowel_penalty + bigram_penalty + diversity_penalty) / 3.0

    return score > threshold


def is_placeholder_text(text: str) -> bool:
    """Detect common placeholder / dummy text.

    Matches patterns such as ``'lorem ipsum'``, ``'N/A'``, ``'TBD'``,
    ``'test'``, ``'xxx'``, ``'TODO'`` and similar.

    Args:
        text (str): The input text.

    Returns:
        bool: ``True`` if the text looks like placeholder content.

    Raises:
        None

    Example Usage:
        is_placeholder_text("lorem ipsum dolor")  # True
        is_placeholder_text("Quarterly report")    # False

    Cost:
        O(n)
    """
    if not isinstance(text, str) or not text.strip():
        return True

    normalised = text.strip().lower()

    if normalised in _PLACEHOLDERS:
        return True

    if normalised.startswith("lorem ipsum"):
        return True

    # Repeated single character: "xxxx", "----", "...."
    if len(set(normalised.replace(" ", ""))) <= 1:
        return True

    return False


def text_density_score(text: str) -> float:
    """Compute informational density of a text string.

    Density = (non-whitespace alphabetic/digit chars) / total length.
    A score of 1.0 means every character is informational; lower
    values indicate sparse or heavily padded content.

    Args:
        text (str): The input text.

    Returns:
        float: Density in [0.0, 1.0].

    Raises:
        None

    Example Usage:
        text_density_score("Hello World")     # ~0.91
        text_density_score("   x   ")         # ~0.14

    Cost:
        O(n)
    """
    if not isinstance(text, str) or not text:
        return 0.0

    total = len(text)
    useful = sum(1 for ch in text if ch.isalnum())

    return round(useful / total, 4)
