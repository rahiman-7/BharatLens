import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest

from app.ml.text_processing import preprocess_text
from app.ml.category_classifier import (
    CategoryClassifier,
    ALLOWED_CATEGORIES,
    DEFAULT_DATASET_PATH,
    get_category_classifier,
)
from app.ml.similarity import calculate_similarity, is_near_duplicate, group_similar_articles
from app.services.classifier import classify_category, classify_category_deterministic
from app.services.news_provider import RawArticle
from app.services.ingest import ingest_raw_article
from app.db.database import SessionLocal


# ==============================================================================
# 1. CATEGORY CLASSIFIER TESTS
# ==============================================================================

def test_training_dataset_loads_and_contains_expected_categories():
    """Test 1 & 2: Dataset loads and contains all 11 expected categories."""
    classifier = CategoryClassifier()
    texts, labels = classifier.load_dataset(DEFAULT_DATASET_PATH)

    assert len(texts) > 0
    assert len(labels) == len(texts)
    
    unique_labels = set(labels)
    assert len(unique_labels) == 11
    for cat in ALLOWED_CATEGORIES:
        assert cat in unique_labels


def test_model_training_and_evaluation_metrics():
    """Test 3 & 9: Training completes successfully and generates evaluation metrics."""
    classifier = CategoryClassifier()
    metrics = classifier.train(dataset_path=DEFAULT_DATASET_PATH, test_size=0.25, random_state=42)

    assert metrics["dataset_type"] == "DEMO / BOOTSTRAP TRAINING DATA"
    assert metrics["total_samples"] == len(metrics["categories"]) * 8  # 88 samples
    assert metrics["accuracy"] >= 0.0
    assert "precision_macro" in metrics
    assert "recall_macro" in metrics
    assert "f1_macro" in metrics
    assert "f1_weighted" in metrics
    assert classifier.pipeline is not None


def test_model_saving_and_loading():
    """Test 4 & 5: Model can be saved to disk and reloaded successfully."""
    classifier = CategoryClassifier()
    classifier.train(dataset_path=DEFAULT_DATASET_PATH, test_size=0.25, random_state=42)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_model_path = Path(tmpdir) / "test_model.joblib"
        saved_path = classifier.save_model(tmp_model_path)
        assert saved_path.exists()

        new_classifier = CategoryClassifier(model_path=tmp_model_path)
        loaded = new_classifier.load_model()
        assert loaded is True
        assert new_classifier.pipeline is not None
        assert set(new_classifier.classes_) == set(ALLOWED_CATEGORIES)


def test_prediction_returns_allowed_category_with_confidence():
    """Test 6: Prediction returns an allowed category slug and valid confidence score."""
    classifier = CategoryClassifier()
    classifier.train(dataset_path=DEFAULT_DATASET_PATH)

    cat, conf = classifier.predict(
        title="ISRO launches advanced communication satellite into geostationary orbit",
        description="The rocket successfully deployed the payload for deep space observation.",
    )
    assert cat in ALLOWED_CATEGORIES
    assert 0.0 <= conf <= 1.0


def test_prediction_handles_missing_description():
    """Test 7: Prediction functions properly without crashing when description is None."""
    classifier = CategoryClassifier()
    classifier.train(dataset_path=DEFAULT_DATASET_PATH)

    cat, conf = classifier.predict(
        title="Virat Kohli scores magnificent century in one day international cricket match",
        description=None,
    )
    assert cat in ALLOWED_CATEGORIES
    assert cat == "sports"
    assert conf > 0.0


def test_prediction_handles_empty_and_whitespace_safely():
    """Test 8: Prediction handles empty or whitespace-only inputs without throwing exceptions."""
    classifier = CategoryClassifier()
    classifier.train(dataset_path=DEFAULT_DATASET_PATH)

    cat1, conf1 = classifier.predict(title="", description="")
    assert cat1 in ALLOWED_CATEGORIES
    assert conf1 == 0.0

    cat2, conf2 = classifier.predict(title="   \n\t   ", description=None)
    assert cat2 in ALLOWED_CATEGORIES
    assert conf2 == 0.0


# ==============================================================================
# 2. TEXT SIMILARITY TESTS
# ==============================================================================

def test_similarity_identical_texts():
    """Test 10: Identical texts produce similarity exactly equal to 1.0."""
    text = "Prime Minister addresses the annual technology summit in Bengaluru"
    sim = calculate_similarity(text, text)
    assert sim == 1.0


def test_similarity_near_duplicate_high_score():
    """Test: Strongly similar / near-duplicate texts receive a high similarity score (> 0.80)."""
    text_a = "ISRO successfully launches new earth observation satellite into orbit"
    text_b = "ISRO successfully launches new earth observation satellite into space orbit"
    sim = calculate_similarity(text_a, text_b)

    assert sim >= 0.80
    assert 0.0 <= sim <= 1.0


def test_similarity_relative_order_and_bounds():
    """Test 11, 12 & 13: Similar texts have higher similarity than unrelated texts, bounded in [0, 1]."""
    text_a = "ISRO launches new Earth observation satellite into space orbit"
    text_b = "India's space agency launches advanced Earth observation satellite"
    text_c = "Bollywood actor wins best actor trophy at global film festival ceremony"

    sim_ab = calculate_similarity(text_a, text_b)
    sim_ac = calculate_similarity(text_a, text_c)

    assert 0.0 <= sim_ab <= 1.0
    assert 0.0 <= sim_ac <= 1.0
    # Text A and B share space/satellite themes; Text A and C are unrelated
    assert sim_ab > sim_ac
    assert sim_ab >= 0.40
    assert sim_ac < 0.10


def test_similarity_empty_text_safety():
    """Test 14: Empty, None, or whitespace texts return 0.0 safely without error."""
    assert calculate_similarity("", "Sample text") == 0.0
    assert calculate_similarity(None, "Sample text") == 0.0
    assert calculate_similarity("   ", "   ") == 0.0
    assert calculate_similarity(None, None) == 0.0


def test_is_near_duplicate_configurable_threshold():
    """Test 15: Near duplicate threshold check behaves according to configured value."""
    text_a = "Sensex and Nifty climb to historic all-time highs amid strong market rally"
    text_b = "Sensex and Nifty surge to record all-time highs amid strong market rally"

    # With a high threshold (0.80), near-duplicate is recognized
    assert is_near_duplicate(text_a, text_b, threshold=0.80) is True
    # With an impossible threshold (0.999), should be False
    assert is_near_duplicate(text_a, text_b, threshold=0.999) is False


def test_story_grouping_foundation():
    """Test foundational clustering of multi-source coverage."""
    articles = [
        {
            "id": 1,
            "title": "ISRO launches navigation satellite successfully",
            "description": "The mission was executed from Sriharikota spaceport.",
        },
        {
            "id": 2,
            "title": "ISRO launches navigation satellite successfully from Sriharikota",
            "description": "Navigation spacecraft placed into precise orbit.",
        },
        {
            "id": 3,
            "title": "Stock market reaches new record high as banking shares surge",
            "description": "Sensex gained over 500 points today.",
        },
    ]

    groups = group_similar_articles(articles, threshold=0.40)
    assert len(groups) == 2  # Space group and Market group
    assert len(groups[0]) == 2  # The 2 ISRO articles grouped together
    assert len(groups[1]) == 1  # The financial article in its own group


# ==============================================================================
# 3. CLASSIFIER SERVICE & SAFE FALLBACK TESTS
# ==============================================================================

def test_provider_category_priority_respected():
    """Test: Raw category supplied directly by the upstream provider is respected and not overridden."""
    # Even if title mentions cricket, if provider explicitly flagged business, provider metadata is honored
    cat = classify_category(
        title="Cricket board signs multi-billion dollar sponsorship contract",
        description="Major corporate enterprise invests in media broadcast rights.",
        raw_category="business",
    )
    assert cat == "business"


def test_classifier_service_ml_prediction():
    """Test that classify_category uses ML prediction when confident."""
    cat = classify_category(
        title="OpenAI releases new generative artificial intelligence model with deep learning neural network",
        description="The AI model optimizes software programming and developer workflows.",
    )
    assert cat == "technology"


def test_classifier_service_low_confidence_fallback(monkeypatch):
    """Test that classify_category falls back to deterministic heuristic when ML confidence is low."""
    class LowConfidenceClassifier:
        pipeline = object()  # Not None
        def predict(self, title, description):
            # Returns a category with low confidence below 0.18 gate
            return "lifestyle", 0.05

    monkeypatch.setattr("app.ml.category_classifier.get_category_classifier", lambda: LowConfidenceClassifier())

    # Text contains strong sports keyword 'badminton'
    cat = classify_category(
        title="Star badminton champion advances to tournament finals",
        description="Ace player defeated top seed in straight sets.",
    )
    assert cat == "sports"


def test_classifier_service_fallback_when_model_missing(monkeypatch):
    """Test that classify_category falls back safely to deterministic rules if model is missing."""
    empty_classifier = CategoryClassifier(model_path=Path("/non_existent_path/model.joblib"))
    monkeypatch.setattr("app.ml.category_classifier.get_category_classifier", lambda: empty_classifier)

    # Politics keyword: 'parliament'
    cat_pol = classify_category(title="Parliament passes landmark taxation reform bill")
    assert cat_pol == "politics"

    # Sports keyword: 'cricket'
    cat_spo = classify_category(title="Indian cricket team secures championship series trophy")
    assert cat_spo == "sports"


def test_ingestion_pipeline_with_ml_integration():
    """Test end-to-end raw article ingestion through the ML-integrated classifier."""
    db = SessionLocal()
    try:
        raw = RawArticle(
            title="Advanced Quantum Processor Achieves Breakthrough in Semiconductor Lab",
            description="Engineering teams created high-coherence silicon quantum bits for artificial intelligence.",
            canonical_url=f"https://technews.example.com/quantum-{datetime.now(timezone.utc).timestamp()}",
            source_name="Tech Review",
            source_domain="technews.example.com",
            country_hint="IN",
            raw_category=None,
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        article = ingest_raw_article(db, raw)
        assert article is not None
        db.commit()
        db.refresh(article)
        assert article.category is not None
        assert article.category.slug in ["technology", "science"]
        assert article.region == "INDIA"
    finally:
        db.close()

