from datetime import datetime
 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
 
from backend.auth.models import User
from backend.auth.service import AuthService
from backend.database import get_db
from backend.folllow.schemes.post import (
    UserBriefSchema,
    UserProfileSchema,
)
from backend.folllow.service import FollowService
 
router = APIRouter(prefix="/users", tags=["Follow"])
 
 
@router.post("/{user_id}/follow")
async def follow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    await FollowService.follow_user(db=db, follower_id=current_user.id, following_id=user_id)
    return {"message": "Kuzatishga qo'shildi"}
 
 
@router.delete("/{user_id}/follow")
async def unfollow_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AuthService.get_current_user),
):
    await FollowService.unfollow_user(db=db, follower_id=current_user.id, following_id=user_id)
    return {"message": "Kuzatishdan chiqarildi"}
 
 
@router.get("/{user_id}/followers", response_model=list[UserBriefSchema])
async def get_followers(
    user_id: int,
    cursor: datetime | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    return await FollowService.get_followers_paginated(
        db=db, user_id=user_id, cursor=cursor, limit=limit
    )
 
 
@router.get("/{user_id}/following", response_model=list[UserBriefSchema])
async def get_following(
    user_id: int,
    cursor: datetime | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    return await FollowService.get_following_paginated(
        db=db, user_id=user_id, cursor=cursor, limit=limit
    )
 
 
@router.get("/{user_id}/profile", response_model=UserProfileSchema)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(AuthService.get_current_user_optional),
):
    user = await FollowService.get_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
 
    followers_count, following_count = await FollowService.get_counts(db=db, user_id=user_id)
 
    is_following = False
    if current_user is not None:
        is_following = await FollowService.is_following(
            db=db, follower_id=current_user.id, following_id=user_id
        )
 
    return UserProfileSchema(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        profile_picture=user.profile_picture,
        followers_count=followers_count,
        following_count=following_count,
        is_following=is_following,
    )
