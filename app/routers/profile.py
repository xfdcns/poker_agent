"""画像路由 /api/profile"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.config.db_conf import get_db
from app.crud.user_poker_profile import get_or_create_user_profile
from app.crud.opponent_profile import get_opponent_profiles
from app.utils.auth import get_current_user
from app.utils.response import success
from app.models.user import User
import json

router = APIRouter(prefix="/api/profile", tags=["画像"])


@router.get("/my")
async def get_my_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await get_or_create_user_profile(db, user.id)

    # 解析 JSON 字段
    strengths = json.loads(profile.strengths) if profile.strengths else []
    weaknesses = json.loads(profile.weaknesses) if profile.weaknesses else []
    preferred = [p.strip() for p in profile.preferred_positions.split(",")] if profile.preferred_positions else []

    return success({
        "user_id": user.id,
        "level": profile.level,
        "total_hands": profile.total_hands,
        "win_rate": float(profile.win_rate or 0),
        "total_profit": float(profile.total_profit or 0),
        "style": profile.style,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "preferred_positions": preferred,
        "vpip": float(profile.vpip or 0),
        "pfr": float(profile.pfr or 0),
        "aggression": float(profile.aggression or 0),
        "updated_at": str(profile.updated_at) if profile.updated_at else None,
    })


@router.get("/opponents")
async def get_opponents(keyword: Optional[str] = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    opponents = await get_opponent_profiles(db, user.id, keyword)
    items = []
    for opp in opponents:
        items.append({
            "id": opp.id,
            "opponent_name": opp.opponent_name,
            "total_hands": opp.total_hands,
            "vpip": float(opp.vpip or 0),
            "pfr": float(opp.pfr or 0),
            "aggression": float(opp.aggression or 0),
            "style": opp.style,
            "notes": opp.notes,
            "updated_at": str(opp.updated_at) if opp.updated_at else None,
        })
    return success({"items": items})
