import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import utc_now
from app.db.query_filters import apply_demo_filter
from app.models.article import Article
from app.models.reading_event import ReadingEvent
from app.schemas.article import PaginatedArticlesResponse
from app.recommendation.profile import build_user_profile
from app.recommendation.scoring import calculate_article_score

logger = logging.getLogger("bharatlens.recommendation.service")


def apply_category_diversity(articles: List[Article], max_consecutive: int = 2) -> List[Article]:
    """Reorders articles to avoid long clusters of the same category.
    
    If more than `max_consecutive` articles of the same category appear in a row,
    we look ahead for the next article from a different category to insert.
    """
    if len(articles) <= 2:
        return articles

    result: List[Article] = []
    remaining = list(articles)

    while remaining:
        # Check current consecutive streak of the same category at the end of result
        current_streak_category = None
        streak_count = 0
        if len(result) >= max_consecutive:
            last_cats = [
                a.category.slug if a.category else "general"
                for a in result[-max_consecutive:]
            ]
            if len(set(last_cats)) == 1:
                current_streak_category = last_cats[0]
                streak_count = max_consecutive

        chosen_idx = 0
        if streak_count >= max_consecutive and current_streak_category is not None:
            # Find the first item with a different category
            found_different = False
            for idx, candidate in enumerate(remaining):
                cand_cat = candidate.category.slug if candidate.category else "general"
                if cand_cat != current_streak_category:
                    chosen_idx = idx
                    found_different = True
                    break
            # If no different category remains, just pick the top item
            if not found_different:
                chosen_idx = 0

        result.append(remaining.pop(chosen_idx))

    return result


def get_personalized_recommendations(
    db: Session,
    user_id: int,
    page: int = 1,
    limit: int = 10,
    now: Optional[datetime] = None,
) -> PaginatedArticlesResponse:
    """Generate personalized news feed for an authenticated user.
    
    Workflow:
    1. Build user profile (or trigger cold-start fallback if < 3 signals).
    2. Retrieve candidates from last 14 days (excluding recently read articles).
    3. Score each candidate based on category affinity (70%) + freshness (30%).
    4. Enforce category diversity (max 2 consecutive from same category).
    5. Return paginated articles.
    """
    current_time = now or utc_now()

    # 1. Build profile
    user_profile = build_user_profile(db=db, user_id=user_id, now=current_time)

    # 2. Cold-start fallback if no profile could be constructed
    if not user_profile:
        logger.info(f"User {user_id} in cold-start mode. Returning chronologically fresh articles.")
        query = apply_demo_filter(db.query(Article))
        total = query.count()
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        offset = (page - 1) * limit

        items = (
            query.options(joinedload(Article.source), joinedload(Article.category))
            .order_by(Article.published_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return PaginatedArticlesResponse(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            items=items,
        )

    # 3. Profile exists: Candidate selection
    candidate_window_start = current_time - timedelta(days=14)

    # Fetch recently read article IDs by this user (past 7 days)
    read_cutoff = current_time - timedelta(days=7)
    read_article_ids = set(
        row[0]
        for row in db.query(ReadingEvent.article_id)
        .filter(
            ReadingEvent.user_id == user_id,
            ReadingEvent.event_type == "read",
            ReadingEvent.created_at >= read_cutoff,
        )
        .all()
    )

    # Query candidate articles within window
    candidates_query = (
        apply_demo_filter(db.query(Article))
        .options(joinedload(Article.source), joinedload(Article.category))
        .filter(Article.published_at >= candidate_window_start)
    )

    candidates = candidates_query.all()

    # If candidate pool is too small (< 10), relax window to last 60 days
    if len(candidates) < 10:
        candidates = (
            apply_demo_filter(db.query(Article))
            .options(joinedload(Article.source), joinedload(Article.category))
            .filter(Article.published_at >= (current_time - timedelta(days=60)))
            .all()
        )

    # Filter out already read articles unless pool becomes critically small
    filtered_candidates = [c for c in candidates if c.id not in read_article_ids]
    if len(filtered_candidates) < 5 and candidates:
        filtered_candidates = candidates

    # 4. Score candidates
    scored_candidates = []
    for cand in filtered_candidates:
        score = calculate_article_score(cand, user_profile, now=current_time)
        scored_candidates.append((cand, score))

    # Sort candidates by score descending, then by publication timestamp descending
    scored_candidates.sort(
        key=lambda x: (x[1], x[0].published_at.timestamp() if x[0].published_at else 0.0),
        reverse=True,
    )

    sorted_articles = [item[0] for item in scored_candidates]

    # 5. Apply Category Diversity Filter
    diversified_articles = apply_category_diversity(sorted_articles, max_consecutive=2)

    # 6. Pagination
    total = len(diversified_articles)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    offset = (page - 1) * limit
    paginated_items = diversified_articles[offset : offset + limit]

    return PaginatedArticlesResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=paginated_items,
    )
