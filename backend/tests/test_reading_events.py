import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.category import Category
from app.models.source import Source
from app.services.ingest import compute_url_hash

client = TestClient(app)


def create_test_user_and_token() -> tuple[int, str, str]:
    """Helper to create a user and return (user_id, email, token)."""
    email = f"event_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "EventPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    user_id = login_resp.json()["user"]["id"]
    return user_id, email, token


def create_test_article(title_prefix: str = "Event Test Article") -> int:
    """Helper to insert an article and return its ID."""
    db = SessionLocal()
    try:
        source = db.query(Source).first()
        if not source:
            source = Source(name="Test News", base_url="https://testnews.com", country="IN")
            db.add(source)
            db.flush()

        category = db.query(Category).first()
        if not category:
            category = Category(name="Politics", slug="politics", display_order=1)
            db.add(category)
            db.flush()

        uid = uuid.uuid4().hex[:8]
        url = f"https://testnews.com/event-article-{uid}"
        article = Article(
            title=f"{title_prefix} {uid}",
            description="Test description for reading event test.",
            canonical_url=url,
            url_hash=compute_url_hash(url),
            source_id=source.id,
            category_id=category.id,
            region="INDIA",
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(article)
        db.commit()
        return article.id
    finally:
        db.close()


def test_authenticated_user_can_create_reading_events():
    """Test 18 & 24: Authenticated user creates valid 'view' and 'read' events linked to user."""
    user_id, _, token = create_test_user_and_token()
    article_id = create_test_article()

    # 1. View event
    resp_view = client.post(
        "/api/v1/reading-events",
        json={"article_id": article_id, "event_type": "view", "dwell_time_seconds": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_view.status_code == 201
    view_data = resp_view.json()
    assert view_data["user_id"] == user_id
    assert view_data["article_id"] == article_id
    assert view_data["event_type"] == "view"

    # 2. Read dwell event
    resp_read = client.post(
        "/api/v1/reading-events",
        json={"article_id": article_id, "event_type": "read", "dwell_time_seconds": 45},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_read.status_code == 201
    read_data = resp_read.json()
    assert read_data["user_id"] == user_id
    assert read_data["event_type"] == "read"
    assert read_data["dwell_time_seconds"] == 45


def test_invalid_event_type_rejected():
    """Test 19: Invalid event_type returns 422 Unprocessable Entity."""
    _, _, token = create_test_user_and_token()
    article_id = create_test_article()

    resp = client.post(
        "/api/v1/reading-events",
        json={"article_id": article_id, "event_type": "invalid_event_type", "dwell_time_seconds": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_negative_and_excessive_dwell_time_rejected():
    """Test 20 & 21: Negative or excessive dwell times (>14400s) return 422."""
    _, _, token = create_test_user_and_token()
    article_id = create_test_article()

    # Negative dwell time
    resp_neg = client.post(
        "/api/v1/reading-events",
        json={"article_id": article_id, "event_type": "read", "dwell_time_seconds": -5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_neg.status_code == 422

    # Excessive dwell time (e.g. 50,000 seconds)
    resp_excess = client.post(
        "/api/v1/reading-events",
        json={"article_id": article_id, "event_type": "read", "dwell_time_seconds": 50000},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_excess.status_code == 422


def test_nonexistent_article_event_rejected():
    """Test 22: Reading event for non-existent article returns 404 Not Found."""
    _, _, token = create_test_user_and_token()
    resp = client.post(
        "/api/v1/reading-events",
        json={"article_id": 9999999, "event_type": "view", "dwell_time_seconds": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_unauthenticated_reading_event_rejected():
    """Test 23: Unauthenticated reading event request returns 401 Unauthorized."""
    article_id = create_test_article()
    resp = client.post(
        "/api/v1/reading-events",
        json={"article_id": article_id, "event_type": "view", "dwell_time_seconds": 0},
    )
    assert resp.status_code == 401
