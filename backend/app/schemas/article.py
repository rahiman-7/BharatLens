from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator
from app.schemas.source import SourceResponse
from app.schemas.category import CategoryResponse


class ArticleResponse(BaseModel):
    id: int
    title: str
    description: str
    canonical_url: str
    url: Optional[str] = None
    source_id: int
    category_id: int
    region: str
    state: Optional[str] = None
    language_code: str = "en"
    image_url: Optional[str] = None
    author: Optional[str] = None
    published_at: datetime
    fetched_at: datetime
    created_at: datetime
    is_demo: bool = False

    # Embedded relationships
    source: Optional[SourceResponse] = None
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def populate_url(self):
        if not self.url and self.canonical_url:
            self.url = self.canonical_url
        return self


class PaginatedArticlesResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    items: List[ArticleResponse]
