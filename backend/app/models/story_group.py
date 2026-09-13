from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from app.db.base import Base


class StoryGroup(Base):
    __tablename__ = "story_groups"

    id = Column(Integer, primary_key=True, index=True)
    representative_article_id = Column(
        Integer,
        ForeignKey("articles.id", ondelete="SET NULL", use_alter=True, name="fk_story_groups_rep_article"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    representative_article = relationship(
        "Article",
        foreign_keys=[representative_article_id],
        post_update=True,
    )
    articles = relationship(
        "Article",
        back_populates="story_group",
        foreign_keys="Article.story_group_id",
    )
