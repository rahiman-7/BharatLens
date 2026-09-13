import math
import logging
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import utc_now
from app.models.reading_event import ReadingEvent
from app.models.bookmark import Bookmark
from app.models.article import Article

logger = logging.getLogger("bharatlens.recommendation.profile")


def build_user_profile(
    db: Session,
    user_id: int,
    min_events: int = 3,
    max_events: int = 100,
    recency_half_life_days: float = 7.0,
    now: Optional[datetime] = None,
) -> Optional[Dict[str, float]]:
    """Build a content-based user interest profile over BharatLens categories.
    
    Returns:
        Dict mapping category slug to normalized interest probability (sums to 1.0),
        or None if user has insufficient interaction history (< min_events).
    """
    current_time = now or utc_now()

    # 1. Fetch recent reading events (capped to max_events for fast O(1) performance)
    events = (
        db.query(ReadingEvent)
        .filter(ReadingEvent.user_id == user_id)
        .options(joinedload(ReadingEvent.article).joinedload(Article.category))
        .order_by(ReadingEvent.created_at.desc())
        .limit(max_events)
        .all()
    )

    # 2. Fetch bookmarks as positive supporting signals
    bookmarks = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == user_id)
        .options(joinedload(Bookmark.article).joinedload(Article.category))
        .order_by(Bookmark.created_at.desc())
        .limit(30)
        .all()
    )

    total_signals = len(events) + len(bookmarks)
    if total_signals < min_events:
        logger.debug(f"User {user_id} has {total_signals} signals (< {min_events}). Triggering cold start.")
        return None

    category_scores: Dict[str, float] = {}

    # Process reading events
    for event in events:
        if not event.article or not event.article.category:
            continue

        cat_slug = event.article.category.slug

        # Base event weight
        if event.event_type == "read":
            dwell = max(0, min(event.dwell_time_seconds, 300))
            event_weight = 1.0 + (dwell / 120.0)  # 1.0 to 3.5
        elif event.event_type == "view":
            event_weight = 0.25
        else:
            event_weight = 0.50

        # Recency decay (7-day exponential decay)
        delta_days = max(0.0, (current_time - event.created_at).total_seconds() / 86400.0)
        recency_factor = math.exp(-delta_days / recency_half_life_days)

        effective_score = event_weight * recency_factor
        category_scores[cat_slug] = category_scores.get(cat_slug, 0.0) + effective_score

    # Process bookmarks (positive affinity boost)
    for bm in bookmarks:
        if not bm.article or not bm.article.category:
            continue

        cat_slug = bm.article.category.slug
        delta_days = max(0.0, (current_time - bm.created_at).total_seconds() / 86400.0)
        recency_factor = math.exp(-delta_days / recency_half_life_days)

        # Bookmarks act as a gentle supporting positive signal (base weight = 1.0)
        # Note: Active reading events carry higher weight (1.0 to 3.5 based on dwell duration),
        # ensuring reading behavior remains the dominant signal.
        effective_score = 1.0 * recency_factor
        category_scores[cat_slug] = category_scores.get(cat_slug, 0.0) + effective_score

    if not category_scores:
        return None

    # Normalize category scores to probability distribution summing to 1.0
    total_score = sum(category_scores.values())
    if total_score <= 0.0:
        return None

    normalized_profile = {
        cat: round(score / total_score, 4)
        for cat, score in category_scores.items()
    }

    logger.debug(f"Computed user {user_id} interest profile: {normalized_profile}")
    return normalized_profile
