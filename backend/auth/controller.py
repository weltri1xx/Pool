from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.models import User
from backend.auth.schemes.post import RefreshSchema
from backend.auth.schemes.post import LoginSchema, SignupSchema
from backend.auth.service import AuthService
from backend.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(data: SignupSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.sign_up(data, db)


@router.post("/login")
async def login(data: LoginSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(data, db)


@router.get("/me")
async def me(current_user: User = Depends(AuthService.get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "profile_picture": current_user.profile_picture,
    }

@router.post("/refresh")
async def refresh(data: RefreshSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_access_token(data.refresh_token, db)


@router.post("/profile-picture")
async def upload_profile_picture(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    user = await AuthService.update_profile_picture(db, current_user, image)
    return {
        "message": "Profil rasmi yangilandi",
        "profile_picture": user.profile_picture,
    }