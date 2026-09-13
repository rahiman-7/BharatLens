import uuid
from datetime import datetime, timezone
from typing import List, Optional
import pytest
from app.db.database import SessionLocal
from app.models.article import Article
from app.services.classifier import classify_region, classify_category, detect_indian_state
from app.services.news_provider import BaseNewsProvider, NewsAPIProvider, RawArticle
from app.services.ingest import compute_url_hash, run_ingestion


class MockNewsProvider(BaseNewsProvider):
    """Mock News Provider for deterministic testing."""

    def __init__(self, articles: List[RawArticle]):
        self.articles = articles

    def fetch_india_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        return [a for a in self.articles if a.country_hint == "IN"]

    def fetch_international_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        return [a for a in self.articles if a.country_hint == "GLOBAL"]


def test_compute_url_hash():
    url1 = "https://example.com/news/123?utm_source=twitter&utm_medium=social"
    url2 = "https://example.com/news/123"
    # Hashes should match because tracking parameters are normalized
    assert compute_url_hash(url1) == compute_url_hash(url2)
    assert len(compute_url_hash(url1)) == 64


def test_classify_region():
    assert classify_region("ISRO launches new satellite", country_hint="IN") == "INDIA"
    assert classify_region("UN Security Council holds emergency summit", country_hint="GLOBAL") == "INTERNATIONAL"
    assert classify_region("Indian Parliament debates economic reforms", source_name="The Hindu") == "INDIA"
    assert classify_region("European central bank cuts interest rates", source_name="Reuters Global") == "INTERNATIONAL"


def test_classify_category():
    assert classify_category("Virat Kohli hits century in historic test match") == "sports"
    assert classify_category("OpenAI announces new reasoning AI model") == "technology"
    assert classify_category("Supreme Court constitution bench delivers verdict") == "politics"
    assert classify_category("Sensex hits all-time high as quarterly profits surge") == "business"
    assert classify_category("New medical discovery in cancer immunotherapy", raw_category="health") == "health"
    assert classify_category("Delhi air quality index drops to severe category") == "environment"


def test_detect_indian_state():
    assert detect_indian_state("Hyderabad tech cluster adds 10,000 new jobs", region="INDIA") == "Telangana"
    assert detect_indian_state("Bengaluru metro expands green line", region="INDIA") == "Karnataka"
    assert detect_indian_state("Mumbai local trains upgrade automated signaling", region="INDIA") == "Maharashtra"
    assert detect_indian_state("Chennai port inaugurates new container terminal", region="INDIA") == "Tamil Nadu"
    assert detect_indian_state("Global summit takes place in Paris", region="INTERNATIONAL") is None
    assert detect_indian_state("Union cabinet announces national tax scheme", region="INDIA") is None


def test_ingestion_pipeline_and_deduplication():
    db = SessionLocal()
    run_id = uuid.uuid4().hex[:8]
    url_india = f"https://example.com/test-article-hyderabad-pharma-{run_id}"
    url_intl = f"https://example.com/test-article-global-renewable-{run_id}"
    
    try:
        sample_articles = [
            RawArticle(
                title=f"Test Ingestion {run_id}: Hyderabad Pharma Hub Expansion",
                description="Hyderabad pharma companies expand global export facilities with new investments.",
                canonical_url=url_india,
                source_name="Indian Express",
                published_at=datetime.now(timezone.utc).replace(tzinfo=None),
                country_hint="IN",
            ),
            RawArticle(
                title=f"Test Ingestion {run_id}: Global Renewable Energy Accord",
                description="World leaders sign treaty on solar and wind installation targets.",
                canonical_url=url_intl,
                source_name="Reuters Global",
                published_at=datetime.now(timezone.utc).replace(tzinfo=None),
                country_hint="GLOBAL",
            ),
        ]

        provider = MockNewsProvider(sample_articles)

        # Run 1: Should save both articles
        stats1 = run_ingestion(db, provider=provider, fetch_india=True, fetch_international=True)
        assert stats1["saved"] >= 2
        assert stats1["errors"] == 0

        # Verify records in database
        saved1 = db.query(Article).filter(Article.canonical_url == url_india).first()
        assert saved1 is not None
        assert saved1.region == "INDIA"
        assert saved1.state == "Telangana"
        assert saved1.category.slug in ["business", "health", "politics"]

        # Run 2: Exact same articles -> Should be marked as duplicates, saved = 0
        stats2 = run_ingestion(db, provider=provider, fetch_india=True, fetch_international=True)
        assert stats2["saved"] == 0
        assert stats2["duplicates"] >= 2
        assert stats2["errors"] == 0
    finally:
        db.close()


def test_newsapi_provider_missing_key_behavior():
    """Regression test: verify provider sets last_error and returns empty list when API key is None/empty."""
    provider = NewsAPIProvider(api_key="")
    articles_in = provider.fetch_india_news()
    assert articles_in == []
    assert provider.last_error is not None
    assert "NEWS_API_KEY is not configured" in provider.last_error

    articles_intl = provider.fetch_international_news()
    assert articles_intl == []
    assert provider.last_error is not None
    assert "NEWS_API_KEY is not configured" in provider.last_error


def test_newsapi_provider_error_extraction_no_secret_leak():
    """Regression test: verify error extraction parses NewsAPI error JSON without leaking secrets."""
    import httpx
    provider = NewsAPIProvider(api_key="secret_super_secret_token_123")
    
    # Mock a 401 response
    req = httpx.Request("GET", "https://newsapi.org/v2/top-headlines")
    res = httpx.Response(
        status_code=401,
        json={"status": "error", "code": "apiKeyInvalid", "message": "Your API key is invalid or incorrect."},
        request=req
    )
    detail = provider._extract_error_detail(res)
    assert "HTTP 401 [apiKeyInvalid]" in detail
    assert "secret_super_secret_token_123" not in detail

