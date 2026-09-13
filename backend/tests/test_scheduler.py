from datetime import datetime, timezone
from typing import List, Optional
from fastapi.testclient import TestClient
from app.main import app
from app.services.scheduler import (
    IngestionStatusTracker,
    scheduled_ingestion_job,
    start_news_scheduler,
    stop_news_scheduler,
    ingestion_tracker,
    _ingest_lock,
)
from app.services.news_provider import BaseNewsProvider, RawArticle

client = TestClient(app)


class MockSchedulerNewsProvider(BaseNewsProvider):
    """Mock News Provider for deterministic scheduler testing."""

    def __init__(self, articles: List[RawArticle], raise_error: bool = False):
        self.articles = articles
        self.raise_error = raise_error

    def fetch_india_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        if self.raise_error:
            raise RuntimeError("Simulated news provider network error")
        return [a for a in self.articles if a.country_hint == "IN"]

    def fetch_international_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        if self.raise_error:
            raise RuntimeError("Simulated news provider network error")
        return [a for a in self.articles if a.country_hint == "GLOBAL"]


def test_ingestion_status_tracker():
    tracker = IngestionStatusTracker()
    assert tracker.is_running is False
    assert tracker.last_started_at is None

    tracker.mark_started()
    assert tracker.is_running is True
    assert tracker.last_started_at is not None

    tracker.mark_completed(fetched=20, saved=5, duplicates=15, success=True)
    assert tracker.is_running is False
    assert tracker.last_completed_at is not None
    assert tracker.last_saved_count == 5
    assert tracker.last_duplicate_count == 15
    assert tracker.last_success is True
    assert tracker.last_error is None

    status = tracker.get_status()
    assert status["is_running"] is False
    assert status["last_saved_count"] == 5
    assert "interval_minutes" in status


def test_scheduled_ingestion_job_execution():
    sample_articles = [
        RawArticle(
            title="Scheduler Ingestion Test Article 1",
            description="Testing background scheduler automatic ingestion execution.",
            canonical_url="https://example.com/scheduler-test-article-1",
            source_name="The Hindu",
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
            country_hint="IN",
        ),
        RawArticle(
            title="Scheduler Ingestion Test Article 2",
            description="Testing international background scheduler article.",
            canonical_url="https://example.com/scheduler-test-article-2",
            source_name="BBC World",
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
            country_hint="GLOBAL",
        ),
    ]

    provider = MockSchedulerNewsProvider(sample_articles)
    scheduled_ingestion_job(provider=provider)

    # Verify tracker updated
    status = ingestion_tracker.get_status()
    assert status["last_completed_at"] is not None
    assert status["last_success"] is True
    assert status["is_running"] is False


def test_concurrency_lock_prevents_overlapping_runs():
    # Artificially acquire the lock
    _ingest_lock.acquire()
    try:
        # A second invocation should detect lock and skip immediately without error
        provider = MockSchedulerNewsProvider([])
        scheduled_ingestion_job(provider=provider)
    finally:
        _ingest_lock.release()


def test_failure_isolation_on_provider_error():
    # If the provider raises an exception, the job must isolate it, record error in tracker, and release lock
    error_provider = MockSchedulerNewsProvider([], raise_error=True)
    scheduled_ingestion_job(provider=error_provider)

    status = ingestion_tracker.get_status()
    assert status["last_success"] is False
    assert "Simulated news provider network error" in str(status["last_error"])
    assert _ingest_lock.locked() is False


def test_scheduler_lifecycle():
    # Start and stop scheduler
    start_news_scheduler()
    stop_news_scheduler()


def test_health_endpoint_reports_ingestion_telemetry():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "ingestion" in data
    ingestion = data["ingestion"]
    assert "scheduler_enabled" in ingestion
    assert "interval_minutes" in ingestion
    assert "is_running" in ingestion
    assert "last_success" in ingestion
