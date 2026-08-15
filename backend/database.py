from os import getenv
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)