"""对手画像 CRUD"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.opponent_profile import OpponentProfile
from typing import Optional, List


async def get_opponent_by_name(db: AsyncSession, user_id: int, opponent_name: str) -> Optional[OpponentProfile]:
    result = await db.execute(
        select(OpponentProfile).where(
            OpponentProfile.user_id == user_id,
            OpponentProfile.opponent_name == opponent_name,
        )
    )
    return result.scalar_one_or_none()


async def get_opponent_profiles(db: AsyncSession, user_id: int, keyword: Optional[str] = None) -> List[OpponentProfile]:
    query = select(OpponentProfile).where(OpponentProfile.user_id == user_id)
    if keyword:
        query = query.where(OpponentProfile.opponent_name.like(f"%{keyword}%"))
    query = query.order_by(OpponentProfile.updated_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_opponent_profile(
    db: AsyncSession, user_id: int, opponent_name: str, **kwargs
) -> OpponentProfile:
    profile = OpponentProfile(user_id=user_id, opponent_name=opponent_name, **kwargs)
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def update_opponent_profile(db: AsyncSession, profile: OpponentProfile, **kwargs) -> OpponentProfile:
    for key, value in kwargs.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def upsert_opponent_profile(
    db: AsyncSession, user_id: int, opponent_name: str, **kwargs
) -> OpponentProfile:
    """不存在则创建，存在则更新"""
    profile = await get_opponent_by_name(db, user_id, opponent_name)
    if not profile:
        profile = await create_opponent_profile(db, user_id, opponent_name)

    # 更新对战局数
    profile.total_hands = (profile.total_hands or 0) + 1

    # 更新其他字段
    for key, value in kwargs.items():
        if hasattr(profile, key) and key != "total_hands":
            setattr(profile, key, value)

    await db.flush()
    await db.refresh(profile)
    return profile
