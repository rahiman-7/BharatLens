from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

ALLOWED_EVENT_TYPES = Literal["view", "read"]


class ReadingEventCreate(BaseModel):
    article_id: int = Field(..., description="ID of the read article")
    event_type: ALLOWED_EVENT_TYPES = Field("view", description="Type of interaction: 'view' or 'read'")
    dwell_time_seconds: int = Field(0, ge=0, le=14400, description="Dwell time in seconds (0 to 14400)")


class ReadingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    article_id: int
    event_type: str
    dwell_time_seconds: int
    created_at: datetime
