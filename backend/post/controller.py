from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.auth.models import User  # Auth modulingizdagi User modeli
from backend.auth.servise import AuthService  # get_current_user qayerda bo'lsa o'sha yerdan import qiling
from backend.post.schemes import PostResponse, CursorPaginationResponse
from backend.post.service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/", response_model=PostResponse)
async def create_post(
    content: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(AuthService.get_current_user),              
    db: AsyncSession = Depends(get_db)
):
    if not content and not file:
        raise HTTPException(status_code=400, detail="Postda kamida matn yoki fayl bo'lishi kerak")
        
    return await PostService.create_post(db, current_user.id, content, file)

@router.get("/", response_model=CursorPaginationResponse)
async def get_posts(
    cursor: str | None = Query(None, description="ISO vaqt formati"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    return await PostService.get_posts_cursor(db, cursor, limit)