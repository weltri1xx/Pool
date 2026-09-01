from datetime import datetime
 
from pydantic import BaseModel
 
 
class SendMessageSchema(BaseModel):
    receiver_id: int
    text: str | None = None
 
 
class MessageResponseSchema(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    text: str | None
    image_url: str | None
    video_url: str | None
    created_at: datetime
 
    model_config = {"from_attributes": True}
 
 
class ConversationResponseSchema(BaseModel):
    id: int
    user_one_id: int
    user_two_id: int
    created_at: datetime
 
    model_config = {"from_attributes": True}