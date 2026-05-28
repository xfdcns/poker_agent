"""用户扑克画像 CRUD"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_poker_profile import UserPokerProfile
from typing import Optional
import json


async def get_user_profile(db: AsyncSession, user_id: int) -> Optional[UserPokerProfile]:
    result = await db.execute(
        select(UserPokerProfile).where(UserPokerProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user_profile(db: AsyncSession, user_id: int) -> UserPokerProfile:
    profile = UserPokerProfile(user_id=user_id)
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def get_or_create_user_profile(db: AsyncSession, user_id: int) -> UserPokerProfile:
    profile = await get_user_profile(db, user_id)
    if not profile:
        profile = await create_user_profile(db, user_id)
    return profile


async def update_user_profile(db: AsyncSession, profile: UserPokerProfile, **kwargs) -> UserPokerProfile:
    for key, value in kwargs.items():
        if hasattr(profile, key):
            # strengths/weaknesses 存 JSON 字符串
            if key in ("strengths", "weaknesses") and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            setattr(profile, key, value)
    await db.flush()
    await db.refresh(profile)
    return profile


async def update_profile_after_settle(
    db: AsyncSession,
    user_id: int,
    result: str,
    profit: float,
    position: str,
) -> UserPokerProfile:
    """结算后更新用户画像统计"""
    profile = await get_or_create_user_profile(db, user_id)

    # 总局数
    profile.total_hands = (profile.total_hands or 0) + 1

    # 胜率
    total = profile.total_hands
    current_wins = int(float(profile.win_rate or 0) / 100 * (total - 1))
    if result == "win":
        current_wins += 1
    profile.win_rate = round(current_wins / total * 100, 2)

    # 总盈利
    profile.total_profit = float(profile.total_profit or 0) + profit

    # 等级
    if total >= 100 and float(profile.win_rate or 0) >= 55:
        profile.level = "高级"
    elif total >= 30:
        profile.level = "中级"
    else:
        profile.level = "初级"

    # 擅长位置
    preferred = profile.preferred_positions or ""
    if result == "win" and position not in preferred:
        preferred = f"{preferred},{position}" if preferred else position
        profile.preferred_positions = preferred

    await db.flush()
    await db.refresh(profile)
    return profile
