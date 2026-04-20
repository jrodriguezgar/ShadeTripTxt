"""
Match Result - Rich Result Object for Text Comparison

This module provides a rich result class for text matching operations
that replaces fragile tuple/boolean returns with a robust object-oriented API.

Classes:
    MatchResult: Rich result object for match operations

Author: AI Assistant
Date: November 9, 2025
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class MatchResult:
    """
    Rich result object for text matching operations.

    Description:
        This class replaces fragile tuple returns (e.g., (is_match, metrics))
        with a robust, self-documenting object. It provides:

        - **Clear Properties**: `.is_match`, `.score`, `.best_candidate`
        - **Detailed Metrics**: `.metrics` dictionary with algorithm scores
        - **Explanations**: `.explain()` method for debugging
        - **Type Safety**: Proper typing for all attributes

        **Why MatchResult?**

        Before (fragile):
        ```python
        is_match, score, metrics = matcher.find_best_match(...)
        # What does position 1 mean again? Score or metrics?
        ```

        After (robust):
        ```python
        result = matcher.find_best_match(...)
        if result.is_match:
            print(f"Best: {result.best_candidate} (score: {result.score})")
            print(result.explain())
        ```

    Attributes:
        is_match (bool): Whether a match was found above threshold
        score (float): Overall similarity score (0.0-1.0)
        best_candidate (Optional[str]): Best matching candidate (if any)
        query (str): Original query string
        candidates (List[str]): List of candidates compared
        metrics (Dict[str, float]): Detailed algorithm metrics
        threshold (float): Threshold used for matching
        explanation (Optional[str]): Detailed explanation (if debug_mode=True)
        config (Optional[Dict[str, Any]]): Configuration used for matching

    Example Usage:
        # Basic usage
        result = matcher.find_best_match("John Smith", ["Jon Smith", "Jane Doe"])

        if result.is_match:
            print(f"Found: {result.best_candidate}")
            print(f"Score: {result.score:.2f}")
        else:
            print("No match found")

        # Access detailed metrics
        print(f"Levenshtein: {result.metrics['levenshtein_ratio']:.2f}")
        print(f"Jaro-Winkler: {result.metrics['jaro_winkler_score']:.2f}")

        # Get explanation
        if result.explanation:
            print(result.explain())

        # Check properties
        result.is_perfect_match  # True if score == 1.0
        result.is_high_confidence  # True if score >= 0.90
        result.is_medium_confidence  # True if score >= 0.75

    Cost:
        O(1) for property access
    """

    # Core attributes
    is_match: bool
    score: float
    best_candidate: Optional[str] = None
    query: str = ""
    candidates: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    threshold: float = 0.0
    explanation: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    # Additional context
    all_scores: List[float] = field(default_factory=list)  # Scores for all candidates
    algorithm_used: str = "composite"  # Which algorithm produced the result

    def __post_init__(self):
        """Validate result data."""
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {self.threshold}")

    @property
    def is_perfect_match(self) -> bool:
        """
        Check if this is a perfect match (score == 1.0).

        Returns:
            bool: True if perfect match

        Example:
            if result.is_perfect_match:
                print("Exact match!")
        """
        return self.score >= 0.9999  # Account for floating point precision

    @property
    def is_high_confidence(self) -> bool:
        """
        Check if this is a high-confidence match (score >= 0.90).

        Returns:
            bool: True if high confidence

        Example:
            if result.is_high_confidence:
                auto_approve(result.best_candidate)
        """
        return self.score >= 0.90

    @property
    def is_medium_confidence(self) -> bool:
        """
        Check if this is a medium-confidence match (0.75 <= score < 0.90).

        Returns:
            bool: True if medium confidence

        Example:
            if result.is_medium_confidence:
                request_manual_review(result)
        """
        return 0.75 <= self.score < 0.90

    @property
    def is_low_confidence(self) -> bool:
        """
        Check if this is a low-confidence match (threshold <= score < 0.75).

        Returns:
            bool: True if low confidence
        """
        return self.threshold <= self.score < 0.75

    @property
    def confidence_level(self) -> str:
        """
        Get human-readable confidence level.

        Returns:
            str: 'perfect', 'high', 'medium', 'low', or 'no_match'

        Example:
            result = matcher.find_best_match(...)
            print(f"Confidence: {result.confidence_level}")
            # Output: "Confidence: high"
        """
        if self.is_perfect_match:
            return "perfect"
        elif self.is_high_confidence:
            return "high"
        elif self.is_medium_confidence:
            return "medium"
        elif self.is_low_confidence:
            return "low"
        else:
            return "no_match"

    def explain(self, verbose: bool = False) -> str:
        """
        Get detailed explanation of the match result.

        Description:
            Returns a formatted explanation showing:
            - Query and best candidate
            - Overall score and threshold
            - Individual algorithm metrics
            - Match decision reasoning
            - Configuration used (if verbose=True)

        Args:
            verbose (bool): Include configuration details. Default: False

        Returns:
            str: Formatted explanation

        Example:
            result = matcher.find_best_match("John Smith", ["Jon Smith"])
            print(result.explain())

            # Output:
            # Match Result Explanation
            # ========================
            # Query: "John Smith"
            # Best Candidate: "Jon Smith"
            # Overall Score: 0.87
            # Threshold: 0.85
            # Confidence: HIGH
            #
            # Algorithm Metrics:
            #   ✓ Levenshtein Ratio: 0.89 (>= 0.85)
            #   ✓ Jaro-Winkler Score: 92.5 (>= 0.9)
            #   ✓ Metaphone Match: Yes
            #
            # Decision: MATCH (score 0.87 >= threshold 0.85)

        Cost:
            O(n) where n is number of metrics
        """
        # Use pre-generated explanation if available (from debug_mode)
        if self.explanation:
            return self.explanation

        # Build explanation from scratch
        lines = []
        lines.append("Match Result Explanation")
        lines.append("=" * 60)
        lines.append(f'Query: "{self.query}"')

        if self.best_candidate:
            lines.append(f'Best Candidate: "{self.best_candidate}"')
        else:
            lines.append("Best Candidate: (none found)")

        lines.append(f"Overall Score: {self.score:.2f}")
        lines.append(f"Threshold: {self.threshold:.2f}")
        lines.append(f"Confidence: {self.confidence_level.upper()}")
        lines.append("")

        # Algorithm metrics
        if self.metrics:
            lines.append("Algorithm Metrics:")

            # Levenshtein
            if "levenshtein_ratio" in self.metrics:
                lev_ratio = self.metrics["levenshtein_ratio"]
                lev_threshold = self.config.get("levenshtein_threshold", 0.85) if self.config else 0.85
                symbol = "✓" if lev_ratio >= lev_threshold else "✗"
                lines.append(f"  {symbol} Levenshtein Ratio: {lev_ratio:.2f} (>= {lev_threshold:.2f})")

            # Jaro-Winkler
            if "jaro_winkler_score" in self.metrics:
                jaro_score = self.metrics["jaro_winkler_score"]
                jaro_threshold = self.config.get("jaro_winkler_threshold", 0.9) if self.config else 0.9
                symbol = "✓" if jaro_score >= jaro_threshold else "✗"
                lines.append(f"  {symbol} Jaro-Winkler Score: {jaro_score:.2f} (>= {jaro_threshold:.2f})")

            # Metaphone
            if "metaphone_match" in self.metrics:
                metaphone = self.metrics["metaphone_match"]
                symbol = "✓" if metaphone else "✗"
                lines.append(f"  {symbol} Metaphone Match: {'Yes' if metaphone else 'No'}")

            # Other metrics
            for key, value in self.metrics.items():
                if key not in ["levenshtein_ratio", "jaro_winkler_score", "metaphone_match"]:
                    lines.append(f"  • {key}: {value}")

            lines.append("")

        # Decision
        if self.is_match:
            lines.append(f"Decision: MATCH (score {self.score:.2f} >= threshold {self.threshold:.2f})")
        else:
            lines.append(f"Decision: NO MATCH (score {self.score:.2f} < threshold {self.threshold:.2f})")

        # Verbose: Configuration details
        if verbose and self.config:
            lines.append("")
            lines.append("Configuration:")
            for key, value in self.config.items():
                lines.append(f"  {key}: {value}")

        # Alternative candidates
        if len(self.candidates) > 1 and self.all_scores:
            lines.append("")
            lines.append("Alternative Candidates:")
            for i, (candidate, score) in enumerate(zip(self.candidates, self.all_scores)):
                if candidate != self.best_candidate:
                    lines.append(f'  {i + 1}. "{candidate}" (score: {score:.2f})')

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        Returns:
            Dict[str, Any]: Result as dictionary

        Example:
            result = matcher.find_best_match(...)
            data = result.to_dict()
            json.dump(data, file)

        Cost:
            O(1)
        """
        return {
            "is_match": self.is_match,
            "score": self.score,
            "best_candidate": self.best_candidate,
            "query": self.query,
            "candidates": self.candidates,
            "metrics": self.metrics,
            "threshold": self.threshold,
            "confidence_level": self.confidence_level,
            "algorithm_used": self.algorithm_used,
            "all_scores": self.all_scores,
        }

    def __str__(self) -> str:
        """
        String representation of result.

        Returns:
            str: Human-readable string

        Example:
            result = matcher.find_best_match(...)
            print(result)
            # Output: MatchResult(match=True, score=0.87, candidate="Jon Smith")
        """
        if self.is_match:
            return f'MatchResult(match=True, score={self.score:.2f}, candidate="{self.best_candidate}")'
        else:
            return f"MatchResult(match=False, score={self.score:.2f})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"MatchResult(is_match={self.is_match}, score={self.score:.2f}, "
            f'best_candidate="{self.best_candidate}", threshold={self.threshold:.2f}, '
            f'confidence="{self.confidence_level}")'
        )

    def __bool__(self) -> bool:
        """
        Boolean conversion returns is_match.

        Returns:
            bool: True if match found

        Example:
            result = matcher.find_best_match(...)
            if result:  # Equivalent to: if result.is_match:
                print("Match found!")
        """
        return self.is_match

    @staticmethod
    def no_match(query: str, candidates: List[str], threshold: float = 0.0, config: Optional[Dict[str, Any]] = None) -> "MatchResult":
        """
        Create a "no match" result.

        Args:
            query (str): Original query
            candidates (List[str]): Candidates that were compared
            threshold (float): Threshold used. Default: 0.0
            config (Optional[Dict[str, Any]]): Configuration used

        Returns:
            MatchResult: No match result

        Example:
            result = MatchResult.no_match(
                query="John Smith",
                candidates=["Jane Doe", "Bob Green"],
                threshold=0.85
            )

        Cost:
            O(1)
        """
        return MatchResult(is_match=False, score=0.0, best_candidate=None, query=query, candidates=candidates, threshold=threshold, config=config)

    @staticmethod
    def from_tuple(
        query: str,
        candidates: List[str],
        tuple_result: Tuple[bool, float, Dict[str, float]],
        threshold: float = 0.0,
        best_candidate: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> "MatchResult":
        """
        Create MatchResult from legacy tuple format (is_match, score, metrics).

        Args:
            query (str): Original query
            candidates (List[str]): Candidates compared
            tuple_result (Tuple): (is_match, score, metrics) tuple
            threshold (float): Threshold used
            best_candidate (Optional[str]): Best matching candidate
            config (Optional[Dict[str, Any]]): Configuration used

        Returns:
            MatchResult: Rich result object

        Example:
            # Legacy code returns tuple
            is_match, score, metrics = old_function(...)

            # Convert to MatchResult
            result = MatchResult.from_tuple(
                query="John Smith",
                candidates=["Jon Smith"],
                tuple_result=(is_match, score, metrics),
                threshold=0.85,
                best_candidate="Jon Smith"
            )

        Cost:
            O(1)
        """
        is_match, score, metrics = tuple_result

        return MatchResult(
            is_match=is_match,
            score=score,
            best_candidate=best_candidate,
            query=query,
            candidates=candidates,
            metrics=metrics,
            threshold=threshold,
            config=config,
        )
