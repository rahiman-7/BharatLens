from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SourceResponse(BaseModel):
    id: int
    name: str
    base_url: str
    country: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
