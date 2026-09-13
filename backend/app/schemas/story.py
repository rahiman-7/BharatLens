from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator


class StoryArticleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    canonical_url: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    author: Optional[str] = None
    region: str = "INDIA"
    state: Optional[str] = None
    language_code: str = "en"
    published_at: datetime
    source_name: str
    category_name: str
    category_slug: str
    read_time_minutes: Optional[int] = 3

    @model_validator(mode="after")
    def populate_url(self):
        if not self.url and self.canonical_url:
            self.url = self.canonical_url
        return self


class StoryGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    representative_article: Optional[StoryArticleSummary] = None
    article_count: int
    sources: List[str]
    created_at: datetime
    updated_at: datetime


class StoryGroupDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    representative_article: Optional[StoryArticleSummary] = None
    article_count: int
    sources: List[str]
    articles: List[StoryArticleSummary]
    created_at: datetime
    updated_at: datetime


class PaginatedStoriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    limit: int
    total: int
    total_pages: int
    items: List[StoryGroupResponse]
