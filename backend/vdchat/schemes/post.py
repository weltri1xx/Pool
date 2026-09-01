from typing import Any, Literal
 
from pydantic import BaseModel
 
 
class SignalMessage(BaseModel):
 
    type: Literal["call:offer", "call:answer", "call:ice-candidate", "call:end"]
    to_user_id: int
    payload: dict[str, Any] = {}