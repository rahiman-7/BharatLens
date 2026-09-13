from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(255), nullable=False)
    feed_url = Column(String(500), nullable=True)
    country = Column(String(10), default="IN", nullable=False)  # 'IN' or 'GLOBAL'
    created_at = Column(DateTime, default=utc_now, nullable=False)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")
