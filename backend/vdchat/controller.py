from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
 
from backend.database import SessionLocal
from backend.vdchat.auth import get_current_user_ws
from backend.vdchat.schemes.post import SignalMessage
from backend.vdchat.service import VideoCallService
 
router = APIRouter(prefix="/ws", tags=["websocket"])
 
 
@router.websocket("/video-call")
async def video_call_ws(websocket: WebSocket):
    async with SessionLocal() as db:
        user = await get_current_user_ws(websocket, db)
 
    await VideoCallService.connect_user(user.id, websocket)
 
    try:
        while True:
            raw_data = await websocket.receive_json()
 
            try:
                message = SignalMessage(**raw_data)
            except ValidationError as exc:
                await websocket.send_json({"type": "error", "detail": exc.errors()})
                continue
 
            delivered = await VideoCallService.relay_signal(user.id, message)
 
            if not delivered:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": f"User {message.to_user_id} online emas",
                    }
                )
 
    except WebSocketDisconnect:
        VideoCallService.disconnect_user(user.id)