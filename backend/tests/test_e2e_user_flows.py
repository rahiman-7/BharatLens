import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.user import User
from app.models.category import Category
from app.models.source import Source
from app.models.article import Article
from app.models.bookmark import Bookmark
from app.models.reading_event import ReadingEvent
from app.services.ingest import compute_url_hash

client = TestClient(app)


def create_e2e_user(email_prefix: str = "e2e_user") -> tuple[int, str, str]:
    """Helper to register and login a user, returning (user_id, email, access_token)."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    reg_resp = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_resp.status_code == 201

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    data = login_resp.json()
    return data["user"]["id"], email, data["access_token"]


# ==============================================================================
# FLOW A: Logged-Out User Complete Experience
# ==============================================================================
def test_e2e_flow_a_logged_out_user_experience():
    """Verify complete browsing journey for an unauthenticated visitor."""
    # 1. Open Homepage Feed
    resp = client.get("/api/v1/news/latest?page=1&limit=10")
    assert resp.status_code == 200
    latest_data = resp.json()
    assert "items" in latest_data
    assert len(latest_data["items"]) > 0
    sample_article = latest_data["items"][0]
    article_id = sample_article["id"]

    # 2. Browse India Section
    resp_india = client.get("/api/v1/news/india?page=1&limit=5")
    assert resp_india.status_code == 200
    for art in resp_india.json()["items"]:
        assert art["region"] == "INDIA"

    # 3. Browse International Section
    resp_intl = client.get("/api/v1/news/international?page=1&limit=5")
    assert resp_intl.status_code == 200
    for art in resp_intl.json()["items"]:
        assert art["region"] == "INTERNATIONAL"

    # 4. Open Category
    resp_cat = client.get("/api/v1/news/category/technology?page=1&limit=5")
    assert resp_cat.status_code == 200
    for art in resp_cat.json()["items"]:
        assert art["category"]["slug"] == "technology"

    # 5. Open Single Article
    resp_art = client.get(f"/api/v1/news/{article_id}")
    assert resp_art.status_code == 200
    art_data = resp_art.json()
    assert art_data["id"] == article_id
    assert "title" in art_data
    assert "source" in art_data
    assert "category" in art_data

    # 6. View "Wider Perspective" / Related Coverage
    resp_related = client.get(f"/api/v1/news/{article_id}/related")
    assert resp_related.status_code == 200
    related_items = resp_related.json()
    assert isinstance(related_items, list)
    # The current article itself must never be in related items
    assert article_id not in [r["id"] for r in related_items]

    # 7. Search for News
    resp_search = client.get("/api/v1/search?q=India")
    assert resp_search.status_code == 200
    assert "items" in resp_search.json()

    # 8. Open Archive by Date
    resp_archive = client.get("/api/v1/archive?date=2026-09-05")
    assert resp_archive.status_code == 200
    assert "items" in resp_archive.json()

    # 9. Browse Story Groups
    resp_stories = client.get("/api/v1/stories?page=1&limit=5")
    assert resp_stories.status_code == 200
    assert "items" in resp_stories.json()

    # 10. Open a Story Group if available
    if resp_stories.json()["items"]:
        story_id = resp_stories.json()["items"][0]["id"]
        resp_story = client.get(f"/api/v1/stories/{story_id}")
        assert resp_story.status_code == 200
        story_detail = resp_story.json()
        assert story_detail["id"] == story_id
        assert "articles" in story_detail
        assert "sources" in story_detail


# ==============================================================================
# FLOW B: New User Complete Onboarding & Interaction Journey
# ==============================================================================
def test_e2e_flow_b_new_user_journey():
    """Verify new user registration, login, bookmarking, reading events, and personalization."""
    # 1. Register & Login
    user_id, email, token = create_e2e_user(email_prefix="journey_user")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Verify Session via /auth/me
    resp_me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp_me.status_code == 200
    assert resp_me.json()["id"] == user_id
    assert resp_me.json()["email"] == email

    # 3. Obtain a valid article to interact with
    latest_resp = client.get("/api/v1/news/latest?limit=1")
    assert latest_resp.status_code == 200
    article_id = latest_resp.json()["items"][0]["id"]

    # 4. Bookmark the Article
    bm_add = client.post(f"/api/v1/bookmarks/{article_id}", headers=auth_headers)
    assert bm_add.status_code == 201
    assert bm_add.json()["is_bookmarked"] is True

    # 5. Check Bookmark Status
    bm_status = client.get(f"/api/v1/bookmarks/{article_id}", headers=auth_headers)
    assert bm_status.status_code == 200
    assert bm_status.json()["is_bookmarked"] is True

    # 6. List User's Bookmarks
    bm_list = client.get("/api/v1/bookmarks", headers=auth_headers)
    assert bm_list.status_code == 200
    bm_items = bm_list.json()["items"]
    assert any(item["id"] == article_id for item in bm_items)

    # 7. Record Reading Events (View + Read with dwell time)
    evt_view = client.post(
        "/api/v1/reading-events",
        headers=auth_headers,
        json={"article_id": article_id, "event_type": "view", "dwell_time_seconds": 15},
    )
    assert evt_view.status_code == 201

    evt_read = client.post(
        "/api/v1/reading-events",
        headers=auth_headers,
        json={"article_id": article_id, "event_type": "read", "dwell_time_seconds": 180},
    )
    assert evt_read.status_code == 201

    # 8. Open Personalized "For You" Feed
    for_you = client.get("/api/v1/news/for-you?page=1&limit=10", headers=auth_headers)
    assert for_you.status_code == 200
    assert "items" in for_you.json()
    assert len(for_you.json()["items"]) > 0

    # 9. Remove Bookmark
    bm_del = client.delete(f"/api/v1/bookmarks/{article_id}", headers=auth_headers)
    assert bm_del.status_code == 200
    assert bm_del.json()["is_bookmarked"] is False

    # 10. Verify Bookmark List is now empty of this article
    bm_list_after = client.get("/api/v1/bookmarks", headers=auth_headers)
    assert bm_list_after.status_code == 200
    assert not any(item["id"] == article_id for item in bm_list_after.json()["items"])


# ==============================================================================
# FLOW C: Multi-User Isolation & Security Enforcement
# ==============================================================================
def test_e2e_flow_c_multi_user_isolation_and_security():
    """Verify strict tenant isolation and authentication barriers."""
    # 1. Create User A and User B
    user_a_id, email_a, token_a = create_e2e_user("user_a")
    user_b_id, email_b, token_b = create_e2e_user("user_b")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Obtain two distinct articles
    latest = client.get("/api/v1/news/latest?limit=2").json()["items"]
    art_1 = latest[0]["id"]
    art_2 = latest[1]["id"]

    # User A bookmarks Article 1
    client.post(f"/api/v1/bookmarks/{art_1}", headers=headers_a)

    # User B bookmarks Article 2
    client.post(f"/api/v1/bookmarks/{art_2}", headers=headers_b)

    # 2. Verify User B does NOT see User A's bookmarks
    b_bookmarks = client.get("/api/v1/bookmarks", headers=headers_b).json()["items"]
    b_ids = [b["id"] for b in b_bookmarks]
    assert art_1 not in b_ids
    assert art_2 in b_ids

    # 3. User B cannot delete User A's bookmark
    del_resp = client.delete(f"/api/v1/bookmarks/{art_1}", headers=headers_b)
    assert del_resp.status_code == 200
    # User A's bookmark must still exist
    a_status = client.get(f"/api/v1/bookmarks/{art_1}", headers=headers_a).json()
    assert a_status["is_bookmarked"] is True

    # 4. Unauthenticated Access Rejections
    unauth_bookmarks = client.get("/api/v1/bookmarks")
    assert unauth_bookmarks.status_code == 401

    unauth_for_you = client.get("/api/v1/news/for-you")
    assert unauth_for_you.status_code == 401

    unauth_events = client.post("/api/v1/reading-events", json={"article_id": art_1, "event_type": "view"})
    assert unauth_events.status_code == 401

    unauth_me = client.get("/api/v1/auth/me")
    assert unauth_me.status_code == 401

    # 5. Invalid JWT Token Rejection
    fake_headers = {"Authorization": "Bearer invalid.malformed.token"}
    fake_resp = client.get("/api/v1/auth/me", headers=fake_headers)
    assert fake_resp.status_code == 401
