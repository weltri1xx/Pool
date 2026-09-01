from datetime import datetime, timedelta, timezone
from os import getenv
from typing import TypedDict
import bcrypt
import jwt  
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import User
from backend.auth.schemes.post import LoginSchema, SignupSchema
from backend.database import get_db

load_dotenv()

SECRET_KEY = getenv("ACCESS_SECRET_KEY", "fallback_access_secret")
REFRESH_SECRET_KEY = getenv("REFRESH_SECRET_KEY", "fallback_refresh_secret")
ALGORITHM = getenv("ALGORITHM", "HS256")

# Swagger UI uchun faqat bitta HTTP Bearer sxemasini belgilaymiz
security = HTTPBearer(auto_error=False)


class TokenData(TypedDict):
    username: str


class AuthService:

    @classmethod
    async def get_current_user(
        cls, 
        auth: HTTPAuthorizationCredentials | None = Depends(security), 
        db: AsyncSession = Depends(get_db)
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if not auth or not auth.credentials:
            raise credentials_exception

        token = auth.credentials
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("username")
            if username is None:
                raise credentials_exception
        except jwt.PyJWTError: 
            raise credentials_exception

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        return user

    @classmethod
    async def get_current_user_optional(
        cls, 
        auth: HTTPAuthorizationCredentials | None = Depends(security), 
        db: AsyncSession = Depends(get_db)
    ) -> User | None:
        if not auth or not auth.credentials:
            return None
        try:
            return await cls.get_current_user(auth=auth, db=db)
        except HTTPException:
            return None

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    async def sign_up(data: SignupSchema, db: AsyncSession):
        result = await db.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        user = User(
            username=data.username,
            password=AuthService.get_password_hash(data.password),
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        tokens = {
            "access_token": AuthService.create_access_token({"username": user.username}),
            "refresh_token": AuthService.create_refresh_token({"username": user.username}),
        }
        return {"message": "User registered successfully", "tokens": tokens}

    @classmethod
    async def refresh_access_token(cls, refresh_token: str, db: AsyncSession):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("username")
            if username is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        new_access_token = cls.create_access_token({"username": user.username})

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    @staticmethod
    async def login(data: LoginSchema, db: AsyncSession):
        result = await db.execute(select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()

        if user is None or not AuthService.verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        tokens = {
            "access_token": AuthService.create_access_token({"username": user.username}),
            "refresh_token": AuthService.create_refresh_token({"username": user.username}),
        }
        return {"message": "Login successful", "tokens": tokens}