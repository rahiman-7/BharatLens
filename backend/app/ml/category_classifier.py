import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from app.ml.text_processing import preprocess_text

logger = logging.getLogger("bharatlens.ml")

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "category_model.joblib"
DEFAULT_DATASET_PATH = Path(__file__).resolve().parent / "data" / "sample_dataset.json"

ALLOWED_CATEGORIES = [
    "politics",
    "sports",
    "technology",
    "business",
    "movies-entertainment",
    "education",
    "science",
    "health",
    "lifestyle",
    "crime",
    "environment",
]


class CategoryClassifier:
    """Lightweight, explainable news category classifier using TF-IDF + Logistic Regression."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.pipeline: Optional[Pipeline] = None
        self.classes_: list[str] = []

    def build_pipeline(self) -> Pipeline:
        """Construct a scikit-learn NLP pipeline."""
        return Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=5000,
                    stop_words="english",
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    random_state=42,
                    max_iter=1000,
                ),
            ),
        ])

    def load_dataset(self, dataset_path: Optional[Path] = None) -> Tuple[list[str], list[str]]:
        """Load bootstrap dataset from JSON file."""
        target_path = Path(dataset_path) if dataset_path else DEFAULT_DATASET_PATH
        if not target_path.exists():
            raise FileNotFoundError(f"Training dataset not found at {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        samples = data.get("samples", [])
        if not samples:
            raise ValueError("Training dataset contains no samples.")

        texts = []
        labels = []
        for sample in samples:
            text = preprocess_text(sample.get("title", ""), sample.get("description", ""))
            label = sample.get("category", "").strip().lower()
            if text and label in ALLOWED_CATEGORIES:
                texts.append(text)
                labels.append(label)

        return texts, labels

    def train(
        self,
        dataset_path: Optional[Path] = None,
        test_size: float = 0.25,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """Train the classifier on bootstrap data and evaluate on a held-out test split."""
        texts, labels = self.load_dataset(dataset_path)
        
        # Train / Test split with stratification
        X_train, X_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=test_size,
            random_state=random_state,
            stratify=labels,
        )

        eval_pipeline = self.build_pipeline()
        eval_pipeline.fit(X_train, y_train)

        # Evaluate on test split
        y_pred = eval_pipeline.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
            y_test, y_pred, average="macro", zero_division=0
        )
        p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
            y_test, y_pred, average="weighted", zero_division=0
        )

        # Train final pipeline on all available data for maximum vocabulary coverage
        self.pipeline = self.build_pipeline()
        self.pipeline.fit(texts, labels)
        self.classes_ = list(self.pipeline.named_steps["clf"].classes_)

        metrics = {
            "dataset_type": "DEMO / BOOTSTRAP TRAINING DATA",
            "total_samples": len(texts),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_categories": len(set(labels)),
            "categories": sorted(list(set(labels))),
            "accuracy": round(acc, 4),
            "precision_macro": round(float(p_macro), 4),
            "recall_macro": round(float(r_macro), 4),
            "f1_macro": round(float(f1_macro), 4),
            "precision_weighted": round(float(p_weighted), 4),
            "recall_weighted": round(float(r_weighted), 4),
            "f1_weighted": round(float(f1_weighted), 4),
            "note": "Metrics are demonstration-level from a synthetic bootstrap dataset.",
        }

        return metrics

    def save_model(self, model_path: Optional[Path] = None) -> Path:
        """Persist trained model pipeline to disk using joblib."""
        if self.pipeline is None:
            raise ValueError("Cannot save an untrained model. Call train() or load_model() first.")

        target_path = Path(model_path) if model_path else self.model_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, target_path)
        logger.info(f"Saved ML category classifier model to {target_path}")
        return target_path

    def load_model(self, model_path: Optional[Path] = None) -> bool:
        """Load trained pipeline artifact from disk."""
        target_path = Path(model_path) if model_path else self.model_path
        if not target_path.exists():
            logger.warning(f"ML model artifact not found at {target_path}. Using fallback classifier.")
            return False

        try:
            self.pipeline = joblib.load(target_path)
            self.classes_ = list(self.pipeline.named_steps["clf"].classes_)
            logger.info(f"Loaded ML category classifier model from {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load ML model artifact from {target_path}: {e}")
            self.pipeline = None
            return False

    def predict(
        self,
        title: Optional[str],
        description: Optional[str] = None,
    ) -> Tuple[str, float]:
        """Predict category slug and return (category_slug, confidence_score)."""
        text = preprocess_text(title, description)
        if not text:
            return "politics", 0.0

        if self.pipeline is None:
            # Try lazy load once
            if not self.load_model():
                return "politics", 0.0

        try:
            probs = self.pipeline.predict_proba([text])[0]
            best_idx = int(np.argmax(probs))
            best_class = str(self.pipeline.named_steps["clf"].classes_[best_idx])
            confidence = float(probs[best_idx])
            return best_class, round(confidence, 4)
        except Exception as e:
            logger.error(f"Error during ML category prediction: {e}")
            return "politics", 0.0


# Global singleton instance
_GLOBAL_CLASSIFIER: Optional[CategoryClassifier] = None


def get_category_classifier() -> CategoryClassifier:
    """Returns initialized singleton instance of CategoryClassifier."""
    global _GLOBAL_CLASSIFIER
    if _GLOBAL_CLASSIFIER is None:
        _GLOBAL_CLASSIFIER = CategoryClassifier()
        _GLOBAL_CLASSIFIER.load_model()
    return _GLOBAL_CLASSIFIER
