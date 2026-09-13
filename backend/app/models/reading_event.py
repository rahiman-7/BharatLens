from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from app.db.base import Base


class ReadingEvent(Base):
    __tablename__ = "reading_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # 'click', 'read_dwell', 'share', 'bookmark'
    dwell_time_seconds = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="reading_events")
    article = relationship("Article", back_populates="reading_events")

    __table_args__ = (
        Index("idx_reading_user_article", "user_id", "article_id"),
    )
