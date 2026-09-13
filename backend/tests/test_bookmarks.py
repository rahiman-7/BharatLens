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
    email = f"bm_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    user_id = login_resp.json()["user"]["id"]
    return user_id, email, token


def create_test_article(title_prefix: str = "Bookmark Test Article") -> int:
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
        url = f"https://testnews.com/article-{uid}"
        article = Article(
            title=f"{title_prefix} {uid}",
            description="Test description for bookmark test.",
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


def test_authenticated_user_can_bookmark_article():
    """Test 11: Authenticated user bookmarks an article and receives status True."""
    _, _, token = create_test_user_and_token()
    article_id = create_test_article()

    resp = client.post(
        f"/api/v1/bookmarks/{article_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["is_bookmarked"] is True
    assert resp.json()["article_id"] == article_id

    # Check status endpoint
    status_resp = client.get(
        f"/api/v1/bookmarks/{article_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["is_bookmarked"] is True


def test_duplicate_bookmark_is_prevented():
    """Test 12: Bookmarking the same article twice is idempotent and safe."""
    _, _, token = create_test_user_and_token()
    article_id = create_test_article()

    resp1 = client.post(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 201

    resp2 = client.post(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 201
    assert resp2.json()["is_bookmarked"] is True


def test_user_can_remove_bookmark():
    """Test 13: User can remove a bookmark and status becomes False."""
    _, _, token = create_test_user_and_token()
    article_id = create_test_article()

    # Add
    client.post(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token}"})
    
    # Remove
    del_resp = client.delete(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 200
    assert del_resp.json()["is_bookmarked"] is False

    # Check status endpoint
    status_resp = client.get(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token}"})
    assert status_resp.json()["is_bookmarked"] is False


def test_user_can_list_their_bookmarks():
    """Test 14: User retrieves their bookmarked articles."""
    _, _, token = create_test_user_and_token()
    art1_id = create_test_article("Article One")
    art2_id = create_test_article("Article Two")

    client.post(f"/api/v1/bookmarks/{art1_id}", headers={"Authorization": f"Bearer {token}"})
    client.post(f"/api/v1/bookmarks/{art2_id}", headers={"Authorization": f"Bearer {token}"})

    list_resp = client.get("/api/v1/bookmarks", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 2
    bookmarked_ids = [item["id"] for item in data["items"]]
    assert art1_id in bookmarked_ids
    assert art2_id in bookmarked_ids


def test_nonexistent_article_cannot_be_bookmarked():
    """Test 15: Bookmarking a non-existent article returns 404 Not Found."""
    _, _, token = create_test_user_and_token()
    resp = client.post("/api/v1/bookmarks/9999999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_unauthenticated_bookmark_request_rejected():
    """Test 16: Unauthenticated bookmark actions return 401 Unauthorized."""
    article_id = create_test_article()
    resp = client.post(f"/api/v1/bookmarks/{article_id}")
    assert resp.status_code == 401

    resp_list = client.get("/api/v1/bookmarks")
    assert resp_list.status_code == 401


def test_cross_user_bookmark_isolation():
    """Test 17: User A cannot see or modify User B's bookmarks."""
    _, _, token_a = create_test_user_and_token()
    _, _, token_b = create_test_user_and_token()
    article_id = create_test_article()

    # User A bookmarks
    client.post(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token_a}"})

    # User B checks status -> False
    status_b = client.get(f"/api/v1/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert status_b.json()["is_bookmarked"] is False

    # User B bookmarks list does not contain article
    list_b = client.get("/api/v1/bookmarks", headers={"Authorization": f"Bearer {token_b}"})
    assert article_id not in [item["id"] for item in list_b.json()["items"]]
