from datetime import datetime, timedelta, timezone
from os import getenv
from typing import TypedDict
import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import User
from backend.auth.schemes.post import LoginSchema, SignupSchema

load_dotenv()

SECRET_KEY = getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = getenv("REFRESH_SECRET_KEY")
ALGORITHM = getenv("ALGORITHM", "HS256")


class TokenData(TypedDict):
    username: str

class AuthService:
    
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
