import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.services.ingest import compute_url_hash

client = TestClient(app)


def setup_search_test_data():
    db = SessionLocal()
    try:
        tech_cat = db.query(Category).filter(Category.slug == "technology").first()
        sports_cat = db.query(Category).filter(Category.slug == "sports").first()
        source = db.query(Source).first()

        run_id = uuid.uuid4().hex[:6]

        art1 = Article(
            title=f"SearchTest {run_id}: Quantum Semiconductor Fab Announced in Gujarat",
            description="Next-generation quantum silicon fab opens in Dholera manufacturing corridor.",
            canonical_url=f"https://example.com/search-test-1-{run_id}",
            url_hash=compute_url_hash(f"https://example.com/search-test-1-{run_id}"),
            source_id=source.id,
            category_id=tech_cat.id,
            region="INDIA",
            state="Gujarat",
            published_at=datetime(2026, 9, 7, 12, 0, 0),
        )

        art2 = Article(
            title=f"SearchTest {run_id}: Indian Cricket Team Prepares for World Championship",
            description="Training camp begins at the national cricket academy.",
            canonical_url=f"https://example.com/search-test-2-{run_id}",
            url_hash=compute_url_hash(f"https://example.com/search-test-2-{run_id}"),
            source_id=source.id,
            category_id=sports_cat.id,
            region="INDIA",
            state="Karnataka",
            published_at=datetime(2026, 9, 8, 14, 0, 0),
        )

        db.add_all([art1, art2])
        db.commit()
        return run_id
    finally:
        db.close()


def test_search_title_and_description_match():
    run_id = setup_search_test_data()

    # Search title keyword
    resp_title = client.get(f"/api/v1/search?q=Semiconductor")
    assert resp_title.status_code == 200
    assert any(f"SearchTest {run_id}" in a["title"] for a in resp_title.json()["items"])

    # Search description keyword
    resp_desc = client.get(f"/api/v1/search?q=Dholera")
    assert resp_desc.status_code == 200
    assert any(f"SearchTest {run_id}" in a["title"] for a in resp_desc.json()["items"])


def test_search_case_insensitivity():
    run_id = setup_search_test_data()

    # Uppercase
    resp_upper = client.get(f"/api/v1/search?q=QUANTUM")
    assert resp_upper.status_code == 200
    assert any(f"SearchTest {run_id}" in a["title"] for a in resp_upper.json()["items"])

    # Lowercase
    resp_lower = client.get(f"/api/v1/search?q=quantum")
    assert resp_lower.status_code == 200
    assert any(f"SearchTest {run_id}" in a["title"] for a in resp_lower.json()["items"])


def test_search_with_facets():
    run_id = setup_search_test_data()

    # Search with category
    resp_cat = client.get(f"/api/v1/search?q=SearchTest+{run_id}&category=sports")
    assert resp_cat.status_code == 200
    items = resp_cat.json()["items"]
    assert len(items) == 1
    assert "Cricket" in items[0]["title"]

    # Search with state
    resp_state = client.get(f"/api/v1/search?q=SearchTest+{run_id}&state=Gujarat")
    assert resp_state.status_code == 200
    items_state = resp_state.json()["items"]
    assert len(items_state) == 1
    assert "Semiconductor" in items_state[0]["title"]

    # Search with date
    resp_date = client.get(f"/api/v1/search?q=SearchTest+{run_id}&date=2026-09-08")
    assert resp_date.status_code == 200
    items_date = resp_date.json()["items"]
    assert len(items_date) == 1
    assert "Cricket" in items_date[0]["title"]


def test_search_empty_and_missing_query():
    # Empty query string should return 0 items rather than dumping the whole database
    resp_empty = client.get("/api/v1/search?q=")
    assert resp_empty.status_code == 200
    assert resp_empty.json()["total"] == 0
    assert len(resp_empty.json()["items"]) == 0

    resp_none = client.get("/api/v1/search")
    assert resp_none.status_code == 200
    assert resp_none.json()["total"] == 0


def test_search_non_matching_query():
    resp_none = client.get("/api/v1/search?q=xyznonexistentphrase99999")
    assert resp_none.status_code == 200
    assert resp_none.json()["total"] == 0
    assert len(resp_none.json()["items"]) == 0
