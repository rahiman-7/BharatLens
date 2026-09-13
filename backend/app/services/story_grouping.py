import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.models.article import Article
from app.models.story_group import StoryGroup
from app.ml.similarity import calculate_similarity
from app.schemas.story import StoryArticleSummary, StoryGroupResponse, StoryGroupDetailResponse

logger = logging.getLogger("bharatlens.services.story_grouping")

# Empirically validated similarity threshold for story clustering (TF-IDF Cosine Similarity)
# Identical: 1.0, Near-Duplicates: 0.85-0.95, Multi-outlet same event: 0.55-0.85, Unrelated: 0.00-0.20
STORY_GROUP_SIMILARITY_THRESHOLD: float = settings.STORY_GROUP_SIMILARITY_THRESHOLD
CANDIDATE_WINDOW_DAYS: int = settings.STORY_GROUP_CANDIDATE_WINDOW_DAYS


def serialize_article_summary(article: Article) -> StoryArticleSummary:
    """Format an Article model into a safe StoryArticleSummary schema."""
    words = (len(article.description.split()) if article.description else 0) + len(article.title.split())
    read_time = max(1, round(words / 50))  # ~200 WPM

    source_name = article.source.name if article.source else "Independent Wire"
    category_name = article.category.name if article.category else "General"
    category_slug = article.category.slug if article.category else "politics"

    return StoryArticleSummary(
        id=article.id,
        title=article.title,
        description=article.description,
        canonical_url=article.canonical_url,
        url=article.canonical_url,
        image_url=article.image_url,
        author=article.author,
        region=article.region or "INDIA",
        state=article.state,
        language_code=getattr(article, "language_code", "en") or "en",
        published_at=article.published_at,
        source_name=source_name,
        category_name=category_name,
        category_slug=category_slug,
        read_time_minutes=read_time,
    )


def serialize_story_group(story_group: StoryGroup) -> StoryGroupResponse:
    """Serialize StoryGroup into StoryGroupResponse with distinct source names."""
    all_articles = story_group.articles or []
    articles = [a for a in all_articles if settings.SHOW_DEMO_ARTICLES or not getattr(a, 'is_demo', False)]
    sources = list(dict.fromkeys([
        a.source.name for a in articles if a.source
    ]))

    rep_article = story_group.representative_article
    if rep_article and (settings.SHOW_DEMO_ARTICLES or not getattr(rep_article, 'is_demo', False)):
        rep_summary = serialize_article_summary(rep_article)
    else:
        rep_summary = serialize_article_summary(articles[0]) if articles else None

    return StoryGroupResponse(
        id=story_group.id,
        representative_article=rep_summary,
        article_count=len(articles),
        sources=sources,
        created_at=story_group.created_at,
        updated_at=story_group.updated_at,
    )


def serialize_story_group_detail(story_group: StoryGroup) -> StoryGroupDetailResponse:
    """Serialize StoryGroup into detailed response containing all articles sorted by published_at DESC."""
    all_articles = list(story_group.articles or [])
    articles = [a for a in all_articles if settings.SHOW_DEMO_ARTICLES or not getattr(a, 'is_demo', False)]
    articles.sort(
        key=lambda a: a.published_at.timestamp() if a.published_at else 0.0,
        reverse=True,
    )

    sources = list(dict.fromkeys([
        a.source.name for a in articles if a.source
    ]))

    rep_article = story_group.representative_article
    if rep_article and (settings.SHOW_DEMO_ARTICLES or not getattr(rep_article, 'is_demo', False)):
        rep_summary = serialize_article_summary(rep_article)
    else:
        rep_summary = serialize_article_summary(articles[0]) if articles else None

    serialized_articles = [serialize_article_summary(a) for a in articles]

    return StoryGroupDetailResponse(
        id=story_group.id,
        representative_article=rep_summary,
        article_count=len(articles),
        sources=sources,
        articles=serialized_articles,
        created_at=story_group.created_at,
        updated_at=story_group.updated_at,
    )


def update_representative_article(story_group: StoryGroup) -> None:
    """Deterministically select representative article as the one with earliest publication timestamp."""
    if not story_group.articles:
        return

    # Sort deterministically by published_at ASC, then ID ASC
    sorted_articles = sorted(
        story_group.articles,
        key=lambda a: (a.published_at.timestamp() if a.published_at else 0.0, a.id or 0),
    )
    story_group.representative_article = sorted_articles[0]
    story_group.representative_article_id = sorted_articles[0].id


def assign_article_to_story_group(
    db: Session,
    article: Article,
    threshold: float = STORY_GROUP_SIMILARITY_THRESHOLD,
    candidate_days: int = CANDIDATE_WINDOW_DAYS,
    now: Optional[datetime] = None,
) -> StoryGroup:
    """Group an ingested article into an existing StoryGroup if sufficiently similar, or create a new one.
    
    Workflow:
    1. Query bounded pool of recent articles within candidate_days window.
    2. Compute TF-IDF cosine similarity against candidate titles and descriptions.
    3. If max similarity >= threshold:
       - Attach article to the matched candidate's StoryGroup (or create group for both).
       - Maintain earliest article as deterministic representative.
    4. If no match found:
       - Create new StoryGroup with this article as representative.
    """
    current_time = now or utc_now()
    window_start = current_time - timedelta(days=candidate_days)

    # 1. Fetch recent candidate articles within window (excluding this article itself if already has ID)
    candidates_query = (
        db.query(Article)
        .options(
            joinedload(Article.source),
            joinedload(Article.category),
            joinedload(Article.story_group).joinedload(StoryGroup.articles),
        )
        .filter(Article.published_at >= window_start)
    )
    if article.id:
        candidates_query = candidates_query.filter(Article.id != article.id)

    candidates: List[Article] = candidates_query.all()

    best_candidate: Optional[Article] = None
    best_similarity: float = 0.0

    # 2. Compare similarity
    for candidate in candidates:
        sim = calculate_similarity(
            text_a=article.title,
            text_b=candidate.title,
            description_a=article.description,
            description_b=candidate.description,
        )
        if sim > best_similarity:
            best_similarity = sim
            best_candidate = candidate

    candidate_title = best_candidate.title[:30] if best_candidate else "None"
    logger.debug(
        f"Article '{article.title[:30]}' best similarity: {best_similarity:.4f} "
        f"(with '{candidate_title}')"
    )

    # 3. Match found
    if best_similarity >= threshold and best_candidate is not None:
        target_group = best_candidate.story_group
        if not target_group:
            target_group = StoryGroup(
                representative_article_id=best_candidate.id,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(target_group)
            db.flush()
            best_candidate.story_group_id = target_group.id

        article.story_group_id = target_group.id
        target_group.updated_at = utc_now()

        # Update representative deterministically (earliest publication date)
        all_group_articles = list(target_group.articles or [])
        if article not in all_group_articles:
            all_group_articles.append(article)
        
        earliest_article = min(
            all_group_articles,
            key=lambda a: (a.published_at.timestamp() if a.published_at else 0.0, a.id or 0),
        )
        target_group.representative_article_id = earliest_article.id
        db.flush()
        logger.info(
            f"[StoryGroup] Grouped article #{article.id} into StoryGroup #{target_group.id} "
            f"(Similarity: {best_similarity:.4f} with Article #{best_candidate.id})"
        )
        return target_group

    # 4. No match found -> create new StoryGroup
    new_group = StoryGroup(
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(new_group)
    db.flush()

    article.story_group_id = new_group.id
    new_group.representative_article_id = article.id
    db.flush()

    logger.debug(f"[StoryGroup] Created new StoryGroup #{new_group.id} for article #{article.id}")
    return new_group
