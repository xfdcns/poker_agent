"""操作记录 CRUD"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.action import GameAction
from typing import Optional, List


async def create_action(
    db: AsyncSession,
    table_id: int,
    stage: str,
    position: str,
    action: str,
    action_type: str = "user_decision",
    amount: float = 0.00,
    pot_after: Optional[float] = None,
    community_cards: Optional[str] = None,
    agent_suggestion: Optional[str] = None,
    agent_win_rate: Optional[float] = None,
    agent_reasoning: Optional[str] = None,
) -> GameAction:
    record = GameAction(
        table_id=table_id,
        stage=stage,
        position=position,
        action=action,
        action_type=action_type,
        amount=amount,
        pot_after=pot_after,
        community_cards=community_cards,
        agent_suggestion=agent_suggestion,
        agent_win_rate=agent_win_rate,
        agent_reasoning=agent_reasoning,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_actions_by_table(db: AsyncSession, table_id: int) -> List[GameAction]:
    result = await db.execute(
        select(GameAction)
        .where(GameAction.table_id == table_id)
        .order_by(GameAction.created_at)
    )
    return list(result.scalars().all())


async def get_actions_by_stage(db: AsyncSession, table_id: int, stage: str) -> List[GameAction]:
    result = await db.execute(
        select(GameAction)
        .where(GameAction.table_id == table_id, GameAction.stage == stage)
        .order_by(GameAction.created_at)
    )
    return list(result.scalars().all())
