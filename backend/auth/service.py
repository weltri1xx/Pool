from datetime import datetime, timedelta, timezone
from os import getenv
from typing import Optional, TypedDict
import os
import shutil

import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.models import User
from backend.auth.schemes.post import LoginSchema, SignupSchema
from backend.database import get_db

load_dotenv()

SECRET_KEY = getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = getenv("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

PROFILE_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
MAX_PROFILE_IMAGE_SIZE = 10 * 1024 * 1024

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)


class TokenData(TypedDict):
    email: str


class AuthService:
    @staticmethod
    async def sign_up(data: SignupSchema, db: AsyncSession):
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        user = User(
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email, 
            password=AuthService.get_password_hash(data.password),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        tokens = {
            "access_token": AuthService.create_access_token({"email": user.email}),
            "refresh_token": AuthService.create_refresh_token({"email": user.email}),
        }
        return {"message": "User registered successfully", "tokens": tokens}

    @staticmethod
    async def login(data: LoginSchema, db: AsyncSession):
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if user is None or not AuthService.verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",  
            )

        tokens = {
            "access_token": AuthService.create_access_token({"email": user.email}),
            "refresh_token": AuthService.create_refresh_token({"email": user.email}),
        }
        return {"message": "Login successful", "tokens": tokens}    
    
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
    async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("email")
            if email is None:
                raise credentials_exception
        except jwt.PyJWTError:  
            raise credentials_exception

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception

        new_access_token = AuthService.create_access_token({"email": user.email})
        return {"access_token": new_access_token}


    @staticmethod
    async def update_profile_picture(db: AsyncSession, user: User, image: UploadFile) -> User:
        if not image.filename:
            raise HTTPException(status_code=400, detail="Rasm tanlanmadi")

        file_ext = image.filename[image.filename.rfind("."):].lower()
        if file_ext not in PROFILE_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Faqat rasm formatidagi fayllar yuklanishi mumkin!",
            )

        content = await image.read()
        if len(content) > MAX_PROFILE_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Rasm hajmi 10 MB dan oshmasligi kerak!",
            )
        await image.seek(0)

        image_path = os.path.join(
            UPLOAD_DIR, f"avatar_{user.id}_{datetime.now().timestamp()}{file_ext}"
        )
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        user.profile_picture = f"/{image_path}".replace("\\", "/")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("email")
            if email is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception

        return user

    @staticmethod
    async def get_current_user_optional(
        credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User | None:
        if credentials is None:
            return None
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("email")
            if email is None:
                return None
        except jwt.PyJWTError:
            return None

        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()