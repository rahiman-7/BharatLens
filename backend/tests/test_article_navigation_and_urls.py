from fastapi.testclient import TestClient
from datetime import datetime, timezone
import pytest

from app.main import app
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.models.story_group import StoryGroup
from app.services.rss_provider import RSSNewsProvider
from app.services.ingest import ingest_raw_article
from app.services.news_provider import RawArticle

client = TestClient(app)


def test_article_detail_loads_by_id_with_original_url():
    """Verify GET /api/v1/news/{article_id} returns the complete article, preserving id and canonical url."""
    db = SessionLocal()
    try:
        source = db.query(Source).first()
        category = db.query(Category).first()
        now = datetime.now(timezone.utc)

        art = Article(
            title="India Launches Advanced Solar Mission",
            description="ISRO expands solar research with Aditya-L2 telescope.",
            canonical_url="https://indianexpress.com/article/technology/science/india-solar-mission-aditya-99881/",
            url_hash="test_hash_solar_001",
            source_id=source.id,
            category_id=category.id,
            region="INDIA",
            published_at=now,
            fetched_at=now,
            is_demo=False,
        )
        db.add(art)
        db.commit()
        db.refresh(art)

        # Load article detail by ID
        detail_resp = client.get(f"/api/v1/news/{art.id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()

        assert data["id"] == art.id
        assert data["title"] == art.title
        assert data["canonical_url"] == "https://indianexpress.com/article/technology/science/india-solar-mission-aditya-99881/"
        assert data["url"] == data["canonical_url"]
        assert data["source"]["id"] == source.id
        assert data["category"]["id"] == category.id
    finally:
        db.close()


def test_related_articles_response_contains_id_and_url():
    """Verify GET /api/v1/news/{article_id}/related returns peer articles with valid id and url."""
    db = SessionLocal()
    try:
        source = db.query(Source).first()
        category = db.query(Category).first()
        now = datetime.now(timezone.utc)

        # Create a story group with 2 articles
        sg = StoryGroup()
        db.add(sg)
        db.flush()

        art1 = Article(
            title="ISRO Tests New Cryogenic Engine Stage 1",
            description="ISRO engineers successfully tested the new cryogenic upper stage.",
            canonical_url="https://indianexpress.com/article/technology/science/isro-test-cryo-1",
            url_hash="hash_cryo_1",
            source_id=source.id,
            category_id=category.id,
            region="INDIA",
            published_at=now,
            fetched_at=now,
            story_group_id=sg.id,
            is_demo=False,
        )
        art2 = Article(
            title="ISRO Achieves Milestone in Rocket Propulsion",
            description="India's space agency validated a milestone cryogenic test.",
            canonical_url="https://thehindu.com/sci-tech/science/isro-milestone-propulsion-2",
            url_hash="hash_cryo_2",
            source_id=source.id,
            category_id=category.id,
            region="INDIA",
            published_at=now,
            fetched_at=now,
            story_group_id=sg.id,
            is_demo=False,
        )
        db.add_all([art1, art2])
        db.commit()

        sg.representative_article_id = art1.id
        db.commit()

        # Query related for art1
        related_resp = client.get(f"/api/v1/news/{art1.id}/related")
        assert related_resp.status_code == 200
        related_items = related_resp.json()

        assert len(related_items) == 1
        peer = related_items[0]
        assert peer["id"] == art2.id
        assert peer["title"] == art2.title
        assert peer["canonical_url"] == "https://thehindu.com/sci-tech/science/isro-milestone-propulsion-2"
        assert peer["url"] == peer["canonical_url"]
        assert peer["source_name"] == source.name
    finally:
        db.close()


def test_rss_entry_link_becomes_canonical_url():
    """Verify RSS provider maps entry.link directly to canonical_url without feed URLs."""
    provider = RSSNewsProvider()
    feed_config = {
        "name": "Indian Express Tech",
        "url": "https://indianexpress.com/section/technology/feed/",
        "category_hint": "technology",
        "state_hint": None,
    }
    mock_entry = {
        "title": "OpenAI Launches Advanced Reasoning Engine",
        "link": "https://indianexpress.com/article/technology/artificial-intelligence/openai-launches-model-12345/",
        "summary": "A breakthrough in automated reasoning and code synthesis.",
        "author": "Tech Desk",
    }

    raw = provider._parse_entry(mock_entry, feed_config)
    assert raw is not None
    assert raw.canonical_url == "https://indianexpress.com/article/technology/artificial-intelligence/openai-launches-model-12345/"
    assert raw.source_domain == "indianexpress.com"
    assert "feed" not in raw.canonical_url


def test_rss_missing_or_invalid_link_is_rejected_safely():
    """Verify missing, empty, or feed URL in RSS entry is rejected safely."""
    provider = RSSNewsProvider()
    feed_config = {
        "name": "Indian Express Tech",
        "url": "https://indianexpress.com/section/technology/feed/",
        "category_hint": "technology",
        "state_hint": None,
    }

    # Missing link
    assert provider._parse_entry({"title": "Test Title", "link": ""}, feed_config) is None
    assert provider._parse_entry({"title": "Test Title"}, feed_config) is None

    # Invalid protocol
    assert provider._parse_entry({"title": "Test Title", "link": "javascript:alert(1)"}, feed_config) is None

    # Feed URL mistakenly supplied as link
    assert provider._parse_entry({
        "title": "Test Title",
        "link": "https://indianexpress.com/section/technology/feed/"
    }, feed_config) is None


def test_ingest_raw_article_rejects_empty_or_invalid_url():
    """Verify ingest_raw_article rejects items with missing or invalid canonical URLs."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        raw_invalid = RawArticle(
            title="Some News",
            description="Description",
            canonical_url="",
            source_name="Test Source",
            source_domain="test.com",
            published_at=now,
        )
        assert ingest_raw_article(db, raw_invalid) is None

        raw_null_str = RawArticle(
            title="Some News",
            description="Description",
            canonical_url="null",
            source_name="Test Source",
            source_domain="test.com",
            published_at=now,
        )
        assert ingest_raw_article(db, raw_null_str) is None
    finally:
        db.close()


def test_story_cluster_articles_navigation_structure():
    """Verify GET /api/v1/stories/{id} returns representative article and article list with valid IDs."""
    db = SessionLocal()
    try:
        source = db.query(Source).first()
        category = db.query(Category).first()
        now = datetime.now(timezone.utc)

        sg = StoryGroup()
        db.add(sg)
        db.flush()

        art = Article(
            title="Global Semiconductor Summit Opens in Bengaluru",
            description="Leaders convene for the annual semiconductor summit.",
            canonical_url="https://indianexpress.com/article/technology/semiconductor-summit-2026",
            url_hash="hash_semi_summit_1",
            source_id=source.id,
            category_id=category.id,
            region="INDIA",
            published_at=now,
            fetched_at=now,
            story_group_id=sg.id,
            is_demo=False,
        )
        db.add(art)
        db.commit()

        sg.representative_article_id = art.id
        db.commit()

        resp = client.get(f"/api/v1/stories/{sg.id}")
        assert resp.status_code == 200
        data = resp.json()

        assert data["id"] == sg.id
        assert data["representative_article"] is not None
        assert data["representative_article"]["id"] == art.id
        assert data["representative_article"]["canonical_url"] == art.canonical_url
        assert len(data["articles"]) == 1
        assert data["articles"][0]["id"] == art.id
    finally:
        db.close()
