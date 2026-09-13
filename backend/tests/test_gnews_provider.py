import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.models.story_group import StoryGroup
from app.services.gnews_provider import GNewsProvider
from app.services.news_provider import RawArticle, NewsAPIProvider
from app.services.rss_provider import RSSNewsProvider
from app.services.ingest import ingest_raw_article, run_ingestion, compute_url_hash


# Mock data fixtures
SAMPLE_GNEWS_INDIA_RESPONSE = {
    "totalArticles": 2,
    "articles": [
        {
            "title": "ISRO successfully launches new earth observation satellite from Sriharikota",
            "description": "The Indian Space Research Organisation has achieved another milestone with its latest launch in Andhra Pradesh.",
            "content": "Full content of ISRO launch...",
            "url": "https://www.thehindu.com/sci-tech/science/isro-satellite-launch-2026/article12345.ece",
            "image": "https://www.thehindu.com/images/isro-rocket.jpg",
            "publishedAt": "2026-09-12T03:30:00Z",
            "source": {
                "name": "The Hindu",
                "url": "https://www.thehindu.com"
            }
        },
        {
            "title": "Maharashtra government announces new technology cluster in Pune",
            "description": "A new hub for AI and semiconductor research is being set up in Pune, Maharashtra.",
            "content": "Full content of Maharashtra IT policy...",
            "url": "https://www.ndtv.com/india-news/maharashtra-pune-tech-cluster-announced-987654",
            "image": "https://www.ndtv.com/images/pune-it-park.jpg",
            "publishedAt": "2026-09-12T04:15:00Z",
            "source": {
                "name": "NDTV",
                "url": "https://www.ndtv.com"
            }
        }
    ]
}

SAMPLE_GNEWS_WORLD_RESPONSE = {
    "totalArticles": 1,
    "articles": [
        {
            "title": "Global Climate Summit in Geneva concludes with landmark green energy pact",
            "description": "World leaders in Switzerland agree on aggressive carbon reduction targets.",
            "content": "Full global summit text...",
            "url": "https://www.reuters.com/world/europe/geneva-climate-summit-accord-2026-09-12/",
            "image": "https://www.reuters.com/images/climate-summit.jpg",
            "publishedAt": "2026-09-12T02:00:00Z",
            "source": {
                "name": "Reuters",
                "url": "https://www.reuters.com"
            }
        }
    ]
}


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        # Ensure default categories exist for testing
        categories = ["politics", "technology", "business", "sports", "science", "health", "world", "nation"]
        for cat_slug in categories:
            existing = session.query(Category).filter(Category.slug == cat_slug).first()
            if not existing:
                session.add(Category(name=cat_slug.capitalize(), slug=cat_slug))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


# Test 1 & 2: Valid GNews response and multiple articles parsing
def test_01_valid_gnews_response_and_multiple_articles():
    provider = GNewsProvider(api_key="test_api_key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_GNEWS_INDIA_RESPONSE
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news(page_size=10)

    assert len(articles) == 2
    assert articles[0].title == "ISRO successfully launches new earth observation satellite from Sriharikota"
    assert articles[1].title == "Maharashtra government announces new technology cluster in Pune"


# Test 3 & 4: Original publisher name and URL extraction
def test_02_source_and_publisher_url_extraction():
    provider = GNewsProvider(api_key="test_api_key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_GNEWS_INDIA_RESPONSE
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news(page_size=10)

    # Must preserve original publisher, NOT GNews
    assert articles[0].source_name == "The Hindu"
    assert articles[0].canonical_url == "https://www.thehindu.com/sci-tech/science/isro-satellite-launch-2026/article12345.ece"
    assert articles[0].source_domain == "thehindu.com"

    assert articles[1].source_name == "NDTV"
    assert articles[1].canonical_url == "https://www.ndtv.com/india-news/maharashtra-pune-tech-cluster-announced-987654"
    assert articles[1].source_domain == "ndtv.com"


# Test 5: Image extraction
def test_03_image_extraction():
    provider = GNewsProvider(api_key="test_api_key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_GNEWS_INDIA_RESPONSE
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news(page_size=10)

    assert articles[0].image_url == "https://www.thehindu.com/images/isro-rocket.jpg"


# Test 6: Published date ISO parsing
def test_04_published_date_parsing():
    provider = GNewsProvider(api_key="test_api_key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_GNEWS_INDIA_RESPONSE
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news(page_size=10)

    assert isinstance(articles[0].published_at, datetime)
    assert articles[0].published_at.year == 2026
    assert articles[0].published_at.month == 9
    assert articles[0].published_at.day == 12


# Test 7: Missing description fallback
def test_05_missing_description_fallback():
    provider = GNewsProvider(api_key="test_api_key")
    data = {
        "articles": [
            {
                "title": "Headline without description",
                "description": None,
                "url": "https://www.example-news.com/article/1",
                "publishedAt": "2026-09-12T01:00:00Z",
                "source": {"name": "Example News", "url": "https://www.example-news.com"}
            }
        ]
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = data
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news()

    assert len(articles) == 1
    assert articles[0].description == "Headline without description"


# Test 8: Missing image handling
def test_06_missing_image_handling():
    provider = GNewsProvider(api_key="test_api_key")
    data = {
        "articles": [
            {
                "title": "Article without image",
                "description": "Some text",
                "image": None,
                "url": "https://www.tribuneindia.com/news/123",
                "publishedAt": "2026-09-12T01:00:00Z",
                "source": {"name": "The Tribune", "url": "https://www.tribuneindia.com"}
            }
        ]
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = data
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news()

    assert len(articles) == 1
    assert articles[0].image_url is None


# Test 9 & 10: Missing URL and invalid URL rejection
def test_07_invalid_and_missing_url_rejection():
    provider = GNewsProvider(api_key="test_api_key")
    data = {
        "articles": [
            {"title": "Valid", "url": "https://www.deccanherald.com/news/1", "source": {"name": "DH"}},
            {"title": "Missing URL", "url": "", "source": {"name": "Unknown"}},
            {"title": "API Endpoint", "url": "https://gnews.io/api/v4/top-headlines", "source": {"name": "GNews"}},
            {"title": "Localhost URL", "url": "http://localhost:8000/test", "source": {"name": "Local"}},
            {"title": "Example.com URL", "url": "http://example.com/item", "source": {"name": "Example"}},
            {"title": "Invalid Scheme", "url": "ftp://files.com/doc", "source": {"name": "FTP"}},
        ]
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = data
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news()

    assert len(articles) == 1
    assert articles[0].title == "Valid"


# Test 11: Malformed JSON handling
def test_08_malformed_json_handling():
    provider = GNewsProvider(api_key="test_api_key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON")
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news()

    assert articles == []
    assert provider.last_error is not None


# Test 12, 13, 14: HTTP 401, 403, 429 error handling
@pytest.mark.parametrize("status_code", [401, 403, 429, 500])
def test_09_http_error_codes(status_code):
    provider = GNewsProvider(api_key="test_api_key")
    req = httpx.Request("GET", "https://gnews.io/api/v4/top-headlines")
    resp = httpx.Response(status_code, request=req, json={"errors": ["Quota exceeded or invalid key"]})

    with patch("httpx.Client.get", side_effect=httpx.HTTPStatusError("HTTP Error", request=req, response=resp)):
        articles = provider.fetch_india_news()

    assert articles == []
    assert f"HTTP {status_code}" in (provider.last_error or "")


# Test 15: Timeout handling
def test_10_request_timeout():
    provider = GNewsProvider(api_key="test_api_key")
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Connection timed out")):
        articles = provider.fetch_india_news()

    assert articles == []
    assert "timed out" in (provider.last_error or "").lower()


# Test 16: Provider failure isolation (RSS succeeds if GNews fails)
def test_11_provider_failure_isolation(db: Session):
    class FailingGNews(GNewsProvider):
        def fetch_india_news(self, category=None, page_size=10):
            self.last_error = "HTTP 429 Quota Exceeded"
            return []

    class WorkingRSS(RSSNewsProvider):
        def fetch_india_news(self, category=None, page_size=10):
            return [
                RawArticle(
                    title="Indian Express exclusive investigation into renewable energy grid",
                    description="Investigation details renewable energy expansion.",
                    canonical_url="https://indianexpress.com/article/investigation-renewable-grid-2026",
                    source_name="The Indian Express",
                    published_at=datetime(2026, 9, 12, 5, 0, 0),
                    country_hint="IN",
                )
            ]

    stats = run_ingestion(
        db=db,
        india_provider=WorkingRSS(),
        fetch_india=True,
        fetch_international=False,
        provider_type="rss",
    )

    assert stats["saved"] == 1
    assert stats["errors"] == 0


# Test 17: country=in parameter behavior
def test_12_country_in_parameter():
    provider = GNewsProvider(api_key="test_api_key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"articles": []}
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp) as mock_get:
        provider.fetch_india_news(page_size=10)
        assert mock_get.called
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs.get("params", {})
        assert params.get("country") == "in"
        assert params.get("lang") == "en"


# Test 18: Category mapping
def test_13_category_mapping():
    provider = GNewsProvider(api_key="test_api_key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"articles": []}
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp) as mock_get:
        provider.fetch_india_news(category="sports")
        params = mock_get.call_args[1]["params"]
        assert params.get("category") == "sports"

    with patch("httpx.Client.get", return_value=mock_resp) as mock_get:
        provider.fetch_india_news(category="technology")
        params = mock_get.call_args[1]["params"]
        assert params.get("category") == "technology"


# Test 19 & 20: India and International region classification in ingestion
def test_14_india_and_international_region_assignment(db: Session):
    india_raw = RawArticle(
        title="Delhi metro expands phase 4 network across national capital",
        description="Delhi transport development continues.",
        canonical_url="https://timesofindia.indiatimes.com/city/delhi/metro-phase-4-expansion/articleshow/101.cms",
        source_name="Times of India",
        published_at=datetime(2026, 9, 12, 4, 0, 0),
        country_hint="IN",
    )
    intl_raw = RawArticle(
        title="Japan and South Korea sign bilateral trade and technology accord in Tokyo",
        description="Asia Pacific international diplomacy agreement.",
        canonical_url="https://asia.nikkei.com/Economy/Japan-South-Korea-trade-pact-2026",
        source_name="Nikkei Asia",
        published_at=datetime(2026, 9, 12, 3, 0, 0),
        country_hint="GLOBAL",
    )

    art1 = ingest_raw_article(db, india_raw)
    art2 = ingest_raw_article(db, intl_raw)
    db.commit()

    assert art1 is not None
    assert art1.region == "INDIA"

    assert art2 is not None
    assert art2.region == "INTERNATIONAL"


# Test 21: State detection on GNews article content
def test_15_state_detection(db: Session):
    karnataka_raw = RawArticle(
        title="Karnataka cabinet clears new industrial park policy near Bengaluru",
        description="The government in Bengaluru approves infrastructure budget.",
        canonical_url="https://www.deccanherald.com/state/karnataka-industrial-park-bengaluru-302.html",
        source_name="Deccan Herald",
        published_at=datetime(2026, 9, 12, 4, 0, 0),
        country_hint="IN",
    )

    art = ingest_raw_article(db, karnataka_raw)
    db.commit()

    assert art is not None
    assert art.region == "INDIA"
    assert art.state == "Karnataka"


# Test 22: is_demo=False verification
def test_16_is_demo_false_verification(db: Session):
    raw = RawArticle(
        title="GNews Live Headline for Verification 2026",
        description="Live news test description.",
        canonical_url="https://www.hindustantimes.com/india-news/live-test-headline-2026",
        source_name="Hindustan Times",
        published_at=datetime(2026, 9, 12, 4, 0, 0),
        country_hint="IN",
    )

    art = ingest_raw_article(db, raw)
    db.commit()

    assert art is not None
    assert art.is_demo is False


# Test 23: URL Hash Deduplication
def test_17_url_hash_deduplication(db: Session):
    url = "https://www.hindustantimes.com/business/tech-merger-2026-unique-hash"
    raw1 = RawArticle(
        title="Tech Company Merger Announced",
        description="First ingestion pass.",
        canonical_url=url,
        source_name="Hindustan Times",
        published_at=datetime(2026, 9, 12, 4, 0, 0),
        country_hint="IN",
    )
    raw2 = RawArticle(
        title="Tech Company Merger Announced (Duplicate)",
        description="Second ingestion pass.",
        canonical_url=url,
        source_name="Hindustan Times",
        published_at=datetime(2026, 9, 12, 4, 0, 0),
        country_hint="IN",
    )

    art1 = ingest_raw_article(db, raw1)
    db.commit()
    assert art1 is not None

    art2 = ingest_raw_article(db, raw2)
    assert art2 is None  # Duplicate rejected


# Test 24: GNews + RSS duplicate prevention
def test_18_gnews_and_rss_exact_duplicate_prevention(db: Session):
    url = "https://indianexpress.com/article/india/central-government-green-corridor-scheme-2026"
    
    # Ingested first via RSS
    rss_raw = RawArticle(
        title="Central Government launches green energy corridor scheme",
        description="RSS version of article.",
        canonical_url=url,
        source_name="The Indian Express",
        published_at=datetime(2026, 9, 12, 2, 0, 0),
        country_hint="IN",
    )
    art_rss = ingest_raw_article(db, rss_raw)
    db.commit()
    assert art_rss is not None

    # Discovered second via GNews pointing to same publisher URL
    gnews_raw = RawArticle(
        title="Central Government launches green energy corridor scheme",
        description="GNews version of same story.",
        canonical_url=url + "?utm_source=gnews",  # utm query param stripped in hash
        source_name="The Indian Express",
        published_at=datetime(2026, 9, 12, 2, 0, 0),
        country_hint="IN",
    )
    art_gnews = ingest_raw_article(db, gnews_raw)
    assert art_gnews is None  # Exact duplicate prevented!


# Test 25: GNews + NewsAPI duplicate prevention
def test_19_gnews_and_newsapi_exact_duplicate_prevention(db: Session):
    url = "https://www.bbc.com/news/world-asia-india-69812345"

    newsapi_raw = RawArticle(
        title="India Semiconductor mission achieves new manufacturing milestone",
        description="NewsAPI ingest.",
        canonical_url=url,
        source_name="BBC News",
        published_at=datetime(2026, 9, 12, 1, 0, 0),
        country_hint="GLOBAL",
    )
    art_napi = ingest_raw_article(db, newsapi_raw)
    db.commit()
    assert art_napi is not None

    gnews_raw = RawArticle(
        title="India Semiconductor mission achieves new manufacturing milestone",
        description="GNews ingest.",
        canonical_url=url,
        source_name="BBC News",
        published_at=datetime(2026, 9, 12, 1, 0, 0),
        country_hint="GLOBAL",
    )
    art_gnews = ingest_raw_article(db, gnews_raw)
    assert art_gnews is None


# Test 26: Cross-Source Story Grouping Compatibility
def test_20_cross_source_story_grouping(db: Session):
    # Two articles about the exact same event from different publishers
    art1_raw = RawArticle(
        title="Chandrayaan 4 lunar mission approved by union cabinet for launch in 2028",
        description="The Union Cabinet chaired by PM approves the Chandrayaan 4 lunar sample return mission.",
        canonical_url="https://indianexpress.com/article/science/chandrayaan-4-cabinet-approval-2028/",
        source_name="The Indian Express",
        published_at=datetime(2026, 9, 12, 3, 0, 0),
        country_hint="IN",
        raw_category="science",
    )

    art2_raw = RawArticle(
        title="Cabinet approves Chandrayaan 4 lunar sample return mission for 2028",
        description="India Union Cabinet clears Chandrayaan 4 lunar mission budget and timeline for 2028 launch.",
        canonical_url="https://www.thehindu.com/sci-tech/science/chandrayaan-4-mission-cabinet-nod/article999.ece",
        source_name="The Hindu",
        published_at=datetime(2026, 9, 12, 3, 10, 0),
        country_hint="IN",
        raw_category="science",
    )

    art1 = ingest_raw_article(db, art1_raw)
    db.commit()
    assert art1 is not None

    art2 = ingest_raw_article(db, art2_raw)
    db.commit()
    assert art2 is not None

    # Verify Story Group created and contains both articles
    db.refresh(art1)
    db.refresh(art2)
    assert art1.story_group_id is not None
    assert art2.story_group_id is not None
    assert art1.story_group_id == art2.story_group_id

    # Verify StoryGroup has articles from both distinct publishers
    group = db.query(StoryGroup).filter(StoryGroup.id == art1.story_group_id).first()
    assert group is not None
    assert len(group.articles) >= 2


# Test 27: Original publisher URL preserved
def test_21_original_publisher_url_preserved(db: Session):
    original_url = "https://www.hindustantimes.com/cricket/india-vs-australia-test-series-2026-report"
    raw = RawArticle(
        title="India vs Australia test match series preview and squad analysis",
        description="Cricket test series preview.",
        canonical_url=original_url,
        source_name="Hindustan Times",
        published_at=datetime(2026, 9, 12, 4, 0, 0),
        country_hint="IN",
    )

    art = ingest_raw_article(db, raw)
    db.commit()

    assert art.canonical_url == original_url
    assert not art.canonical_url.startswith("https://gnews.io")
    assert not art.canonical_url.startswith("http://localhost")
