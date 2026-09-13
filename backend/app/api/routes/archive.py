from typing import Optional, List
from datetime import datetime, time
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.db.query_filters import apply_demo_filter
from app.models.article import Article
from app.models.category import Category
from app.schemas.article import PaginatedArticlesResponse

router = APIRouter(prefix="/archive", tags=["Archive"])


class ArchiveDateInfo(BaseModel):
    date: str
    article_count: int


@router.get("/dates", response_model=List[ArchiveDateInfo], summary="Get Available Archive Dates")
def get_archive_dates(
    limit: int = Query(30, ge=1, le=100, description="Max number of distinct archive dates to return"),
    db: Session = Depends(get_db),
):
    """Retrieve distinct publication dates that contain at least one stored visible article, ordered newest first."""
    query = apply_demo_filter(db.query(Article))
    date_col = func.date(Article.published_at)
    rows = (
        query.with_entities(date_col.label("pub_date"), func.count(Article.id).label("count"))
        .filter(Article.published_at.isnot(None))
        .group_by(date_col)
        .order_by(date_col.desc())
        .limit(limit)
        .all()
    )
    return [
        ArchiveDateInfo(date=str(r[0]), article_count=r[1])
        for r in rows
        if r[0] and r[1] > 0
    ]


@router.get("", response_model=PaginatedArticlesResponse, summary="Get Historical News Archive")
def get_archive(
    date: Optional[str] = Query(None, description="Historical date in YYYY-MM-DD format (filters published_at)"),
    region: Optional[str] = Query(None, description="Filter by region: 'INDIA' or 'INTERNATIONAL'"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. 'en', 'te', 'ta', 'hi')"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieve historical news articles stored in the database based on publication date and facets."""
    query = apply_demo_filter(db.query(Article))

    # Date Filtering (Calendar Day on published_at)
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

    # Region Filtering
    if region and region.upper() != "ALL":
        query = query.filter(Article.region == region.upper())

    # State Filtering
    if state and state.upper() != "ALL":
        query = query.filter(Article.state.ilike(f"%{state}%"))

    # Language Filtering
    if language and language.lower() != "all":
        query = query.filter(Article.language_code == language.lower().strip())

    # Category Filtering
    if category and category.upper() != "ALL":
        query = query.join(Category).filter(Category.slug == category.lower())

    # Sorting: newest publication first
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
