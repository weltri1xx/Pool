from datetime import datetime
from pydantic import BaseModel

class PostResponseSchema(BaseModel):
    id: int
    text: str | None
    image_url: str | None
    video_url: str | None
    created_at: datetime
    user_id: int
    likes_count: int = 0
    liked_by_me: bool = False

    model_config = {
        "from_attributes": True
    }


class LikeResponseSchema(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }