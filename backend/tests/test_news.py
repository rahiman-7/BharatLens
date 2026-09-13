from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_latest_news():
    response = client.get("/api/v1/news/latest?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["items"]) > 0

def test_get_india_news():
    response = client.get("/api/v1/news/india")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for article in data["items"]:
        assert article["region"].upper() == "INDIA"

def test_get_international_news():
    response = client.get("/api/v1/news/international")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for article in data["items"]:
        assert article["region"].upper() == "INTERNATIONAL"

def test_get_category_news():
    response = client.get("/api/v1/news/category/technology")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for article in data["items"]:
        assert article["category"]["slug"] == "technology"

def test_get_category_not_found():
    response = client.get("/api/v1/news/category/non-existent-category-slug")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category 'non-existent-category-slug' not found"

def test_get_single_article_and_not_found():
    # First get latest news to obtain a real ID
    latest_resp = client.get("/api/v1/news/latest")
    assert latest_resp.status_code == 200
    articles = latest_resp.json()["items"]
    assert len(articles) > 0
    first_id = articles[0]["id"]

    # Test single article lookup
    single_resp = client.get(f"/api/v1/news/{first_id}")
    assert single_resp.status_code == 200
    article = single_resp.json()
    assert article["id"] == first_id
    assert "title" in article
    assert "source" in article
    assert "category" in article

    # Test 404 for invalid ID
    not_found_resp = client.get("/api/v1/news/99999999")
    assert not_found_resp.status_code == 404
    assert "99999999 not found" in not_found_resp.json()["detail"]
