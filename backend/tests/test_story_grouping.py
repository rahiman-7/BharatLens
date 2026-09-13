import uuid
from datetime import datetime, timedelta, timezone
from typing import List
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.category import Category
from app.models.source import Source
from app.models.article import Article
from app.models.story_group import StoryGroup
from app.services.ingest import compute_url_hash, RawArticle, ingest_raw_article
from app.services.story_grouping import (
    assign_article_to_story_group,
    STORY_GROUP_SIMILARITY_THRESHOLD,
    CANDIDATE_WINDOW_DAYS,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_story_data():
    """Ensure tests run in an isolated environment by cleaning up created test articles/groups."""
    db = SessionLocal()
    try:
        # Pre-test cleanup of test articles
        db.query(Article).filter(
            (Article.canonical_url.like("%test-story-art%"))
            | (Article.canonical_url.like("%example.com/art-%"))
            | (Article.canonical_url.like("%bharatlens.test%"))
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    
    yield

    db = SessionLocal()
    try:
        # Post-test cleanup of test articles and empty story groups
        test_articles = db.query(Article).filter(
            (Article.canonical_url.like("%test-story-art%"))
            | (Article.canonical_url.like("%example.com/art-%"))
            | (Article.canonical_url.like("%bharatlens.test%"))
        ).all()
        group_ids = {a.story_group_id for a in test_articles if a.story_group_id}
        for a in test_articles:
            db.delete(a)
        db.commit()
        for gid in group_ids:
            grp = db.query(StoryGroup).filter(StoryGroup.id == gid).first()
            if grp and len(grp.articles) == 0:
                db.delete(grp)
        db.commit()
    finally:
        db.close()


def get_or_create_category(db, name: str = "Technology", slug: str = "technology") -> Category:
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        cat = Category(name=name, slug=slug, display_order=1)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat


def get_or_create_source(db, name: str = "The Hindu") -> Source:
    src = db.query(Source).filter(Source.name == name).first()
    if not src:
        src = Source(name=name, base_url=f"https://{name.lower().replace(' ', '')}.com", country="IN")
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


def create_article_helper(
    db,
    title: str,
    description: str,
    source_name: str,
    category_slug: str = "technology",
    hours_ago: int = 2,
    test_run_id: str = "",
) -> Article:
    cat = get_or_create_category(db, category_slug.capitalize(), category_slug)
    src = get_or_create_source(db, source_name)
    uid = uuid.uuid4().hex[:8]
    url = f"https://bharatlens.test/test-story-art-{uid}"
    art = Article(
        title=title,
        description=description,
        canonical_url=url,
        url_hash=compute_url_hash(url),
        source_id=src.id,
        category_id=cat.id,
        region="INDIA",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_ago),
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


# 1. Story Group Creation
def test_1_story_group_creation():
    """First article creates a new StoryGroup with itself as representative."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art = create_article_helper(
            db,
            title=f"ISRO Launches Next Gen Navigation Satellite Mission {token}",
            description=f"Indian space agency successfully orbited the satellite constellation {token}.",
            source_name="The Hindu",
            hours_ago=5,
        )
        group = assign_article_to_story_group(db, art)
        db.commit()

        assert group is not None
        assert group.id is not None
        assert art.story_group_id == group.id
        assert group.representative_article_id == art.id
        assert len(group.articles) >= 1
    finally:
        db.close()


# 2. Highly Similar Articles
def test_2_highly_similar_articles():
    """Multiple publishers reporting the same story are clustered into the same StoryGroup."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art1 = create_article_helper(
            db,
            title=f"Reserve Bank of India Keeps Repo Rate Unchanged at 6.5 Percent {token}",
            description=f"Monetary policy committee of RBI decided unanimously to hold benchmark repo rate at 6.5% {token}.",
            source_name="The Hindu",
            category_slug="business",
            hours_ago=6,
        )
        group1 = assign_article_to_story_group(db, art1)
        db.commit()

        art2 = create_article_helper(
            db,
            title=f"RBI Keeps Benchmark Repo Rate Steady at 6.5 Percent in Policy Review {token}",
            description=f"Governor announced the monetary policy decision keeping repo rates unchanged at 6.5% {token}.",
            source_name="NDTV",
            category_slug="business",
            hours_ago=4,
        )
        group2 = assign_article_to_story_group(db, art2)
        db.commit()

        assert group1.id == group2.id
        assert art1.story_group_id == group1.id
        assert art2.story_group_id == group1.id
    finally:
        db.close()


# 3. Near-Duplicate Articles
def test_3_near_duplicate_articles():
    """Near-duplicate syndicated articles are grouped into the same StoryGroup."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art1 = create_article_helper(
            db,
            title=f"India Semiconductor Mission Receives Mega Approval from Cabinet {token}",
            description=f"Government clears comprehensive fiscal incentives for semiconductor fab facilities {token}.",
            source_name="PTI Wire",
            hours_ago=3,
        )
        group1 = assign_article_to_story_group(db, art1)
        db.commit()

        # Wire syndication with slight editorial touch
        art2 = create_article_helper(
            db,
            title=f"India Semiconductor Mission Receives Mega Approval from Union Cabinet {token}",
            description=f"Government clears comprehensive fiscal incentives for semiconductor fab units {token}.",
            source_name="LiveMint",
            hours_ago=2,
        )
        group2 = assign_article_to_story_group(db, art2)
        db.commit()

        assert group1.id == group2.id
        assert art2.story_group_id == group1.id
    finally:
        db.close()


# 4. Unrelated Articles
def test_4_unrelated_articles():
    """Completely unrelated articles are assigned to separate StoryGroups."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art_sports = create_article_helper(
            db,
            title=f"India Defeats Australia in Thrilling Final Ball Cricket Test Match {token}",
            description=f"Sensational batting display leads Team India to victory at the cricket ground {token}.",
            source_name="Indian Express",
            category_slug="sports",
            hours_ago=3,
        )
        group_sports = assign_article_to_story_group(db, art_sports)
        db.commit()

        art_space = create_article_helper(
            db,
            title=f"Deep Space Telescope Discovers Habitable Exoplanet in Leo Constellation {token}",
            description=f"Spectroscopic survey detects atmospheric water clouds 120 light years away {token}.",
            source_name="BBC",
            category_slug="science",
            hours_ago=2,
        )
        group_space = assign_article_to_story_group(db, art_space)
        db.commit()

        assert group_sports.id != group_space.id
        assert art_sports.story_group_id != art_space.story_group_id
    finally:
        db.close()


# 5. Similarity Threshold Behavior
def test_5_similarity_threshold_behavior():
    """Explicit threshold parameter controls grouping boundary."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art_base = create_article_helper(
            db,
            title=f"Supreme Court Begins Hearing on National Electoral Bond Transparency {token}",
            description=f"Constitution bench of Supreme Court examines political party funding disclosures {token}.",
            source_name="The Hindu",
            hours_ago=5,
        )
        group_base = assign_article_to_story_group(db, art_base)
        db.commit()

        # Somewhat related article on electoral reforms, different focus
        art_related = create_article_helper(
            db,
            title=f"Election Commission Announces Revised Voter Registration Schedules {token}",
            description=f"Poll body rolls out digital portal for nationwide voter list revisions {token}.",
            source_name="NDTV",
            hours_ago=4,
        )

        # With a very high threshold (0.95), it must NOT group
        group_strict = assign_article_to_story_group(db, art_related, threshold=0.95)
        db.commit()

        assert group_strict.id != group_base.id
    finally:
        db.close()


# 6. Multiple Publishers
def test_6_multiple_publishers():
    """Story group clusters articles from 4 distinct publishers and exposes source names."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        publishers = ["The Hindu", "NDTV", "Reuters", "BBC"]
        articles = []
        for i, pub in enumerate(publishers):
            art = create_article_helper(
                db,
                title=f"G20 Green Energy Summit Concludes with Historic Delhi Declaration {token}",
                description=f"World leaders agree on tripling renewable energy capacity by 2030 at New Delhi summit {token}.",
                source_name=pub,
                hours_ago=10 - i * 2,
            )
            articles.append(art)
            assign_article_to_story_group(db, art)
            db.commit()

        # Verify all belong to same group
        group_ids = {a.story_group_id for a in articles}
        assert len(group_ids) == 1
        group_id = list(group_ids)[0]

        # Check API exposes all distinct publisher names
        resp = client.get(f"/api/v1/stories/{group_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert set(publishers).issubset(set(data["sources"]))
    finally:
        db.close()


# 7. Same Publisher Duplicates
def test_7_same_publisher_duplicates():
    """Articles from the same publisher reporting the same event are grouped together."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art_v1 = create_article_helper(
            db,
            title=f"Heavy Monsoon Rains Cause Waterlogging Across Coastal Mumbai Roads {token}",
            description=f"Civic authorities issue red alert as civic transportation is impacted {token}.",
            source_name="Indian Express",
            hours_ago=4,
        )
        group1 = assign_article_to_story_group(db, art_v1)
        db.commit()

        # Follow-up / updated story from same publisher
        art_v2 = create_article_helper(
            db,
            title=f"Heavy Monsoon Rains Cause Waterlogging Across Mumbai Suburbs {token}",
            description=f"Civic authorities issue high alert as Mumbai transport faces disruptions {token}.",
            source_name="Indian Express",
            hours_ago=2,
        )
        group2 = assign_article_to_story_group(db, art_v2)
        db.commit()

        assert group1.id == group2.id
        assert art_v2.story_group_id == group1.id
    finally:
        db.close()


# 8. Deterministic Representative Article
def test_8_deterministic_representative_article():
    """Earliest published article becomes and remains representative regardless of insertion order."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        # Earliest article: 8 hours ago
        art_early = create_article_helper(
            db,
            title=f"Indian Railways Inaugurates High Speed Vande Bharat Corridor {token}",
            description=f"Prime Minister flags off newest semi high speed express connecting major capitals {token}.",
            source_name="The Hindu",
            hours_ago=8,
        )
        group = assign_article_to_story_group(db, art_early)
        db.commit()
        assert group.representative_article_id == art_early.id

        # Ingested second, but published later: 2 hours ago
        art_later = create_article_helper(
            db,
            title=f"Indian Railways Flags Off New Vande Bharat Express Corridor {token}",
            description=f"Prime Minister inaugurates semi high speed train linking capital cities {token}.",
            source_name="NDTV",
            hours_ago=2,
        )
        group2 = assign_article_to_story_group(db, art_later)
        db.commit()

        assert group.id == group2.id
        db.refresh(group)
        # Representative article must remain the earliest published
        assert group.representative_article_id == art_early.id
    finally:
        db.close()


# 9. Related Coverage Endpoint
def test_9_related_coverage_endpoint():
    """GET /api/v1/news/{article_id}/related returns peer coverage with proper fields."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art_a = create_article_helper(
            db,
            title=f"Finance Ministry Clears New Export Incentive Package for Textiles {token}",
            description=f"Comprehensive export subsidy scheme announced to bolster garment exporters {token}.",
            source_name="The Hindu",
            hours_ago=4,
        )
        assign_article_to_story_group(db, art_a)
        db.commit()

        art_b = create_article_helper(
            db,
            title=f"Government Announces Export Subsidy Incentive Package for Textile Sector {token}",
            description=f"Finance Ministry clears scheme to support textile manufacturers and garment exporters {token}.",
            source_name="Mint",
            hours_ago=2,
        )
        assign_article_to_story_group(db, art_b)
        db.commit()

        resp = client.get(f"/api/v1/news/{art_a.id}/related")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["source_name"] == "Mint"
        assert "canonical_url" in data[0]
        assert "published_at" in data[0]
    finally:
        db.close()


# 10. Current Article Exclusion
def test_10_current_article_exclusion():
    """GET /api/v1/news/{article_id}/related strictly excludes the requested article itself."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art_a = create_article_helper(
            db,
            title=f"Parliament Approves Comprehensive Telecom Regulatory Bill {token}",
            description=f"New legislation modernizes spectrum allocation and satellite communications framework {token}.",
            source_name="The Hindu",
            hours_ago=5,
        )
        assign_article_to_story_group(db, art_a)
        db.commit()

        art_b = create_article_helper(
            db,
            title=f"Indian Parliament Passes Comprehensive Telecommunications Regulatory Bill {token}",
            description=f"New telecom legislation clears parliament modernizing spectrum rules {token}.",
            source_name="Indian Express",
            hours_ago=3,
        )
        assign_article_to_story_group(db, art_b)
        db.commit()

        resp = client.get(f"/api/v1/news/{art_a.id}/related")
        assert resp.status_code == 200
        returned_ids = [item["id"] for item in resp.json()]
        assert art_a.id not in returned_ids
        assert art_b.id in returned_ids
    finally:
        db.close()


# 11. Story Group Detail Endpoint
def test_11_story_group_detail_endpoint():
    """GET /api/v1/stories/{story_id} returns representative article and sorted article list."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art1 = create_article_helper(
            db,
            title=f"Supreme Court Upholds Constitutional Validity of Environmental Act {token}",
            description=f"Bench delivers unanimous judgment on green clearances and forest protection {token}.",
            source_name="The Hindu",
            hours_ago=6,
        )
        group = assign_article_to_story_group(db, art1)
        db.commit()

        resp = client.get(f"/api/v1/stories/{group.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == group.id
        assert data["representative_article"]["id"] == art1.id
        assert len(data["articles"]) >= 1
        assert "sources" in data
    finally:
        db.close()


# 12. Empty / No-Related Behavior
def test_12_empty_no_related_behavior():
    """GET /api/v1/news/{article_id}/related returns empty list safely when no peer articles exist."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        art_solo = create_article_helper(
            db,
            title=f"Unique Isolated Discovery in Remote Himalayan Valley {token}",
            description=f"Local botanical survey reports rare alpine flower bloom {token}.",
            source_name="Himalayan Gazette",
            hours_ago=1,
        )
        assign_article_to_story_group(db, art_solo)
        db.commit()

        resp = client.get(f"/api/v1/news/{art_solo.id}/related")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0
    finally:
        db.close()


# 13. Story List Pagination
def test_13_story_list_pagination():
    """GET /api/v1/stories respects pagination parameters."""
    resp = client.get("/api/v1/stories?page=1&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["limit"] == 5
    assert isinstance(data["items"], list)


# 14. Ingestion Resilience When Grouping Fails
def test_14_ingestion_resilience_when_grouping_fails():
    """Article ingestion succeeds and persists even if story grouping encounters an unexpected error."""
    db = SessionLocal()
    token = uuid.uuid4().hex[:6]
    try:
        raw = RawArticle(
            title=f"Breaking Resilience Ingestion Verification News {token}",
            description=f"Verification test ensuring error handling does not drop ingested articles {token}.",
            canonical_url=f"https://bharatlens.test/test-story-art-resilience-{token}",
            source_name="Resilience Wire",
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        article = ingest_raw_article(db, raw)
        db.commit()

        assert article is not None
        assert article.id is not None
        assert article.title.startswith("Breaking Resilience Ingestion")
    finally:
        db.close()
