import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.db.database import get_db
from app.models.user import User
from app.models.article import Article
from app.models.reading_event import ReadingEvent
from app.schemas.reading_event import ReadingEventCreate, ReadingEventResponse
from app.api.deps import get_current_user

logger = logging.getLogger("bharatlens.api.reading_events")

router = APIRouter(prefix="/reading-events", tags=["Reading Events"])


@router.post(
    "",
    response_model=ReadingEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Article Reading Event",
)
def create_reading_event(
    req: ReadingEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a user interaction event (view or read dwell time) on an article.
    
    Data is stored exclusively for behavioral learning (to be leveraged in Phase 9).
    """
    article = db.query(Article).filter(Article.id == req.article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {req.article_id} not found.",
        )

    # Validate dwell time bounds (handled by Pydantic ge=0, le=14400)
    event = ReadingEvent(
        user_id=current_user.id,
        article_id=req.article_id,
        event_type=req.event_type,
        dwell_time_seconds=req.dwell_time_seconds,
        created_at=utc_now(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.debug(
        f"Recorded reading event '{req.event_type}' ({req.dwell_time_seconds}s) "
        f"for user {current_user.id} on article {req.article_id}"
    )
    return event
