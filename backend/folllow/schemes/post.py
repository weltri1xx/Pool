from datetime import datetime
from pydantic import BaseModel
 
 
class UserBriefSchema(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    profile_picture: str | None = None
 
    model_config = {"from_attributes": True}
 
 
class FollowResponseSchema(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime
 
    model_config = {"from_attributes": True}
 
 
class UserProfileSchema(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    profile_picture: str | None = None
    followers_count: int
    following_count: int
    is_following: bool
 