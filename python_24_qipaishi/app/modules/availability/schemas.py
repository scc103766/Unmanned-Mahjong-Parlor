from datetime import datetime

from pydantic import BaseModel, Field


class RoomAvailabilityResponse(BaseModel):
    room_id: str
    store_id: str
    start_at: datetime
    end_at: datetime
    available: bool
    conflict_reasons: list[str] = Field(default_factory=list)
