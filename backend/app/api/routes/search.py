from typing import Optional
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.db.database import get_db
from app.db.query_filters import apply_demo_filter
from app.models.article import Article
from app.models.category import Category
from app.schemas.article import PaginatedArticlesResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=PaginatedArticlesResponse, summary="Search Stored Articles")
def search_articles(
    q: Optional[str] = Query(None, description="Search keyword matching title or description"),
    region: Optional[str] = Query(None, description="Filter by region: 'INDIA' or 'INTERNATIONAL'"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. 'en', 'te', 'ta', 'hi')"),
    date: Optional[str] = Query(None, description="Filter by date in YYYY-MM-DD format"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Database-powered case-insensitive search across stored article headlines and summaries."""
    # If search query is missing or whitespace only, return empty result set safely
    if not q or not q.strip():
        return PaginatedArticlesResponse(
            page=page,
            limit=limit,
            total=0,
            total_pages=1,
            items=[],
        )

    clean_q = q.strip()
    query = apply_demo_filter(
        db.query(Article).filter(
            or_(
                Article.title.ilike(f"%{clean_q}%"),
                Article.description.ilike(f"%{clean_q}%"),
            )
        )
    )

    # Optional Date filter
    if date:
        try:
            target_date = datetime.strptime(date.strip(), "%Y-%m-%d").date()
            start_dt = datetime.combine(target_date, time.min)
            end_dt = datetime.combine(target_date, time.max)
            query = query.filter(Article.published_at >= start_dt, Article.published_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format '{date}'. Expected YYYY-MM-DD (e.g. 2026-09-05).",
            )

    # Region filter
    if region and region.upper() != "ALL":
        query = query.filter(Article.region == region.upper())

    # State filter
    if state and state.upper() != "ALL":
        query = query.filter(Article.state.ilike(f"%{state}%"))

    # Language filter
    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    # Category filter
    if category and category.upper() != "ALL":
        query = query.join(Category).filter(Category.slug == category.lower())

    # Sorting & Pagination
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
