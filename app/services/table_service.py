"""牌桌业务编排 - 组合 CRUD + Agent，处理创建/开始/结算等业务"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.table import create_table, get_table_by_id_and_user, update_table
from app.crud.action import create_action
from app.crud.opponent_profile import upsert_opponent_profile
from app.crud.user_poker_profile import update_profile_after_settle
from app.models.table import GameTable
from fastapi.encoders import jsonable_encoder
import json


async def create_table_service(
    db: AsyncSession,
    user_id: int,
    num_players: int,
    my_position: str,
    my_hole_cards: str,
    my_stack: float = 1000.00,
    opponents: list = None,
) -> dict:
    """创建牌桌"""
    opponents_json = json.dumps(opponents, ensure_ascii=False) if opponents else None

    table = await create_table(
        db=db,
        user_id=user_id,
        num_players=num_players,
        my_position=my_position,
        my_hole_cards=my_hole_cards,
        my_stack=my_stack,
        opponents_info=opponents_json,
    )

    return {
        "table_id": table.id,
        "num_players": table.num_players,
        "my_position": table.my_position,
        "my_hole_cards": table.my_hole_cards,
        "my_stack": float(table.my_stack),
        "community_cards": table.community_cards,
        "pot_size": float(table.pot_size),
        "status": table.status,
        "opponents": opponents or [],
    }


async def start_game_service(db: AsyncSession, table_id: int, user_id: int) -> dict:
    """开始游戏"""
    table = await get_table_by_id_and_user(db, table_id, user_id)
    if not table:
        return None
    if table.status != "waiting":
        return {"error": "牌桌已开始"}

    # 底池 = SB + BB
    initial_pot = float(table.sb_amount or 10) + float(table.bb_amount or 20)
    table = await update_table(db, table, status="preflop", pot_size=initial_pot)

    return {
        "table_id": table.id,
        "status": table.status,
        "pot_size": float(table.pot_size),
        "community_cards": table.community_cards,
        "sb_amount": float(table.sb_amount or 10),
        "bb_amount": float(table.bb_amount or 20),
        "current_stage": table.status,
    }


async def settle_game_service(
    db: AsyncSession,
    table_id: int,
    user_id: int,
    result: str,
    profit: float,
    opponent_hands: list = None,
    notes: str = None,
) -> dict:
    """结算游戏"""
    table = await get_table_by_id_and_user(db, table_id, user_id)
    if not table:
        return None

    # 1. 更新牌桌状态
    table = await update_table(db, table, status="settled", result=result, profit=profit, notes=notes)

    # 2. 更新用户画像
    profile = await update_profile_after_settle(
        db=db, user_id=user_id, result=result, profit=profit, position=table.my_position
    )

    # 3. 更新对手画像
    opponent_updates = {}
    if opponent_hands:
        for opp in opponent_hands:
            opp_name = opp.get("position", "unknown")
            opp_profile = await upsert_opponent_profile(
                db=db, user_id=user_id, opponent_name=opp_name
            )
            opponent_updates[opp_name] = f"已更新（对战{opp_profile.total_hands}局）"

    # 4. 生成复盘
    review = {
        "summary": f"你在{table.my_position}位置，手牌{table.my_hole_cards}，{'获胜' if result == 'win' else '落败'}，盈亏{profit}筹码。",
        "good_plays": [],
        "improvements": [],
        "opponent_updates": opponent_updates,
    }

    return {
        "table_id": table.id,
        "result": result,
        "profit": profit,
        "review": review,
    }
