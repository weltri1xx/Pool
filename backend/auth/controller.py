from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes.post import LoginSchema, RefreshSchema, SignupSchema
from backend.auth.servise import AuthService
from backend.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()

