from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.auth.service import AuthService
from backend.post.service import PostService
from backend.post.schemes.post import PostResponseSchema

router = APIRouter(prefix="/posts", tags=["Posts"])

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv"]

MAX_IMAGE_SIZE = 10 * 1024 * 1024  
MAX_VIDEO_SIZE = 50 * 1024 * 1024  

@router.post("/", response_model=PostResponseSchema)
async def create_post(
    text: str | None = Form(None),
    image: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)  # <- '=' tenglik qo'shildi
):
    has_text = text is not None and text.strip() != ""
    has_image = bool(image and image.filename)
    has_video = bool(video and video.filename)

    if not has_text and not has_image and not has_video:
        raise HTTPException(
            status_code=400,
            detail="Post uchun matn, rasm yoki video kamida bittasi kerak!",
        )

    if image and image.filename:
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

    if video and video.filename:
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

    return await PostService.create_post(
        db=db, 
        user_id=current_user.id, 
        text=text, 
        image=image, 
        video=video
    )

@router.get("/", response_model=list[PostResponseSchema])
async def get_posts(
    cursor: datetime | None = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user_optional),  # <- '=' tenglik qo'shildi
):
    current_user_id = current_user.id if current_user else None
    return await PostService.get_posts_paginated(
        db=db, cursor=cursor, limit=limit, current_user_id=current_user_id
    )


@router.post("/{post_id}/like")
async def like_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user),  # <- '=' tenglik qo'shildi
):
    await PostService.like_post(db=db, user_id=current_user.id, post_id=post_id)
    return {"message": "Layk qo'yildi"}


@router.delete("/{post_id}/like")
async def unlike_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user),  # <- '=' tenglik qo'shildi
):
    await PostService.unlike_post(db=db, user_id=current_user.id, post_id=post_id)
    return {"message": "Layk olib tashlandi"}