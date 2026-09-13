import time
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.models.story_group import StoryGroup
from app.models.user import User
from app.services.news_provider import RawArticle, NewsAPIProvider
from app.services.rss_provider import RSSNewsProvider, INDIAN_EXPRESS_FEEDS
from app.services.ingest import ingest_raw_article, compute_url_hash, run_ingestion


client = TestClient(app)


# Sample valid RSS XML for mocking feed responses
SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Indian Express Technology</title>
    <link>https://indianexpress.com/section/technology/</link>
    <description>Latest Technology News</description>
    <item>
      <title>ISRO Launches Advanced Navigation Satellite from Sriharikota</title>
      <link>https://indianexpress.com/article/technology/science/isro-satellite-launch-2026/</link>
      <description>ISRO has successfully placed the navigation satellite into geosynchronous orbit.</description>
      <author>Express News Service</author>
      <pubDate>Fri, 11 Sep 2026 10:30:00 +0530</pubDate>
      <media:content url="https://images.indianexpress.com/2026/09/isro-satellite.jpg" medium="image" />
    </item>
    <item>
      <title>AI Supercomputing Cluster Inaugurated at IIT Hyderabad</title>
      <link>https://indianexpress.com/article/technology/ai-supercomputer-iit-hyderabad/</link>
      <description>The computational cluster will facilitate natural language models in 22 Indian languages.</description>
      <author>Tech Desk</author>
      <pubDate>Fri, 11 Sep 2026 08:00:00 +0530</pubDate>
      <enclosure url="https://images.indianexpress.com/2026/09/iit-cluster.jpg" type="image/jpeg" />
    </item>
  </channel>
</rss>
"""


def test_rss_valid_parsing_with_mocked_entries():
    """Test 1: Valid RSS feed parsing extracts title, canonical_url, and description."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_RSS_XML.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        provider = RSSNewsProvider(feeds=[INDIAN_EXPRESS_FEEDS[3]])  # Tech feed
        articles = provider.fetch_india_news(page_size=10)

        assert len(articles) == 2
        assert "ISRO Launches Advanced Navigation Satellite" in articles[0].title
        assert articles[0].canonical_url == "https://indianexpress.com/article/technology/science/isro-satellite-launch-2026/"
        assert articles[0].country_hint == "IN"
        assert articles[0].source_name == "Indian Express"


def test_rss_multiple_entries_extraction():
    """Test 2: Multiple RSS entries are properly extracted with pagination limit."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_RSS_XML.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        provider = RSSNewsProvider(feeds=[INDIAN_EXPRESS_FEEDS[3]])
        # Request limit = 1
        articles = provider.fetch_india_news(page_size=1)
        assert len(articles) == 1


def test_rss_missing_description_fallback_to_title():
    """Test 3: Missing description falls back to title cleanly."""
    xml_no_desc = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>Cabinet Clears New Semiconductor Subsidy Package</title>
          <link>https://indianexpress.com/article/business/cabinet-clears-subsidies/</link>
        </item>
      </channel>
    </rss>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = xml_no_desc.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        provider = RSSNewsProvider(feeds=[INDIAN_EXPRESS_FEEDS[2]])
        articles = provider.fetch_india_news()
        assert len(articles) == 1
        assert articles[0].description == "Cabinet Clears New Semiconductor Subsidy Package"


def test_rss_missing_image_fallback_to_none():
    """Test 4: Missing image falls back to None."""
    xml_no_img = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>Headline Without Image Available</title>
          <link>https://indianexpress.com/article/india/headline-no-img/</link>
          <description>Some description</description>
        </item>
      </channel>
    </rss>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = xml_no_img.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        provider = RSSNewsProvider(feeds=[INDIAN_EXPRESS_FEEDS[0]])
        articles = provider.fetch_india_news()
        assert len(articles) == 1
        assert articles[0].image_url is None


def test_rss_missing_pubdate_fallback():
    """Test 5: Missing or invalid publication date falls back to UTC now."""
    xml_no_date = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>Headline Without Date</title>
          <link>https://indianexpress.com/article/india/headline-no-date/</link>
          <description>Some description</description>
        </item>
      </channel>
    </rss>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = xml_no_date.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        provider = RSSNewsProvider(feeds=[INDIAN_EXPRESS_FEEDS[0]])
        articles = provider.fetch_india_news()
        assert len(articles) == 1
        assert isinstance(articles[0].published_at, datetime)


def test_rss_malformed_xml_resilience():
    """Test 6: Malformed feed does not crash provider."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<html><body>This is an HTML page, not RSS feed!</body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        provider = RSSNewsProvider(feeds=[{"name": "Bad Feed", "url": "https://example.com/bad"}])
        articles = provider.fetch_india_news()
        assert articles == []


def test_rss_http_network_failure_handling():
    """Test 7: HTTP 500 error is handled gracefully without crashing."""
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Network unreachable")):
        provider = RSSNewsProvider(feeds=[{"name": "Offline Feed", "url": "https://example.com/offline"}])
        articles = provider.fetch_india_news()
        assert articles == []
        assert provider.last_error is not None


def test_rss_duplicate_url_hash_rejection():
    """Test 8: Ingestion skips duplicate URL hashes correctly."""
    db = SessionLocal()
    try:
        raw = RawArticle(
            title="Duplicate Test Headline",
            description="Testing deduplication of RSS entries",
            canonical_url="https://indianexpress.com/article/tech/unique-test-12345",
            source_name="Indian Express",
            source_domain="indianexpress.com",
            published_at=utc_now(),
            raw_category="technology",
            country_hint="IN",
        )
        a1 = ingest_raw_article(db, raw)
        db.commit()
        assert a1 is not None

        # Second ingestion attempt with identical canonical URL
        a2 = ingest_raw_article(db, raw)
        assert a2 is None
    finally:
        db.close()


def test_rss_region_assignment_india():
    """Test 9: RSS provider raw articles receive region = INDIA in database."""
    db = SessionLocal()
    try:
        raw = RawArticle(
            title="National Highway Corridor Approved",
            description="Cabinet grants approval for new expressway",
            canonical_url="https://indianexpress.com/article/india/national-highway-12345",
            source_name="Indian Express",
            source_domain="indianexpress.com",
            published_at=utc_now(),
            country_hint="IN",
        )
        article = ingest_raw_article(db, raw)
        db.commit()
        assert article.region == "INDIA"
        assert article.is_demo is False
    finally:
        db.close()


def test_rss_hyderabad_feed_state_telangana():
    """Test 10: Hyderabad city feed automatically sets state to Telangana."""
    db = SessionLocal()
    try:
        raw = RawArticle(
            title="BioAsia Summit Opens in Hyderabad with Global Delegates",
            description="The life sciences conference hosts researchers and pharma leaders",
            canonical_url="https://indianexpress.com/article/cities/hyderabad/bioasia-summit-2026-unique",
            source_name="Indian Express",
            source_domain="indianexpress.com",
            published_at=utc_now(),
            state_hint="Telangana",
            country_hint="IN",
        )
        article = ingest_raw_article(db, raw)
        db.commit()
        assert article.state == "Telangana"
    finally:
        db.close()


def test_rss_reliable_category_mapping():
    """Test 11: raw_category from feed assigns the corresponding database Category."""
    db = SessionLocal()
    try:
        raw = RawArticle(
            title="Premier Badminton League Commences in New Delhi",
            description="Top ranked shuttlers compete for championship",
            canonical_url="https://indianexpress.com/article/sports/badminton-league-2026-unique",
            source_name="Indian Express",
            source_domain="indianexpress.com",
            published_at=utc_now(),
            raw_category="sports",
            country_hint="IN",
        )
        article = ingest_raw_article(db, raw)
        db.commit()
        assert article.category.slug == "sports"
    finally:
        db.close()


def test_rss_provider_feed_isolation():
    """Test 12: Failure in one feed does not abort other valid feeds."""
    mock_get = MagicMock()

    def side_effect(url, **kwargs):
        if "bad-feed" in url:
            raise httpx.ConnectError("Feed down")
        resp = MagicMock()
        resp.status_code = 200
        resp.content = SAMPLE_RSS_XML.encode("utf-8")
        resp.raise_for_status = MagicMock()
        return resp

    mock_get.side_effect = side_effect

    with patch("httpx.Client.get", side_effect=side_effect):
        provider = RSSNewsProvider(feeds=[
            {"name": "Broken Feed", "url": "https://example.com/bad-feed", "category_hint": "general"},
            INDIAN_EXPRESS_FEEDS[3],  # Good tech feed
        ])
        articles = provider.fetch_india_news()
        assert len(articles) == 2  # The good feed succeeded


def test_demo_article_exclusion_when_setting_false():
    """Test 13: GET /news/latest excludes demo articles when SHOW_DEMO_ARTICLES=False."""
    # Ensure SHOW_DEMO_ARTICLES is False
    with patch.object(settings, "SHOW_DEMO_ARTICLES", False):
        res = client.get("/api/v1/news/latest?limit=100")
        assert res.status_code == 200
        data = res.json()
        for item in data["items"]:
            assert item.get("is_demo", False) is False
            assert "example.com/demo" not in item.get("canonical_url", "")


def test_live_article_visibility():
    """Test 14: Ingested live articles (is_demo=False) are visible in GET /news/latest."""
    db = SessionLocal()
    try:
        raw = RawArticle(
            title="Live Verified Breaking News Story From Bangalore",
            description="Karnataka launches public tech portal",
            canonical_url=f"https://indianexpress.com/article/tech/live-test-{time.time()}",
            source_name="Indian Express",
            source_domain="indianexpress.com",
            published_at=utc_now(),
            raw_category="technology",
            country_hint="IN",
        )
        article = ingest_raw_article(db, raw)
        db.commit()
        article_id = article.id
    finally:
        db.close()

    with patch.object(settings, "SHOW_DEMO_ARTICLES", False):
        res = client.get("/api/v1/news/latest?limit=50")
        assert res.status_code == 200
        ids = [item["id"] for item in res.json()["items"]]
        assert article_id in ids


def test_archive_excludes_demo_articles():
    """Test 15: GET /archive excludes demo articles when SHOW_DEMO_ARTICLES=False."""
    with patch.object(settings, "SHOW_DEMO_ARTICLES", False):
        res = client.get("/api/v1/archive?limit=100")
        assert res.status_code == 200
        items = res.json()["items"]
        for item in items:
            assert "example.com/demo" not in item.get("canonical_url", "")


def test_search_excludes_demo_articles():
    """Test 16: GET /search excludes demo articles matching query."""
    # Even if query matches a demo article like 'Semiconductor'
    with patch.object(settings, "SHOW_DEMO_ARTICLES", False):
        res = client.get("/api/v1/search?q=Semiconductor")
        assert res.status_code == 200
        items = res.json()["items"]
        for item in items:
            assert "example.com/demo" not in item.get("canonical_url", "")


def test_stories_excludes_demo_articles():
    """Test 17: GET /stories excludes demo-only story clusters."""
    with patch.object(settings, "SHOW_DEMO_ARTICLES", False):
        res = client.get("/api/v1/stories")
        assert res.status_code == 200
        groups = res.json()["items"]
        for g in groups:
            rep = g.get("representative_article")
            if rep:
                assert "example.com/demo" not in rep.get("canonical_url", "")


def test_for_you_excludes_demo_articles():
    """Test 18: Cold start / recommendations query excludes demo articles."""
    db = SessionLocal()
    try:
        from app.recommendation.service import get_personalized_recommendations
        res = get_personalized_recommendations(db=db, user_id=999999)  # Cold start user
        for item in res.items:
            assert item.is_demo is False
            assert "example.com/demo" not in item.canonical_url
    finally:
        db.close()


def test_cross_provider_deduplication():
    """Test 19: Cross-provider deduplication between RSS and NewsAPI."""
    db = SessionLocal()
    try:
        # 1. RSS article
        url = "https://timesofindia.indiatimes.com/world/south-asia/cross-provider-test"
        raw_rss = RawArticle(
            title="Shared International Breaking Story",
            description="First ingested via RSS provider",
            canonical_url=url,
            source_name="Times of India",
            source_domain="timesofindia.indiatimes.com",
            published_at=utc_now(),
            country_hint="IN",
        )
        a1 = ingest_raw_article(db, raw_rss)
        db.commit()
        assert a1 is not None

        # 2. NewsAPI article with identical canonical URL (perhaps with tracking query)
        raw_newsapi = RawArticle(
            title="Shared International Breaking Story Headline",
            description="Second ingested via NewsAPI provider with utm tags",
            canonical_url=url + "?utm_source=twitter&utm_medium=social",
            source_name="Times of India",
            source_domain="timesofindia.indiatimes.com",
            published_at=utc_now(),
            country_hint="IN",
        )
        a2 = ingest_raw_article(db, raw_newsapi)
        assert a2 is None  # Accurately rejected as duplicate!
    finally:
        db.close()
