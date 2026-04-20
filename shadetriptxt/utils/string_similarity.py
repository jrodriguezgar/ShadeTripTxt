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
    - Soundex
    - Metaphone
    - Double Metaphone

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

    bigrams1 = {s1[i : i + 2] for i in range(len(s1) - 1)}
    bigrams2 = {s2[i : i + 2] for i in range(len(s2) - 1)}

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
        return {"lcs_length": 0, "similarity": 0.0, "score": 0.0}

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

    return {"lcs_length": lcs_len, "similarity": sim, "score": sim * 100.0}


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


# Soundex letter-to-digit mapping (hoisted to module level)
_SOUNDEX_MAP: dict[str, str] = {
    "B": "1",
    "F": "1",
    "P": "1",
    "V": "1",
    "C": "2",
    "G": "2",
    "J": "2",
    "K": "2",
    "Q": "2",
    "S": "2",
    "X": "2",
    "Z": "2",
    "D": "3",
    "T": "3",
    "L": "4",
    "M": "5",
    "N": "5",
    "R": "6",
}


def soundex(text: str) -> str:
    """
    Compute the Soundex phonetic code for a word.

    Soundex maps similarly-sounding English names to the same 4-character
    code (one letter followed by three digits).

    Args:
        text: The input word.

    Returns:
        A 4-character Soundex code (e.g. ``"R163"`` for ``"Robert"``).
        Returns ``"0000"`` for empty or non-alphabetic input.

    Raises:
        None

    Example Usage:
        soundex("Robert")   # "R163"
        soundex("Rupert")   # "R163"

    Cost:
        O(n), where n is the length of the input string.
    """
    if not text:
        return "0000"

    word = "".join(c for c in text.upper() if c.isalpha())

    if not word:
        return "0000"

    first = word[0]
    prev_code = _SOUNDEX_MAP.get(first, "0")
    digits: list[str] = []

    for ch in word[1:]:
        code = _SOUNDEX_MAP.get(ch, "0")

        if code != "0" and code != prev_code:
            digits.append(code)

        prev_code = code

    return (first + "".join(digits) + "000")[:4]


def metaphone(text: str) -> str:
    """
    Compute the Metaphone phonetic code for a word.

    Metaphone improves on Soundex by modelling English pronunciation rules
    (silent letters, consonant clusters, etc.).

    Args:
        text: The input word.

    Returns:
        A Metaphone code string, or ``""`` for empty input.

    Raises:
        None

    Example Usage:
        metaphone("Smith")     # "SM0"
        metaphone("Schmidt")   # "SXMTT"

    Cost:
        O(n), where n is the length of the input string.
    """
    if not text:
        return ""

    word = "".join(c for c in text.upper() if c.isalpha())

    if not word:
        return ""

    _VOWELS = set("AEIOU")

    # Drop initial silent letter pairs
    if word[:2] in ("AE", "GN", "KN", "PN", "WR"):
        word = word[1:]

    # Initial X → S
    if word[0] == "X":
        word = "S" + word[1:]

    length = len(word)

    def _at(pos: int) -> str:
        return word[pos] if 0 <= pos < length else ""

    code: list[str] = []
    i = 0

    while i < length:
        c = word[i]

        # Vowels — only encode at start of word
        if c in _VOWELS:
            if i == 0:
                code.append(c)
            i += 1
            continue

        # Skip duplicate consecutive letters (except C)
        if c == _at(i - 1) and c != "C":
            i += 1
            continue

        if c == "B":
            # Silent B after M at end of word
            if not (_at(i - 1) == "M" and i == length - 1):
                code.append("B")

        elif c == "C":
            if _at(i + 1) == "H":
                code.append("X")
                i += 1
            elif _at(i + 1) in "IEY":
                code.append("S")
            else:
                code.append("K")

        elif c == "D":
            if _at(i + 1) == "G" and _at(i + 2) in "IEY":
                code.append("J")
            else:
                code.append("T")

        elif c == "F":
            code.append("F")

        elif c == "G":
            if _at(i + 1) == "H" and i + 2 < length and _at(i + 2) not in _VOWELS:
                pass  # silent GH before consonant
            elif i + 1 == length - 1 and _at(i + 1) == "H":
                pass  # trailing GH
            elif _at(i + 1) == "N" and (i + 1 == length - 1 or (i + 2 == length - 1 and _at(i + 2) in "AEIOUNS")):
                pass  # silent GN at end / GNED at end
            elif _at(i - 1) == "G":
                pass  # second G in double-G
            elif _at(i + 1) in "IEY":
                code.append("J")
            else:
                code.append("K")

        elif c == "H":
            if _at(i - 1) not in _VOWELS and _at(i + 1) in _VOWELS:
                code.append("H")

        elif c == "J":
            code.append("J")

        elif c == "K":
            if _at(i - 1) != "C":
                code.append("K")

        elif c == "L":
            code.append("L")

        elif c == "M":
            code.append("M")

        elif c == "N":
            code.append("N")

        elif c == "P":
            if _at(i + 1) == "H":
                code.append("F")
                i += 1
            else:
                code.append("P")

        elif c == "Q":
            code.append("K")

        elif c == "R":
            code.append("R")

        elif c == "S":
            if _at(i + 1) == "H":
                code.append("X")
                i += 1
            elif _at(i + 1) == "I" and _at(i + 2) in "AO":
                code.append("X")
            else:
                code.append("S")

        elif c == "T":
            if _at(i + 1) == "H":
                code.append("0")
                i += 1
            elif _at(i + 1) == "I" and _at(i + 2) in "AO":
                code.append("X")
            else:
                code.append("T")

        elif c == "V":
            code.append("F")

        elif c == "W":
            if _at(i + 1) in _VOWELS:
                code.append("W")

        elif c == "X":
            code.append("KS")

        elif c == "Y":
            if _at(i + 1) in _VOWELS:
                code.append("Y")

        elif c == "Z":
            code.append("S")

        i += 1

    return "".join(code)


def double_metaphone(text: str) -> Tuple[str, str]:
    """
    Compute Double Metaphone codes for a word.

    Returns primary and alternate phonetic codes. They differ when a word
    has ambiguous pronunciation (e.g. Germanic vs. non-Germanic origins).

    Args:
        text: The input word.

    Returns:
        A tuple ``(primary, alternate)`` of phonetic code strings.
        Both may be identical when no alternate encoding exists.

    Raises:
        None

    Example Usage:
        double_metaphone("Schmidt")  # ("XMT", "SMT")
        double_metaphone("Smith")    # ("SM0", "XMT")

    Cost:
        O(n), where n is the length of the input string.
    """
    if not text:
        return ("", "")

    word = text.upper()
    word = "".join(c for c in word if c.isalpha())

    if not word:
        return ("", "")

    length = len(word)
    last = length - 1
    primary: list[str] = []
    alternate: list[str] = []
    i = 0

    _VOWELS = set("AEIOUY")

    def _at(pos: int) -> str:
        return word[pos] if 0 <= pos < length else ""

    def _substr(start: int, count: int) -> str:
        return word[start : start + count]

    def _slavo_germanic() -> bool:
        return "W" in word or "K" in word or "CZ" in word or "WITZ" in word

    def _add(main: str, alt: str | None = None) -> None:
        primary.append(main)
        alternate.append(alt if alt is not None else main)

    # Skip initial silent letters
    if _substr(0, 2) in ("GN", "KN", "PN", "AE", "WR"):
        i = 1

    # Initial X → S
    if _at(0) == "X":
        _add("S")
        i = 1

    while i < length:
        c = _at(i)

        if c in _VOWELS:
            if i == 0:
                _add("A")
            i += 1
            continue

        if c == "B":
            _add("P")
            i += 2 if _at(i + 1) == "B" else 1

        elif c == "C":
            if (
                i > 1
                and _at(i - 2) not in _VOWELS
                and _substr(i - 1, 3) == "ACH"
                and _at(i + 2) != "I"
                and (_at(i + 2) != "E" or _substr(i - 2, 6) in ("BACHER", "MACHER"))
            ):
                _add("K")
                i += 2
            elif i == 0 and _substr(0, 6) == "CAESAR":
                _add("S")
                i += 2
            elif _substr(i, 2) == "CH":
                if i > 0 and _substr(i, 4) == "CHAE":
                    _add("K", "X")
                elif i == 0 and _substr(1, 5) in ("HARAC", "HARIS", "HOR", "HYM", "HIA", "HEM"):
                    _add("K")
                elif _substr(0, 4) in ("VAN ", "VON ") or _substr(0, 3) == "SCH":
                    _add("K")
                else:
                    if i > 0:
                        _add("X", "K")
                    else:
                        _add("X")
                i += 2
            elif _substr(i, 2) == "CZ" and not _substr(i - 2, 4) == "WICZ":
                _add("S", "X")
                i += 2
            elif _substr(i + 1, 3) == "CIA":
                _add("X")
                i += 3
            elif _substr(i, 2) == "CC" and not (i == 1 and _at(0) == "M"):
                if _at(i + 2) in "IEH" and _substr(i + 2, 2) != "HU":
                    _add("KS")
                else:
                    _add("K")
                i += 2
            elif _substr(i, 2) in ("CK", "CG", "CQ"):
                _add("K")
                i += 2
            elif _substr(i, 2) in ("CI", "CE", "CY"):
                if _substr(i, 3) in ("CIO", "CIE", "CIA"):
                    _add("S", "X")
                else:
                    _add("S")
                i += 2
            else:
                _add("K")
                if _at(i + 1) in " CQ":
                    i += 2
                else:
                    i += 1

        elif c == "D":
            if _substr(i, 2) == "DG":
                if _at(i + 2) in "IEY":
                    _add("J")
                    i += 3
                else:
                    _add("TK")
                    i += 2
            elif _substr(i, 2) in ("DT", "DD"):
                _add("T")
                i += 2
            else:
                _add("T")
                i += 1

        elif c == "F":
            _add("F")
            i += 2 if _at(i + 1) == "F" else 1

        elif c == "G":
            if _at(i + 1) == "H":
                if i > 0 and _at(i - 1) not in _VOWELS:
                    _add("K")
                    i += 2
                elif i == 0:
                    if _at(i + 2) == "I":
                        _add("J")
                    else:
                        _add("K")
                    i += 2
                elif i > 1 and (_at(i - 2) in "BHD" or _at(i - 3) in "BH" or _at(i - 4) in "B"):
                    i += 2
                else:
                    _add("F")
                    i += 2
            elif _at(i + 1) == "N":
                if i == 1 and _at(0) in _VOWELS and not _slavo_germanic():
                    _add("KN", "N")
                elif _substr(i + 2, 2) != "EY" and _at(i + 1) != "Y" and not _slavo_germanic():
                    _add("N", "KN")
                else:
                    _add("KN")
                i += 2
            elif _substr(i + 1, 2) == "LI" and not _slavo_germanic():
                _add("KL", "L")
                i += 2
            elif i == 0 and (_at(1) == "Y" or _at(1) == "E" and _substr(1, 2) in ("ES", "EP", "EB", "EL", "EY", "EI", "ER")):
                _add("K", "J")
                i += 2
            elif (
                (_substr(i + 1, 2) == "ER" or _at(i + 1) == "Y")
                and _substr(0, 6) not in ("DANGER", "RANGER", "MANGER")
                and _at(i - 1) not in "EI"
                and _substr(i - 1, 3) not in ("RGY", "OGY")
            ):
                _add("K", "J")
                i += 2
            elif _at(i + 1) in "EIY" or _substr(i - 1, 4) in ("AGGI", "OGGI"):
                if _substr(0, 4) in ("VAN ", "VON ") or _substr(0, 3) == "SCH" or _substr(i + 1, 2) == "ET":
                    _add("K")
                elif _substr(i + 1, 4) in ("IER "):
                    _add("J")
                else:
                    _add("J", "K")
                i += 2
            else:
                _add("K")
                i += 2 if _at(i + 1) == "G" else 1

        elif c == "H":
            if _at(i + 1) in _VOWELS and _at(i - 1) not in _VOWELS:
                _add("H")
            i += 1

        elif c == "J":
            if _substr(i, 4) == "JOSE" or _substr(0, 4) == "SAN ":
                if (i == 0 and _at(i + 4) == " ") or _substr(0, 4) == "SAN ":
                    _add("H")
                else:
                    _add("J", "H")
            elif i == 0:
                _add("J", "A")
            elif _at(i - 1) in _VOWELS and not _slavo_germanic() and _at(i + 1) in "AO":
                _add("J", "H")
            elif i == last:
                _add("", "J")
            elif _at(i - 1) not in "SKLT" and _at(i + 1) not in "SLTZ":
                _add("J")
            i += 2 if _at(i + 1) == "J" else 1

        elif c == "K":
            _add("K")
            i += 2 if _at(i + 1) == "K" else 1

        elif c == "L":
            if _at(i + 1) == "L":
                if (i == length - 3 and _substr(i - 1, 4) in ("ILLO", "ILLA", "ALLE")) or (
                    (_substr(last - 1, 2) in ("AS", "OS") or _at(last) in "AO") and _substr(i - 1, 4) == "ALLE"
                ):
                    _add("L", "")
                    i += 2
                else:
                    _add("L")
                    i += 2
            else:
                _add("L")
                i += 1

        elif c == "M":
            _add("M")
            if _at(i + 1) == "M" or (_at(i - 1) == "U" and _at(i + 1) == "B"):
                i += 2
            else:
                i += 1

        elif c == "N":
            _add("N")
            i += 2 if _at(i + 1) == "N" else 1

        elif c == "P":
            if _at(i + 1) == "H":
                _add("F")
                i += 2
            else:
                _add("P")
                i += 2 if _at(i + 1) in "PB" else 1

        elif c == "Q":
            _add("K")
            i += 2 if _at(i + 1) == "Q" else 1

        elif c == "R":
            if i == last and not _slavo_germanic() and _substr(i - 2, 2) == "IE" and _substr(i - 4, 2) not in ("ME", "MA"):
                _add("", "R")
            else:
                _add("R")
            i += 2 if _at(i + 1) == "R" else 1

        elif c == "S":
            if _substr(i - 1, 3) in ("ISL", "YSL"):
                i += 1
            elif i == 0 and _substr(0, 5) == "SUGAR":
                _add("X", "S")
                i += 1
            elif _substr(i, 2) == "SH":
                if _substr(i + 1, 4) in ("HEIM", "HOEK", "HOLM", "HOLZ"):
                    _add("S")
                else:
                    _add("X")
                i += 2
            elif _substr(i, 3) in ("SIO", "SIA") or _substr(i, 4) == "SIAN":
                if not _slavo_germanic():
                    _add("S", "X")
                else:
                    _add("S")
                i += 3
            elif (i == 0 and _at(1) in "MNLW") or _at(i + 1) == "Z":
                _add("S", "X")
                i += 2 if _at(i + 1) == "Z" else 1
            elif _substr(i, 2) == "SC":
                if _at(i + 2) == "H":
                    if _substr(i + 3, 2) in ("OO", "ER", "EN", "UY", "ED", "EM"):
                        if _substr(i + 3, 2) in ("ER", "EN"):
                            _add("X", "SK")
                        else:
                            _add("SK")
                    else:
                        _add("X", "S")
                    i += 3
                elif _at(i + 2) in "IEY":
                    _add("S")
                    i += 3
                else:
                    _add("SK")
                    i += 3
            elif i == last and _substr(i - 2, 2) in ("AI", "OI"):
                _add("", "S")
                i += 1
            else:
                _add("S")
                i += 2 if _at(i + 1) in "SZ" else 1

        elif c == "T":
            if _substr(i, 4) in ("TION", "TIA", "TCH"):
                _add("X")
                i += 3
            elif _substr(i, 2) == "TH" or _substr(i, 3) == "TTH":
                if _substr(i + 2, 2) in ("OM", "AM") or _substr(0, 4) in ("VAN ", "VON ") or _substr(0, 3) == "SCH":
                    _add("T")
                else:
                    _add("0", "T")
                i += 2
            else:
                _add("T")
                i += 2 if _at(i + 1) in "TD" else 1

        elif c == "V":
            _add("F")
            i += 2 if _at(i + 1) == "V" else 1

        elif c == "W":
            if _substr(i, 2) == "WR":
                _add("R")
                i += 2
            elif i == 0 and (_at(1) in _VOWELS or _substr(0, 2) == "WH"):
                if _at(1) in _VOWELS:
                    _add("A", "F")
                else:
                    _add("A")
                i += 1
            elif (i == last and _at(i - 1) in _VOWELS) or _substr(i - 1, 5) in ("EWSKI", "EWSKY", "OWSKI", "OWSKY") or _substr(0, 3) == "SCH":
                _add("", "F")
                i += 1
            elif _substr(i, 4) in ("WICZ", "WITZ"):
                _add("TS", "FX")
                i += 4
            else:
                i += 1

        elif c == "X":
            if not (i == last and (_substr(i - 3, 3) in ("IAU", "EAU") or _substr(i - 2, 2) in ("AU", "OU"))):
                _add("KS")
            i += 2 if _at(i + 1) in "CX" else 1

        elif c == "Z":
            if _at(i + 1) == "H":
                _add("J")
                i += 2
            elif _substr(i + 1, 2) in ("ZO", "ZI", "ZA") or (_slavo_germanic() and i > 0 and _at(i - 1) != "T"):
                _add("S", "TS")
                i += 1
            else:
                _add("S")
                i += 2 if _at(i + 1) == "Z" else 1

        else:
            i += 1

    return ("".join(primary), "".join(alternate))


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def are_words_equivalent(
    w1: str, w2: str, levenshtein_threshold: float = 0.85, jaro_winkler_threshold: float = 0.9, metaphone_required: bool = True
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
        w1, w2, levenshtein_threshold=levenshtein_threshold, jaro_winkler_threshold=jaro_winkler_threshold, metaphone_required=metaphone_required
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
        self, w1: str, w2: str, levenshtein_threshold: float = 0.85, jaro_winkler_threshold: float = 0.9, metaphone_required: bool = True
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

        metrics = {"levenshtein_ratio": lev, "jaro_winkler_score": jaro, "phonetic_match": phonetic_match, "mra_similarity": mra_sim}

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
            return {"distance": 1.0 - res, "similarity": res, "score": res * 100.0}

        elif algo == "jaro_winkler":
            res = jaro_winkler_score(s1, s2)
            return {"distance": 1.0 - res, "similarity": res, "score": res * 100.0}

        elif algo == "jaccard":
            res = jaccard_similarity(s1, s2)
            return {"distance": 1.0 - res, "similarity": res, "score": res * 100.0}

        elif algo == "sorensen_dice":
            res = sorensen_dice_coefficient(s1, s2)
            return {"distance": 1.0 - res, "similarity": res, "score": res * 100.0}

        elif algo == "lcs":
            return lcs_score(s1, s2)

        elif algo == "mra":
            res = mra_similarity(s1, s2)
            return {"distance": 1.0 - res, "similarity": res, "score": res * 100.0}

        elif algo == "soundex":
            c1, c2 = soundex(s1), soundex(s2)
            match = 1.0 if c1 == c2 else 0.0
            return {"code_1": c1, "code_2": c2, "match": bool(c1 == c2), "similarity": match, "score": match * 100.0}

        elif algo == "metaphone":
            c1, c2 = metaphone(s1), metaphone(s2)
            match = 1.0 if c1 == c2 else 0.0
            return {"code_1": c1, "code_2": c2, "match": bool(c1 == c2), "similarity": match, "score": match * 100.0}

        elif algo == "double_metaphone":
            p1, a1 = double_metaphone(s1)
            p2, a2 = double_metaphone(s2)
            match = p1 == p2 or p1 == a2 or a1 == p2 or a1 == a2
            sim = 1.0 if match else 0.0
            return {"primary_1": p1, "alternate_1": a1, "primary_2": p2, "alternate_2": a2, "match": match, "similarity": sim, "score": sim * 100.0}

        return {"error": f"Unknown algorithm: {algorithm}"}


def string_distance_hamming(s1: str, s2: str) -> int:
    """
    Compute the Hamming distance between two equal-length strings.

    The Hamming distance counts the number of positions at which the
    corresponding characters differ.

    Args:
        s1 (str): First string.
        s2 (str): Second string (must be same length as *s1*).

    Returns:
        int: Number of differing positions.

    Raises:
        TypeError: If either argument is not a string.
        ValueError: If strings have different lengths.

    Example Usage:
        string_distance_hamming("karolin", "kathrin")   # 3
        string_distance_hamming("1011101", "1001001")   # 2

    Cost:
        O(n), where n is the string length.
    """
    if not isinstance(s1, str) or not isinstance(s2, str):
        raise TypeError("Both arguments must be strings")

    if len(s1) != len(s2):
        raise ValueError(f"Strings must be of equal length, got {len(s1)} and {len(s2)}")

    return sum(c1 != c2 for c1, c2 in zip(s1, s2))
