import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from backend.post.models import Post, MediaType

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class PostService:
    @classmethod
    async def create_post(cls, db: AsyncSession, user_id: int, content: str | None, file) -> Post:
        media_url = None
        media_type = MediaType.TEXT

        if file:
            file_ext = file.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{file_ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(await file.read())
                
            media_url = f"/uploads/{filename}"
            media_type = MediaType.VIDEO if file.content_type.startswith("video") else MediaType.IMAGE

        new_post = Post(
            user_id=user_id,
            content=content,
            media_url=media_url,
            media_type=media_type
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        return new_post

    @classmethod
    async def get_posts_cursor(cls, db: AsyncSession, cursor: str | None, limit: int):
        query = select(Post).order_by(desc(Post.created_at)).limit(limit + 1)
        
        if cursor:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Post.created_at < cursor_dt)
            
        result = await db.execute(query)
        posts = list(result.scalars().all())
        
        next_cursor = None
        if len(posts) > limit:
            next_post = posts.pop()
            next_cursor = next_post.created_at.isoformat()
            
        return {"items": posts, "next_cursor": next_cursor}