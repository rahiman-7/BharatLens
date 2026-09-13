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


def setup_archive_test_data():
    db = SessionLocal()
    try:
        # Resolve category and source
        tech_cat = db.query(Category).filter(Category.slug == "technology").first()
        politics_cat = db.query(Category).filter(Category.slug == "politics").first()
        source = db.query(Source).first()

        run_id = uuid.uuid4().hex[:6]
        
        # Article A on Sept 5, 2026 10:00 UTC
        url_a = f"https://example.com/archive-test-a-{run_id}"
        art_a = Article(
            title=f"Archive Test A {run_id}: AI Supercomputer Launched in Hyderabad",
            description="Hyderabad inaugurates high-performance computing cluster.",
            canonical_url=url_a,
            url_hash=compute_url_hash(url_a),
            source_id=source.id,
            category_id=tech_cat.id,
            region="INDIA",
            state="Telangana",
            published_at=datetime(2026, 9, 5, 10, 0, 0),
        )

        # Article B on Sept 5, 2026 18:30 UTC
        url_b = f"https://example.com/archive-test-b-{run_id}"
        art_b = Article(
            title=f"Archive Test B {run_id}: Global Tech Summit Closes in Geneva",
            description="International delegates establish AI governance protocols.",
            canonical_url=url_b,
            url_hash=compute_url_hash(url_b),
            source_id=source.id,
            category_id=tech_cat.id,
            region="INTERNATIONAL",
            published_at=datetime(2026, 9, 5, 18, 30, 0),
        )

        # Article C on Sept 6, 2026 09:00 UTC (Next day)
        url_c = f"https://example.com/archive-test-c-{run_id}"
        art_c = Article(
            title=f"Archive Test C {run_id}: Parliament Debates Digital India Bill",
            description="New legislation introduced in Lok Sabha.",
            canonical_url=url_c,
            url_hash=compute_url_hash(url_c),
            source_id=source.id,
            category_id=politics_cat.id,
            region="INDIA",
            state="Delhi",
            published_at=datetime(2026, 9, 6, 9, 0, 0),
        )

        db.add_all([art_a, art_b, art_c])
        db.commit()
        return run_id
    finally:
        db.close()


def test_archive_date_filtering_and_exclusion():
    run_id = setup_archive_test_data()

    # Query Sept 5, 2026
    response = client.get("/api/v1/archive?date=2026-09-05&limit=100")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 2
    
    titles = [a["title"] for a in data["items"]]
    # Must contain A and B, but NOT C
    assert any(f"Archive Test A {run_id}" in t for t in titles)
    assert any(f"Archive Test B {run_id}" in t for t in titles)
    assert not any(f"Archive Test C {run_id}" in t for t in titles)

    # Query Sept 6, 2026 -> Must contain C, but NOT A or B
    response_c = client.get("/api/v1/archive?date=2026-09-06&limit=100")
    assert response_c.status_code == 200
    titles_c = [a["title"] for a in response_c.json()["items"]]
    assert any(f"Archive Test C {run_id}" in t for t in titles_c)
    assert not any(f"Archive Test A {run_id}" in t for t in titles_c)


def test_archive_region_filtering():
    run_id = setup_archive_test_data()

    # Filter India on Sept 5
    resp_india = client.get("/api/v1/archive?date=2026-09-05&region=india&limit=100")
    assert resp_india.status_code == 200
    titles_india = [a["title"] for a in resp_india.json()["items"]]
    assert any(f"Archive Test A {run_id}" in t for t in titles_india)
    assert not any(f"Archive Test B {run_id}" in t for t in titles_india)

    # Filter International on Sept 5
    resp_intl = client.get("/api/v1/archive?date=2026-09-05&region=international&limit=100")
    assert resp_intl.status_code == 200
    titles_intl = [a["title"] for a in resp_intl.json()["items"]]
    assert any(f"Archive Test B {run_id}" in t for t in titles_intl)
    assert not any(f"Archive Test A {run_id}" in t for t in titles_intl)



def test_archive_category_and_state_filtering():
    run_id = setup_archive_test_data()

    # Category technology on Sept 5
    resp_cat = client.get("/api/v1/archive?date=2026-09-05&category=technology")
    assert resp_cat.status_code == 200
    assert len(resp_cat.json()["items"]) >= 2

    # State Telangana on Sept 5
    resp_state = client.get("/api/v1/archive?date=2026-09-05&state=Telangana")
    assert resp_state.status_code == 200
    for art in resp_state.json()["items"]:
        assert art["state"] == "Telangana"


def test_archive_sorting_descending():
    setup_archive_test_data()
    resp = client.get("/api/v1/archive?date=2026-09-05")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 2
    # Verify published_at is strictly non-increasing
    for i in range(len(items) - 1):
        assert items[i]["published_at"] >= items[i + 1]["published_at"]


def test_archive_empty_date_handling():
    # Far future date
    resp = client.get("/api/v1/archive?date=2099-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_get_archive_dates_endpoint():
    setup_archive_test_data()
    resp = client.get("/api/v1/archive/dates?limit=50")
    assert resp.status_code == 200
    dates = resp.json()
    assert isinstance(dates, list)
    assert len(dates) > 0
    
    # Every date must have date string and article_count > 0
    date_strs = []
    for d in dates:
        assert "date" in d
        assert "article_count" in d
        assert d["article_count"] > 0
        date_strs.append(d["date"])
        
    # Must be sorted descending
    for i in range(len(date_strs) - 1):
        assert date_strs[i] >= date_strs[i + 1]
        
    # Sept 5 and Sept 6 from test setup should be present
    assert "2026-09-05" in date_strs
    assert "2026-09-06" in date_strs
    # Far future empty date should not be present
    assert "2099-01-01" not in date_strs

