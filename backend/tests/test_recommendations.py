import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.models.category import Category
from app.models.source import Source
from app.models.article import Article
from app.models.reading_event import ReadingEvent
from app.models.bookmark import Bookmark
from app.services.ingest import compute_url_hash
from app.recommendation.profile import build_user_profile
from app.recommendation.scoring import calculate_freshness_score, calculate_article_score
from app.recommendation.service import apply_category_diversity, get_personalized_recommendations

client = TestClient(app)


def get_or_create_category(db, name: str, slug: str) -> Category:
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        cat = Category(name=name, slug=slug, display_order=1)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat


def get_or_create_source(db) -> Source:
    src = db.query(Source).first()
    if not src:
        src = Source(name="Test News Wire", base_url="https://testwire.com", country="IN")
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


def create_user(email_prefix: str = "rec_user") -> tuple[int, str, str]:
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    user_id = login_resp.json()["user"]["id"]
    return user_id, email, token


def create_test_article(db, cat_id: int, src_id: int, title: str, hours_ago: int = 1) -> Article:
    uid = uuid.uuid4().hex[:8]
    url = f"https://testwire.com/art-{uid}"
    art = Article(
        title=title,
        description=f"Description for {title}",
        canonical_url=url,
        url_hash=compute_url_hash(url),
        source_id=src_id,
        category_id=cat_id,
        region="INDIA",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_ago),
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


def test_user_profile_cold_start():
    """User with fewer than 3 events should return None (cold start)."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("cold_user")
        profile = build_user_profile(db, user_id)
        assert profile is None
    finally:
        db.close()


def test_user_profile_affinity_calculation():
    """User with read events in Technology should have strong tech category affinity."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("tech_fan")
        cat_tech = get_or_create_category(db, "Technology", "technology")
        cat_sports = get_or_create_category(db, "Sports", "sports")
        src = get_or_create_source(db)

        # Create 3 tech articles and read them with dwell time
        for i in range(3):
            art = create_test_article(db, cat_tech.id, src.id, f"Tech Breakthrough {i}", hours_ago=i + 1)
            event = ReadingEvent(
                user_id=user_id,
                article_id=art.id,
                event_type="read",
                dwell_time_seconds=180,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=i + 1),
            )
            db.add(event)

        # 1 Sports view event
        art_sports = create_test_article(db, cat_sports.id, src.id, "Sports Match", hours_ago=2)
        ev_sp = ReadingEvent(
            user_id=user_id,
            article_id=art_sports.id,
            event_type="view",
            dwell_time_seconds=10,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2),
        )
        db.add(ev_sp)
        db.commit()

        profile = build_user_profile(db, user_id)
        assert profile is not None
        assert "technology" in profile
        assert profile["technology"] > 0.75
        assert abs(sum(profile.values()) - 1.0) < 0.01
    finally:
        db.close()


def test_freshness_scoring():
    """Freshness score should decrease smoothly over time."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    fresh = calculate_freshness_score(now, now=now)
    assert fresh == 1.0

    older = calculate_freshness_score(now - timedelta(hours=72), now=now)
    assert 0.35 < older < 0.38  # exp(-1) ~= 0.3679

    very_old = calculate_freshness_score(now - timedelta(days=30), now=now)
    assert very_old < 0.001


def test_article_scoring_combination():
    """Article score combines category affinity (70%) and freshness (30%)."""
    cat = Category(name="Technology", slug="technology")
    art = Article(category=cat, published_at=datetime.now(timezone.utc).replace(tzinfo=None))
    profile = {"technology": 0.8, "sports": 0.2}

    score = calculate_article_score(art, profile, now=datetime.now(timezone.utc).replace(tzinfo=None))
    # 0.8 * 0.70 + 1.0 * 0.30 = 0.56 + 0.30 = 0.86
    assert abs(score - 0.86) < 0.05


def test_category_diversity_filter():
    """Diversity filter prevents more than 2 consecutive articles of the same category."""
    cat_t = Category(slug="technology")
    cat_p = Category(slug="politics")

    articles = [
        Article(id=1, category=cat_t),
        Article(id=2, category=cat_t),
        Article(id=3, category=cat_t),
        Article(id=4, category=cat_p),
        Article(id=5, category=cat_p),
    ]

    diversified = apply_category_diversity(articles, max_consecutive=2)
    slugs = [a.category.slug for a in diversified]

    for i in range(len(slugs) - 2):
        assert not (slugs[i] == slugs[i + 1] == slugs[i + 2])


def test_get_personalized_recommendations_cold_start():
    """Cold-start user gets latest articles without crashing."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("cold_feed_user")
        res = get_personalized_recommendations(db, user_id, page=1, limit=5)
        assert res.total >= 0
        assert isinstance(res.items, list)
    finally:
        db.close()


def test_get_personalized_recommendations_customized():
    """Personalized user gets unread articles ranked according to affinity."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("pref_user")
        cat_pol = get_or_create_category(db, "Politics", "politics")
        src = get_or_create_source(db)

        # Add 3 reading events
        for i in range(3):
            art = create_test_article(db, cat_pol.id, src.id, f"Politics Review {i}", hours_ago=i + 1)
            event = ReadingEvent(
                user_id=user_id,
                article_id=art.id,
                event_type="read",
                dwell_time_seconds=120,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=i + 1),
            )
            db.add(event)
        db.commit()

        # Add new unread politics article
        fresh_art = create_test_article(db, cat_pol.id, src.id, "Fresh Politics Headline", hours_ago=1)

        res = get_personalized_recommendations(db, user_id, page=1, limit=10)
        assert res.total > 0
        assert len(res.items) > 0
        # The top recommended article should belong to the user's preferred category (politics)
        top_cats = [a.category.slug for a in res.items if a.category]
        assert "politics" in top_cats
        assert top_cats[0] == "politics"
    finally:
        db.close()


def test_for_you_api_unauthorized():
    """GET /api/v1/news/for-you should return 401 when unauthorized."""
    resp = client.get("/api/v1/news/for-you")
    assert resp.status_code == 401


def test_for_you_api_authorized():
    """Authenticated user gets personalized feed from /api/v1/news/for-you."""
    _, _, token = create_user("api_for_you_user")
    resp = client.get(
        "/api/v1/news/for-you",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1


def test_cold_start_threshold_progression():
    """Cold-start requires >= 3 interaction signals before activating profile."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("cold_step_user")
        cat_tech = get_or_create_category(db, "Technology", "technology")
        src = get_or_create_source(db)

        # 0 signals -> Cold-start (None)
        assert build_user_profile(db, user_id) is None

        # 1 accidental view -> Cold-start (None)
        art1 = create_test_article(db, cat_tech.id, src.id, "Tech Article 1", hours_ago=2)
        ev1 = ReadingEvent(
            user_id=user_id,
            article_id=art1.id,
            event_type="view",
            dwell_time_seconds=3,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2),
        )
        db.add(ev1)
        db.commit()
        assert build_user_profile(db, user_id) is None

        # 2 weak interactions -> Cold-start (None)
        art2 = create_test_article(db, cat_tech.id, src.id, "Tech Article 2", hours_ago=1)
        ev2 = ReadingEvent(
            user_id=user_id,
            article_id=art2.id,
            event_type="view",
            dwell_time_seconds=5,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
        )
        db.add(ev2)
        db.commit()
        assert build_user_profile(db, user_id) is None

        # 3rd meaningful reading interaction -> Transitions out of cold start
        art3 = create_test_article(db, cat_tech.id, src.id, "Tech Article 3", hours_ago=1)
        ev3 = ReadingEvent(
            user_id=user_id,
            article_id=art3.id,
            event_type="read",
            dwell_time_seconds=180,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=30),
        )
        db.add(ev3)
        db.commit()

        profile = build_user_profile(db, user_id)
        assert profile is not None
        assert "technology" in profile
        assert profile["technology"] == 1.0
    finally:
        db.close()


def test_one_bookmark_cannot_overpower_substantial_reading_history():
    """A single bookmark in another category must NOT overpower substantial reading history."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("bm_overpower_test")
        cat_tech = get_or_create_category(db, "Technology", "technology")
        cat_sports = get_or_create_category(db, "Sports", "sports")
        src = get_or_create_source(db)

        # User has substantial reading history in Technology (4 meaningful reads of 180s each)
        for i in range(4):
            art = create_test_article(db, cat_tech.id, src.id, f"Tech Major Story {i}", hours_ago=i + 1)
            ev = ReadingEvent(
                user_id=user_id,
                article_id=art.id,
                event_type="read",
                dwell_time_seconds=180,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=i + 1),
            )
            db.add(ev)

        # User has ONLY 1 bookmark in Sports
        art_sp = create_test_article(db, cat_sports.id, src.id, "Single Sports Bookmark", hours_ago=1)
        bm = Bookmark(
            user_id=user_id,
            article_id=art_sp.id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
        )
        db.add(bm)
        db.commit()

        profile = build_user_profile(db, user_id)
        assert profile is not None
        assert "technology" in profile
        assert "sports" in profile

        # Reading behavior (Technology) must remain overwhelmingly dominant
        assert profile["technology"] > 0.85
        assert profile["sports"] < 0.15
        assert profile["technology"] > profile["sports"] * 5
    finally:
        db.close()


def test_personalization_sanity_tech_vs_sports_candidates():
    """User with 3 Tech reads and 1 Sports read scores candidate Tech higher than candidate Sports."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("sanity_tech_user")
        cat_tech = get_or_create_category(db, "Technology", "technology")
        cat_sports = get_or_create_category(db, "Sports", "sports")
        src = get_or_create_source(db)

        # 3 meaningful Tech reads
        for i in range(3):
            art = create_test_article(db, cat_tech.id, src.id, f"Tech Read Story {i}", hours_ago=i + 2)
            ev = ReadingEvent(
                user_id=user_id,
                article_id=art.id,
                event_type="read",
                dwell_time_seconds=150,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=i + 2),
            )
            db.add(ev)

        # 1 meaningful Sports read
        art_sp = create_test_article(db, cat_sports.id, src.id, "Sports Read Story", hours_ago=2)
        ev_sp = ReadingEvent(
            user_id=user_id,
            article_id=art_sp.id,
            event_type="read",
            dwell_time_seconds=150,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2),
        )
        db.add(ev_sp)
        db.commit()

        profile = build_user_profile(db, user_id)
        assert profile is not None
        assert profile["technology"] > profile["sports"]

        # Candidate articles with comparable freshness (both published 1 hour ago)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cand_tech = Article(category=cat_tech, published_at=now - timedelta(hours=1))
        cand_sports = Article(category=cat_sports, published_at=now - timedelta(hours=1))

        score_tech = calculate_article_score(cand_tech, profile, now=now)
        score_sports = calculate_article_score(cand_sports, profile, now=now)

        assert score_tech > score_sports
    finally:
        db.close()


def test_personalization_sanity_sports_reads_with_tech_bookmark():
    """User with multiple Sports reads and 1 Tech bookmark retains Sports as dominant preference."""
    db = SessionLocal()
    try:
        user_id, _, _ = create_user("sanity_sports_user")
        cat_tech = get_or_create_category(db, "Technology", "technology")
        cat_sports = get_or_create_category(db, "Sports", "sports")
        src = get_or_create_source(db)

        # Multiple meaningful Sports reads (3 reads of 180s each)
        for i in range(3):
            art = create_test_article(db, cat_sports.id, src.id, f"Sports Match Event {i}", hours_ago=i + 2)
            ev = ReadingEvent(
                user_id=user_id,
                article_id=art.id,
                event_type="read",
                dwell_time_seconds=180,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=i + 2),
            )
            db.add(ev)

        # 1 Tech bookmark
        art_tech = create_test_article(db, cat_tech.id, src.id, "Single Tech Bookmark", hours_ago=1)
        bm = Bookmark(
            user_id=user_id,
            article_id=art_tech.id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
        )
        db.add(bm)
        db.commit()

        profile = build_user_profile(db, user_id)
        assert profile is not None
        assert profile["sports"] > profile["technology"]
        assert profile["sports"] > 0.80

        # Candidate ranking test
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cand_sports = Article(category=cat_sports, published_at=now - timedelta(hours=1))
        cand_tech = Article(category=cat_tech, published_at=now - timedelta(hours=1))

        score_sports = calculate_article_score(cand_sports, profile, now=now)
        score_tech = calculate_article_score(cand_tech, profile, now=now)

        assert score_sports > score_tech
    finally:
        db.close()

