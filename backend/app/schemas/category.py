from typing import List
from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    display_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    total: int
    categories: List[CategoryResponse]
