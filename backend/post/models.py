import enum
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base  # database.py faylingiz joylashuviga qarang

class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[MediaType] = mapped_column(SQLEnum(MediaType), default=MediaType.TEXT)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        index=True
    )