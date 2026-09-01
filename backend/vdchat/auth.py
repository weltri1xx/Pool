import jwt
from fastapi import WebSocket, WebSocketException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.auth.models import User
from backend.auth.service import ALGORITHM, SECRET_KEY
 
 
async def get_current_user_ws(websocket: WebSocket, db: AsyncSession) -> User:
    token = websocket.query_params.get("token")
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Token topilmadi")
 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Yaroqsiz token")
    except jwt.PyJWTError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Yaroqsiz token")
 
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Foydalanuvchi topilmadi")
 
    return user