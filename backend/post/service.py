import os
import shutil
from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.post.models import Post, Like
from datetime import datetime, timezone

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class PostService:
    @staticmethod
    async def create_post(
        db: AsyncSession, 
        user_id: int, 
        text: str | None = None, 
        image: UploadFile | None = None, 
        video: UploadFile | None = None
    ) -> Post:
        image_url = None
        video_url = None

        if image:
            image_path = os.path.join(UPLOAD_DIR, f"img_{datetime.now().timestamp()}_{image.filename}")
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_url = os.path.basename(image_path)

        if video:
            video_path = os.path.join(UPLOAD_DIR, f"vid_{datetime.now().timestamp()}_{video.filename}")
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
            video_url = os.path.basename(video_path)

        new_post = Post(
            text=text,
            image_url=image_url,
            video_url=video_url,
            user_id=user_id
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        return new_post


    @staticmethod
    async def get_posts_paginated(
        db: AsyncSession, 
        cursor: datetime | None = None, 
        limit: int = 10,
        current_user_id: int | None = None,
    ) -> list[Post]:
        query = select(Post)
        
        if cursor:
            if cursor.tzinfo is not None:
                cursor = cursor.astimezone(timezone.utc).replace(tzinfo=None)
                
            query = query.filter(Post.created_at < cursor)

        query = query.order_by(Post.created_at.desc()).limit(limit)
        result = await db.execute(query)
        posts = result.scalars().all()

        if not posts:
            return posts

        post_ids = [post.id for post in posts]

        counts_result = await db.execute(
            select(Like.post_id, func.count(Like.id))
            .where(Like.post_id.in_(post_ids))
            .group_by(Like.post_id)
        )
        counts_map = dict(counts_result.all())

        liked_ids: set[int] = set()
        if current_user_id is not None:
            liked_result = await db.execute(
                select(Like.post_id).where(
                    Like.post_id.in_(post_ids), Like.user_id == current_user_id
                )
            )
            liked_ids = {row[0] for row in liked_result.all()}

        for post in posts:
            post.likes_count = counts_map.get(post.id, 0)
            post.liked_by_me = post.id in liked_ids

        return posts

    @staticmethod
    async def post_exists(db: AsyncSession, post_id: int) -> bool:
        result = await db.execute(select(Post.id).where(Post.id == post_id))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def like_post(db: AsyncSession, user_id: int, post_id: int) -> None:
        if not await PostService.post_exists(db, post_id):
            raise HTTPException(status_code=404, detail="Post topilmadi")

        result = await db.execute(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Siz bu postni allaqachon layk qilgansiz")

        like = Like(user_id=user_id, post_id=post_id)
        db.add(like)
        await db.commit()
    @staticmethod
    async def unlike_post(db: AsyncSession, user_id: int, post_id: int) -> None:
        result = await db.execute(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        like = result.scalar_one_or_none()
        if like is None:
            raise HTTPException(status_code=404, detail="Siz bu postni layk qilmagansiz")

        await db.delete(like)
        await db.commit()