from datetime import datetime
 
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.auth.service import AuthService
from backend.chat.schemes.post import (
    ConversationResponseSchema,
    MessageResponseSchema,
)
from backend.chat.service import ChatService
from backend.database import get_db
 
router = APIRouter(prefix="/chat", tags=["Chat"])

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv"]

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024
 
 
@router.post("/messages", response_model=MessageResponseSchema)
async def send_message(
    receiver_id: int = Form(...),
    text: str | None = Form(None),
    image: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    if receiver_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="O'zingizga xabar yubora olmaysiz"
        )
 
    receiver_exists = await ChatService.user_exists(db, receiver_id)
    if not receiver_exists:
        raise HTTPException(
            status_code=404,
            detail=f"ID={receiver_id} bo'lgan foydalanuvchi topilmadi",
        )

    has_text = text is not None and text.strip() != ""
    has_image = bool(image and image.filename)
    has_video = bool(video and video.filename)

    if not has_text and not has_image and not has_video:
        raise HTTPException(
            status_code=400,
            detail="Xabar uchun matn, rasm yoki video kamida bittasi kerak!",
        )

    if has_image:
        file_ext = image.filename[image.filename.rfind(".") :].lower()
        if file_ext not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Faqat rasm formatidagi fayllar yuklanishi mumkin!",
            )
        image_content = await image.read()
        if len(image_content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Rasm hajmi 10 MB dan oshmasligi kerak!",
            )
        await image.seek(0)

    if has_video:
        file_ext = video.filename[video.filename.rfind(".") :].lower()
        if file_ext not in VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Faqat video formatidagi fayllar yuklanishi mumkin!",
            )
        video_content = await video.read()
        if len(video_content) > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Video hajmi 50 MB dan oshmasligi kerak!",
            )
        await video.seek(0)
 
    return await ChatService.send_message(
        db=db,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        text=text,
        image=image,
        video=video,
    )
 
 
@router.get("/conversations", response_model=list[ConversationResponseSchema])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    return await ChatService.get_user_conversations(db=db, user_id=current_user.id)
 
 
@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponseSchema],
)
async def get_messages(
    conversation_id: int,
    cursor: datetime | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    allowed = await ChatService.is_participant(db, conversation_id, current_user.id)
    if not allowed:
        raise HTTPException(
            status_code=403, detail="Bu suhbatga kirish huquqingiz yo'q"
        )
 
    return await ChatService.get_messages_paginated(
        db=db, conversation_id=conversation_id, cursor=cursor, limit=limit
    )