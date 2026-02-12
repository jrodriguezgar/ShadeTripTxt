"""
Word Similarity - Core similarity engines and classes.

This module provides the WordSimilarity class and auxiliary functions for
comparing words using multiple algorithms.

Algorithms:
    - Levenshtein
    - Jaro-Winkler
    - Hamming
    - Jaccard
    - Sørensen-Dice
    - Metaphone (Phonetic)
    - MRA (Match Rating Approach)

Author: DatamanEdge
"""

from typing import Dict, Any, Tuple, Optional, Union
from . import similarity_engines as engines


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


class WordSimilarity:
    """
    Core class for word-level similarity calculations.
    """
    
    def __init__(self):
        pass
        
    def sorensen_dice_score(self, s1: str, s2: str) -> float:
        return engines.sorensen_dice_score(s1, s2)
        
    def ratcliff_obershelp_score(self, s1: str, s2: str) -> float:
        return engines.ratcliff_obershelp_score(s1, s2)

    def levenshtein_score(self, s1: str, s2: str) -> float:
        return engines.levenshtein_score(s1, s2)
        
    def jaro_winkler_score(self, s1: str, s2: str) -> float:
        # Compatibility: original might return 0-100. We'll return 0-100 here if needed.
        # Looking at TextMatcher.compare_with_abbreviation, it expects 0-100 and divides by 100.
        return engines.jaro_winkler_score(s1, s2) * 100.0
        
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
            
        lev = self.levenshtein_score(w1, w2)
        jaro = engines.jaro_winkler_score(w1, w2) # 0-1
        
        # Phonetic match (Simplified for now)
        mra_sim = engines.mra_similarity(w1, w2)
        phonetic_match = mra_sim >= 0.8
        
        metrics = {
            'levenshtein_ratio': lev,
            'jaro_winkler_score': jaro,
            'phonetic_match': phonetic_match,
            'mra_similarity': mra_sim
        }
        
        is_match = False
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
            res = engines.levenshtein_score(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}
            
        elif algo == "jaro_winkler":
            res = engines.jaro_winkler_score(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}
            
        elif algo == "jaccard":
            res = engines.jaccard_similarity(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}
            
        elif algo == "sorensen_dice":
            res = engines.sorensen_dice_coefficient(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}
            
        elif algo == "lcs":
            return engines.lcs_score(s1, s2)
            
        elif algo == "mra":
            res = engines.mra_similarity(s1, s2)
            return {'distance': 1.0 - res, 'similarity': res, 'score': res * 100.0}
            
        return {'error': f"Unknown algorithm: {algorithm}"}
