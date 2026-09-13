import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import utc_now
from app.db.database import get_db
from app.models.user import User
from app.models.article import Article
from app.models.bookmark import Bookmark
from app.schemas.bookmark import BookmarkStatusResponse, BookmarkListResponse
from app.schemas.article import ArticleResponse
from app.api.deps import get_current_user

logger = logging.getLogger("bharatlens.api.bookmarks")

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])


@router.post(
    "/{article_id}",
    response_model=BookmarkStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bookmark an Article",
)
def add_bookmark(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an article to the authenticated user's bookmarks."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found.",
        )

    # Check if already bookmarked
    existing = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id, Bookmark.article_id == article_id)
        .first()
    )
    if existing:
        return BookmarkStatusResponse(is_bookmarked=True, article_id=article_id)

    bookmark = Bookmark(
        user_id=current_user.id,
        article_id=article_id,
        created_at=utc_now(),
    )
    db.add(bookmark)
    db.commit()
    logger.info(f"User {current_user.id} bookmarked article {article_id}")

    return BookmarkStatusResponse(is_bookmarked=True, article_id=article_id)


@router.delete(
    "/{article_id}",
    response_model=BookmarkStatusResponse,
    summary="Remove a Bookmark",
)
def remove_bookmark(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an article from the authenticated user's bookmarks."""
    bookmark = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id, Bookmark.article_id == article_id)
        .first()
    )
    if bookmark:
        db.delete(bookmark)
        db.commit()
        logger.info(f"User {current_user.id} removed bookmark on article {article_id}")

    return BookmarkStatusResponse(is_bookmarked=False, article_id=article_id)


@router.get(
    "/{article_id}",
    response_model=BookmarkStatusResponse,
    summary="Check Bookmark Status",
)
def get_bookmark_status(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check whether a specific article is currently bookmarked by the user."""
    bookmark = (
        db.query(Bookmark)
        .filter(Bookmark.user_id == current_user.id, Bookmark.article_id == article_id)
        .first()
    )
    return BookmarkStatusResponse(
        is_bookmarked=bookmark is not None,
        article_id=article_id,
    )


@router.get(
    "",
    response_model=BookmarkListResponse,
    summary="List User Bookmarks",
)
def list_bookmarks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all articles saved by the authenticated user in reverse chronological bookmark order."""
    query = (
        db.query(Article)
        .join(Bookmark, Bookmark.article_id == Article.id)
        .filter(Bookmark.user_id == current_user.id)
        .options(joinedload(Article.source), joinedload(Article.category))
        .order_by(Bookmark.created_at.desc())
    )

    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    offset = (page - 1) * limit

    articles = query.offset(offset).limit(limit).all()

    return BookmarkListResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=articles,
    )
