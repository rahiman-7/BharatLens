from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_categories():
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total" in data
    assert data["total"] >= 11
    slugs = [c["slug"] for c in data["categories"]]
    assert "politics" in slugs
    assert "sports" in slugs
    assert "technology" in slugs
    assert "business" in slugs
    assert "movies-entertainment" in slugs
    assert "education" in slugs
    assert "science" in slugs
    assert "health" in slugs
    assert "lifestyle" in slugs
    assert "crime" in slugs
    assert "environment" in slugs

def test_get_states():
    response = client.get("/api/v1/states")
    assert response.status_code == 200
    data = response.json()
    if isinstance(data, dict):
        raw_list = data.get("states", [])
    else:
        raw_list = data
    states = [s["name"] if isinstance(s, dict) else s for s in raw_list]
    assert len(states) >= 28
    assert "Maharashtra" in states
    assert "Delhi" in states
    assert "Tamil Nadu" in states
    assert "Karnataka" in states

