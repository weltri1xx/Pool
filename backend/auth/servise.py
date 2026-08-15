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


