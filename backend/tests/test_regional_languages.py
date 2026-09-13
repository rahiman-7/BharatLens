import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.models.story_group import StoryGroup
from app.core.state_languages import (
    LANGUAGES,
    INDIAN_STATES_REGISTRY,
    get_all_states_metadata,
    get_state_by_slug,
    get_state_by_name,
)
from app.services.gnews_provider import GNewsProvider
from app.services.rss_provider import RSSNewsProvider
from app.services.news_provider import RawArticle, NewsAPIProvider
from app.services.ingest import ingest_raw_article, run_ingestion
from app.services.classifier import detect_indian_state


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        # Ensure default categories exist
        categories = ["politics", "technology", "business", "sports", "science", "health", "world", "nation", "movies-entertainment"]
        for cat_slug in categories:
            existing = session.query(Category).filter(Category.slug == cat_slug).first()
            if not existing:
                session.add(Category(name=cat_slug.capitalize(), slug=cat_slug))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. State-Language Mapping & Metadata
# =========================================================================

def test_01_state_language_mapping_completeness():
    """Verify that state language registry covers 28 states and 8 union territories (36 total)."""
    all_states = get_all_states_metadata()
    assert len(all_states) == 36
    assert len(INDIAN_STATES_REGISTRY) == 36


def test_02_telangana_to_telugu_mapping():
    """Verify Telangana maps to Telugu with code 'te' and native script."""
    meta = get_state_by_slug("telangana")
    assert meta is not None
    assert meta.name == "Telangana"
    assert meta.default_language.code == "te"
    assert meta.default_language.native_name == "తెలుగు"
    assert any(lang.code == "te" for lang in meta.available_languages)
    assert any(lang.code == "en" for lang in meta.available_languages)


def test_03_tamil_nadu_to_tamil_mapping():
    """Verify Tamil Nadu maps to Tamil with code 'ta' and native script."""
    meta = get_state_by_slug("tamil-nadu")
    assert meta is not None
    assert meta.name == "Tamil Nadu"
    assert meta.default_language.code == "ta"
    assert meta.default_language.native_name == "தமிழ்"


def test_04_karnataka_to_kannada_mapping():
    """Verify Karnataka maps to Kannada with code 'kn' and native script."""
    meta = get_state_by_slug("karnataka")
    assert meta is not None
    assert meta.name == "Karnataka"
    assert meta.default_language.code == "kn"
    assert meta.default_language.native_name == "ಕನ್ನಡ"


def test_05_kerala_to_malayalam_mapping():
    """Verify Kerala maps to Malayalam with code 'ml' and native script."""
    meta = get_state_by_slug("kerala")
    assert meta is not None
    assert meta.name == "Kerala"
    assert meta.default_language.code == "ml"
    assert meta.default_language.native_name == "മലയാളം"


def test_06_maharashtra_to_marathi_mapping():
    """Verify Maharashtra maps to Marathi with code 'mr' and native script."""
    meta = get_state_by_slug("maharashtra")
    assert meta is not None
    assert meta.name == "Maharashtra"
    assert meta.default_language.code == "mr"
    assert meta.default_language.native_name == "मराठी"


def test_07_bengali_support():
    """Verify West Bengal maps to Bengali with code 'bn' and native script."""
    meta = get_state_by_slug("west-bengal")
    assert meta is not None
    assert meta.default_language.code == "bn"
    assert meta.default_language.native_name == "বাংলা"


def test_08_hindi_support():
    """Verify Hindi states (Uttar Pradesh, Bihar, Madhya Pradesh) map to Hindi."""
    for slug in ["uttar-pradesh", "bihar", "madhya-pradesh", "delhi"]:
        meta = get_state_by_slug(slug)
        assert meta is not None
        assert meta.default_language.code == "hi"
        assert meta.default_language.native_name == "हिन्दी"


def test_09_english_fallback_availability():
    """Verify English ('en') is universally available across state metadata."""
    all_states = get_all_states_metadata()
    for state in all_states:
        lang_codes = [l.code for l in state.available_languages]
        assert "en" in lang_codes



# =========================================================================
# 2. GNews Regional Language Parameter & State Ingestion
# =========================================================================

def test_10_gnews_regional_language_parameters():
    """Verify GNews fetch_regional_news sends query with state, language code, and country='in'."""
    provider = GNewsProvider(api_key="test_gnews_key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "totalArticles": 1,
        "articles": [
            {
                "title": "తెలంగాణలో కొత్త ఐటీ ప్రాజెక్టు ప్రారంభం",
                "description": "హైదరాబాద్‌లో కొత్త ఐటీ విధానం ప్రకటించిన ప్రభుత్వం.",
                "url": "https://www.eenadu.net/telangana/it-project-2026",
                "image": "https://www.eenadu.net/images/it-park.jpg",
                "publishedAt": "2026-09-12T04:00:00Z",
                "source": {"name": "Eenadu", "url": "https://www.eenadu.net"}
            }
        ]
    }
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp) as mock_get:
        articles = provider.fetch_regional_news(state="Telangana", language="te", page_size=10)
        assert mock_get.called
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs["params"]
        assert params.get("country") == "in"
        assert params.get("lang") == "te"
        assert "Telangana" in params.get("q", "")

    assert len(articles) == 1
    assert articles[0].language_code == "te"
    assert articles[0].state_hint == "Telangana"
    assert articles[0].source_name == "Eenadu"


def test_11_state_classification():
    """Verify deterministic state classification detects Indian states from regional news."""
    assert detect_indian_state("Telangana cabinet passes new IT policy in Hyderabad", region="INDIA") == "Telangana"
    assert detect_indian_state("Bengaluru tech park expansion cleared by Karnataka CM", region="INDIA") == "Karnataka"
    assert detect_indian_state("Mumbai suburban rail network gets new funding", region="INDIA") == "Maharashtra"


# =========================================================================
# 3. Persistence, Filtering, and Pagination
# =========================================================================

def test_12_language_persistence(db: Session):
    """Verify language_code is persisted to the Article database table."""
    raw = RawArticle(
        title="తెలంగాణ ఐటీ రంగం అభివృద్ధి",
        description="హైదరాబాద్ అభివృద్ధి పథకాలు.",
        canonical_url="https://www.ntnews.com/telangana-it-growth-2026-unique",
        source_name="Namasthe Telangana",
        published_at=datetime(2026, 9, 12, 5, 0, 0),
        country_hint="IN",
        state_hint="Telangana",
        language_code="te",
    )

    art = ingest_raw_article(db, raw)
    db.commit()

    assert art is not None
    assert art.language_code == "te"
    assert art.state == "Telangana"

    # Query from DB to ensure persisted
    stored = db.query(Article).filter(Article.id == art.id).first()
    assert stored is not None
    assert stored.language_code == "te"


def test_13_state_and_language_filtering(client: TestClient, db: Session):
    """Verify GET /api/v1/news/india and /api/v1/news/state/{state_slug} filter by state and language."""
    # Seed 1 Telugu Telangana article and 1 English Telangana article
    raw_te = RawArticle(
        title="తెలంగాణ ప్రాజెక్ట్ సమీక్ష",
        description="తెలంగాణ సమీక్ష వివరాలు.",
        canonical_url="https://www.andhrajyothy.com/telangana-review-2026",
        source_name="Andhra Jyothy",
        published_at=datetime(2026, 9, 12, 6, 0, 0),
        country_hint="IN",
        state_hint="Telangana",
        language_code="te",
    )
    raw_en = RawArticle(
        title="Telangana government launches new green energy initiative",
        description="Green power project launched in Hyderabad.",
        canonical_url="https://telanganatoday.com/green-energy-hyd-2026",
        source_name="Telangana Today",
        published_at=datetime(2026, 9, 12, 6, 30, 0),
        country_hint="IN",
        state_hint="Telangana",
        language_code="en",
    )

    ingest_raw_article(db, raw_te)
    ingest_raw_article(db, raw_en)
    db.commit()

    # Query /news/india?state=Telangana&language=te
    resp_te = client.get("/api/v1/news/india?state=Telangana&language=te")
    assert resp_te.status_code == 200
    data_te = resp_te.json()
    assert all(item["language_code"] == "te" for item in data_te["items"])
    assert any(item["canonical_url"] == raw_te.canonical_url for item in data_te["items"])

    # Query /news/state/telangana?language=en
    resp_en = client.get("/api/v1/news/state/telangana?language=en")
    assert resp_en.status_code == 200
    data_en = resp_en.json()
    assert all(item["language_code"] == "en" for item in data_en["items"])
    assert any(item["canonical_url"] == raw_en.canonical_url for item in data_en["items"])


def test_14_pagination(client: TestClient):
    """Verify pagination works on state news endpoints."""
    resp = client.get("/api/v1/news/state/telangana?page=1&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["limit"] == 5
    assert "total" in data
    assert "total_pages" in data


def test_15_archive_state_and_language_filtering(client: TestClient, db: Session):
    """Verify archive endpoint supports filtering by state and language."""
    date_str = "2026-09-12"
    raw_mr = RawArticle(
        title="महाराष्ट्रात नवीन उद्योग धोरण जाहीर",
        description="मुंबईत उद्योग परिषदेत घोषणा.",
        canonical_url="https://www.loksatta.com/maharashtra-industry-policy-2026",
        source_name="Loksatta",
        published_at=datetime(2026, 9, 12, 7, 0, 0),
        country_hint="IN",
        state_hint="Maharashtra",
        language_code="mr",
    )
    ingest_raw_article(db, raw_mr)
    db.commit()

    resp = client.get(f"/api/v1/archive?date={date_str}&state=Maharashtra&language=mr")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["language_code"] == "mr"


def test_16_search_language_filtering(client: TestClient, db: Session):
    """Verify search endpoint supports language query parameter."""
    raw = RawArticle(
        title="కర్ణాటక ఎన్నికల ప్రచారం",
        description="బెంగళూరులో రాజకీయ సమావేశం.",
        canonical_url="https://www.prajavani.net/karnataka-politics-2026",
        source_name="Prajavani",
        published_at=datetime(2026, 9, 12, 8, 0, 0),
        country_hint="IN",
        state_hint="Karnataka",
        language_code="kn",
    )
    ingest_raw_article(db, raw)
    db.commit()

    resp = client.get("/api/v1/search?q=కర్ణాటక&language=kn")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["language_code"] == "kn"


def test_17_missing_language_handling(client: TestClient):
    """Verify endpoint gracefully handles non-existent or unsupported language query."""
    resp = client.get("/api/v1/news/india?state=Telangana&language=nonexistent_lang")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_18_existing_articles_remain_valid(client: TestClient, db: Session):
    """Verify articles without explicit language_code default safely to 'en'."""
    raw_default = RawArticle(
        title="National Highway Infrastructure Update 2026",
        description="Highway projects across India.",
        canonical_url="https://indianexpress.com/article/india/national-highway-update-2026",
        source_name="The Indian Express",
        published_at=datetime(2026, 9, 12, 9, 0, 0),
        country_hint="IN",
    )
    art = ingest_raw_article(db, raw_default)
    db.commit()

    assert art.language_code == "en"

    resp = client.get(f"/api/v1/news/{art.id}")
    assert resp.status_code == 200
    assert resp.json()["language_code"] == "en"


# =========================================================================
# 4. Provider Regression & Pipeline Integrity
# =========================================================================

def test_19_existing_rss_ingestion_still_works(db: Session):
    """Verify RSS ingestion pipeline works with language metadata."""
    class MockRSS(RSSNewsProvider):
        def fetch_india_news(self, category=None, page_size=10):
            return [
                RawArticle(
                    title="RSS News item with English language tag",
                    description="RSS feed description.",
                    canonical_url="https://indianexpress.com/article/rss-item-2026",
                    source_name="The Indian Express",
                    published_at=datetime(2026, 9, 12, 9, 30, 0),
                    country_hint="IN",
                    language_code="en",
                )
            ]

    stats = run_ingestion(db=db, india_provider=MockRSS(), fetch_india=True, fetch_international=False, provider_type="rss")
    assert stats["saved"] >= 1
    assert stats["errors"] == 0


def test_20_existing_newsapi_ingestion_still_works(db: Session):
    """Verify NewsAPI international ingestion continues to work cleanly."""
    class MockNewsAPI(NewsAPIProvider):
        def fetch_international_news(self, category=None, page_size=10):
            return [
                RawArticle(
                    title="Global Trade Summit in Tokyo Reaches Historic Agreement",
                    description="International trade delegates conclude talks.",
                    canonical_url="https://www.reuters.com/world/tokyo-trade-summit-2026-regional-test",
                    source_name="Reuters",
                    published_at=datetime(2026, 9, 12, 10, 0, 0),
                    country_hint="GLOBAL",
                    language_code="en",
                )
            ]

    stats = run_ingestion(db=db, international_provider=MockNewsAPI(), fetch_india=False, fetch_international=True, provider_type="newsapi")
    assert stats["saved"] >= 1
    assert stats["errors"] == 0


def test_21_existing_gnews_ingestion_still_works(db: Session):
    """Verify GNews national/international ingestion functions without disruption."""
    provider = GNewsProvider(api_key="test_api_key")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "totalArticles": 1,
        "articles": [
            {
                "title": "National Space Mission Update 2026",
                "description": "Space exploration milestone.",
                "url": "https://www.thehindu.com/sci-tech/space-mission-update-2026-test",
                "image": "https://www.thehindu.com/images/space.jpg",
                "publishedAt": "2026-09-12T10:30:00Z",
                "source": {"name": "The Hindu", "url": "https://www.thehindu.com"}
            }
        ]
    }
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.Client.get", return_value=mock_resp):
        articles = provider.fetch_india_news(page_size=10)

    assert len(articles) == 1
    assert articles[0].title == "National Space Mission Update 2026"
    assert articles[0].language_code == "en"


def test_22_story_clustering_does_not_crash_with_non_english(db: Session):
    """Verify story clustering does not crash when handling regional language articles."""
    raw1 = RawArticle(
        title="తెలంగాణ బడ్జెట్ 2026 అసెంబ్లీలో ప్రవేశపెట్టారు",
        description="తెలంగాణ ఆర్థిక మంత్రి బడ్జెట్ ప్రవేశపెట్టారు.",
        canonical_url="https://www.eenadu.net/budget-2026-telangana",
        source_name="Eenadu",
        published_at=datetime(2026, 9, 12, 11, 0, 0),
        country_hint="IN",
        state_hint="Telangana",
        language_code="te",
    )
    raw2 = RawArticle(
        title="తెలంగాణ బడ్జెట్ 2026 అసెంబ్లీలో ప్రవేశపెట్టారు - ముఖ్యాంశాలు",
        description="తెలంగాణ బడ్జెట్ కేటాయింపులు మరియు పథకాలు.",
        canonical_url="https://www.sakshi.com/budget-2026-telangana-highlights",
        source_name="Sakshi",
        published_at=datetime(2026, 9, 12, 11, 15, 0),
        country_hint="IN",
        state_hint="Telangana",
        language_code="te",
    )

    art1 = ingest_raw_article(db, raw1)
    art2 = ingest_raw_article(db, raw2)
    db.commit()

    assert art1 is not None
    assert art2 is not None


def test_23_for_you_recommendations_with_regional_articles(client: TestClient, db: Session):
    """Verify /api/v1/news/for-you works seamlessly without breaking on regional articles."""
    email = f"foryou_reg_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    pwd = "SecurePassword123!"
    reg_resp = client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    assert reg_resp.status_code == 201

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/news/for-you?limit=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)




def test_24_image_handling_continues_to_work(db: Session):
    """Verify publisher-provided image URLs on regional articles are persisted correctly."""
    img_url = "https://images.eenadu.net/2026/09/hyderabad-metro.jpg"
    raw = RawArticle(
        title="హైదరాబాద్ మెట్రో రెండవ దశ విస్తరణ",
        description="మెట్రో రైల్ ప్రాజెక్ట్ తాజా వార్తలు.",
        canonical_url="https://www.eenadu.net/hyderabad-metro-phase-2",
        source_name="Eenadu",
        image_url=img_url,
        published_at=datetime(2026, 9, 12, 11, 30, 0),
        country_hint="IN",
        state_hint="Telangana",
        language_code="te",
    )

    art = ingest_raw_article(db, raw)
    db.commit()

    assert art is not None
    assert art.image_url == img_url
