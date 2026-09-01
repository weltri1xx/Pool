from datetime import datetime, timezone
 
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.auth.models import User
from backend.folllow.models import Follow
 
 
class FollowService:
    @staticmethod
    async def user_exists(db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(select(User.id).where(User.id == user_id))
        return result.scalar_one_or_none() is not None
 
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
 
    @staticmethod
    async def follow_user(db: AsyncSession, follower_id: int, following_id: int) -> Follow:
        if follower_id == following_id:
            raise HTTPException(
                status_code=400, detail="O'zingizni kuzata olmaysiz"
            )
 
        if not await FollowService.user_exists(db, following_id):
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
 
        result = await db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=400, detail="Siz bu foydalanuvchini allaqachon kuzatyapsiz"
            )
 
        follow = Follow(follower_id=follower_id, following_id=following_id)
        db.add(follow)
        await db.commit()
        await db.refresh(follow)
        return follow
 
    @staticmethod
    async def unfollow_user(db: AsyncSession, follower_id: int, following_id: int) -> None:
        result = await db.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        follow = result.scalar_one_or_none()
        if follow is None:
            raise HTTPException(
                status_code=404, detail="Siz bu foydalanuvchini kuzatmagansiz"
            )
 
        await db.delete(follow)
        await db.commit()
 
    @staticmethod
    async def is_following(db: AsyncSession, follower_id: int, following_id: int) -> bool:
        result = await db.execute(
            select(Follow.id).where(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
        )
        return result.scalar_one_or_none() is not None
 
    @staticmethod
    async def get_counts(db: AsyncSession, user_id: int) -> tuple[int, int]:
        followers_result = await db.execute(
            select(func.count(Follow.id)).where(Follow.following_id == user_id)
        )
        following_result = await db.execute(
            select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        )
        return followers_result.scalar() or 0, following_result.scalar() or 0
 
    @staticmethod
    async def get_followers_paginated(
        db: AsyncSession,
        user_id: int,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[User]:
        query = (
            select(User, Follow.created_at)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
        )
 
        if cursor:
            if cursor.tzinfo is not None:
                cursor = cursor.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.filter(Follow.created_at < cursor)
 
        query = query.order_by(Follow.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return [row[0] for row in result.all()]
 
    @staticmethod
    async def get_following_paginated(
        db: AsyncSession,
        user_id: int,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[User]:
        query = (
            select(User, Follow.created_at)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
        )
 
        if cursor:
            if cursor.tzinfo is not None:
                cursor = cursor.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.filter(Follow.created_at < cursor)
 
        query = query.order_by(Follow.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return [row[0] for row in result.all()]
 