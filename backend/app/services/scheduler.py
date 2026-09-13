import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.db.database import SessionLocal
from app.services.ingest import run_ingestion
from app.services.news_provider import BaseNewsProvider, NewsAPIProvider

logger = logging.getLogger("bharatlens.scheduler")

# Process-local concurrency lock to prevent overlapping ingestion runs
_ingest_lock = threading.Lock()
_scheduler: Optional[BackgroundScheduler] = None


class IngestionStatusTracker:
    """Thread-safe in-memory status tracker for news ingestion."""

    def __init__(self):
        self._lock = threading.Lock()
        self.last_started_at: Optional[datetime] = None
        self.last_completed_at: Optional[datetime] = None
        self.last_success: bool = True
        self.last_error: Optional[str] = None
        self.last_fetched_count: int = 0
        self.last_saved_count: int = 0
        self.last_duplicate_count: int = 0
        self.is_running: bool = False

    def mark_started(self):
        with self._lock:
            self.last_started_at = utc_now()
            self.is_running = True

    def mark_completed(self, fetched: int, saved: int, duplicates: int, success: bool = True, error: Optional[str] = None):
        with self._lock:
            self.last_completed_at = utc_now()
            self.last_fetched_count = fetched
            self.last_saved_count = saved
            self.last_duplicate_count = duplicates
            self.last_success = success
            self.last_error = error
            self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "scheduler_enabled": settings.ENABLE_NEWS_SCHEDULER,
                "interval_minutes": settings.NEWS_INGEST_INTERVAL_MINUTES,
                "is_running": self.is_running,
                "last_started_at": self.last_started_at.isoformat() if self.last_started_at else None,
                "last_completed_at": self.last_completed_at.isoformat() if self.last_completed_at else None,
                "last_success": self.last_success,
                "last_error": self.last_error,
                "last_saved_count": self.last_saved_count,
                "last_duplicate_count": self.last_duplicate_count,
            }


# Global Ingestion Tracker Singleton
ingestion_tracker = IngestionStatusTracker()


def scheduled_ingestion_job(provider: Optional[BaseNewsProvider] = None):
    """Execute a single ingestion run with concurrency locking and error isolation."""
    # Attempt to acquire process-local lock without blocking
    acquired = _ingest_lock.acquire(blocking=False)
    if not acquired:
        logger.warning("[!] Previous ingestion job is still in progress. Skipping this scheduled interval.")
        return

    ingestion_tracker.mark_started()
    start_time = utc_now()
    logger.info("==================================================")
    logger.info("  BharatLens Background News Ingestion Started   ")
    logger.info(f"  Time: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("==================================================")

    db = SessionLocal()
    try:
        stats = run_ingestion(
            db=db,
            provider=provider,
            provider_type="all",
            fetch_india=True,
            fetch_international=True,
            limit=15,  # Balanced per-run batch size to stay well under API rate limits
        )

        has_blocking_error = stats.get("saved", 0) == 0 and stats.get("duplicates", 0) == 0 and stats.get("error")
        ingestion_tracker.mark_completed(
            fetched=stats.get("fetched", 0),
            saved=stats.get("saved", 0),
            duplicates=stats.get("duplicates", 0),
            success=not bool(has_blocking_error),
            error=stats.get("error") if has_blocking_error else None,
        )

        logger.info("==================================================")
        logger.info(f"  Ingestion Finished Successfully in {(utc_now() - start_time).total_seconds():.1f}s")
        logger.info(f"  Saved: {stats.get('saved', 0)} | Duplicates: {stats.get('duplicates', 0)} | Fetched: {stats.get('fetched', 0)}")
        logger.info("==================================================")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[!] Background ingestion failed: {error_msg}")
        ingestion_tracker.mark_completed(
            fetched=0,
            saved=0,
            duplicates=0,
            success=False,
            error=error_msg,
        )
    finally:
        db.close()
        _ingest_lock.release()


def start_news_scheduler():
    """Initialize and start the APScheduler background scheduler."""
    global _scheduler
    if not settings.ENABLE_NEWS_SCHEDULER:
        logger.info("[*] Background news scheduler is disabled via configuration.")
        return

    if _scheduler is not None and _scheduler.running:
        logger.info("[*] News scheduler is already running.")
        return

    _scheduler = BackgroundScheduler(daemon=True)

    # Register periodic interval job
    interval_minutes = max(1, settings.NEWS_INGEST_INTERVAL_MINUTES)
    _scheduler.add_job(
        scheduled_ingestion_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="bharatlens_news_ingestion",
        name="Periodic News Ingestion Job",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info(f"[*] BharatLens news scheduler started. Interval: every {interval_minutes} minutes.")

    # Trigger optional immediate initial ingestion in background thread so server starts without delay
    if settings.NEWS_INGEST_ON_STARTUP:
        logger.info("[*] Triggering initial startup news ingestion in background...")
        startup_thread = threading.Thread(target=scheduled_ingestion_job, daemon=True, name="StartupNewsIngest")
        startup_thread.start()


def stop_news_scheduler():
    """Cleanly shut down the APScheduler background scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[*] BharatLens news scheduler stopped.")
    _scheduler = None
