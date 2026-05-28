"""牌桌 CRUD"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.table import GameTable
from typing import Optional


async def create_table(
    db: AsyncSession,
    user_id: int,
    num_players: int,
    my_position: str,
    my_hole_cards: str,
    my_stack: float = 1000.00,
    opponents_info: Optional[str] = None,
) -> GameTable:
    table = GameTable(
        user_id=user_id,
        num_players=num_players,
        my_position=my_position,
        my_hole_cards=my_hole_cards,
        my_stack=my_stack,
        opponents_info=opponents_info,
    )
    db.add(table)
    await db.flush()
    await db.refresh(table)
    return table


async def get_table_by_id(db: AsyncSession, table_id: int) -> Optional[GameTable]:
    result = await db.execute(select(GameTable).where(GameTable.id == table_id))
    return result.scalar_one_or_none()


async def get_table_by_id_and_user(db: AsyncSession, table_id: int, user_id: int) -> Optional[GameTable]:
    result = await db.execute(
        select(GameTable).where(GameTable.id == table_id, GameTable.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_table(db: AsyncSession, table: GameTable, **kwargs) -> GameTable:
    for key, value in kwargs.items():
        if hasattr(table, key):
            setattr(table, key, value)
    await db.flush()
    await db.refresh(table)
    return table
