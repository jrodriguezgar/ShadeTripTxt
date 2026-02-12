"""
Similarity Engines - Optimized string similarity algorithms.

This module provides high-performance implementations of common string
similarity algorithms without external dependencies.

Algorithms:
    - Levenshtein Distance
    - Jaro-Winkler Similarity
    - Jaccard Similarity
    - Sørensen-Dice Coefficient
    - Hamming Distance
    - Longest Common Subsequence (LCS)

Author: DatamanEdge
"""

import math
from typing import List, Set, Tuple, Union, Dict, Any


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
    max_dist = (max(len1, len2) // 2) - 1
    if max_dist < 0:
        max_dist = 0

    match1 = [False] * len1
    match2 = [False] * len2
    matches = 0
    transpositions = 0

    # Find matches
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

    # Count transpositions
    k = 0
    for i in range(len1):
        if match1[i]:
            while not match2[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
    
    # Jaro Similarity
    jaro = (matches/len1 + matches/len2 + (matches - transpositions/2)/matches) / 3.0
    
    # Winkler adjustment for common prefix (max 4 chars)
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
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def sorensen_dice_coefficient(s1: str, s2: str) -> float:
    """
    Calculate Sørensen-Dice coefficient (bigram similarity).
    """
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
        
    def get_bigrams(s):
        return {s[i:i+2] for i in range(len(s)-1)}
        
    bigrams1 = get_bigrams(s1)
    bigrams2 = get_bigrams(s2)
    
    if not bigrams1 and not bigrams2:
        return 0.0
        
    intersection = len(bigrams1.intersection(bigrams2))
    return (2.0 * intersection) / (len(bigrams1) + len(bigrams2))


def sorensen_dice_score(s1: str, s2: str) -> float:
    """Convenience wrapper for sorensen_dice_coefficient."""
    return sorensen_dice_coefficient(s1, s2)


def ratcliff_obershelp_score(s1: str, s2: str) -> float:
    """
    Ratcliff-Obershelp similarity (standardized via difflib).
    """
    import difflib
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def lcs_score(s1: str, s2: str) -> Dict[str, Any]:
    """
    Calculate Longest Common Subsequence metrics.
    """
    if not s1 or not s2:
        return {'lcs_length': 0, 'similarity': 0.0, 'score': 0.0}
        
    # Standard LCS using DP (O(N*M))
    len1, len2 = len(s1), len(s2)
    # Optimization: Use only two rows
    prev = [0] * (len2 + 1)
    curr = [0] * (len2 + 1)
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if s1[i-1] == s2[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev = list(curr)
        
    lcs_len = prev[len2]
    max_len = max(len1, len2)
    sim = lcs_len / max_len if max_len > 0 else 0.0
    
    return {
        'lcs_length': lcs_len,
        'similarity': sim,
        'score': sim * 100.0
    }


def mra_similarity(s1: str, s2: str) -> float:
    """
    Match Rating Approach (MRA) - Phonetic similarity metric.
    Simplified version focusing on consonant comparison.
    """
    if not s1 or not s2:
        return 0.0
        
    def mra_encode(s):
        s = s.upper()
        # Remove vowels except first char
        first = s[0]
        vowels = "AEIOU"
        rest = "".join(c for c in s[1:] if c not in vowels)
        # Remove consecutive duplicates
        encoded = first
        for c in rest:
            if c != encoded[-1]:
                encoded += c
        # Keep max 6 chars (3 first, 3 last)
        if len(encoded) > 6:
            return encoded[:3] + encoded[-3:]
        return encoded

    e1 = mra_encode(s1)
    e2 = mra_encode(s2)
    
    # Compare encoded strings (diff length allowed <= 2)
    if abs(len(e1) - len(e2)) > 2:
        return 0.0
        
    # Matching starts here...
    # (Reduced version: use Jaro-Winkler on encoded strings for simplicity)
    return jaro_winkler_score(e1, e2)
