from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    reading_events = relationship("ReadingEvent", back_populates="user", cascade="all, delete-orphan")
