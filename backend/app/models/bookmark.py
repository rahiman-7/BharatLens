from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from app.db.base import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")

    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_user_article_bookmark"),
    )
