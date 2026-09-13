import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.db.database import get_db
from app.models.story_group import StoryGroup
from app.models.article import Article
from app.schemas.story import (
    StoryGroupResponse,
    StoryGroupDetailResponse,
    PaginatedStoriesResponse,
)
from app.services.story_grouping import serialize_story_group, serialize_story_group_detail

logger = logging.getLogger("bharatlens.api.stories")

router = APIRouter(prefix="/stories", tags=["Story Groups"])


@router.get("", response_model=PaginatedStoriesResponse, summary="Get Paginated Story Clusters")
def get_stories(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    min_articles: int = Query(1, ge=1, description="Filter by minimum clustered articles"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated story groups with representative headlines and multi-source coverage summaries."""
    query = (
        db.query(StoryGroup)
        .options(
            joinedload(StoryGroup.representative_article).joinedload(Article.source),
            joinedload(StoryGroup.representative_article).joinedload(Article.category),
            joinedload(StoryGroup.articles).joinedload(Article.source),
            joinedload(StoryGroup.articles).joinedload(Article.category),
        )
        .order_by(StoryGroup.updated_at.desc())
    )

    all_groups = query.all()
    # Filter by minimum articles and demo isolation
    filtered_groups = []
    for g in all_groups:
        articles = [a for a in (g.articles or []) if settings.SHOW_DEMO_ARTICLES or not a.is_demo]
        if not articles:
            continue
        rep = g.representative_article
        if not settings.SHOW_DEMO_ARTICLES and rep and rep.is_demo:
            continue
        if len(articles) >= min_articles:
            filtered_groups.append(g)

    total = len(filtered_groups)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    offset = (page - 1) * limit
    page_items = filtered_groups[offset : offset + limit]

    serialized_items = [serialize_story_group(g) for g in page_items]

    return PaginatedStoriesResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=serialized_items,
    )


@router.get("/{story_id}", response_model=StoryGroupDetailResponse, summary="Get Single Story Group Coverage")
def get_story(
    story_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full multi-source coverage timeline for a specific story group."""
    story_group = (
        db.query(StoryGroup)
        .options(
            joinedload(StoryGroup.representative_article).joinedload(Article.source),
            joinedload(StoryGroup.representative_article).joinedload(Article.category),
            joinedload(StoryGroup.articles).joinedload(Article.source),
            joinedload(StoryGroup.articles).joinedload(Article.category),
        )
        .filter(StoryGroup.id == story_id)
        .first()
    )

    if not story_group:
        raise HTTPException(status_code=404, detail=f"Story group with ID {story_id} not found")

    if not settings.SHOW_DEMO_ARTICLES:
        if story_group.representative_article and story_group.representative_article.is_demo:
            raise HTTPException(status_code=404, detail=f"Story group with ID {story_id} not found")
        live_articles = [a for a in (story_group.articles or []) if not a.is_demo]
        if not live_articles:
            raise HTTPException(status_code=404, detail=f"Story group with ID {story_id} not found")

    return serialize_story_group_detail(story_group)
