from fastapi import WebSocket
 
from backend.vdchat.schemes.post import SignalMessage
 
 
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        self.active_connections.pop(user_id, None)

    def is_online(self, user_id: int) -> bool:
        return user_id in self.active_connections

    async def send_to_user(self, user_id: int, message: dict) -> bool:
        websocket = self.active_connections.get(user_id)
        if websocket is None:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(user_id)
            return False


manager = ConnectionManager()
 
 
class VideoCallService:
 
    @staticmethod
    async def connect_user(user_id: int, websocket: WebSocket) -> None:
        await manager.connect(user_id, websocket)
 
    @staticmethod
    def disconnect_user(user_id: int) -> None:
        manager.disconnect(user_id)
 
    @staticmethod
    async def relay_signal(from_user_id: int, message: SignalMessage) -> bool:
        return await manager.send_to_user(
            message.to_user_id,
            {
                "type": message.type,
                "from_user_id": from_user_id,
                "payload": message.payload,
            },
        )