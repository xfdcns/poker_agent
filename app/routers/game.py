"""游戏路由 /api/game - 核心对战接口"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.db_conf import get_db
from app.crud.table import get_table_by_id_and_user, update_table
from app.crud.action import create_action, get_actions_by_table
from app.crud.opponent_profile import get_opponent_by_name
from app.crud.user_poker_profile import get_or_create_user_profile
from app.services.table_service import settle_game_service
from app.agent.graph import run_agent
from app.agent.state import PokerAgentState
from app.utils.auth import get_current_user
from app.utils.response import success
from app.schemas.game import GameActionRequest, GameSubmitRequest, GameSettleRequest
from app.models.user import User
from fastapi.encoders import jsonable_encoder
import json

router = APIRouter(prefix="/api/game", tags=["游戏"])


@router.post("/action")
async def game_action(
    req: GameActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交当前局面 → Agent分析 → 返回建议"""

    # 1. 校验牌桌
    table = await get_table_by_id_and_user(db, req.table_id, user.id)
    if not table:
        raise HTTPException(status_code=404, detail="牌桌不存在")
    if table.status == "settled":
        raise HTTPException(status_code=400, detail="牌桌已结算")

    # 2. 加载对手画像
    opponent_profiles = []
    if req.opponent_bets:
        for bet in req.opponent_bets:
            opp = await get_opponent_by_name(db, user.id, bet.position)
            if opp:
                opponent_profiles.append({
                    "opponent_name": opp.opponent_name,
                    "vpip": float(opp.vpip or 0),
                    "pfr": float(opp.pfr or 0),
                    "aggression": float(opp.aggression or 0),
                    "style": opp.style,
                })

    # 3. 加载用户画像
    user_profile_obj = await get_or_create_user_profile(db, user.id)
    user_profile = {
        "level": user_profile_obj.level,
        "total_hands": user_profile_obj.total_hands,
        "win_rate": float(user_profile_obj.win_rate or 0),
        "style": user_profile_obj.style,
    }

    # 4. 计算实际活跃对手数：前端传 > opponent_bets长度 > 兜底
    effective_num_opponents = (
        req.num_opponents
        or (len(req.opponent_bets) if req.opponent_bets else None)
        or (table.num_players - 1)
    )

    # 5. 构造 Agent 状态
    agent_state: PokerAgentState = {
        "table_id": req.table_id,
        "stage": req.stage,
        "hole_cards": req.hole_cards or table.my_hole_cards or "",
        "community_cards": req.community_cards or "",
        "num_opponents": effective_num_opponents,
        "my_position": table.my_position,
        "my_stack": float(table.my_stack),
        "pot_size": req.pot_size,
        "opponent_bets": [b.model_dump() for b in req.opponent_bets] if req.opponent_bets else [],
        "user_profile": user_profile,
        "opponent_profiles": opponent_profiles,
        "analysis_type": req.analysis_type,
    }

    # 6. 运行 Agent
    result = run_agent(agent_state)

    # 7. 保存 Agent 分析记录
    await create_action(
        db=db,
        table_id=req.table_id,
        stage=req.stage,
        position=table.my_position,
        action="agent_analysis",
        action_type="agent_analysis",
        amount=0,
        pot_after=req.pot_size,
        community_cards=req.community_cards,
        agent_suggestion=result.get("suggested_action"),
        agent_win_rate=result.get("win_rate"),
        agent_reasoning=result.get("reasoning"),
    )

    # 8. 更新牌桌状态和公共牌
    update_data = {}
    if req.community_cards:
        update_data["community_cards"] = req.community_cards
    if table.status == "waiting":
        update_data["status"] = req.stage
    if update_data:
        await update_table(db, table, **update_data)

    # 9. 返回分析结果
    response_data = {
        "win_rate": result.get("win_rate", 0),
        "tie_rate": result.get("tie_rate", 0),
        "loss_rate": round(100 - result.get("win_rate", 0) - result.get("tie_rate", 0), 1),
        "hand_name": result.get("hand_name", ""),
        "suggested_action": result.get("suggested_action", "fold"),
        "suggested_amount": result.get("suggested_amount", 0),
        "reasoning": result.get("reasoning", ""),
        "confidence": result.get("confidence", 0),
        "opponent_range": result.get("opponent_range", ""),
        "risk_warning": result.get("risk_warning", ""),
        "decision_source": result.get("decision_source", "rule_engine"),
        "opponent_analysis": {
            bet.position: {"action": bet.action, "amount": bet.amount}
            for bet in (req.opponent_bets or [])
        },
        "pot_odds": result.get("pot_odds", {}),
    }
    return success(response_data, message="分析成功")


@router.post("/submit")
async def game_submit(
    req: GameSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交用户决策"""
    table = await get_table_by_id_and_user(db, req.table_id, user.id)
    if not table:
        raise HTTPException(status_code=404, detail="牌桌不存在")
    if table.status == "settled":
        raise HTTPException(status_code=400, detail="牌桌已结算")

    # 保存决策记录
    action_record = await create_action(
        db=db,
        table_id=req.table_id,
        stage=req.stage,
        position=table.my_position,
        action=req.action,
        action_type="user_decision",
        amount=req.amount,
        community_cards=table.community_cards,
    )

    # 更新牌桌
    current_pot = float(table.pot_size or 0)
    current_stack = float(table.my_stack or 0)
    if req.action in ("call", "raise", "all-in"):
        current_pot += req.amount
        current_stack -= req.amount
    await update_table(db, table, pot_size=current_pot, my_stack=current_stack)

    # 下一阶段
    stage_order = ["preflop", "flop", "turn", "river"]
    current_idx = stage_order.index(req.stage) if req.stage in stage_order else 0
    next_stage = stage_order[current_idx + 1] if current_idx < len(stage_order) - 1 else "river"

    return success({
        "action_id": action_record.id,
        "table_id": req.table_id,
        "stage": req.stage,
        "position": table.my_position,
        "action": req.action,
        "amount": req.amount,
        "pot_after": current_pot,
        "my_stack_after": current_stack,
        "next_stage": next_stage,
    }, message="决策已记录")


@router.post("/settle")
async def game_settle(
    req: GameSettleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """结算"""
    data = await settle_game_service(
        db=db,
        table_id=req.table_id,
        user_id=user.id,
        result=req.result,
        profit=req.profit,
        opponent_hands=[h.model_dump() for h in req.opponent_hands] if req.opponent_hands else None,
        notes=req.notes,
    )
    if not data:
        raise HTTPException(status_code=404, detail="牌桌不存在")
    return success(data, message="结算成功")
