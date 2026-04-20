"""
ML Similarity Adapter - Machine Learning Integration for Text Similarity

This module provides an abstract adapter interface for integrating custom
machine learning models into the text matching pipeline. When heuristic
rules fail, ML models can provide learned similarity scoring.

Classes:
    MLSimilarityAdapter: Abstract base class for ML similarity models
    SklearnSimilarityAdapter: Example adapter for scikit-learn models

Author: AI Assistant
Date: November 9, 2025
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional

# numpy is imported lazily inside methods that need it.
# Install with: pip install numpy


class MLSimilarityAdapter(ABC):
    """
    Abstract base class for ML-based similarity scoring.

    Description:
        This class defines the interface for integrating custom machine learning
        models into the text matching pipeline. Users can implement this interface
        to inject trained models (scikit-learn, PyTorch, TensorFlow, etc.) that
        predict similarity scores based on learned patterns.

        **Use Cases**:
        - When rule-based approaches fail on domain-specific data
        - When you have labeled training data (pairs + similarity labels)
        - When similarity patterns are complex and non-obvious

        **Workflow**:
        1. Train your ML model externally (e.g., Random Forest, Neural Network)
        2. Implement this interface to wrap your model
        3. Pass the adapter to TextMatcher
        4. TextMatcher will use ML predictions when available

    Methods to Implement:
        - predict_similarity(): Returns similarity score (0.0-1.0) for text pair
        - predict_batch(): Returns scores for multiple pairs (optional optimization)
        - get_features(): Extracts features from text pair for model input

    Attributes:
        model: The underlying ML model (scikit-learn, PyTorch, etc.)
        feature_names: Names of features used by the model

    Example Implementation:
        class MyMLAdapter(MLSimilarityAdapter):
            def __init__(self, model_path: str):
                import joblib
                self.model = joblib.load(model_path)
                self.feature_names = ['levenshtein', 'jaro_winkler', 'length_diff']

            def predict_similarity(self, text1: str, text2: str) -> float:
                features = self.get_features(text1, text2)
                score = self.model.predict_proba([features])[0][1]  # Probability of match
                return score

            def get_features(self, text1: str, text2: str) -> List[float]:
                from ..utils.string_similarity import WordSimilarity
                ws = WordSimilarity()

                lev = ws.levenshtein_score(text1, text2)
                jaro = ws.jaro_winkler_score(text1, text2)
                len_diff = abs(len(text1) - len(text2))

                return [lev, jaro, len_diff]

        # Usage
        adapter = MyMLAdapter('my_trained_model.pkl')
        matcher = TextMatcher(ml_adapter=adapter)

        score = matcher.find_best_match("Jose Garcia", candidates)
        # Uses ML model for similarity scoring

    Cost:
        Depends on underlying ML model complexity
    """

    @abstractmethod
    def predict_similarity(self, text1: str, text2: str) -> float:
        """
        Predict similarity score for a text pair using ML model.

        Description:
            This method should return a normalized similarity score (0.0-1.0)
            where 0.0 means completely different and 1.0 means identical.

        Args:
            text1 (str): First text
            text2 (str): Second text

        Returns:
            float: Similarity score (0.0-1.0)

        Raises:
            ValueError: If texts are invalid
            RuntimeError: If model prediction fails

        Example:
            adapter = MyMLAdapter('model.pkl')
            score = adapter.predict_similarity("John Smith", "Jon Smith")
            # Returns: 0.87 (from trained model)

        Cost:
            O(f + m) where f is feature extraction cost, m is model inference cost
        """
        pass

    def predict_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Predict similarity scores for multiple text pairs (batch processing).

        Description:
            Default implementation calls predict_similarity() for each pair.
            Override this method for optimized batch inference if your ML
            framework supports it (e.g., batch prediction in scikit-learn,
            TensorFlow batching, etc.).

        Args:
            pairs (List[Tuple[str, str]]): List of (text1, text2) tuples

        Returns:
            List[float]: Similarity scores (0.0-1.0) for each pair

        Example:
            adapter = MyMLAdapter('model.pkl')

            pairs = [
                ("John Smith", "Jon Smith"),
                ("Jane Doe", "J. Doe"),
                ("Alice Brown", "Bob Green")
            ]

            scores = adapter.predict_batch(pairs)
            # Returns: [0.87, 0.92, 0.15]

        Cost:
            Default: O(n * (f + m)) where n is number of pairs
            Optimized: O(f*n + m) with batch inference
        """
        return [self.predict_similarity(t1, t2) for t1, t2 in pairs]

    @abstractmethod
    def get_features(self, text1: str, text2: str) -> List[float]:
        """
        Extract features from text pair for model input.

        Description:
            This method should extract numerical features that your ML model
            expects as input. Common features include:

            - String similarity metrics (Levenshtein, Jaro-Winkler, etc.)
            - Length differences
            - Character n-gram overlaps
            - Word embedding similarities
            - Phonetic features

        Args:
            text1 (str): First text
            text2 (str): Second text

        Returns:
            List[float]: Feature vector

        Example:
            def get_features(self, text1: str, text2: str) -> List[float]:
                lev_ratio = levenshtein_ratio(text1, text2)
                jaro_score = jaro_winkler_score(text1, text2)
                len_diff = abs(len(text1) - len(text2))
                len_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2))

                return [lev_ratio, jaro_score, len_diff, len_ratio]

        Cost:
            O(n + m) where n and m are text lengths (for typical features)
        """
        pass

    def get_feature_names(self) -> List[str]:
        """
        Get names of features extracted by get_features().

        Returns:
            List[str]: Feature names

        Example:
            adapter = MyMLAdapter('model.pkl')
            names = adapter.get_feature_names()
            # Returns: ['levenshtein_ratio', 'jaro_winkler', 'length_diff', 'length_ratio']

        Cost:
            O(1)
        """
        return getattr(self, "feature_names", [])

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the underlying ML model.

        Returns:
            Dict[str, Any]: Model metadata

        Example:
            adapter = MyMLAdapter('model.pkl')
            info = adapter.get_model_info()
            # Returns: {
            #     'model_type': 'RandomForestClassifier',
            #     'n_features': 4,
            #     'trained_on': 10000,
            #     'accuracy': 0.94
            # }

        Cost:
            O(1)
        """
        return {"model_type": type(self.model).__name__ if hasattr(self, "model") else "Unknown", "feature_count": len(self.get_feature_names())}


class SklearnSimilarityAdapter(MLSimilarityAdapter):
    """
    Example ML adapter implementation using scikit-learn.

    Description:
        This is a concrete implementation of MLSimilarityAdapter that
        demonstrates how to integrate scikit-learn models. It can work
        with any scikit-learn classifier that has predict_proba() method.

        **Supported Models**:
        - RandomForestClassifier
        - GradientBoostingClassifier
        - LogisticRegression
        - SVC (with probability=True)
        - MLPClassifier

    Attributes:
        model: Trained scikit-learn classifier
        feature_names: Names of extracted features
        threshold: Classification threshold (default: 0.5)

    Example Usage:
        # Step 1: Train a model externally
        from sklearn.ensemble import RandomForestClassifier
        import joblib

        # Assume you have training data
        X_train = [...]  # Feature vectors
        y_train = [...]  # Labels (0=different, 1=similar)

        model = RandomForestClassifier(n_estimators=100)
        model.fit(X_train, y_train)
        joblib.dump(model, 'similarity_model.pkl')

        # Step 2: Load and use with adapter
        model = joblib.load('similarity_model.pkl')
        adapter = SklearnSimilarityAdapter(model)

        # Step 3: Integrate with TextMatcher
        from .text_matcher import TextMatcher
        matcher = TextMatcher(ml_adapter=adapter)

        # Step 4: Use normally
        score = matcher.find_best_match("Jose Garcia", candidates)

    Cost:
        Depends on scikit-learn model complexity (typically O(log n) for tree-based)
    """

    def __init__(self, model: Any, feature_names: Optional[List[str]] = None, threshold: float = 0.5):
        """
        Initialize scikit-learn adapter.

        Args:
            model: Trained scikit-learn classifier with predict_proba()
            feature_names (Optional[List[str]]): Names of features. If None,
                                                 uses default feature set.
            threshold (float): Classification threshold (0.0-1.0). Default: 0.5

        Raises:
            ValueError: If model doesn't have predict_proba()
            ValueError: If threshold is outside valid range
        """
        if not hasattr(model, "predict_proba"):
            raise ValueError("Model must have predict_proba() method")

        if not (0.0 <= threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")

        self.model = model
        self.threshold = threshold
        self.feature_names = feature_names or [
            "levenshtein_ratio",
            "jaro_winkler_score",
            "length_difference",
            "length_ratio",
            "common_prefix_ratio",
            "common_suffix_ratio",
        ]

    def predict_similarity(self, text1: str, text2: str) -> float:
        """
        Predict similarity using scikit-learn model.

        Args:
            text1 (str): First text
            text2 (str): Second text

        Returns:
            float: Similarity score (0.0-1.0)

        Example:
            adapter = SklearnSimilarityAdapter(model)
            score = adapter.predict_similarity("John Smith", "Jon Smith")
            # Returns: 0.87
        """
        features = self.get_features(text1, text2)

        # Get probability of "similar" class (class 1)
        proba = self.model.predict_proba([features])[0]

        # Return probability of similarity (assumes binary classification)
        if len(proba) == 2:
            return float(proba[1])  # Probability of class 1 (similar)
        else:
            # Multi-class: return max probability
            return float(max(proba))

    def predict_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Batch prediction using scikit-learn (optimized).

        Args:
            pairs (List[Tuple[str, str]]): Text pairs

        Returns:
            List[float]: Similarity scores
        """
        # Extract features for all pairs
        features_list = [self.get_features(t1, t2) for t1, t2 in pairs]

        # Batch predict
        probas = self.model.predict_proba(features_list)

        # Extract similarity probabilities
        if probas.shape[1] == 2:
            return [float(p[1]) for p in probas]
        else:
            return [float(max(p)) for p in probas]

    def get_features(self, text1: str, text2: str) -> List[float]:
        """
        Extract default feature set for similarity comparison.

        Args:
            text1 (str): First text
            text2 (str): Second text

        Returns:
            List[float]: Feature vector [lev_ratio, jaro, len_diff, len_ratio, prefix, suffix]
        """
        from ..utils.string_similarity import WordSimilarity

        ws = WordSimilarity()

        # Basic similarity metrics
        lev_ratio = ws.levenshtein_score(text1, text2)
        jaro_score = ws.jaro_winkler_score(text1, text2)

        # Length features
        len1, len2 = len(text1), len(text2)
        len_diff = abs(len1 - len2)
        len_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0

        # Prefix/suffix overlap
        common_prefix_len = 0
        for c1, c2 in zip(text1, text2):
            if c1 == c2:
                common_prefix_len += 1
            else:
                break

        common_suffix_len = 0
        for c1, c2 in zip(reversed(text1), reversed(text2)):
            if c1 == c2:
                common_suffix_len += 1
            else:
                break

        prefix_ratio = common_prefix_len / max(len1, len2) if max(len1, len2) > 0 else 0.0
        suffix_ratio = common_suffix_len / max(len1, len2) if max(len1, len2) > 0 else 0.0

        return [
            lev_ratio,
            jaro_score / 100.0,  # Normalize to 0-1
            len_diff,
            len_ratio,
            prefix_ratio,
            suffix_ratio,
        ]

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get scikit-learn model information.

        Returns:
            Dict[str, Any]: Model metadata
        """
        info = super().get_model_info()
        info.update({"threshold": self.threshold, "sklearn_version": self._get_sklearn_version()})

        # Add model-specific info if available
        if hasattr(self.model, "n_estimators"):
            info["n_estimators"] = self.model.n_estimators
        if hasattr(self.model, "max_depth"):
            info["max_depth"] = self.model.max_depth

        return info

    def _get_sklearn_version(self) -> str:
        """Get scikit-learn version."""
        try:
            import sklearn

            return sklearn.__version__
        except ImportError:
            return "unknown"


# Example training code (for documentation)
"""
Example: Training a Similarity Model
=====================================

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Step 1: Prepare training data
# Each sample is a pair of texts with label (0=different, 1=similar)
training_pairs = [
    ("John Smith", "Jon Smith", 1),
    ("Jane Doe", "J. Doe", 1),
    ("Alice Brown", "Bob Green", 0),
    ("María García", "Maria Garcia", 1),
    ("Microsoft Corp", "Microsoft Corporation", 1),
    ("Apple Inc", "Orange Ltd", 0),
    # ... add thousands more examples
]

# Step 2: Extract features
adapter = SklearnSimilarityAdapter(None)  # Temporary for feature extraction

X = []
y = []
for text1, text2, label in training_pairs:
    features = adapter.get_features(text1, text2)
    X.append(features)
    y.append(label)

# Step 3: Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Step 4: Train model
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42
)
model.fit(X_train, y_train)

# Step 5: Evaluate
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
print(classification_report(y_test, y_pred))

# Step 6: Save model
joblib.dump(model, 'similarity_model.pkl')

# Step 7: Use in production
model = joblib.load('similarity_model.pkl')
adapter = SklearnSimilarityAdapter(model)

score = adapter.predict_similarity("John Smith", "Jon Smith")
print(f"Similarity: {score:.2f}")
```

Expected Output:
Accuracy: 0.94
              precision    recall  f1-score   support
           0       0.93      0.95      0.94       500
           1       0.95      0.93      0.94       500
    accuracy                           0.94      1000
   macro avg       0.94      0.94      0.94      1000
weighted avg       0.94      0.94      0.94      1000

Similarity: 0.87
"""
