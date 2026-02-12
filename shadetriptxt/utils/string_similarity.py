"""
Word Similarity - String similarity algorithms and classes.

This module provides the WordSimilarity class and standalone functions for
comparing words using multiple algorithms. All algorithm implementations
are included directly — no external engine dependency required.

Algorithms:
    - Levenshtein Distance
    - Jaro-Winkler Similarity
    - Jaccard Similarity
    - Sørensen-Dice Coefficient
    - Ratcliff-Obershelp (via difflib)
    - Longest Common Subsequence (LCS)
    - MRA (Match Rating Approach)

Author: DatamanEdge
"""

import difflib
from typing import Dict, Any, Tuple


# ---------------------------------------------------------------------------
# Algorithm implementations
# ---------------------------------------------------------------------------

def levenshtein_score(s1: str, s2: str) -> float:
    """
    Calculate the Levenshtein similarity ratio between two strings.

    Returns a value between 0.0 and 1.0, where 1.0 means strings are identical.

    Cost: O(N*M) time, O(min(N, M)) space.
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    # Ensure s2 is the shorter string to save space
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    len1, len2 = len(s1), len(s2)
    previous_row = list(range(len2 + 1))

    for i, char1 in enumerate(s1):
        current_row = [i + 1]
        for j, char2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (char1 != char2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    distance = previous_row[-1]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


def jaro_winkler_score(s1: str, s2: str) -> float:
    """
    Calculate the Jaro-Winkler similarity between two strings.

    Returns a value between 0.0 and 1.0.

    Cost: O(N*M).
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    max_dist = max((max(len1, len2) // 2) - 1, 0)

    match1 = [False] * len1
    match2 = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len2)
        for j in range(start, end):
            if not match2[j] and s1[i] == s2[j]:
                match1[i] = True
                match2[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if match1[i]:
            while not match2[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3.0

    prefix_len = 0
    for c1, c2 in zip(s1[:4], s2[:4]):
        if c1 == c2:
            prefix_len += 1
        else:
            break

    return jaro + (prefix_len * 0.1 * (1.0 - jaro))


def jaccard_similarity(s1: str, s2: str, mode: str = "char") -> float:
    """
    Calculate Jaccard Similarity.

    Modes:
        - "char": Character-level set similarity
        - "token": Word-level set similarity
    """
    if not s1 or not s2:
        return 0.0

    if mode == "token":
        set1 = set(s1.split())
        set2 = set(s2.split())
    else:
        set1 = set(s1)
        set2 = set(s2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def sorensen_dice_coefficient(s1: str, s2: str) -> float:
    """
    Calculate Sørensen-Dice coefficient (bigram similarity).
    """
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    bigrams1 = {s1[i:i + 2] for i in range(len(s1) - 1)}
    bigrams2 = {s2[i:i + 2] for i in range(len(s2) - 1)}

    if not bigrams1 and not bigrams2:
        return 0.0

    intersection = len(bigrams1 & bigrams2)
    return (2.0 * intersection) / (len(bigrams1) + len(bigrams2))


def ratcliff_obershelp_score(s1: str, s2: str) -> float:
    """
    Ratcliff-Obershelp similarity (standardized via difflib).
    """
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def lcs_score(s1: str, s2: str) -> Dict[str, Any]:
    """
    Calculate Longest Common Subsequence metrics.
    """
    if not s1 or not s2:
        return {'lcs_length': 0, 'similarity': 0.0, 'score': 0.0}

    len1, len2 = len(s1), len(s2)
    prev = [0] * (len2 + 1)
    curr = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if s1[i - 1] == s2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev

    lcs_len = prev[len2]
    max_len = max(len1, len2)
    sim = lcs_len / max_len if max_len > 0 else 0.0

    return {'lcs_length': lcs_len, 'similarity': sim, 'score': sim * 100.0}


def mra_similarity(s1: str, s2: str) -> float:
    """
    Match Rating Approach (MRA) - Phonetic similarity metric.
    Simplified version focusing on consonant comparison.
    """
    if not s1 or not s2:
        return 0.0

    def mra_encode(s: str) -> str:
        s = s.upper()
        first = s[0]
        vowels = "AEIOU"
        rest = "".join(c for c in s[1:] if c not in vowels)
        encoded = first
        for c in rest:
            if c != encoded[-1]:
                encoded += c
        if len(encoded) > 6:
            return encoded[:3] + encoded[-3:]
        return encoded

    e1 = mra_encode(s1)
    e2 = mra_encode(s2)

    if abs(len(e1) - len(e2)) > 2:
        return 0.0

    return jaro_winkler_score(e1, e2)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def are_words_equivalent(
    w1: str,
    w2: str,
    levenshtein_threshold: float = 0.85,
    jaro_winkler_threshold: float = 0.9,
    metaphone_required: bool = True
) -> Tuple[bool, Dict[str, Any]]:
    """
    Standalone function to determine if two words are equivalent.

    Args:
        w1: First word.
        w2: Second word.
        levenshtein_threshold: Min ratio for Levenshtein.
        jaro_winkler_threshold: Min score for Jaro-Winkler.
        metaphone_required: If True, phonetic similarity is prioritized.

    Returns:
        Tuple of (is_equivalent, metrics_dict).
    """
    ws = WordSimilarity()
    return ws.are_equivalent(
        w1, w2,
        levenshtein_threshold=levenshtein_threshold,
        jaro_winkler_threshold=jaro_winkler_threshold,
        metaphone_required=metaphone_required
    )


def calculate_similarity(s1: str, s2: str, algorithm: str = "levenshtein") -> Dict[str, Any]:
    """
    Calculate similarity between two strings using a specific algorithm.
    """
    ws = WordSimilarity()
    return ws.calculate(s1, s2, algorithm=algorithm)


# ---------------------------------------------------------------------------
# WordSimilarity class
# ---------------------------------------------------------------------------

class WordSimilarity:
    """
    Core class for word-level similarity calculations.
    """

    def sorensen_dice_score(self, s1: str, s2: str) -> float:
        return sorensen_dice_coefficient(s1, s2)

    def ratcliff_obershelp_score(self, s1: str, s2: str) -> float:
        return ratcliff_obershelp_score(s1, s2)

    def levenshtein_score(self, s1: str, s2: str) -> float:
        return levenshtein_score(s1, s2)

    def jaro_winkler_score(self, s1: str, s2: str) -> float:
        return jaro_winkler_score(s1, s2) * 100.0

    def are_equivalent(
        self,
        w1: str,
        w2: str,
        levenshtein_threshold: float = 0.85,
        jaro_winkler_threshold: float = 0.9,
        metaphone_required: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Comprehensive equivalence check using multiple algorithms.
        """
        if not w1 or not w2:
            return False, {}

        lev = levenshtein_score(w1, w2)
        jaro = jaro_winkler_score(w1, w2)

        mra_sim = mra_similarity(w1, w2)
        phonetic_match = mra_sim >= 0.8

        metrics = {
            'levenshtein_ratio': lev,
            'jaro_winkler_score': jaro,
            'phonetic_match': phonetic_match,
            'mra_similarity': mra_sim
        }

        if metaphone_required:
            is_match = phonetic_match or (lev >= levenshtein_threshold and jaro >= jaro_winkler_threshold)
        else:
            is_match = (lev >= levenshtein_threshold) or (jaro >= jaro_winkler_threshold)

        return is_match, metrics

    def calculate(self, s1: str, s2: str, algorithm: str = "levenshtein") -> Dict[str, Any]:
        """
        Unified entry point for all similarity algorithms.
        """
        algo = algorithm.lower().replace("-", "_")

        if algo == "levenshtein":
            res = levenshtein_score(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}

        elif algo == "jaro_winkler":
            res = jaro_winkler_score(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}

        elif algo == "jaccard":
            res = jaccard_similarity(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}

        elif algo == "sorensen_dice":
            res = sorensen_dice_coefficient(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}

        elif algo == "lcs":
            return lcs_score(s1, s2)

        elif algo == "mra":
            res = mra_similarity(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}

        return {'error': f"Unknown algorithm: {algorithm}"}
