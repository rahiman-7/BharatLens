import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from app.db.base import Base


class RegionType(str, enum.Enum):
    INDIA = "INDIA"
    INTERNATIONAL = "INTERNATIONAL"


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    canonical_url = Column(String(1000), unique=True, nullable=False)
    url_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 for fast duplicate check
    
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    story_group_id = Column(
        Integer,
        ForeignKey("story_groups.id", ondelete="SET NULL", use_alter=True, name="fk_articles_story_group"),
        nullable=True,
        index=True,
    )
    
    region = Column(String(20), default="INDIA", nullable=False, index=True)  # 'INDIA' | 'INTERNATIONAL'
    state = Column(String(100), nullable=True, index=True)  # Nullable for national/international news
    language_code = Column(String(10), default="en", nullable=False, index=True)  # ISO-639 e.g. 'en', 'te', 'ta', 'hi'
    
    image_url = Column(String(1000), nullable=True)
    author = Column(String(255), nullable=True)
    
    published_at = Column(DateTime, nullable=False, index=True)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    # Phase 12 — Clean Demo / Real Live Data Separation
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    source = relationship("Source", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    story_group = relationship("StoryGroup", back_populates="articles", foreign_keys=[story_group_id])
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")
    reading_events = relationship("ReadingEvent", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_articles_region_published", "region", "published_at"),
        Index("idx_articles_category_published", "category_id", "published_at"),
        Index("idx_articles_state_published", "state", "published_at"),
        Index("idx_articles_state_lang_published", "state", "language_code", "published_at"),
    )
