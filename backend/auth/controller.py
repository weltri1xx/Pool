from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes.post import LoginSchema, RefreshSchema, SignupSchema
from backend.auth.servise import AuthService
from backend.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()

@router.post("/signup")
async def signup(data: SignupSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.sign_up(data, db)

@router.post("/login")
async def login(data: LoginSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(data, db)