import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.database import SessionLocal, engine
from app.models.user import User
from app.models.category import Category
from app.models.source import Source
from app.models.article import Article
from app.models.bookmark import Bookmark
from app.models.reading_event import ReadingEvent
from app.core.datetime_utils import utc_now

client = TestClient(app)


def test_sqlite_foreign_keys_pragma_enabled():
    """Verify that SQLite connection pragma enforces foreign key constraints."""
    db = SessionLocal()
    try:
        result = db.execute(text("PRAGMA foreign_keys")).scalar()
        assert result == 1, "PRAGMA foreign_keys must be enabled (1) for data integrity."
    finally:
        db.close()


def test_cascade_delete_integrity_user_and_bookmarks():
    """Verify that deleting a user cleanly cascades to bookmarks and reading events."""
    db = SessionLocal()
    try:
        # 1. Create temporary user
        unique_email = f"cascade_test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(email=unique_email, password_hash="dummyhash", created_at=utc_now())
        db.add(user)
        db.flush()

        # 2. Grab an existing article
        article = db.query(Article).first()
        assert article is not None, "At least one article required for testing."

        # 3. Create bookmark and reading event
        bm = Bookmark(user_id=user.id, article_id=article.id, created_at=utc_now())
        re = ReadingEvent(
            user_id=user.id,
            article_id=article.id,
            event_type="read",
            dwell_time_seconds=60,
            created_at=utc_now(),
        )
        db.add_all([bm, re])
        db.commit()

        user_id = user.id
        bm_id = bm.id
        re_id = re.id

        # 4. Delete user
        db.delete(user)
        db.commit()

        # 5. Verify cascade deletion
        assert db.query(Bookmark).filter(Bookmark.id == bm_id).first() is None
        assert db.query(ReadingEvent).filter(ReadingEvent.id == re_id).first() is None
    finally:
        db.close()


def test_password_hash_never_exposed_in_api():
    """Verify that password hash is never exposed in registration, login, or /me."""
    email = f"security_audit_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "AuditPassword123!"

    # Registration
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    assert reg.status_code == 201
    assert "password_hash" not in reg.json()
    assert "password" not in reg.json()

    # Login
    login = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert login.status_code == 200
    token_data = login.json()
    assert "password_hash" not in token_data
    assert "password_hash" not in token_data["user"]
    token = token_data["access_token"]

    # /me endpoint
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert "password_hash" not in me.json()
    assert "password" not in me.json()


def test_api_input_validation_and_error_handling():
    """Verify input validation rejecting out-of-bound pagination and invalid IDs gracefully."""
    # Invalid negative page
    resp1 = client.get("/api/v1/news/latest?page=0")
    assert resp1.status_code == 422

    # Excessive limit
    resp2 = client.get("/api/v1/news/latest?limit=999")
    assert resp2.status_code == 422

    # Non-integer article ID
    resp3 = client.get("/api/v1/news/not-an-id")
    assert resp3.status_code == 422

    # Non-existent article ID
    resp4 = client.get("/api/v1/news/99999999")
    assert resp4.status_code == 404

    # Malformed date format in archive
    resp5 = client.get("/api/v1/archive?date=invalid-date")
    assert resp5.status_code == 400
