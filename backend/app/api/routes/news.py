from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.db.database import get_db
from app.db.query_filters import apply_demo_filter
from app.models.article import Article
from app.models.category import Category
from app.models.user import User
from app.models.story_group import StoryGroup
from app.api.deps import get_current_user
from app.recommendation.service import get_personalized_recommendations
from app.schemas.article import ArticleResponse, PaginatedArticlesResponse
from app.schemas.story import StoryArticleSummary
from app.services.story_grouping import serialize_article_summary

router = APIRouter(prefix="/news", tags=["News"])


def paginate_articles(
    query,
    page: int = 1,
    limit: int = 10,
) -> PaginatedArticlesResponse:
    """Helper function to paginate SQLAlchemy article queries."""
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


@router.get("/latest", response_model=PaginatedArticlesResponse, summary="Get Latest News Feed")
def get_latest_news(
    region: Optional[str] = Query(None, description="Filter by region: 'INDIA' or 'INTERNATIONAL'"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. 'en', 'te', 'ta', 'hi')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = apply_demo_filter(db.query(Article))

    if region and region.upper() != "ALL":
        query = query.filter(Article.region == region.upper())
    
    if state and state.upper() != "ALL":
        query = query.filter(Article.state.ilike(f"%{state}%"))
        
    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    if category and category.lower() != "all":
        query = query.join(Category).filter(Category.slug == category.lower().strip())

    return paginate_articles(query, page=page, limit=limit)


@router.get("/india", response_model=PaginatedArticlesResponse, summary="Get India Focus News")
def get_india_news(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. 'en', 'te', 'ta', 'hi')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = apply_demo_filter(db.query(Article)).filter(Article.region == "INDIA")

    if state and state.upper() != "ALL":
        query = query.filter(Article.state.ilike(f"%{state}%"))

    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    if category and category.lower() != "all":
        query = query.join(Category).filter(Category.slug == category.lower().strip())

    return paginate_articles(query, page=page, limit=limit)


@router.get("/state/{state_slug}", response_model=PaginatedArticlesResponse, summary="Get News by Indian State Slug")
def get_state_news(
    state_slug: str,
    category: Optional[str] = Query(None, description="Filter by category slug"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. 'te', 'ta', 'en')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    from app.core.state_languages import get_state_by_slug
    state_meta = get_state_by_slug(state_slug)
    state_name = state_meta.name if state_meta else state_slug.replace("-", " ").title()

    query = apply_demo_filter(db.query(Article)).filter(
        Article.region == "INDIA",
        Article.state.ilike(f"%{state_name}%"),
    )

    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    if category and category.lower() != "all":
        query = query.join(Category).filter(Category.slug == category.lower().strip())

    return paginate_articles(query, page=page, limit=limit)


@router.get("/international", response_model=PaginatedArticlesResponse, summary="Get International News")
def get_international_news(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = apply_demo_filter(db.query(Article)).filter(Article.region == "INTERNATIONAL")

    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    if category and category.lower() != "all":
        query = query.join(Category).filter(Category.slug == category.lower().strip())

    return paginate_articles(query, page=page, limit=limit)


@router.get("/category/{slug}", response_model=PaginatedArticlesResponse, summary="Get News by Category")
def get_category_news(
    slug: str,
    region: Optional[str] = Query(None, description="Filter by region: 'INDIA' or 'INTERNATIONAL'"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    # Verify category exists
    cat = db.query(Category).filter(Category.slug == slug.lower()).first()
    if not cat:
        raise HTTPException(status_code=404, detail=f"Category '{slug}' not found")

    query = apply_demo_filter(db.query(Article)).filter(Article.category_id == cat.id)

    if region and region.upper() != "ALL":
        query = query.filter(Article.region == region.upper())

    if state and state.upper() != "ALL":
        query = query.filter(Article.state.ilike(f"%{state}%"))

    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    return paginate_articles(query, page=page, limit=limit)


@router.get("/for-you", response_model=PaginatedArticlesResponse, summary="Get Personalized News Feed")
def get_for_you_news(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_personalized_recommendations(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit,
    )


@router.get("/{article_id}", response_model=ArticleResponse, summary="Get Single Article by ID")
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
):
    query = apply_demo_filter(db.query(Article))
    article = (
        query
        .options(joinedload(Article.source), joinedload(Article.category))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found")

    return article


@router.get("/{article_id}/related", response_model=List[StoryArticleSummary], summary="Get Related Multi-Source Coverage")
def get_related_coverage(
    article_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve other news articles covering the same story cluster, excluding the current article."""
    query = apply_demo_filter(db.query(Article))
    article = (
        query
        .options(
            joinedload(Article.story_group).joinedload(StoryGroup.articles).joinedload(Article.source),
            joinedload(Article.story_group).joinedload(StoryGroup.articles).joinedload(Article.category),
        )
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found")

    if not article.story_group or not article.story_group.articles:
        return []

    # Exclude the current article and demo articles (unless enabled), sort by published_at DESC
    peer_articles = [
        a for a in article.story_group.articles
        if a.id != article_id and (settings.SHOW_DEMO_ARTICLES or not a.is_demo)
    ]
    peer_articles.sort(
        key=lambda a: a.published_at.timestamp() if a.published_at else 0.0,
        reverse=True,
    )

    return [serialize_article_summary(a) for a in peer_articles]

