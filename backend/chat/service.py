import os
import shutil
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.auth.models import User
from backend.chat.models import Conversation, Message
from backend.vdchat.service import manager

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _safe_save(upload: UploadFile, prefix: str) -> str:
    file_ext = os.path.splitext(upload.filename)[1].lower()
    safe_name = f"{prefix}_{datetime.now().timestamp()}{file_ext}"
    path = os.path.join(UPLOAD_DIR, safe_name)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return f"/{path}".replace("\\", "/")

 
class ChatService:
    @staticmethod
    async def user_exists(db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(select(User.id).where(User.id == user_id))
        return result.scalar_one_or_none() is not None
 
    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession, user_a_id: int, user_b_id: int
    ) -> Conversation:
        query = select(Conversation).where(
            or_(
                and_(
                    Conversation.user_one_id == user_a_id,
                    Conversation.user_two_id == user_b_id,
                ),
                and_(
                    Conversation.user_one_id == user_b_id,
                    Conversation.user_two_id == user_a_id,
                ),
            )
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation
 
        conversation = Conversation(user_one_id=user_a_id, user_two_id=user_b_id)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
 
    @staticmethod
    async def send_message(
        db: AsyncSession,
        sender_id: int,
        receiver_id: int,
        text: str | None = None,
        image: UploadFile | None = None,
        video: UploadFile | None = None,
    ) -> Message:
        conversation = await ChatService.get_or_create_conversation(
            db, sender_id, receiver_id
        )

        image_url = _safe_save(image, "chat_img") if image and image.filename else None
        video_url = _safe_save(video, "chat_vid") if video and video.filename else None

        message = Message(
            conversation_id=conversation.id,
            sender_id=sender_id,
            text=text,
            image_url=image_url,
            video_url=video_url,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        await manager.send_to_user(
            receiver_id,
            {
                "type": "chat:message",
                "conversation_id": conversation.id,
                "from_user_id": sender_id,
                "text": text,
                "image_url": image_url,
                "video_url": video_url,
            },
        )
 
        return message
 
    @staticmethod
    async def get_user_conversations(
        db: AsyncSession, user_id: int
    ) -> list[Conversation]:
        query = (
            select(Conversation)
            .where(
                or_(
                    Conversation.user_one_id == user_id,
                    Conversation.user_two_id == user_id,
                )
            )
            .order_by(Conversation.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()
 
    @staticmethod
    async def is_participant(
        db: AsyncSession, conversation_id: int, user_id: int
    ) -> bool:
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            or_(
                Conversation.user_one_id == user_id,
                Conversation.user_two_id == user_id,
            ),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
 
    @staticmethod
    async def get_messages_paginated(
        db: AsyncSession,
        conversation_id: int,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id)
 
        if cursor:
            if cursor.tzinfo is not None:
                cursor = cursor.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.filter(Message.created_at < cursor)
 
        query = query.order_by(Message.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()