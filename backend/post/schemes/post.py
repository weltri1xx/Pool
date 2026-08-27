from pydantic import BaseModel
from datetime import datetime
from backend.post.models import MediaType

class PostResponse(BaseModel):
    id: int
    user_id: int
    content: str | None
    media_url: str | None
    media_type: MediaType
    created_at: datetime

    class Config:
        from_attributes = True

class CursorPaginationResponse(BaseModel):
    items: list[PostResponse]
    next_cursor: str | None