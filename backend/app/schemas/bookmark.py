from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.article import ArticleResponse


class BookmarkStatusResponse(BaseModel):
    is_bookmarked: bool
    article_id: int


class BookmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    article_id: int
    created_at: datetime
    article: Optional[ArticleResponse] = None


class BookmarkListResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    items: List[ArticleResponse]
