"""BharatLens Machine Learning Subsystem.

Provides lightweight, explainable NLP modules for category classification,
text similarity, and duplicate detection.
"""

from app.ml.category_classifier import CategoryClassifier, get_category_classifier
from app.ml.similarity import calculate_similarity, is_near_duplicate, group_similar_articles
from app.ml.text_processing import preprocess_text

__all__ = [
    "CategoryClassifier",
    "get_category_classifier",
    "calculate_similarity",
    "is_near_duplicate",
    "group_similar_articles",
    "preprocess_text",
]
